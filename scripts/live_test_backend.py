from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title="NeuralWatt Live Test Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

HOUSEHOLD_ID = "demo-household"
DEVICE_ID = "pzem-1"
DEVICE_KEY = "dev-pzem-key"
USER = {
    "id": "demo-user",
    "email": "simulator@neuralwatt.app",
    "full_name": "NeuralWatt Live Test",
}
HOUSEHOLD = {
    "id": HOUSEHOLD_ID,
    "name": "ESP32 PZEM Test Home",
    "address": "Local live test",
    "num_occupants": 4,
    "devices": [],
}
DEVICE = {
    "id": DEVICE_ID,
    "name": "PZEM Phase 1",
    "device_type": "energy_meter",
    "rated_power_watts": 5000,
    "location": "Main Panel",
    "device_key": DEVICE_KEY,
}

readings: list[dict[str, Any]] = []
alert_config: dict[str, Any] | None = None
connections: dict[str, list[WebSocket]] = defaultdict(list)


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def parse_timestamp(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str) and value:
        normalized = value.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalized)
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except ValueError:
            pass
    return now_utc()


def rounded(value: float | None, digits: int = 3) -> float | None:
    if value is None:
        return None
    return round(float(value), digits)


def reading_response(reading: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": reading["id"],
        "device_id": reading["device_id"],
        "household_id": reading["household_id"],
        "power_w": reading["power_w"],
        "voltage_v": reading.get("voltage_v"),
        "current_a": reading.get("current_a"),
        "energy_kwh": reading.get("energy_kwh"),
        "frequency_hz": reading.get("frequency_hz"),
        "power_factor": reading.get("power_factor"),
        "source": reading.get("source", "pzem_004t"),
        "watts": reading["power_w"],
        "voltage": reading.get("voltage_v"),
        "current": reading.get("current_a"),
        "timestamp": reading["timestamp"].isoformat(),
    }


def selected_readings(device_id: str = DEVICE_ID) -> list[dict[str, Any]]:
    return [reading for reading in readings if reading["device_id"] == device_id]


def readings_since(days: int, device_id: str = DEVICE_ID) -> list[dict[str, Any]]:
    cutoff = now_utc() - timedelta(days=days)
    return [
        reading
        for reading in selected_readings(device_id)
        if reading["timestamp"] >= cutoff
    ]


def device_with_household() -> dict[str, Any]:
    household = dict(HOUSEHOLD)
    household["devices"] = [DEVICE]
    return household


async def broadcast(household_id: str, payload: dict[str, Any]) -> None:
    stale: list[WebSocket] = []
    for socket in connections.get(household_id, []):
        try:
            await socket.send_json(payload)
        except Exception:
            stale.append(socket)
    for socket in stale:
        connections[household_id].remove(socket)


@app.get("/")
async def root() -> dict[str, str]:
    return {"status": "ok", "service": "neuralwatt-live-test"}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/auth/register")
async def register(_: Request) -> dict[str, Any]:
    return USER


@app.post("/api/v1/auth/login")
async def login(_: Request) -> dict[str, str]:
    return {"access_token": "dev-token", "token_type": "bearer"}


@app.get("/api/v1/auth/me")
async def me() -> dict[str, Any]:
    return USER


@app.post("/api/v1/households")
async def create_household(_: Request) -> dict[str, Any]:
    return device_with_household()


@app.get("/api/v1/households/me")
async def get_household() -> dict[str, Any]:
    return device_with_household()


@app.post("/api/v1/households/{household_id}/devices")
async def create_device(household_id: str, request: Request) -> dict[str, Any]:
    payload = await request.json()
    DEVICE.update(
        {
            "name": payload.get("name") or DEVICE["name"],
            "device_type": payload.get("device_type") or DEVICE["device_type"],
            "rated_power_watts": payload.get("rated_power_watts")
            or DEVICE["rated_power_watts"],
            "location": payload.get("location") or DEVICE["location"],
        }
    )
    return DEVICE


@app.get("/api/v1/households/{household_id}/devices")
async def list_devices(household_id: str) -> list[dict[str, Any]]:
    return [DEVICE]


@app.post("/api/v1/households/{household_id}/devices/{device_id}/readings")
async def create_reading(
    household_id: str, device_id: str, request: Request
) -> dict[str, Any]:
    payload = await request.json()
    power_w = payload.get("power_w", payload.get("watts"))
    if power_w is None:
        power_w = 0.0

    voltage_v = payload.get("voltage_v", payload.get("voltage"))
    current_a = payload.get("current_a", payload.get("current"))
    timestamp = parse_timestamp(payload.get("timestamp"))

    reading = {
        "id": f"reading-{len(readings) + 1}",
        "household_id": household_id,
        "device_id": device_id,
        "power_w": rounded(power_w, 2) or 0.0,
        "voltage_v": rounded(voltage_v, 2),
        "current_a": rounded(current_a, 3),
        "energy_kwh": rounded(payload.get("energy_kwh"), 6),
        "frequency_hz": rounded(payload.get("frequency_hz"), 2),
        "power_factor": rounded(payload.get("power_factor"), 2),
        "source": payload.get("source") or "pzem_004t",
        "timestamp": timestamp,
    }
    readings.append(reading)

    await broadcast(
        household_id,
        {
            "type": "reading",
            "watts": reading["power_w"],
            "power_w": reading["power_w"],
            "timestamp": reading["timestamp"].isoformat(),
            "device_id": device_id,
        },
    )

    print(
        "live reading",
        f"{reading['power_w']:.2f}W",
        f"V={reading.get('voltage_v')}",
        f"I={reading.get('current_a')}",
        flush=True,
    )
    return reading_response(reading)


@app.get("/api/v1/households/{household_id}/devices/{device_id}/readings")
async def list_readings(
    household_id: str, device_id: str, limit: int = 100
) -> dict[str, Any]:
    rows = sorted(selected_readings(device_id), key=lambda item: item["timestamp"], reverse=True)
    limited = rows[:limit]
    return {
        "device_id": device_id,
        "readings": [reading_response(row) for row in limited],
        "total": len(limited),
    }


@app.get("/api/v1/households/{household_id}/devices/{device_id}/stats")
async def reading_stats(household_id: str, device_id: str) -> dict[str, Any]:
    rows = selected_readings(device_id)
    watts = [row["power_w"] for row in rows]
    return {
        "device_id": device_id,
        "count": len(rows),
        "avg_watts": round(sum(watts) / len(watts), 2) if watts else 0,
        "min_watts": round(min(watts), 2) if watts else 0,
        "max_watts": round(max(watts), 2) if watts else 0,
        "total_kwh": round(sum(row.get("energy_kwh") or 0 for row in rows), 4),
        "from_timestamp": (rows[0]["timestamp"] if rows else now_utc()).isoformat(),
        "to_timestamp": (rows[-1]["timestamp"] if rows else now_utc()).isoformat(),
    }


@app.get("/api/v1/households/{household_id}/devices/{device_id}/analytics/daily")
async def daily_analytics(
    household_id: str, device_id: str, days: int = 30
) -> dict[str, Any]:
    rows = readings_since(days, device_id)
    start = (now_utc() - timedelta(days=days - 1)).date()
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        buckets[row["timestamp"].date().isoformat()].append(row)

    day_rows: list[dict[str, Any]] = []
    for offset in range(days):
        date = (start + timedelta(days=offset)).isoformat()
        bucket = buckets.get(date, [])
        watts = [row["power_w"] for row in bucket]
        kwh = sum(row.get("energy_kwh") or 0 for row in bucket)
        if not kwh and bucket:
            kwh = sum(watts) / len(watts) / 1000 / 60
        day_rows.append(
            {
                "date": date,
                "kwh": round(kwh, 4),
                "peak_watts": round(max(watts), 2) if watts else 0,
                "avg_watts": round(sum(watts) / len(watts), 2) if watts else 0,
                "reading_count": len(bucket),
            }
        )

    return {
        "device_id": device_id,
        "from_date": day_rows[0]["date"] if day_rows else start.isoformat(),
        "to_date": day_rows[-1]["date"] if day_rows else now_utc().date().isoformat(),
        "total_kwh": round(sum(day["kwh"] for day in day_rows), 4),
        "days": day_rows,
    }


@app.get("/api/v1/households/{household_id}/devices/{device_id}/analytics/hourly")
async def hourly_analytics(
    household_id: str, device_id: str, days: int = 7
) -> dict[str, Any]:
    rows = readings_since(days, device_id)
    buckets: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        buckets[row["timestamp"].hour].append(row)

    hours = []
    for hour, bucket in sorted(buckets.items()):
        watts = [row["power_w"] for row in bucket]
        hours.append(
            {
                "hour": hour,
                "avg_watts": round(sum(watts) / len(watts), 2),
                "peak_watts": round(max(watts), 2),
                "reading_count": len(bucket),
            }
        )
    peak = max(hours, key=lambda item: item["avg_watts"], default=None)
    return {
        "device_id": device_id,
        "hours": hours,
        "peak_hour": peak["hour"] if peak else now_utc().hour,
        "peak_hour_avg_watts": peak["avg_watts"] if peak else 0,
    }


@app.get("/api/v1/households/{household_id}/devices/{device_id}/analytics/report")
async def analytics_report(household_id: str, device_id: str, period: str = "monthly") -> dict[str, Any]:
    rows = readings_since(30, device_id)
    watts = [row["power_w"] for row in rows]
    return {
        "period": period,
        "reading_count": len(rows),
        "avg_watts": round(sum(watts) / len(watts), 2) if watts else 0,
        "peak_watts": round(max(watts), 2) if watts else 0,
        "anomaly_count": sum(1 for watt in watts if watt > 3000),
    }


@app.get("/api/v1/households/{household_id}/devices/{device_id}/analytics/cost")
async def cost_analytics(household_id: str, device_id: str, days: int = 30) -> dict[str, Any]:
    rows = readings_since(days, device_id)
    total_kwh = sum(row.get("energy_kwh") or 0 for row in rows)
    if not total_kwh and rows:
        avg_watts = sum(row["power_w"] for row in rows) / len(rows)
        total_kwh = avg_watts * days * 24 / 1000

    rate = 5.0
    energy_charge = total_kwh * rate
    fixed_charge = 45.0 if total_kwh else 0.0
    electricity_duty = energy_charge * 0.10
    meter_rent = 12.0 if total_kwh else 0.0
    return {
        "total_kwh": round(total_kwh, 4),
        "energy_charge": round(energy_charge, 2),
        "fixed_charge": round(fixed_charge, 2),
        "electricity_duty": round(electricity_duty, 2),
        "meter_rent": round(meter_rent, 2),
        "total_bill": round(energy_charge + fixed_charge + electricity_duty + meter_rent, 2),
        "slab_breakdown": [
            {
                "slab_label": "Live test slab",
                "units": round(total_kwh, 3),
                "rate_per_unit": rate,
                "slab_cost": round(energy_charge, 2),
            }
        ],
    }


@app.get("/api/v1/anomalies/triggered-alerts")
async def triggered_alerts(household_id: str, limit: int = 20) -> dict[str, Any]:
    high_rows = [row for row in readings if row["power_w"] > 3000]
    alerts = [
        {
            "id": f"alert-{row['id']}",
            "severity": "high",
            "timestamp": row["timestamp"].isoformat(),
            "reason": "High power draw detected in live test",
            "watts": row["power_w"],
            "expected_watts": 1200,
            "channels": ["dashboard"],
        }
        for row in high_rows[-limit:]
    ]
    return {"household_id": household_id, "count": len(alerts), "triggered_alerts": alerts}


@app.get("/api/v1/households/{household_id}/devices/{device_id}/anomalies")
async def list_anomalies(household_id: str, device_id: str, limit: int = 20) -> dict[str, Any]:
    return {"anomalies": [], "count": 0, "limit": limit}


@app.get("/api/v1/households/{household_id}/devices/{device_id}/baseline")
async def baseline(household_id: str, device_id: str) -> dict[str, Any]:
    rows = readings_since(30, device_id)
    watts = [row["power_w"] for row in rows]
    avg = sum(watts) / len(watts) if watts else 0
    variance = sum((watt - avg) ** 2 for watt in watts) / len(watts) if watts else 0
    return {
        "avg_watts": round(avg, 2),
        "std_dev": round(variance**0.5, 2),
        "sample_count": len(watts),
    }


@app.get("/api/v1/households/{household_id}/devices/{device_id}/alert-config")
async def get_alert_config(household_id: str, device_id: str) -> dict[str, Any]:
    return alert_config or {
        "id": "alert-config-live-test",
        "severity_threshold": "high",
        "email_enabled": False,
        "email_address": None,
        "webhook_enabled": False,
        "webhook_url": None,
    }


@app.post("/api/v1/households/{household_id}/devices/{device_id}/alert-config")
async def create_alert_config(household_id: str, device_id: str, request: Request) -> dict[str, Any]:
    global alert_config
    alert_config = {"id": "alert-config-live-test", **await request.json()}
    return alert_config


@app.patch("/api/v1/households/{household_id}/devices/{device_id}/alert-config")
async def update_alert_config(household_id: str, device_id: str, request: Request) -> dict[str, Any]:
    global alert_config
    alert_config = {"id": "alert-config-live-test", **await request.json()}
    return alert_config


@app.delete("/api/v1/households/{household_id}/devices/{device_id}/alert-config")
async def delete_alert_config(household_id: str, device_id: str) -> dict[str, str]:
    global alert_config
    alert_config = None
    return {"status": "deleted"}


@app.post("/api/v1/nilm/predict")
async def nilm_predict(request: Request) -> dict[str, Any]:
    payload = await request.json()
    input_readings = payload.get("readings") or []
    windows = []
    for index, row in enumerate(input_readings[:8]):
        watts = row.get("power_w", row.get("watts", 0))
        appliance = "iron" if watts > 700 else "fan" if watts > 60 else "fridge"
        windows.append(
            {
                "window_index": index + 1,
                "predicted_appliance": appliance,
                "confidence": 0.72,
            }
        )
    return {
        "feature_set_version": "live-test",
        "classes": ["fridge", "fan", "iron"],
        "windows": windows,
    }


@app.get("/api/v1/nilm/model-card")
async def model_card() -> dict[str, Any]:
    return {
        "n_classes": 6,
        "test_accuracy": 0.8616,
        "cv_mean_accuracy": 0.7189,
        "total_feature_windows": 4877,
        "classes": [
            "electric_kettle",
            "fan",
            "fridge",
            "iron",
            "mixer_grinder",
            "washing_machine",
        ],
        "top_feature_importance": [
            {"feature": "power_mean", "importance": 0.42},
            {"feature": "power_max", "importance": 0.31},
            {"feature": "power_std", "importance": 0.18},
        ],
        "limitation": "Live-test backend: appliance predictions are placeholders.",
    }


@app.get("/api/v1/nilm/shap")
async def shap_importance() -> dict[str, Any]:
    return {
        "source": "fallback",
        "feature_importance": [
            {"feature": "power_mean", "importance": 0.42},
            {"feature": "power_max", "importance": 0.31},
            {"feature": "current_a", "importance": 0.15},
        ],
    }


@app.get("/api/v1/nilm/data-validation")
async def data_validation() -> dict[str, Any]:
    return {
        "is_stationary": True,
        "adf_statistic": -4.21,
        "p_value": 0.01,
        "recommendation": "Live-test data is only for dashboard verification.",
    }


@app.get("/api/v1/forecast/{household_id}")
async def forecast(household_id: str, days: int = 30) -> dict[str, Any]:
    base = now_utc().replace(minute=0, second=0, microsecond=0)
    rows = []
    recent = selected_readings()
    avg = sum(row["power_w"] for row in recent[-20:]) / len(recent[-20:]) if recent else 200
    for hour in range(24):
        predicted = max(avg / 1000, 0.02)
        rows.append(
            {
                "hour": (base + timedelta(hours=hour)).isoformat(),
                "predicted_kwh": round(predicted, 4),
                "upper_kwh": round(predicted * 1.2, 4),
            }
        )
    return {"household_id": household_id, "forecast": rows}


@app.get("/api/v1/recommendations/{household_id}")
async def recommendations(household_id: str) -> dict[str, Any]:
    return {
        "summary": {"estimated_daily_cost": 12.0},
        "total_estimated_saving_inr": 0,
        "recommendations": [
            {
                "id": "live-test",
                "title": "Live PZEM feed active",
                "priority": "info",
                "description": "Use this screen to verify ESP32 readings reach the dashboard.",
            }
        ],
    }


@app.websocket("/ws/readings/{household_id}")
async def websocket_readings(websocket: WebSocket, household_id: str) -> None:
    await websocket.accept()
    connections[household_id].append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in connections[household_id]:
            connections[household_id].remove(websocket)
