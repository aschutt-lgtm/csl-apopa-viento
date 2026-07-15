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
import math
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
    "&hourly=wind_speed_10m,wind_gusts_10m,precipitation,cape"
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

SNET_METAR_URL = "https://snet.gob.sv/meteorologia/metar/metarjson.php"

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


def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def fetch_nearest_snet_station():
    """Consulta la red de estaciones automaticas de MARN/DGOA (SNET) y
    devuelve la estacion mas cercana a CSL Apopa. No reintenta tan
    agresivo como el pronostico: si falla, el dashboard sigue funcionando
    sin este panel (es un dato complementario, no critico)."""
    try:
        resp = requests.get(SNET_METAR_URL, timeout=20)
        resp.raise_for_status()
        stations = resp.json()
    except Exception as exc:  # noqa: BLE001
        print(f"[snet] no se pudo obtener la red de estaciones: {exc}")
        return None

    best = None
    best_dist = None
    for s in stations:
        try:
            lat = float(s["latitud"])
            lon = float(s["longitud"])
            vel = s.get("velocidad", "")
            if vel in (None, ""):
                continue  # estacion sin dato de viento en este momento
        except (KeyError, ValueError, TypeError):
            continue
        dist = haversine_km(LAT, LON, lat, lon)
        if best_dist is None or dist < best_dist:
            best_dist = dist
            best = s

    if best is None:
        print("[snet] ninguna estacion con dato de viento disponible ahora mismo")
        return None

    direction_raw = ""
    try:
        direction_raw = best.get("dirviento", "").rstrip("/").split("/")[-1].replace(".png", "")
    except Exception:  # noqa: BLE001
        pass

    return {
        "distance_km": round(best_dist, 1),
        "lat": float(best["latitud"]),
        "lon": float(best["longitud"]),
        "wind_speed": best.get("velocidad", ""),
        "direction": direction_raw.upper(),
        "temperature": best.get("temperatura", ""),
        "humidity": best.get("humedad", ""),
        "station_time": best.get("hora", ""),
    }


def main():
    print("Consultando pronostico Open-Meteo (10 dias)...")
    forecast = fetch_with_retries(FORECAST_URL, "pronostico")

    print("Consultando archivo historico Open-Meteo (2015-2024)...")
    archive = fetch_with_retries(ARCHIVE_URL, "historico")

    print("Consultando red de estaciones MARN/DGOA (SNET)...")
    snet_station = fetch_nearest_snet_station()

    # El template solo necesita el bloque "daily" de cada respuesta
    forecast_payload = {"daily": dict(forecast["daily"])}
    climate_payload = {"daily": archive["daily"]}

    # CAPE viene por hora; calculamos el maximo diario y lo anexamos como
    # "cape_max" alineado con las fechas de forecast_payload["daily"]["time"]
    hourly_time = forecast["hourly"]["time"]
    hourly_cape = forecast["hourly"]["cape"]
    cape_by_date = {}
    for t, v in zip(hourly_time, hourly_cape):
        date_key = t.split("T")[0]
        if v is None:
            continue
        cape_by_date[date_key] = max(cape_by_date.get(date_key, 0), v)

    forecast_payload["daily"]["cape_max"] = [
        cape_by_date.get(d, None) for d in forecast_payload["daily"]["time"]
    ]

    build_dt = datetime.now(ZoneInfo(TIMEZONE))
    build_timestamp = build_dt.strftime("%Y-%m-%d %H:%M %Z")

    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    html = html.replace("__FORECAST_JSON__", json.dumps(forecast_payload))
    html = html.replace("__CLIMATE_JSON__", json.dumps(climate_payload))
    html = html.replace("__SNET_JSON__", json.dumps(snet_station))
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
