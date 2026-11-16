#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Open Data Euskadi - inventario de sensores y flujos de tráfico por municipio.

Municipios objetivo:
  Aramaio, Arratzua-Ubarrundia, Legutio, Zuia, Zigoitia y Urkabustaiz.

Instalación:
  python -m pip install requests

Ejemplos:
  python API_flow.py meters --refresh
  python API_flow.py ids --provincia 1 --max-municipality-id 200
  python API_flow.py cobertura --desde 2018 --hasta 2024
  python API_flow.py probe
  python API_flow.py flows --year 2023 --municipio Zigoitia --max-pages 2
  python API_flow.py flows --year 2023 --municipio Zigoitia
  python API_flow.py flows --year 2023
  python API_flow.py flows --year 2023 --month 10
  python API_flow.py flows --year 2023 --month 10 --day 15

Notas:
- El inventario usa /meters/byMunicipality/{provinceId}/{municipalityId}.
- El descubrimiento de IDs recorre un rango configurable. No garantiza encontrar
  IDs superiores a --max-municipality-id; revisa el resultado de "ids".
- La caché meters_municipios.json se reutiliza salvo que uses --refresh.
- El API puede limitar o cambiar su paginación. El script informa de páginas fallidas.
"""
from __future__ import annotations

import argparse
import calendar
import csv
import json
import logging
import os
import re
import sys
import time
import unicodedata
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE = "https://api.euskadi.eus/traffic/v1.0"
CACHE_MEDIDORES = "meters_municipios.json"
WORKERS = 6
PAGE_SIZE = None
TIMEOUT = (10, 60)

MUNICIPIOS = {
    "Aramaio": ["aramaio"],
    "Arratzua-Ubarrundia": ["arratzua", "ubarrundia"],
    "Legutio": ["legutio", "legutiano"],
    "Zuia": ["zuia", "zuya"],
    "Zigoitia": ["zigoitia", "cigoitia"],
    "Urkabustaiz": ["urkabustaiz", "urcabustaiz"],
}

# Códigos municipales INE de los seis municipios objetivo.
# Formato INE: 01XXX = provincia 01 (Álava) + código municipal de 3 dígitos.
# El endpoint de la API recibe provincia y municipio por separado:
# /meters/byMunicipality/{provinceId}/{municipalityId}
CODIGOS_MUNICIPALES = {
    "Aramaio": "01003",
    "Arratzua-Ubarrundia": "01008",
    "Legutio": "01058",
    "Zuia": "01063",
    "Zigoitia": "01018",
    "Urkabustaiz": "01054",
}

MANUAL_IDS: dict[str, tuple[int, int]] = {
    nombre: (int(codigo[:2]), int(codigo[2:]))
    for nombre, codigo in CODIGOS_MUNICIPALES.items()
}


def normalizar(valor: Any) -> str:
    texto = unicodedata.normalize("NFD", str(valor or ""))
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]", "", texto.lower())


def extraer_lista(data: Any) -> list:
    """Admite listas directas y formatos habituales de respuestas paginadas."""
    if isinstance(data, list):
        return data
    if not isinstance(data, dict):
        return []
    for clave in ("features", "items", "results", "data", "meters", "flows"):
        valor = data.get(clave)
        if isinstance(valor, list):
            return valor
    # Compatibilidad con respuestas cuyo nombre de colección varía.
    for valor in data.values():
        if isinstance(valor, list):
            return valor
    return []


def propiedades(registro: Any) -> dict:
    if not isinstance(registro, dict):
        return {}
    props = registro.get("properties")
    return props if isinstance(props, dict) else registro


def nombre_municipio(props: dict) -> str | None:
    texto = normalizar(props.get("municipality") or props.get("municipalityName"))
    if not texto:
        return None
    for nombre, variantes in MUNICIPIOS.items():
        if any(normalizar(v) in texto for v in variantes):
            return nombre
    return None


def configurar_sesion() -> requests.Session:
    sesion = requests.Session()
    reintentos = Retry(
        total=5,
        connect=5,
        read=5,
        status=5,
        backoff_factor=1.0,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["GET"]),
        respect_retry_after_header=True,
    )
    adaptador = HTTPAdapter(max_retries=reintentos, pool_connections=WORKERS,
                            pool_maxsize=WORKERS)
    sesion.mount("https://", adaptador)
    sesion.mount("http://", adaptador)
    sesion.headers.update({"Accept": "application/json, application/geo+json, */*",
                           "User-Agent": "API-flow-Euskadi/2.0"})
    return sesion


def pedir(sesion: requests.Session, ruta: str, pagina: int = 1,
          silencioso: bool = False) -> requests.Response | None:
    params = {"_page": pagina}
    if PAGE_SIZE:
        params["_pageSize"] = PAGE_SIZE
    try:
        respuesta = sesion.get(BASE + ruta, params=params, timeout=TIMEOUT)
        if respuesta.status_code == 404 and silencioso:
            return None
        if respuesta.status_code >= 400:
            if silencioso:
                return None
            respuesta.raise_for_status()
        return respuesta
    except requests.RequestException as exc:
        if not silencioso:
            logging.warning("Error consultando %s (página %s): %s", ruta, pagina, exc)
        return None


def descargar(sesion: requests.Session, ruta: str,
              max_paginas: int | None = None) -> list:
    """Descarga las páginas de forma secuencial para evitar compartir Session."""
    primera = pedir(sesion, ruta, 1)
    if primera is None:
        return []
    if primera.status_code == 404:
        logging.info("Ruta sin datos (404): %s", ruta)
        return []
    try:
        data = primera.json()
    except ValueError:
        logging.warning("Respuesta no JSON en %s", ruta)
        return []

    resultados = extraer_lista(data)
    total_paginas = 1
    if isinstance(data, dict):
        try:
            total_paginas = max(1, int(data.get("totalPages") or 1))
        except (TypeError, ValueError):
            total_paginas = 1
        logging.info("%s: %s elementos, %s páginas",
                     ruta, data.get("totalItems", "?"), total_paginas)

    limite = min(total_paginas, max_paginas) if max_paginas else total_paginas
    fallidas = []
    for pagina in range(2, limite + 1):
        respuesta = pedir(sesion, ruta, pagina)
        if respuesta is None:
            fallidas.append(pagina)
            continue
        try:
            resultados.extend(extraer_lista(respuesta.json()))
        except ValueError:
            fallidas.append(pagina)
        if pagina % 10 == 0 or pagina == limite:
            print(f"  páginas: {pagina}/{limite}", end="\r", flush=True)

    if limite > 1:
        print()
    if fallidas:
        logging.warning("%s páginas no descargadas en %s: %s",
                        len(fallidas), ruta, fallidas)
    if max_paginas and total_paginas > max_paginas:
        logging.warning("Descarga limitada a %s de %s páginas.", max_paginas,
                        total_paginas)
    return resultados


def guardar_json(datos: Any, ruta: str) -> None:
    with open(ruta, "w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, ensure_ascii=False, indent=2)


def guardar_csv(filas: list[dict], ruta: str) -> None:
    if not filas:
        logging.warning("No se crea %s: no hay filas.", ruta)
        return
    columnas = list(dict.fromkeys(k for fila in filas for k in fila))
    with open(ruta, "w", newline="", encoding="utf-8-sig") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=columnas, extrasaction="ignore")
        escritor.writeheader()
        escritor.writerows(filas)
    print(f"Guardado: {ruta} ({len(filas)} filas)")


def descubrir_ids_municipios(sesion: requests.Session, provincia: int,
                             max_id: int) -> dict[str, tuple[int, int]]:
    """Busca IDs de municipio que devuelvan sensores y reconoce los seis objetivos."""
    encontrados = {}
    print(f"Explorando IDs municipales 1..{max_id} de la provincia {provincia}...")
    for mid in range(1, max_id + 1):
        ruta = f"/meters/byMunicipality/{provincia}/{mid}"
        respuesta = pedir(sesion, ruta, 1, silencioso=True)
        if respuesta is None or respuesta.status_code != 200:
            continue
        try:
            data = respuesta.json()
            elementos = extraer_lista(data)
        except ValueError:
            continue
        if not elementos:
            continue
        props = propiedades(elementos[0])
        muni = nombre_municipio(props)
        nombre_api = props.get("municipality") or props.get("municipalityName") or "?"
        print(f"  ID {mid}: {nombre_api} ({data.get('totalItems', len(elementos))} sensores)")
        if muni:
            encontrados[muni] = (provincia, mid)
    encontrados.update(MANUAL_IDS)
    return encontrados


def obtener_inventario(sesion: requests.Session, provincia: int,
                       max_id: int) -> list[dict]:
    ids = descubrir_ids_municipios(sesion, provincia, max_id)
    inventario = {}
    for muni, (prov, mid) in ids.items():
        ruta = f"/meters/byMunicipality/{prov}/{mid}"
        print(f"\nDescargando sensores de {muni}...")
        registros = descargar(sesion, ruta)
        for registro in registros:
            props = propiedades(registro)
            meter_id = props.get("meterId")
            if meter_id is None:
                continue
            fila = dict(props)
            fila["municipio"] = muni
            # Coordenadas: se conservan las que entregue el API.
            geom = registro.get("geometry") if isinstance(registro, dict) else None
            if isinstance(geom, dict) and geom.get("type") == "Point":
                coords = geom.get("coordinates") or []
                if len(coords) >= 2:
                    fila.setdefault("longitude", coords[0])
                    fila.setdefault("latitude", coords[1])
            fila["latitude"] = fila.get("latitude", fila.get("lat"))
            fila["longitude"] = fila.get("longitude", fila.get("lon", fila.get("lng")))
            inventario[str(meter_id)] = fila
        print(f"  sensores recibidos: {len(registros)}")
    return list(inventario.values())


def cargar_medidores(sesion: requests.Session, provincia: int,
                     max_id: int, refresh: bool = False) -> list[dict]:
    if not refresh and os.path.exists(CACHE_MEDIDORES):
        try:
            with open(CACHE_MEDIDORES, encoding="utf-8") as archivo:
                datos = json.load(archivo)
            if isinstance(datos, list) and datos:
                print(f"Inventario leído de caché: {CACHE_MEDIDORES} ({len(datos)} sensores)")
                return datos
        except (OSError, json.JSONDecodeError):
            logging.warning("Caché ilegible; se volverá a descargar.")
    datos = obtener_inventario(sesion, provincia, max_id)
    if datos:
        guardar_json(datos, CACHE_MEDIDORES)
        guardar_csv(datos, "meters_municipios.csv")
        coordenadas = [m for m in datos
                       if m.get("latitude") is not None and m.get("longitude") is not None]
        guardar_csv(coordenadas, "coordenadas_todos_los_sensores.csv")
        sin_coords = len(datos) - len(coordenadas)
        print(f"\nInventario total: {len(datos)}; con coordenadas: {len(coordenadas)}; "
              f"sin coordenadas: {sin_coords}")
    else:
        logging.error("No se encontró ningún sensor. Revisa provincia/IDs/API.")
    return datos


def resolver_ids(medidores: list[dict], provincia: int,
                 max_id: int) -> dict[str, tuple[int, int]]:
    ids = {}
    for m in medidores:
        muni = m.get("municipio")
        prov, mid = m.get("provinceId"), m.get("municipalityId")
        if muni and prov is not None and mid is not None:
            ids.setdefault(muni, (int(prov), int(mid)))
    ids.update(MANUAL_IDS)
    return ids


def cmd_meters(sesion, args):
    datos = cargar_medidores(sesion, args.provincia, args.max_municipality_id,
                             refresh=args.refresh)
    resumen = Counter(m.get("municipio", "Sin municipio") for m in datos)
    print("\nSensores por municipio:")
    for muni in MUNICIPIOS:
        print(f"  {muni}: {resumen.get(muni, 0)}")
    no_encontrados = [m for m in MUNICIPIOS if not resumen.get(m)]
    if no_encontrados:
        print("Sin sensores reconocidos:", ", ".join(no_encontrados))
        print("Comprueba los IDs con: python API_flow.py ids --provincia "
              f"{args.provincia} --max-municipality-id {args.max_municipality_id}")


def cmd_ids(sesion, args):
    ids = descubrir_ids_municipios(sesion, args.provincia, args.max_municipality_id)
    print("\nCoincidencias con municipios objetivo:")
    for muni, (prov, mid) in ids.items():
        print(f"  {muni}: provinceId={prov}, municipalityId={mid}")


def total_items(sesion, ruta: str):
    respuesta = pedir(sesion, ruta, 1, silencioso=True)
    if respuesta is None or respuesta.status_code != 200:
        return None
    try:
        data = respuesta.json()
        return data.get("totalItems") if isinstance(data, dict) else len(extraer_lista(data))
    except ValueError:
        return None


def cmd_probe(sesion, args):
    medidores = cargar_medidores(sesion, args.provincia,
                                 args.max_municipality_id, args.refresh)
    ids = resolver_ids(medidores, args.provincia, args.max_municipality_id)
    print("\n=== FUENTES ===")
    respuesta = pedir(sesion, "/sources", 1, silencioso=True)
    if respuesta is not None:
        print(respuesta.text[:3000])
    hoy = date.today()
    fechas = [hoy - timedelta(days=d) for d in (1, 7, 30, 90, 180, 365)]
    for muni, (prov, mid) in ids.items():
        sensores = [m for m in medidores if m.get("municipio") == muni]
        print(f"\n=== {muni} (provincia {prov}, municipio {mid}) ===")
        print("Sensores:", len(sensores),
              "| sourceId:", dict(Counter(m.get("sourceId") for m in sensores)))
        for anio in range(max(2010, hoy.year - 10), hoy.year + 1):
            n = total_items(sesion, f"/flows/byYear/{anio}/byMunicipality/{prov}/{mid}")
            print(f"  año {anio}: {n}")
        for fecha in fechas:
            ruta = (f"/flows/byDate/{fecha.year}/{fecha.month}/{fecha.day}"
                    f"/byMunicipality/{prov}/{mid}")
            print(f"  fecha {fecha}: {total_items(sesion, ruta)}")


def esperado_anual(anio: int) -> int:
    return 48 * (366 if calendar.isleap(anio) else 365)


def cmd_cobertura(sesion, args):
    medidores = cargar_medidores(sesion, args.provincia,
                                 args.max_municipality_id, args.refresh)
    ids = resolver_ids(medidores, args.provincia, args.max_municipality_id)
    anios = range(args.desde, args.hasta + 1)
    tareas = []
    for muni, (prov, mid) in ids.items():
        for anio in anios:
            tareas.append(("municipio", muni, None, anio,
                           f"/flows/byYear/{anio}/byMunicipality/{prov}/{mid}"))
        for med in medidores:
            if med.get("municipio") == muni:
                for anio in anios:
                    tareas.append(("sensor", muni, med.get("meterId"), anio,
                                   f"/flows/byYear/{anio}/byMeter/{med.get('meterId')}"))
    print(f"Consultas de cobertura: {len(tareas)}")
    resultados = {}
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futuros = {pool.submit(total_items, sesion, t[4]): t for t in tareas}
        for i, futuro in enumerate(as_completed(futuros), 1):
            tipo, muni, meter_id, anio, _ = futuros[futuro]
            try:
                resultados[(tipo, muni, meter_id, anio)] = futuro.result()
            except Exception as exc:
                logging.warning("Fallo de consulta: %s", exc)
                resultados[(tipo, muni, meter_id, anio)] = None
            if i % 20 == 0 or i == len(tareas):
                print(f"  {i}/{len(tareas)}", end="\r", flush=True)
    print()

    filas_municipio, filas_sensor = [], []
    for muni in ids:
        sensores = [m for m in medidores if m.get("municipio") == muni]
        for anio in anios:
            n = resultados.get(("municipio", muni, None, anio))
            esperado = len(sensores) * esperado_anual(anio)
            sensores_ok = []
            for med in sensores:
                nm = resultados.get(("sensor", muni, med.get("meterId"), anio))
                if nm is not None and nm > 0:
                    sensores_ok.append(nm)
                filas_sensor.append({
                    "municipio": muni, "meterId": med.get("meterId"),
                    "descripcion": med.get("description"),
                    "lat": med.get("latitude"), "lon": med.get("longitude"),
                    "anio": anio, "registros": nm,
                    "cobertura_pct": (round(100 * nm / esperado_anual(anio), 1)
                                      if nm is not None else None),
                })
            filas_municipio.append({
                "municipio": muni, "anio": anio, "n_sensores": len(sensores),
                "registros": n, "esperados": esperado,
                "cobertura_pct": (round(100 * n / esperado, 1)
                                  if n is not None and esperado else None),
                "sensores_con_datos": len(sensores_ok),
                "sensores_cobertura_ge80": sum(
                    1 for v in sensores_ok if v / esperado_anual(anio) >= .8),
            })

    guardar_csv(filas_municipio,
                f"cobertura_municipio_anio_{args.desde}_{args.hasta}.csv")
    guardar_csv(filas_sensor,
                f"cobertura_medidor_anio_{args.desde}_{args.hasta}.csv")
    print("\nResumen de registros por municipio y año:")
    for fila in filas_municipio:
        print(f"  {fila['municipio']:<22} {fila['anio']}: "
              f"{fila['registros']} registros; cobertura {fila['cobertura_pct']}%")


def aplanar_flujo(registro: dict) -> dict:
    fl = propiedades(registro)
    fila = {k: fl.get(k) for k in (
        "meterDate", "timeRank", "meterId", "sourceId", "totalVehicles",
        "speedAvg", "occupancy", "levelOfService"
    )}
    for item in fl.get("lengthIntervals") or []:
        nombre = item.get("lengthInterval") or (
            f"{item.get('lengthMin')}-{item.get('lengthMax')}")
        fila[f"long_{nombre}"] = item.get("vehicles")
    for item in fl.get("speedIntervals") or []:
        nombre = item.get("speedInterval") or (
            f"{item.get('speedMin')}-{item.get('speedMax')}")
        fila[f"vel_{nombre}"] = item.get("vehicles")
    return fila


def ruta_flujos(anio: int, mes: int | None, dia: int | None,
                provincia: int, municipio_id: int) -> str:
    if mes and dia:
        return (f"/flows/byDate/{anio}/{mes}/{dia}"
                f"/byMunicipality/{provincia}/{municipio_id}")
    if mes:
        return (f"/flows/byMonth/{anio}/{mes}"
                f"/byMunicipality/{provincia}/{municipio_id}")
    return f"/flows/byYear/{anio}/byMunicipality/{provincia}/{municipio_id}"


def cmd_flows(sesion, args):
    medidores = cargar_medidores(sesion, args.provincia,
                                 args.max_municipality_id, args.refresh)
    ids = resolver_ids(medidores, args.provincia, args.max_municipality_id)
    if args.municipio:
        buscado = normalizar(args.municipio)
        ids = {k: v for k, v in ids.items() if buscado in normalizar(k)}
    if not ids:
        logging.error("No hay municipios seleccionados. Revisa el inventario y los IDs.")
        return

    info_sensor = {str(m.get("meterId")): m for m in medidores}
    periodo = "_".join(str(v) for v in (args.year, args.month, args.day) if v)
    todas_filas = []
    for muni, (prov, mid) in ids.items():
        ruta = ruta_flujos(args.year, args.month, args.day, prov, mid)
        print(f"\n{muni}: {ruta}")
        flujos = descargar(sesion, ruta, args.max_pages)
        filas = []
        for flujo in flujos:
            fila = aplanar_flujo(flujo)
            sensor = info_sensor.get(str(fila.get("meterId")), {})
            filas.append({
                "municipio": muni, **fila,
                "meter_desc": sensor.get("description"),
                "meter_lat": sensor.get("latitude"),
                "meter_lon": sensor.get("longitude"),
            })
        print(f"Registros recibidos: {len(filas)}")
        if filas:
            slug = normalizar(muni)
            guardar_csv(filas, f"flujos_{slug}_{periodo}.csv")
            todas_filas.extend(filas)
    if todas_filas:
        guardar_csv(todas_filas, f"flujos_todos_{periodo}.csv")
    else:
        print("No se han descargado registros. Comprueba año, municipio y disponibilidad.")


def construir_parser():
    parser = argparse.ArgumentParser(
        description="Descarga inventario de sensores y flujos de tráfico de Open Data Euskadi."
    )
    parser.add_argument("modo", choices=["meters", "ids", "probe", "cobertura", "flows"])
    parser.add_argument("--provincia", type=int, default=1,
                        help="ID de provincia; 1 suele corresponder a Álava")
    parser.add_argument("--max-municipality-id", type=int, default=200,
                        help="último ID municipal que se explora (default: 200)")
    parser.add_argument("--refresh", action="store_true",
                        help="ignorar caché y volver a descargar el inventario")
    parser.add_argument("--year", type=int, default=2023)
    parser.add_argument("--month", type=int)
    parser.add_argument("--day", type=int)
    parser.add_argument("--km", type=float, default=8,
                        help="conservado por compatibilidad; el inventario municipal no usa radio")
    parser.add_argument("--max-pages", type=int,
                        help="limitar páginas para pruebas")
    parser.add_argument("--page-size", type=int,
                        help="parámetro _pageSize si el API lo admite")
    parser.add_argument("--desde", type=int, default=2010)
    parser.add_argument("--hasta", type=int, default=2026)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--municipio", help="filtrar municipio, por ejemplo Zigoitia")
    return parser


def main():
    global WORKERS, PAGE_SIZE
    args = construir_parser().parse_args()
    if args.month is not None and not 1 <= args.month <= 12:
        raise SystemExit("--month debe estar entre 1 y 12")
    if args.day is not None:
        if args.month is None:
            raise SystemExit("--day requiere --month")
        try:
            date(args.year, args.month, args.day)
        except ValueError as exc:
            raise SystemExit(str(exc))
    if args.desde > args.hasta:
        raise SystemExit("--desde no puede ser mayor que --hasta")
    if args.max_municipality_id < 1:
        raise SystemExit("--max-municipality-id debe ser positivo")
    WORKERS = max(1, args.workers)
    PAGE_SIZE = args.page_size

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    sesion = configurar_sesion()
    try:
        if args.modo == "ids":
            cmd_ids(sesion, args)
        elif args.modo == "meters":
            cmd_meters(sesion, args)
        elif args.modo == "probe":
            cmd_probe(sesion, args)
        elif args.modo == "cobertura":
            cmd_cobertura(sesion, args)
        elif args.modo == "flows":
            cmd_flows(sesion, args)
    finally:
        sesion.close()


if __name__ == "__main__":
    main()


# EN ANACONDA PROMPT
# cd C:\Users\Public\Documentos\aritz-ezkerro\rural-mobility-energy-model\rural-mobility-energy-model\temp_docs
# python -m pip install requests

# python API_flow.py meters --refresh
# python API_flow.py ids --provincia 1 --max-municipality-id 200
# python API_flow.py cobertura --desde 2018 --hasta 2024
# python API_flow.py flows --year 2023 --municipio Zigoitia --max-pages 2
# python API_flow.py flows --year 2023 --municipio Zigoitia
# python API_flow.py flows --year 2023
# 
