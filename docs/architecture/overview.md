# NeuralWatt Month 1 Architecture

NeuralWatt is a household energy monitoring system with a cloud-backed
dashboard and IoT ingestion path.

## Data Flow

1. A user logs into the React dashboard with JWT authentication.
2. The user owns one household and one or more devices.
3. A simulator, ESP32, or PZEM-004T based meter sends readings with
   `X-Device-Key`.
4. FastAPI validates the device key, stores readings in MongoDB, runs Z-score
   anomaly detection, and broadcasts live readings over WebSocket.
5. The dashboard displays live watts, kWh trends, anomaly feed, and KSEB bill
   estimate.

## Core Services

- `auth`: register, login, and current-user lookup.
- `households`: household and device provisioning, including device key
  generation.
- `readings`: IoT ingestion and historical reading queries.
- `analytics`: daily usage, hourly usage, summary, bill estimate, and peak
  hours.
- `anomalies`: rolling Z-score baseline detection and anomaly feed.
- `tariff`: KSEB domestic slab bill calculation.

## Hardware Strategy

Month 1 is designed to be safe to demo without mains wiring. The simulator is
the primary presentation path. ESP32 fake-sensor mode can be added as a physical
prop. ESP32 + PZEM-004T should be used only for supervised AC measurement.

## Month 1 Acceptance

- Dashboard login works.
- A simulator/device continuously sends readings.
- Live card updates from WebSocket.
- MongoDB stores canonical energy fields.
- Bill and anomaly views work from stored readings.
- Backend tests cover tariff, ingestion, analytics, and access boundaries.
