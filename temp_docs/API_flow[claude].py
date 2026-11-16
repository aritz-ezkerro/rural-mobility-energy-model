#!/usr/bin/env python3
"""
=====================================================================
 FLUJOS DE TRÁFICO DE OPEN DATA EUSKADI POR MUNICIPIO  (script único)
=====================================================================
Municipios: Aramaio, Arratzua-Ubarrundia, Legutio, Zuia, Zigoitia, Urkabustaiz.
API: https://api.euskadi.eus/traffic/v1.0   (docs: opendata.euskadi.eus/api-traffic)

REQUISITOS
    Python 3 + librería requests (ya incluida en Anaconda).
    Ejecuta siempre desde la carpeta donde esté este archivo:
        python API_flow.py <modo> [opciones]

---------------------------------------------------------------------
 TUTORIAL: QUÉ HACE CADA MODO (en el orden recomendado)
---------------------------------------------------------------------

 1) meters   -> localizar los medidores de cada municipio
        python API_flow.py meters
    Busca medidores cerca de cada municipio y se queda con los que el API
    asigna a él. Imprime cuántos hay por municipio y sus IDs
    (provinceId, municipalityId). Genera:
        meters_municipios.csv / meters_municipios.json
    Si un municipio sale sin medidores, amplía el radio:  --km 15

 2) ids      -> ver qué municipios de una provincia tienen medidores
        python API_flow.py ids                 (provincia 1 = Álava)
        python API_flow.py ids --provincia 48  (Bizkaia)
    Recorre los IDs 1..99 y escribe nombre y nº de medidores. Útil para
    localizar municipios que no aparecen en el paso 1. Es lento (~100 consultas).

 3) cobertura -> CUÁNTOS DATOS HAY por municipio y año (para elegir el año)
        python API_flow.py cobertura                       (2010-2026)
        python API_flow.py cobertura --desde 2018 --hasta 2024
    No descarga datos: solo cuenta registros. Muestra por pantalla 4 tablas
    (municipio x año):
      - REGISTROS totales.
      - COBERTURA %: registros reales / registros esperados. Se supone 1
        registro por franja de 30 min y medidor => 48 x 365 = 17.520 al año
        (100 % = medidor sin huecos).
      - % DEL TOTAL: cada año como porcentaje de todos los registros del
        periodo (reparto de los datos entre años).
      - MEDIDORES con cobertura >= 80 %.
    Y resume el mejor año. Genera:
        cobertura_municipio_anio_<desde>_<hasta>.csv
        cobertura_medidor_anio_<desde>_<hasta>.csv   (detalle por medidor)

 4) probe    -> diagnóstico si algo no cuadra
        python API_flow.py probe
    Lista las fuentes del API y, por municipio, los flujos por año, por
    fechas recientes y por medidor. Úsalo solo para depurar.

 5) flows    -> DESCARGAR los flujos (franjas de 30 min, 20 registros/página)
        python API_flow.py flows --year 2023 --municipio zigoitia --max-pages 40   # prueba
        python API_flow.py flows --year 2023 --municipio zigoitia                  # un municipio
        python API_flow.py flows --year 2023                                       # todos
        python API_flow.py flows --year 2023 --month 10 --day 15                   # un día
    Descarga en paralelo (--workers 8 por defecto; baja a 4 si hay errores)
    y guarda un CSV por municipio:
        flujos_<municipio>_<periodo>.csv   (+ flujos_todos_<periodo>.csv)
    Columnas: meterDate, timeRank, meterId, sourceId, totalVehicles, speedAvg,
    occupancy, levelOfService, long_* (vehículos por longitud), vel_*
    (vehículos por velocidad), y descripción y coordenadas del medidor.
    ANTES de descargar un año completo, mira el tamaño con --max-pages 1
    (imprime "N elementos en M páginas").

---------------------------------------------------------------------
 FLUJO DE TRABAJO TÍPICO
---------------------------------------------------------------------
    meters  ->  cobertura  ->  elegir año  ->  flows --year AÑO

---------------------------------------------------------------------
 OPCIONES
---------------------------------------------------------------------
    --year / --month / --day   periodo a descargar (solo flows)
    --desde / --hasta          rango de años (solo cobertura; 2010-2026)
    --municipio TEXTO          descargar solo ese municipio (flows)
    --max-pages N              limitar páginas por municipio (pruebas)
    --km N                     radio de búsqueda de medidores (def. 8)
    --provincia N              provincia para el modo ids (def. 1)
    --workers N                peticiones simultáneas (def. 8)

---------------------------------------------------------------------
 NOTAS
---------------------------------------------------------------------
 - El API ignora _pageSize: siempre 20 registros por página.
 - Algunos años no tienen datos (en las pruebas, desde 2025 no hay flujos).
 - Si el servidor da errores 500 el script reintenta solo; si persisten,
   baja --workers.
 - MANUAL_IDS (más abajo) permite fijar a mano (provinceId, municipalityId).
"""
import argparse
import csv
import json
import os
import time
import unicodedata
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta

import requests

BASE = "https://api.euskadi.eus/traffic/v1.0"

MUNICIPIOS = {
    "Aramaio": ["aramaio"],
    "Arratzua-Ubarrundia": ["arratzua", "ubarrundia"],
    "Legutio": ["legutio", "legutiano"],
    "Zuia": ["zuia", "zuya"],
    "Zigoitia": ["zigoitia", "cigoitia"],
    "Urkabustaiz": ["urkabustaiz", "urcabustaiz"],
}

# Puntos aproximados (lat, lon) de cada municipio para buscar medidores cercanos
CENTROS = {
    "Aramaio": (43.04, -2.57),
    "Arratzua-Ubarrundia": (42.90, -2.63),
    "Legutio": (42.98, -2.63),
    "Zuia": (42.96, -2.87),
    "Zigoitia": (42.95, -2.78),
    "Urkabustaiz": (42.99, -2.94),
}

CACHE_MEDIDORES = "meters_municipios.json"
ESPERADO_ANUAL = 48 * 365  # franjas de 30 min en un año sin huecos (supuesto)
WORKERS = 8  # peticiones simultáneas (--workers)
PAGE_SIZE = None  # se rellena con --page-size (parámetro _pageSize del API, sin verificar)

# Rellenar a mano si hace falta: "Zuia": (provinceId, municipalityId)
MANUAL_IDS = {}


def norm(t):
    t = unicodedata.normalize("NFD", str(t))
    return "".join(c for c in t if unicodedata.category(c) != "Mn").lower()


def extraer_lista(data):
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for v in data.values():
            if isinstance(v, list):
                return v
    return []


def pedir(session, ruta, pagina, intentos=4, silencioso=False):
    """GET con reintentos si el servidor devuelve 5xx o se corta la conexión."""
    ultimo = None
    for i in range(intentos):
        try:
            params = {"_page": pagina}
            if PAGE_SIZE:
                params["_pageSize"] = PAGE_SIZE
            r = session.get(BASE + ruta, params=params, timeout=60)
            if r.status_code < 500:
                return r
            ultimo = f"HTTP {r.status_code}"
        except requests.RequestException as e:
            ultimo = str(e)
        if silencioso:
            return None
        time.sleep(2 * (i + 1))
    print(f"\n  AVISO: fallo persistente en {ruta} página {pagina} ({ultimo}); se omite")
    return None


def _lista_pagina(session, ruta, pagina):
    r = pedir(session, ruta, pagina)
    if r is None or r.status_code != 200:
        return None
    try:
        return extraer_lista(r.json())
    except ValueError:
        return None


def descargar(session, ruta, max_paginas=None):
    """Descarga todas las páginas (20 registros/página) pidiendo varias a la vez."""
    r = pedir(session, ruta, 1)
    if r is None:
        return []
    if r.status_code == 404:
        print(f"  HTTP 404 (sin datos o ruta inexistente): {r.text[:200]}")
        return []
    r.raise_for_status()
    data = r.json()
    lote = extraer_lista(data)
    if not lote:
        print(f"  respuesta vacía (HTTP {r.status_code}): {r.text[:200]}")
        return []
    total = int(data.get("totalPages", 1) or 1) if isinstance(data, dict) else 1
    if isinstance(data, dict):
        print(f"  {data.get('totalItems', '?')} elementos en {total} páginas")
    limite = min(total, max_paginas) if max_paginas else total

    paginas = {1: lote}
    pendientes = list(range(2, limite + 1))
    for _ in range(3):  # hasta 3 rondas para reintentar las páginas fallidas
        if not pendientes:
            break
        fallidas = []
        with ThreadPoolExecutor(max_workers=WORKERS) as ex:
            futuros = {ex.submit(_lista_pagina, session, ruta, p): p for p in pendientes}
            for fut in as_completed(futuros):
                p = futuros[fut]
                res = fut.result()
                if res is None:
                    fallidas.append(p)
                else:
                    paginas[p] = res
                print(f"  {len(paginas)}/{limite} páginas", end="\r")
        pendientes = fallidas
    if pendientes:
        print(f"\n  AVISO: {len(pendientes)} páginas sin descargar: {sorted(pendientes)[:20]}")
    print()
    resultados = []
    for p in sorted(paginas):
        resultados.extend(paginas[p])
    return resultados


def propiedades(registro):
    """En GeoJSON los datos están en 'properties'."""
    if isinstance(registro, dict) and isinstance(registro.get("properties"), dict):
        return registro["properties"]
    return registro


def municipio_de_medidor(props):
    texto = norm(props.get("municipality", ""))
    for nombre, variantes in MUNICIPIOS.items():
        if any(v in texto for v in variantes):
            return nombre
    return None


def guardar_csv(filas, ruta):
    columnas = list(dict.fromkeys(k for f in filas for k in f))
    with open(ruta, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=columnas)
        w.writeheader()
        w.writerows(filas)
    print(f"Guardado: {ruta} ({len(filas)} filas)")


def buscar_medidores(session, km):
    """Medidores de los municipios pedidos, buscando por ubicación."""
    encontrados = {}
    for muni, (lat, lon) in CENTROS.items():
        print(f"Buscando medidores cerca de {muni} ({km} km)...")
        for m in descargar(session, f"/meters/byLocation/{lat}/{lon}/{km}"):
            p = propiedades(m)
            nombre = municipio_de_medidor(p)
            if nombre and p.get("meterId") not in encontrados:
                encontrados[p["meterId"]] = {"municipio": nombre, **p}
    return list(encontrados.values())


def cmd_meters(session, km):
    medidores = buscar_medidores(session, km)
    if not medidores:
        print("No se han encontrado medidores. Prueba con --km 15 o --km 25.")
        return
    with open(CACHE_MEDIDORES, "w", encoding="utf-8") as f:
        json.dump(medidores, f, indent=2, ensure_ascii=False)
    guardar_csv(medidores, "meters_municipios.csv")

    resumen, ids = {}, {}
    for m in medidores:
        resumen[m["municipio"]] = resumen.get(m["municipio"], 0) + 1
        ids[m["municipio"]] = (m.get("provinceId"), m.get("municipalityId"))
    print("\nMedidores por municipio:", resumen)
    print("IDs (provinceId, municipalityId):", ids)
    faltan = [m for m in MUNICIPIOS if m not in resumen]
    if faltan:
        print("SIN medidores encontrados:", ", ".join(faltan), "-> prueba con --km 15")


def cmd_ids(session, provincia):
    """Escanea los IDs de municipio de una provincia y muestra su nombre."""
    print(f"Municipios con medidores en la provincia {provincia}:")
    for mid in range(1, 100):
        r = pedir(session, f"/meters/byMunicipality/{provincia}/{mid}", 1,
                  intentos=1, silencioso=True)
        if r is None or r.status_code != 200:
            continue
        try:
            data = r.json()
        except ValueError:
            continue
        feats = extraer_lista(data)
        if feats:
            p = propiedades(feats[0])
            print(f"  id {mid:>3}: {p.get('municipality')} "
                  f"({data.get('totalItems', '?')} medidores)")


def total_items(session, ruta, reintentar=False):
    """Devuelve totalItems de una ruta (o None si falla)."""
    r = pedir(session, ruta, 1, intentos=3 if reintentar else 1, silencioso=not reintentar)
    if r is None or r.status_code != 200:
        return None if r is None else f"HTTP {r.status_code}"
    try:
        return r.json().get("totalItems")
    except ValueError:
        return "no-JSON"


def cmd_probe(session, km):
    """Averigua en qué años/fechas/medidores hay datos de flujos."""
    medidores = cargar_medidores(session, km)
    ids = resolver_ids(medidores)

    print("\n=== FUENTES (sources) ===")
    r = pedir(session, "/sources", 1, intentos=1, silencioso=True)
    if r is not None and r.status_code == 200:
        print(r.text[:2000])

    hoy = date.today()
    fechas = [hoy - timedelta(days=d) for d in (1, 7, 30, 90, 180, 365)]
    for muni, (prov, mid) in ids.items():
        mm = [m for m in medidores if m["municipio"] == muni]
        print(f"\n=== {muni} (prov {prov}, mun {mid}) ===")
        print("  medidores por sourceId:", dict(Counter(m.get("sourceId") for m in mm)))
        print("  flujos por año:")
        for y in range(2015, hoy.year + 1):
            n = total_items(session, f"/flows/byYear/{y}/byMunicipality/{prov}/{mid}")
            print(f"    {y}: {n}")
        print("  flujos por fecha:")
        for f in fechas:
            n = total_items(
                session, f"/flows/byDate/{f.year}/{f.month}/{f.day}/byMunicipality/{prov}/{mid}")
            print(f"    {f}: {n}")
        print("  primeros medidores (flujos por año, por medidor):")
        for m in mm[:3]:
            res = {y: total_items(session, f"/flows/byYear/{y}/byMeter/{m['meterId']}")
                   for y in (2022, 2023, 2024, 2025, hoy.year)}
            print(f"    meter {m['meterId']} (source {m.get('sourceId')}): {res}")


def entero(v):
    return v if isinstance(v, int) else None


def cmd_cobertura(session, km, desde, hasta):
    """Tabla de registros de flujos por municipio y año, y por medidor y año."""
    medidores = cargar_medidores(session, km)
    ids = resolver_ids(medidores)
    anios = list(range(desde, hasta + 1))

    tareas = []
    for muni, (prov, mid) in ids.items():
        for y in anios:
            tareas.append(("muni", muni, None, y,
                           f"/flows/byYear/{y}/byMunicipality/{prov}/{mid}"))
        for m in medidores:
            if m["municipio"] == muni:
                for y in anios:
                    tareas.append(("meter", muni, m["meterId"], y,
                                   f"/flows/byYear/{y}/byMeter/{m['meterId']}"))
    print(f"{len(tareas)} consultas ({len(ids)} municipios, años {desde}-{hasta})...")

    res = {}
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(total_items, session, t[4], True): t for t in tareas}
        for i, fut in enumerate(as_completed(futs), 1):
            t = futs[fut]
            res[t[:4]] = entero(fut.result())
            print(f"  {i}/{len(tareas)}", end="\r")
    print()

    # --- tabla por medidor y año ---
    filas_med = []
    for muni in ids:
        for m in medidores:
            if m["municipio"] != muni:
                continue
            for y in anios:
                n = res.get(("meter", muni, m["meterId"], y))
                filas_med.append({
                    "municipio": muni, "meterId": m["meterId"],
                    "descripcion": m.get("description"),
                    "lat": m.get("latitude"), "lon": m.get("longitude"),
                    "anio": y, "registros": n,
                    "cobertura_pct": None if n is None else round(100 * n / ESPERADO_ANUAL, 1),
                })

    # --- tabla por municipio y año ---
    filas_mun = []
    for muni in ids:
        meds = [m for m in medidores if m["municipio"] == muni]
        for y in anios:
            n = res.get(("muni", muni, None, y))
            por_med = [f["registros"] for f in filas_med
                       if f["municipio"] == muni and f["anio"] == y]
            filas_mun.append({
                "municipio": muni, "anio": y, "n_medidores": len(meds),
                "registros": n,
                "esperados": len(meds) * ESPERADO_ANUAL,
                "cobertura_pct": None if n is None else round(
                    100 * n / (len(meds) * ESPERADO_ANUAL), 1),
                "medidores_con_datos": sum(1 for v in por_med if v),
                "medidores_cobertura_ge80": sum(
                    1 for v in por_med if v and v / ESPERADO_ANUAL >= 0.8),
            })

    # % del total de registros del periodo (por municipio y global)
    tot_muni = {m: sum(f["registros"] or 0 for f in filas_mun if f["municipio"] == m)
                for m in ids}
    tot_global = sum(tot_muni.values())
    for f in filas_mun:
        base_m = tot_muni[f["municipio"]]
        n = f["registros"]
        f["pct_del_total_municipio"] = (
            None if n is None or not base_m else round(100 * n / base_m, 1))
        f["pct_del_total_global"] = (
            None if n is None or not tot_global else round(100 * n / tot_global, 1))

    guardar_csv(filas_mun, f"cobertura_municipio_anio_{desde}_{hasta}.csv")
    guardar_csv(filas_med, f"cobertura_medidor_anio_{desde}_{hasta}.csv")

    # --- resumen en pantalla ---
    def get(muni, campo, y):
        return next(f[campo] for f in filas_mun if f["municipio"] == muni and f["anio"] == y)

    def cuadro(titulo, campo, fmt, total):
        print(f"\n{titulo}")
        print(f"{'municipio':<20}" + "".join(f"{y:>9}" for y in anios))
        for muni in ids:
            linea = f"{muni:<20}"
            for y in anios:
                v = get(muni, campo, y)
                linea += f"{'-' if v is None else fmt(v):>9}"
            print(linea)
        tt = {y: total(y) for y in anios}
        print(f"{'TOTAL':<20}" + "".join(
            f"{('-' if tt[y] is None else fmt(tt[y])):>9}" for y in anios))
        return tt

    miles = lambda v: f"{v:,}".replace(",", ".")
    pct = lambda v: f"{v:.1f}%"

    def suma(campo):
        return lambda y: sum(get(m, campo, y) or 0 for m in ids)

    def cobertura_global(y):
        esp = sum(get(m, "esperados", y) for m in ids)
        return round(100 * suma("registros")(y) / esp, 1) if esp else None

    def pct_global(y):
        return round(100 * suma("registros")(y) / tot_global, 1) if tot_global else None

    tot_reg = cuadro("1) REGISTROS por municipio y año:", "registros", miles, suma("registros"))
    tot_cob = cuadro("2) COBERTURA % (registros reales / esperados, 100 % = sin huecos):",
                     "cobertura_pct", pct, cobertura_global)
    cuadro("3) % DEL TOTAL de registros del periodo (fila municipio: sobre su propio total;"
           " TOTAL: sobre el total global):", "pct_del_total_municipio", pct, pct_global)
    tot_ok = cuadro("4) MEDIDORES con cobertura >= 80 %:", "medidores_cobertura_ge80",
                    str, suma("medidores_cobertura_ge80"))

    mejor = max(anios, key=lambda y: tot_reg[y])
    mejor_cob = max(anios, key=lambda y: tot_cob[y] or 0)
    mejor_ok = max(anios, key=lambda y: tot_ok[y])
    print(f"\nTotal de registros en {desde}-{hasta}: {miles(tot_global)}")
    print(f"Año con más registros:                 {mejor} ({miles(tot_reg[mejor])};"
          f" {pct_global(mejor)} % del total)")
    print(f"Año con mayor cobertura global:        {mejor_cob} ({tot_cob[mejor_cob]} %)")
    print(f"Año con más medidores bien cubiertos:  {mejor_ok} ({tot_ok[mejor_ok]} medidores)")


def cargar_medidores(session, km):
    if os.path.exists(CACHE_MEDIDORES):
        with open(CACHE_MEDIDORES, encoding="utf-8") as f:
            return json.load(f)
    return buscar_medidores(session, km)


def resolver_ids(medidores):
    ids = {}
    for m in medidores:
        if m["municipio"] not in ids and m.get("municipalityId"):
            ids[m["municipio"]] = (m.get("provinceId"), m["municipalityId"])
    ids.update(MANUAL_IDS)
    return ids


def aplanar_flujo(fl):
    """Una fila por Flow, con los intervalos de longitud y velocidad en columnas."""
    fl = propiedades(fl)
    fila = {
        "meterDate": fl.get("meterDate"),
        "timeRank": fl.get("timeRank"),
        "meterId": fl.get("meterId"),
        "sourceId": fl.get("sourceId"),
        "totalVehicles": fl.get("totalVehicles"),
        "speedAvg": fl.get("speedAvg"),
        "occupancy": fl.get("occupancy"),
        "levelOfService": fl.get("levelOfService"),
    }
    for it in fl.get("lengthIntervals") or []:
        nombre = it.get("lengthInterval") or f"{it.get('lengthMin')}-{it.get('lengthMax')}"
        fila[f"long_{nombre}"] = it.get("vehicles")
    for it in fl.get("speedIntervals") or []:
        nombre = it.get("speedInterval") or f"{it.get('speedMin')}-{it.get('speedMax')}"
        fila[f"vel_{nombre}"] = it.get("vehicles")
    return fila


def ruta_flujos(year, month, day, prov, muni):
    if day and month:
        return f"/flows/byDate/{year}/{month}/{day}/byMunicipality/{prov}/{muni}"
    if month:
        return f"/flows/byMonth/{year}/{month}/byMunicipality/{prov}/{muni}"
    return f"/flows/byYear/{year}/byMunicipality/{prov}/{muni}"


def cmd_flows(session, year, month, day, km, max_paginas, solo=None):
    medidores = cargar_medidores(session, km)
    ids = resolver_ids(medidores)
    if solo:
        ids = {m: v for m, v in ids.items() if norm(solo) in norm(m)}
    else:
        faltan = [m for m in MUNICIPIOS if m not in ids]
        if faltan:
            print("Sin ID de municipio para:", ", ".join(faltan), "(se omiten)")
    if not ids:
        print("Ningún municipio que descargar (revisa --municipio).")
        return
    info_medidor = {m["meterId"]: m for m in medidores}
    periodo = "_".join(str(x) for x in (year, month, day) if x)

    todos = []
    for muni, (prov, mid) in ids.items():
        ruta = ruta_flujos(year, month, day, prov, mid)
        print(f"{muni}: {ruta}")
        flujos = descargar(session, ruta, max_paginas)
        print(f"  -> {len(flujos)} registros descargados")
        filas = []
        for fl in flujos:
            fila = aplanar_flujo(fl)
            med = info_medidor.get(fila["meterId"], {})
            filas.append({
                "municipio": muni,
                **fila,
                "meter_desc": med.get("description"),
                "meter_lat": med.get("latitude"),
                "meter_lon": med.get("longitude"),
            })
        if filas:
            slug = norm(muni).replace("-", "_")
            guardar_csv(filas, f"flujos_{slug}_{periodo}.csv")  # un archivo por municipio
            todos.extend(filas)
    if len(ids) > 1 and todos:
        guardar_csv(todos, f"flujos_todos_{periodo}.csv")
    elif not todos:
        print("No se han obtenido flujos.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("modo", choices=["ids", "meters", "probe", "cobertura", "flows"])
    ap.add_argument("--provincia", type=int, default=1, help="solo para el modo ids")
    ap.add_argument("--year", type=int, default=2025)
    ap.add_argument("--month", type=int)
    ap.add_argument("--day", type=int)
    ap.add_argument("--km", type=int, default=8, help="radio de búsqueda de medidores")
    ap.add_argument("--max-pages", type=int, help="limitar páginas por municipio (pruebas)")
    ap.add_argument("--page-size", type=int, help="registros por página (_pageSize)")
    ap.add_argument("--desde", type=int, default=2010, help="año inicial (cobertura)")
    ap.add_argument("--hasta", type=int, default=2026, help="año final (cobertura)")
    ap.add_argument("--workers", type=int, default=8, help="peticiones simultáneas")
    ap.add_argument("--municipio", help="descargar solo este municipio (ej. zigoitia)")
    args = ap.parse_args()

    global PAGE_SIZE, WORKERS
    PAGE_SIZE = args.page_size
    WORKERS = max(1, args.workers)

    s = requests.Session()
    s.headers["Accept"] = "*/*"  # el API devuelve application/geo+json en medidores
    if args.modo == "ids":
        cmd_ids(s, args.provincia)
    elif args.modo == "cobertura":
        cmd_cobertura(s, args.km, args.desde, args.hasta)
    elif args.modo == "probe":
        cmd_probe(s, args.km)
    elif args.modo == "meters":
        cmd_meters(s, args.km)
    else:
        cmd_flows(s, args.year, args.month, args.day, args.km, args.max_pages,
                  args.municipio)

if __name__ == "__main__":
    main()