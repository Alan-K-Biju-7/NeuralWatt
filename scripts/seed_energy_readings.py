#!/usr/bin/env python3
"""
Seed NeuralWatt with 30 days of hourly device readings.

The current backend route is household-scoped, so this script first calls
/households/me to discover the household id, then posts each reading.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import time
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


API_BASE_URL = os.getenv("NW_API_BASE_URL", "http://localhost:8000/api/v1")
AUTH_TOKEN = os.getenv("NW_TOKEN", "")

DEVICES = [
    {
        "name": "AC",
        "id": "6a04373592773c80c9319c53",
        "rated_watts": 1500,
        "active_hours": set(range(14, 23)),
    },
    {
        "name": "Geyser",
        "id": "6a04373e92773c80c9319c54",
        "rated_watts": 2000,
        "active_hours": {6, 7, 18, 19},
    },
    {
        "name": "Washer",
        "id": "6a04374892773c80c9319c56",
        "rated_watts": 2200,
        "active_hours": {8, 9, 10},
        "active_weekdays": {1, 3, 6},  # Tue, Thu, Sun
    },
    {
        "name": "Fridge",
        "id": "6a04375392773c80c9319c57",
        "rated_watts": 200,
        "active_hours": set(range(24)),
    },
    {
        "name": "TV",
        "id": "6a043a3b92773c80c9319c72",
        "rated_watts": 120,
        "active_hours": set(range(19, 24)),
    },
]


def utc_iso(timestamp: datetime) -> str:
    return timestamp.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def api_request(method: str, url: str, payload: dict | None = None) -> tuple[int, dict | str]:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = Request(
        url,
        data=body,
        method=method,
        headers={
            "Authorization": f"Bearer {AUTH_TOKEN}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urlopen(request, timeout=15) as response:
            raw = response.read().decode("utf-8")
            return response.status, json.loads(raw) if raw else {}
    except HTTPError as error:
        raw = error.read().decode("utf-8")
        try:
            return error.code, json.loads(raw)
        except json.JSONDecodeError:
            return error.code, raw
    except URLError as error:
        return 0, str(error.reason)


def get_household_id() -> str:
    status, data = api_request("GET", f"{API_BASE_URL}/households/me")
    if status != 200:
        raise SystemExit(f"Could not load household id. Status {status}: {data}")
    return data["id"]


def is_active(device: dict, timestamp: datetime) -> bool:
    if timestamp.hour not in device["active_hours"]:
        return False
    active_weekdays = device.get("active_weekdays")
    return active_weekdays is None or timestamp.weekday() in active_weekdays


def is_guaranteed_anomaly(device_name: str, timestamp: datetime, now: datetime) -> bool:
    """Put a few obvious spikes inside the last 72h baseline window."""
    hours_ago = int((now - timestamp).total_seconds() // 3600)
    anomaly_hours_by_device = {
        "AC": {6, 30},
        "Geyser": {8, 32},
        "Washer": {10, 34},
        "Fridge": {5, 29},
        "TV": {7, 31},
    }
    return hours_ago in anomaly_hours_by_device.get(device_name, set())


def build_payload(device: dict, timestamp: datetime, anomaly: bool) -> dict:
    rated = device["rated_watts"]
    if anomaly:
        watts = random.uniform(rated * 1.55, rated * 2.4)
    else:
        watts = random.uniform(rated * 0.80, rated * 1.00)

    voltage = random.uniform(218.0, 242.0)
    current_amps = watts / voltage
    energy_kwh = watts / 1000.0  # one hourly reading

    return {
        "power_w": round(watts, 2),
        "voltage_v": round(voltage, 2),
        "current_a": round(current_amps, 3),
        "energy_kwh": round(energy_kwh, 4),
        "frequency_hz": round(random.uniform(49.8, 50.2), 2),
        "power_factor": round(random.uniform(0.86, 0.99), 2),
        "source": "backfill",
        "timestamp": utc_iso(timestamp),
    }


def iter_matching_readings(days: int, anomaly_probability: float):
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    start = now - timedelta(days=days)
    timestamp = start

    while timestamp <= now:
        for device in DEVICES:
            if not is_active(device, timestamp):
                continue

            anomaly = is_guaranteed_anomaly(device["name"], timestamp, now)
            anomaly = anomaly or random.random() < anomaly_probability
            yield device, timestamp, build_payload(device, timestamp, anomaly), anomaly

        timestamp += timedelta(hours=1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--anomaly-probability", type=float, default=0.01)
    parser.add_argument("--sleep", type=float, default=0.0, help="Delay between POSTs in seconds")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not AUTH_TOKEN:
        raise SystemExit("Set NW_TOKEN to a valid Bearer token before running this script.")

    random.seed()
    household_id = get_household_id()
    endpoint = f"{API_BASE_URL}/households/{household_id}/devices/{{device_id}}/readings"
    print(f"Household: {household_id}")
    print(f"Posting to: {endpoint}")

    sent = 0
    anomalies = 0
    for device, timestamp, payload, anomaly in iter_matching_readings(
        args.days,
        args.anomaly_probability,
    ):
        if anomaly:
            anomalies += 1
        url = endpoint.format(device_id=device["id"])

        if args.dry_run:
            status, data = 0, "dry-run"
        else:
            status, data = api_request("POST", url, payload)

        sent += 1
        marker = " ANOMALY" if anomaly else ""
        print(
            f"{status} {device['name']:<6} {payload['timestamp']} "
            f"{payload['power_w']:>8.2f}W{marker}"
        )
        if status >= 400 or status == 0:
            print(f"  response: {data}")

        if args.sleep:
            time.sleep(args.sleep)

    print(f"Done. Requests: {sent}, intentional anomalies: {anomalies}")


if __name__ == "__main__":
    main()
