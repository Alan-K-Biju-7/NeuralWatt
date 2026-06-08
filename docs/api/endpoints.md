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

## NILM Prediction

- `POST /nilm/predict`

Requires `Authorization: Bearer <jwt>`.

Example payload:

```json
{
  "window_size_s": 30,
  "readings": [
    {
      "timestamp": "2026-06-08T12:00:00Z",
      "power_w": 72.5,
      "voltage_v": 235.0,
      "current_a": 0.31
    },
    {
      "timestamp": "2026-06-08T12:00:05Z",
      "power_w": 73.1,
      "voltage_v": 235.2,
      "current_a": 0.31
    },
    {
      "timestamp": "2026-06-08T12:00:10Z",
      "power_w": 71.8,
      "voltage_v": 234.9,
      "current_a": 0.30
    }
  ]
}
```

Response shape:

```json
{
  "model_version": "nilm_v1",
  "feature_set_version": "tapo_signature_v2",
  "window_size_s": 30,
  "classes": ["electric_kettle", "fan", "fridge", "iron", "mixer_grinder", "washing_machine"],
  "windows": [
    {
      "window_index": 0,
      "predicted_appliance": "fridge",
      "confidence": 0.997,
      "probabilities": {
        "electric_kettle": 0.001,
        "fan": 0.001,
        "fridge": 0.997,
        "iron": 0.0,
        "mixer_grinder": 0.001,
        "washing_machine": 0.001
      }
    }
  ]
}
```

This endpoint currently uses the smart-plug appliance signature classifier. It
does not yet perform aggregate household disaggregation.

## Anomalies And Alerts

- `GET /households/{household_id}/devices/{device_id}/anomalies`
- `GET /households/{household_id}/devices/{device_id}/baseline`

## WebSocket

The backend exposes a household-scoped WebSocket route for live dashboard
updates. The simulator and ESP32 ingestion path broadcasts the latest power
reading after each successful insert.
