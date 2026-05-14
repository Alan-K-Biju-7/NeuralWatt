# NeuralWatt Month 1 API

Base URL: `/api/v1`

## Auth

- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`

Dashboard endpoints use `Authorization: Bearer <jwt>`.

## Households And Devices

- `POST /households`
- `GET /households/me`
- `POST /households/{household_id}/devices`
- `GET /households/{household_id}/devices`

Device responses include `device_key`. Treat this as a secret for ESP32 or
simulator ingestion.

## Readings

- `POST /households/{household_id}/devices/{device_id}/readings`
- `GET /households/{household_id}/devices/{device_id}/readings`
- `GET /households/{household_id}/devices/{device_id}/stats`

IoT ingestion uses:

```text
X-Device-Key: <device_key>
```

Canonical payload:

```json
{
  "power_w": 420.5,
  "voltage_v": 231.2,
  "current_a": 1.82,
  "energy_kwh": 0.0035,
  "frequency_hz": 50.0,
  "power_factor": 0.94,
  "source": "esp32"
}
```

Legacy fields `watts`, `voltage`, and `current` are still accepted during the
Month 1 transition.

## Analytics

- `GET /households/{household_id}/devices/{device_id}/analytics/summary`
- `GET /households/{household_id}/devices/{device_id}/analytics/daily`
- `GET /households/{household_id}/devices/{device_id}/analytics/hourly`
- `GET /households/{household_id}/devices/{device_id}/analytics/peak-hours`
- `GET /households/{household_id}/devices/{device_id}/analytics/bill`
- `GET /households/{household_id}/devices/{device_id}/analytics/cost`
- `GET /households/{household_id}/devices/{device_id}/analytics/report`

## Anomalies And Alerts

- `GET /households/{household_id}/devices/{device_id}/anomalies`
- `GET /households/{household_id}/devices/{device_id}/baseline`

## WebSocket

The backend exposes a household-scoped WebSocket route for live dashboard
updates. The simulator and ESP32 ingestion path broadcasts the latest power
reading after each successful insert.
