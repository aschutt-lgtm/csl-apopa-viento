#!/usr/bin/env python3
"""
CSL Apopa — Panel de Riesgo de Viento
Script de actualización diaria (corre vía GitHub Actions)

Consulta Open-Meteo (pronóstico + archivo histórico ERA5) para las
coordenadas de CSL Apopa, y reconstruye csl_apopa_viento.html a partir
de template.html insertando los datos como JSON embebido.

No requiere API key. Si Open-Meteo falla, el script termina con
código de salida distinto de cero para que el workflow lo marque como
fallido en vez de publicar una página rota.
"""

import json
import sys
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import requests

LAT = 13.784
LON = -89.195
TIMEZONE = "America/El_Salvador"

FORECAST_URL = (
    "https://api.open-meteo.com/v1/forecast"
    f"?latitude={LAT}&longitude={LON}"
    "&hourly=wind_speed_10m,wind_gusts_10m,precipitation"
    "&daily=wind_speed_10m_max,wind_gusts_10m_max,precipitation_sum"
    f"&timezone={TIMEZONE}&forecast_days=10&wind_speed_unit=kmh"
)

ARCHIVE_START = "2015-01-01"
ARCHIVE_END = "2024-12-31"
ARCHIVE_URL = (
    "https://archive-api.open-meteo.com/v1/archive"
    f"?latitude={LAT}&longitude={LON}"
    f"&start_date={ARCHIVE_START}&end_date={ARCHIVE_END}"
    "&daily=wind_speed_10m_max,wind_gusts_10m_max,precipitation_sum"
    f"&timezone={TIMEZONE}"
)

TEMPLATE_PATH = "template.html"
OUTPUT_PATH = "csl_apopa_viento.html"

MAX_RETRIES = 5
RETRY_WAIT_SECONDS = 60


def fetch_with_retries(url, label):
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            if "daily" not in data:
                raise ValueError(f"Respuesta sin campo 'daily': {data}")
            return data
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            print(f"[{label}] intento {attempt}/{MAX_RETRIES} fallo: {exc}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_WAIT_SECONDS)
    raise RuntimeError(f"[{label}] no se pudo obtener datos tras {MAX_RETRIES} intentos: {last_error}")


def main():
    print("Consultando pronostico Open-Meteo (10 dias)...")
    forecast = fetch_with_retries(FORECAST_URL, "pronostico")

    print("Consultando archivo historico Open-Meteo (2015-2024)...")
    archive = fetch_with_retries(ARCHIVE_URL, "historico")

    # El template solo necesita el bloque "daily" de cada respuesta
    forecast_payload = {"daily": forecast["daily"]}
    climate_payload = {"daily": archive["daily"]}

    build_dt = datetime.now(ZoneInfo(TIMEZONE))
    build_timestamp = build_dt.strftime("%Y-%m-%d %H:%M %Z")

    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    html = html.replace("__FORECAST_JSON__", json.dumps(forecast_payload))
    html = html.replace("__CLIMATE_JSON__", json.dumps(climate_payload))
    html = html.replace("__BUILD_TIMESTAMP__", build_timestamp)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"OK: {OUTPUT_PATH} generado. Build: {build_timestamp}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR FATAL: {exc}", file=sys.stderr)
        sys.exit(1)
