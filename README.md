# NeuralWatt

AI-based smart energy monitoring foundation for Month 1: FastAPI backend,
MongoDB storage, React dashboard, IoT/simulator ingestion, KSEB billing, and
basic anomaly detection.

## Teacher Demo

Start the full local demo:

```bash
make demo-up
```

Then open:

- Frontend: http://localhost:3001
- Backend docs: http://localhost:8000/docs

The simulator automatically creates/logs into a demo user, creates a household
and device, stores the device key, and sends readings every 30 seconds. It uses
`X-Device-Key`, which is the same auth style the ESP32 firmware should use.

## Month 1 Completion Highlights

- JWT auth for dashboard users.
- Per-device `X-Device-Key` auth for IoT ingestion.
- Canonical reading fields: `power_w`, `voltage_v`, `current_a`,
  `energy_kwh`, `frequency_hz`, `power_factor`, `source`.
- Backward compatibility for old `watts`, `voltage`, and `current` payloads.
- Live dashboard WebSocket broadcast.
- Daily/hourly analytics, summary, peak-hours, KSEB bill estimate.
- 90-day MongoDB TTL retention for readings.
- Request timing logs for backend API calls.

## ESP32/PZEM-004T Path

For Month 1, use the simulator or an ESP32 fake-sensor sketch for safe
presentation. For real mains measurement, use ESP32 + PZEM-004T only with
supervision from someone experienced with AC wiring. The ESP32 should POST to:

```text
POST /api/v1/households/{household_id}/devices/{device_id}/readings
X-Device-Key: <device_key>
```

Payload example:

```json
{
  "power_w": 420.5,
  "voltage_v": 231.2,
  "current_a": 1.82,
  "energy_kwh": 0.0035,
  "frequency_hz": 50.0,
  "power_factor": 0.94,
  "source": "pzem_004t"
}
```

## Backend Tests

```bash
make test-backend
```
