# NeuralWatt

NeuralWatt is an AI-based smart energy monitoring and optimization platform for
households. It combines IoT energy ingestion, a FastAPI backend, MongoDB
storage, a React dashboard, tariff-aware billing, anomaly detection, and an
early NILM appliance-classification pipeline trained on real TP-Link Tapo P110
smart plug data.

The long-term goal is a single-platform energy intelligence system that can
monitor real-time household power, estimate appliance-level usage, detect
wasteful behavior, forecast electricity bills, and recommend when to shift loads
for lower cost and better solar self-consumption.

## Current Status

The project is currently in a strong Month 1 / early Month 2 stage.

| Area | Status |
|---|---|
| FastAPI backend | Implemented |
| MongoDB reading storage | Implemented |
| JWT user authentication | Implemented |
| Device-key IoT ingestion | Implemented |
| React dashboard | Implemented MVP |
| WebSocket live readings | Implemented |
| KSEB bill estimation | Implemented |
| Z-score anomaly detection | Implemented |
| Simulator data source | Implemented |
| Real Tapo P110 data pipeline | Implemented |
| NILM baseline classifier | Implemented six-class baseline |
| NILM prediction CLI/API | Implemented |
| Aggregate main-line NILM | Not yet implemented |
| Forecasting, solar, recommendations, SHAP | Planned |

## Key Features

- Real-time power monitoring with live dashboard updates.
- Household and device management with JWT-secured user sessions.
- Secure IoT ingestion using per-device `X-Device-Key` authentication.
- Canonical energy readings:
  `power_w`, `voltage_v`, `current_a`, `energy_kwh`, `frequency_hz`,
  `power_factor`, and `source`.
- Daily and hourly usage analytics.
- KSEB domestic slab bill estimation.
- Rolling baseline anomaly detection with anomaly feed.
- Email/webhook alert configuration foundation.
- Local simulator for safe demos without mains wiring.
- Feature-rich NILM pipeline using XGBoost on labelled smart-plug appliance data.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, Pydantic, Motor |
| Database | MongoDB |
| Frontend | React, Vite, Tailwind CSS, Recharts |
| Auth | JWT, bcrypt/passlib |
| Realtime | WebSocket |
| ML | pandas, scikit-learn, XGBoost |
| DevOps | Docker Compose, Makefile |
| Data source | Simulator, Tapo P110 smart plug CSVs, future ESP32/PZEM |

## Architecture

```text
Simulator / ESP32 / Tapo P110
        |
        | HTTP JSON readings
        v
FastAPI backend
        |
        | stores readings, runs anomaly detection, broadcasts live updates
        v
MongoDB + WebSocket
        |
        v
React dashboard

ML pipeline:
Tapo raw CSV -> merge -> feature extraction -> XGBoost NILM baseline -> evaluation
Trained NILM baseline -> CLI/API prediction -> future dashboard appliance cards
```

More detail is available in:

- `docs/architecture/overview.md`
- `docs/api/endpoints.md`
- `ml/README.md`

## Repository Structure

```text
NeuralWatt/
|-- backend/              # FastAPI API, schemas, services, tests
|-- frontend/             # React dashboard
|-- simulator/            # Safe local energy-reading simulator
|-- ml/                   # NILM feature extraction, training, evaluation
|-- docs/                 # Architecture and API notes
|-- scripts/              # Demo data seeding utilities
|-- docker-compose.yml
|-- Makefile
`-- README.md
```

## Quick Start

Start the full local demo:

```bash
make demo-up
```

Then open:

- Frontend: `http://localhost:3001`
- Backend docs: `http://localhost:8000/docs`

The simulator automatically registers/logs in a demo user, creates a household
and device, stores the device key, and sends readings every 30 seconds.

Stop the demo:

```bash
make demo-down
```

## API Ingestion

Readings are posted to a household device endpoint:

```text
POST /api/v1/households/{household_id}/devices/{device_id}/readings
X-Device-Key: <device_key>
```

Example payload:

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

Legacy fields `watts`, `voltage`, and `current` are still accepted during the
transition to the canonical schema.

## NILM Baseline

The project currently has an early NILM appliance-classification baseline.

Current real-data classes:

- `electric_kettle`
- `fan`
- `fridge`
- `iron`
- `mixer_grinder`
- `washing_machine`

Current training artifacts:

- `ml/data/appliance_data_real.csv`
- `ml/data/features_extracted.csv`
- `ml/models/nilm_v1_metadata.json`
- `ml/results/confusion_matrix.csv`
- `ml/results/classification_report.txt`

Current baseline result:

| Metric | Value |
|---|---:|
| Classes | 6 |
| Raw rows | 7,911 |
| Feature windows | 2,092 |
| Feature set | `tapo_signature_v2` |
| Test accuracy | 99.05% |
| CV mean accuracy | 99.52% |
| CV std deviation | 0.0034 |

Important limitation: this is currently an appliance signature classifier
trained on smart-plug data. It is not yet a full aggregate NILM disaggregation
model. For full NILM, the project still needs synchronized main-line aggregate
power readings plus appliance-level labels. The current evaluation splits
windows from the same appliance captures, so the result is a strong development
baseline rather than a final real-home generalization score.

Run the ML pipeline:

```bash
cd ml
python data/merge_raw.py
python feature_extraction.py data/appliance_data_real.csv
python train_nilm.py --data data/appliance_data_real.csv
python evaluate.py --model models/nilm_v1.pkl --features data/features_extracted.csv
python predict_nilm.py --csv data/appliance_data_real.csv --limit 10
```

`models/nilm_v1.pkl` is intentionally ignored by git because it is a binary
artifact. The metadata and evaluation reports are tracked.

Prediction is available in two forms:

- CLI: `python ml/predict_nilm.py --csv ml/data/appliance_data_real.csv --limit 10`
- API: `POST /api/v1/nilm/predict` with JWT auth and a list of timestamped
  readings.

## Testing

Backend tests:

```bash
backend/.venv/bin/pytest backend/tests
```

Frontend production build:

```bash
cd frontend
npm run build
```

ML syntax check:

```bash
python -m py_compile ml/feature_extraction.py ml/train_nilm.py ml/evaluate.py ml/prediction.py ml/predict_nilm.py ml/data/merge_raw.py
```

On macOS, the backend virtualenv may need the native OpenMP runtime for the
PyPI XGBoost wheel:

```bash
brew install libomp
```

Latest verified state:

- Backend tests: `12 passed`
- Frontend build: passed
- ML scripts: compile successfully

## Hardware Path

The safe demo path uses the simulator or smart plugs.

For real household measurement, the planned hardware path is:

- ESP32 or Raspberry Pi edge node.
- PZEM-004T or calibrated current/voltage sensing.
- WiFi transmission to the FastAPI ingestion API.

Real AC mains wiring must only be done with proper supervision and safety
precautions.

## Roadmap

Near-term priorities:

1. Collect more real appliance sessions, especially extra fridge, iron,
   washing-machine, and mixer repeats plus new geyser and AC captures.
2. Add appliance breakdown cards/charts to the dashboard.
3. Collect synchronized aggregate household readings.
4. Move from smart-plug signature classification to true aggregate NILM.

Next intelligence layer:

1. Monthly bill forecasting with weather features.
2. Tariff-aware recommendation engine.
3. Carbon footprint tracker.
4. Energy score and gamification.
5. Solar profile CSV parser and solar-aware scheduling.
6. SHAP explanations for NILM and forecast models.
7. WhatsApp alert integration.

## Project Positioning

NeuralWatt is being built as a full-stack energy intelligence platform:

```text
real-time sensing -> cloud ingestion -> analytics -> NILM baseline ->
anomaly detection -> billing insight -> future recommendations and solar scheduling
```

Current honest project claim:

> NeuralWatt has completed the monitoring foundation and started early
> appliance intelligence using real labelled Tapo P110 data and a baseline NILM
> model.

Target final claim:

> NeuralWatt estimates appliance-level consumption from aggregate household
> readings, detects abnormal usage, forecasts bills, and recommends the best
> times to run appliances based on tariff and solar availability.
