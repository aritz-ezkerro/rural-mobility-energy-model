#!/usr/bin/env python
# -*- coding: utf-8 -*-

r"""
Downloads traffic sensors (meters) from Open Data Euskadi
and keeps only those belonging to the 24 selected municipalities.

The /meters endpoints return GeoJSON (application/geo+json), which is why
the Accept header is mandatory: with application/json the server returns 500.

Strategy: download by province (3 paginated queries) and filter
by municipalityId, instead of querying municipality by municipality.

The 24 municipalities are those bordering the case study (Gorbeialdea).
This is a preliminary step: this inventory is later filtered in Excel to
keep only the sensors of interest.

Location: C:\Users\Public\Documentos\aritz-ezkerro\rural-mobility-energy-model\rural-mobility-energy-model\src\gorbiealdea\m1_energy_graph\sensor_coord.py

Output (relative to the repository root):
    docs/sensors_coord/sensors_coord.csv
    docs/sensors_coord/sensors_coord_summary.csv  (sensors per municipality, including 0)
    docs/sensors_coord_errors.txt                 (if there are errors)
"""

import csv
import json
import time
import argparse
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


BASE_URL = "https://api.euskadi.eus/traffic/v1.0"
# This script lives in <root>/src/gorbiealdea/m1_energy_graph/, so the repository
# root is 3 levels above. Thus, outputs always land in
# <root>/docs/, regardless of which folder it is executed from.
REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS_DIR = REPO_ROOT / "docs"
OUTPUT_FILE = DOCS_DIR / "sensors_coord" / "sensors_coord.csv"
SUMMARY_FILE = DOCS_DIR / "sensors_coord" / "sensors_coord_summary.csv"
ERROR_FILE = DOCS_DIR / "sensors_coord_errors.txt"

MAX_PAGES = 1000  # safety cap

# INE Code: 2 digits for province + 3 for municipality.
MUNICIPALITIES = [
    ("Amurrio", "01002"),
    ("Aramaio", "01003"),
    ("Arratzua-Ubarrundia", "01008"),
    ("Barrundia", "01013"),
    ("Zigoitia", "01018"),
    ("Kuartango", "01020"),
    ("Elburgo/Burgelu", "01021"),
    ("Urkabustaiz", "01054"),
    ("Legutio", "01058"),
    ("Vitoria-Gasteiz", "01059"),
    ("Zuia", "01063"),
    ("Aretxabaleta", "20013"),
    ("Eskoriatza", "20034"),
    ("Arrasate/Mondragon", "20055"),
    ("Leintz-Gatzaga", "20068"),
    ("Abadino", "48001"),
    ("Zeanuri", "48024"),
    ("Dima", "48026"),
    ("Elorrio", "48032"),
    ("Otxandio", "48072"),
    ("Urduna/Orduna", "48074"),
    ("Orozko", "48075"),
    ("Ubide", "48088"),
    ("Atxondo", "48091"),
]

# INE prefix -> API provinceId (NORA code).
PROVINCE_IDS = {"01": 1, "20": 20, "48": 48}


def create_session():
    """HTTP session with retries and geo+json header."""

    retry_args = dict(
        total=4,
        connect=4,
        read=4,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        raise_on_status=False,
    )

    try:
        retry = Retry(allowed_methods=["GET"], **retry_args)
    except TypeError:  # urllib3 < 1.26
        retry = Retry(method_whitelist=["GET"], **retry_args)

    session = requests.Session()
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    session.headers.update({
        # Key: the "meters" endpoint produces application/geo+json
        "Accept": "application/geo+json, application/json;q=0.5",
        "User-Agent": "sensor-coord-downloader/1.1",
    })

    return session


def to_int(value):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def extract_features(data):
    """Extracts the list of features/sensors from the response."""

    if isinstance(data, list):
        return data

    if not isinstance(data, dict):
        return []

    for key in ("features", "meters", "items", "results", "data", "content"):
        if isinstance(data.get(key), list):
            return data[key]

    return []


def get_total_pages(data):
    """Total pages, or None if the response does not specify it."""

    if isinstance(data, dict) and "totalPages" in data:
        try:
            return max(1, int(data["totalPages"]))
        except (TypeError, ValueError):
            return None

    return None


def flatten_feature(feature):
    """Flattens a GeoJSON feature: properties + geometry coordinates."""

    if not isinstance(feature, dict):
        return None

    if "properties" not in feature and "geometry" not in feature:
        return dict(feature)  # already flat

    record = dict(feature.get("properties") or {})

    geometry = feature.get("geometry") or {}
    coords = geometry.get("coordinates")

    record["geometry_type"] = geometry.get("type", "")

    # GeoJSON: [longitude, latitude]. Geometry takes precedence over latitude/longitude
    # in properties (the API documentation shows them swapped).
    if (
        isinstance(coords, (list, tuple))
        and len(coords) >= 2
        and isinstance(coords[0], (int, float))
    ):
        record["longitude"] = coords[0]
        record["latitude"] = coords[1]
    elif coords is not None:
        record["geometry_coordinates"] = json.dumps(coords)

    return record


def fetch_page(session, url, page, timeout, elements):
    """Downloads a page. Returns None if there is no data (404)."""

    params = {"_page": page}
    if elements:
        params["_elements"] = elements

    response = session.get(url, params=params, timeout=timeout)

    if response.status_code == 404:
        return None

    if not response.ok:
        raise RuntimeError(
            f"HTTP {response.status_code} at {response.url} -> "
            f"{response.text[:200]!r}"
        )

    try:
        return response.json()
    except ValueError:
        raise RuntimeError(
            f"Non-JSON response at {response.url} -> {response.text[:200]!r}"
        )


def download_province(session, province_id, timeout, pause, elements):
    """Downloads all sensors for a province (paginated)."""

    url = f"{BASE_URL}/meters/byProvince/{province_id}"

    records = []
    seen_first_ids = set()
    total_pages = None
    page = 1

    while page <= MAX_PAGES:

        data = fetch_page(session, url, page, timeout, elements)

        if data is None:
            break

        if page == 1:
            total_pages = get_total_pages(data)

        features = extract_features(data)

        if not features:
            break

        # Protection against APIs that repeat the last page
        marker = json.dumps(features[0], sort_keys=True, default=str)
        if marker in seen_first_ids:
            break
        seen_first_ids.add(marker)

        for feature in features:
            record = flatten_feature(feature)
            if record is not None:
                records.append(record)

        if total_pages is not None and page >= total_pages:
            break

        page += 1
        time.sleep(pause)

    return records, page


def sensor_unique_key(sensor):
    """Key to detect duplicates."""

    meter_id = sensor.get("meterId")
    source_id = sensor.get("sourceId")

    if meter_id not in (None, ""):
        return f"{source_id}:{meter_id}"

    return json.dumps(sensor, sort_keys=True, ensure_ascii=False, default=str)


def write_csv(records, output_file, base_fields=None):
    """Saves records to CSV."""

    output_file.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = list(base_fields or [])

    for record in records:
        for key in record:
            if key not in fieldnames:
                fieldnames.append(key)

    if not fieldnames:
        fieldnames = ["query_municipality", "query_ine_code"]

    with output_file.open("w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()

        for record in records:
            row = {}

            for key in fieldnames:
                value = record.get(key, "")

                if isinstance(value, (dict, list)):
                    value = json.dumps(value, ensure_ascii=False)

                row[key] = value

            writer.writerow(row)


def main():
    parser = argparse.ArgumentParser(
        description="Downloads traffic sensors for 24 municipalities."
    )
    parser.add_argument("--output", default=str(OUTPUT_FILE), help="Output CSV.")
    parser.add_argument("--pause", type=float, default=0.2, help="Pause between requests (s).")
    parser.add_argument("--timeout", type=int, default=30, help="HTTP timeout (s).")
    parser.add_argument(
        "--elements",
        type=int,
        default=None,
        help="Elements per page (_elements). Not sent by default (API uses 20).",
    )
    args = parser.parse_args()

    output_file = Path(args.output)
    session = create_session()
    errors = []

    # (provinceId, municipalityId) -> (name, INE)
    wanted = {}
    for name, ine in MUNICIPALITIES:
        wanted[(PROVINCE_IDS[ine[:2]], int(ine[2:]))] = (name, ine)

    province_ids = sorted({p for p, _ in wanted})

    print("=" * 60)
    print("OPEN DATA EUSKADI - TRAFFIC SENSOR DOWNLOAD")
    print("=" * 60)
    print(f"Target municipalities: {len(wanted)} | Provinces to query: {province_ids}")

    all_records = []
    seen = set()
    counts = {key: 0 for key in wanted}

    for province_id in province_ids:
        print(f"\nProvince {province_id} ...")

        try:
            records, pages = download_province(
                session, province_id, args.timeout, args.pause, args.elements
            )
        except Exception as error:
            errors.append(f"Province {province_id}: {error}")
            print(f"ERROR: {error}")
            continue

        print(f"  Sensors in province: {len(records)} (pages: {pages})")

        kept = 0

        for record in records:
            key_ids = (
                to_int(record.get("provinceId")) or province_id,
                to_int(record.get("municipalityId")),
            )

            if key_ids not in wanted:
                continue

            unique = sensor_unique_key(record)
            if unique in seen:
                continue
            seen.add(unique)

            name, ine = wanted[key_ids]
            record["query_municipality"] = name
            record["query_ine_code"] = ine
            record["query_api_province_id"] = key_ids[0]
            record["query_api_municipality_id"] = key_ids[1]

            all_records.append(record)
            counts[key_ids] += 1
            kept += 1

        print(f"  Sensors in your municipalities: {kept}")

        time.sleep(args.pause)

    write_csv(
        all_records,
        output_file,
        base_fields=[
            "query_municipality",
            "query_ine_code",
            "query_api_province_id",
            "query_api_municipality_id",
        ],
    )

    summary = [
        {
            "municipality": wanted[key][0],
            "ine_code": wanted[key][1],
            "sensors": counts[key],
        }
        for key in wanted
    ]
    write_csv(summary, SUMMARY_FILE)

    print("\n" + "=" * 60)
    print("DOWNLOAD COMPLETED")
    print("=" * 60)

    for row in summary:
        print(f"  {row['municipality']:<22} {row['ine_code']}  {row['sensors']:>4}")

    print(f"\nTotal unique sensors: {len(all_records)}")
    print(f"Output file: {output_file.resolve()}")
    print(f"Summary by municipality: {SUMMARY_FILE.resolve()}")

    if errors:
        ERROR_FILE.parent.mkdir(parents=True, exist_ok=True)
        ERROR_FILE.write_text("\n".join(errors), encoding="utf-8")
        print(f"Errors saved to: {ERROR_FILE.resolve()}")
    else:
        print("No errors in queries.")


if __name__ == "__main__":
    main()