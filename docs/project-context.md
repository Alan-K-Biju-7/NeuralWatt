# NeuralWatt Project Context

Last updated: 2026-06-11

## One-Line Summary

NeuralWatt is an AI-based smart energy monitoring and optimization platform
with a working FastAPI backend, MongoDB storage, React dashboard, simulator/IoT
ingestion, live WebSocket updates, KSEB-style billing, anomaly detection, and a
real-data NILM appliance-signature model trained from Tapo P110 smart-plug CSVs.

## Current Project Stage

The project has completed a strong Month 1 monitoring foundation and has moved
into early Month 2 appliance intelligence.

Implemented:

| Area | Status |
|---|---|
| FastAPI backend | Implemented |
| MongoDB data storage | Implemented |
| JWT user authentication | Implemented |
| Per-device IoT authentication | Implemented |
| Energy reading ingestion | Implemented |
| React dashboard | Implemented MVP |
| Live WebSocket readings | Implemented |
| Daily/hourly analytics | Implemented |
| KSEB-style cost estimation | Implemented |
| Z-score anomaly detection | Implemented |
| Alert configuration foundation | Implemented |
| Simulator data source | Implemented |
| Tapo P110 CSV data pipeline | Implemented |
| NILM feature extraction | Implemented |
| NILM XGBoost baseline | Implemented |
| NILM CLI prediction | Implemented |
| NILM backend prediction API | Implemented |
| True aggregate household NILM | Not yet implemented |
| Forecasting, recommendations, solar, SHAP | Planned |

## Honest Project Claim

Current claim:

> NeuralWatt monitors household energy readings in real time, stores and
> analyzes usage, estimates KSEB-style cost, detects simple anomalies, and
> includes an early real-data appliance signature classifier trained on labelled
> Tapo P110 smart-plug captures.

Important limitation:

> The current NILM model is not yet full aggregate mains disaggregation. It is a
> smart-plug appliance signature classifier. True NILM still requires
> synchronized main-line aggregate readings plus appliance-level labels.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, Pydantic v2, Motor, MongoDB |
| Frontend | React, Vite, Tailwind CSS, Recharts, Zustand |
| Auth | JWT, passlib/bcrypt |
| Realtime | WebSocket |
| ML | pandas, numpy, scikit-learn, XGBoost |
| Data source | Simulator, Tapo P110 smart plug CSVs, future ESP32/PZEM |
| DevOps | Docker Compose, Makefile |
| Testing | Pytest, Vite build, Python compile checks |

## Repository Layout

```text
NeuralWatt/
|-- backend/              # FastAPI API, schemas, services, tests
|-- frontend/             # React dashboard
|-- simulator/            # Local simulator for safe demo readings
|-- ml/                   # NILM data, feature extraction, training, prediction
|-- docs/                 # Architecture, API, planning, context docs
|-- scripts/              # Demo data seeding utilities
|-- docker-compose.yml
|-- Makefile
`-- README.md
```

## System Architecture

```text
Simulator / ESP32 / Tapo CSV
        |
        | HTTP JSON readings / CSV import
        v
FastAPI backend
        |
        | stores readings, runs analytics/anomaly detection, broadcasts live data
        v
MongoDB + WebSocket
        |
        v
React dashboard

ML path:
Tapo raw CSV -> merge -> quality report -> feature extraction -> XGBoost model
              -> evaluation reports -> CLI prediction / backend prediction API
```

## Backend Implementation

Main files:

- `backend/app/main.py`
- `backend/app/api/v1/router.py`
- `backend/app/db/mongodb.py`
- `backend/app/core/security.py`
- `backend/app/core/dependencies.py`
- `backend/app/core/config.py`

Implemented backend endpoint groups:

| Area | Files | Purpose |
|---|---|---|
| Auth | `endpoints/auth.py`, `services/user_service.py` | Register, login, current user |
| Households | `endpoints/households.py`, `services/household_service.py` | Household/device setup |
| Readings | `endpoints/readings.py`, `services/reading_service.py` | IoT/user reading ingestion and history |
| Analytics | `endpoints/analytics.py`, `services/analytics_service.py` | Daily/hourly/report/cost/summary views |
| Anomalies | `endpoints/anomalies.py`, `services/anomaly_service.py` | Baseline and anomaly list |
| Alerts | `endpoints/alert_configs.py`, `services/alert_config_service.py` | Alert configuration foundation |
| NILM | `endpoints/nilm.py`, `services/nilm_service.py` | Appliance prediction from submitted readings |
| WebSocket | `api/ws.py` | Household-scoped live reading updates |

The backend connects to MongoDB on startup and creates useful indexes, including
reading time indexes and a TTL index for old readings.

## Authentication And Ingestion

Dashboard access uses JWT Bearer auth.

IoT ingestion supports:

```text
Authorization: Bearer <jwt>
```

or:

```text
X-Device-Key: <device_key>
```

Canonical reading payload:

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

Legacy aliases are still accepted:

- `watts`
- `voltage`
- `current`

## Data Model

MongoDB collections:

- `users`
- `households`
- `readings`
- `anomalies`
- alert configuration data

Households contain embedded devices. Each device has a generated `device_key`
for IoT ingestion.

Readings store normalized values:

- `power_w`
- `voltage_v`
- `current_a`
- `energy_kwh`
- `frequency_hz`
- `power_factor`
- `source`
- `timestamp`
- household/device identifiers

## Analytics And Billing

Implemented analytics:

- Daily usage
- Hourly usage
- Usage report
- Peak hours
- Live summary
- Cost estimate
- Bill estimate

KSEB-style tariff logic lives in:

- `backend/app/services/tariff.py`

It includes slab charges, fixed charge, electricity duty, and meter rent.

## Anomaly Detection

Implemented in:

- `backend/app/services/anomaly_service.py`

Current method:

1. Use recent readings as a rolling baseline.
2. Compute mean and standard deviation.
3. Compare the current reading with a Z-score.
4. Store anomaly records with severity.

This is a baseline statistical anomaly detector, not yet a deep-learning or
forecast-based detector.

## Frontend Implementation

Main files:

- `frontend/src/main.jsx`
- `frontend/src/App.jsx`
- `frontend/src/pages/Login.jsx`
- `frontend/src/pages/Dashboard.jsx`
- `frontend/src/lib/api.js`
- `frontend/src/hooks/useLiveWatt.js`
- `frontend/src/store/authStore.js`

Dashboard components:

- `LiveWattCard`
- `KPICards`
- `DailyChart`
- `HourlyChart`
- `AnomalyFeed`

Implemented frontend flow:

1. User registers or logs in.
2. Dashboard fetches user, household, and devices.
3. First device is selected automatically.
4. Live watts update through WebSocket.
5. Cards and charts show usage and cost analytics.
6. Anomaly feed shows detected unusual readings.
7. Frontend API client includes `nilmAPI.predict(data)` for future appliance
   prediction UI.

## Simulator Implementation

Main files:

- `simulator/simulator.py`
- `simulator/patterns.py`

The simulator:

- Registers/logs in a demo user.
- Creates or reuses a household.
- Creates or reuses a device.
- Saves household/device/device-key values to env.
- Sends readings at a configured interval.
- Uses `X-Device-Key` when available.
- Generates realistic daily household power patterns.
- Can inject spikes to exercise anomaly detection.

## NILM Pipeline Implementation

Main files:

- `ml/data/merge_raw.py`
- `ml/feature_extraction.py`
- `ml/train_nilm.py`
- `ml/evaluate.py`
- `ml/prediction.py`
- `ml/predict_nilm.py`

Implemented ML flow:

```bash
cd ml
python data/merge_raw.py
python feature_extraction.py data/appliance_data_real.csv
python train_nilm.py --data data/appliance_data_real.csv
python evaluate.py --model models/nilm_v1.pkl --features data/features_extracted.csv
python predict_nilm.py --csv data/appliance_data_real.csv --limit 10
```

The trained binary artifact is:

```text
ml/models/nilm_v1.pkl
```

It is intentionally ignored by git. Tracked artifacts include:

- `ml/models/nilm_v1_metadata.json`
- `ml/results/confusion_matrix.csv`
- `ml/results/classification_report.txt`
- `ml/results/eval_summary.json`

## NILM Prediction API

Endpoint:

```text
POST /api/v1/nilm/predict
Authorization: Bearer <jwt>
```

Input:

- A list of timestamped readings.
- Optional `window_size_s`, default `30`.

Output:

- Predicted appliance per feature window.
- Confidence.
- Per-class probabilities.
- Model/feature-set metadata.

Backend service:

- `backend/app/services/nilm_service.py`

It lazily loads ML dependencies so the backend can still start if the model or
native ML runtime is unavailable.

## Current NILM Dataset

Current real-data classes:

- `electric_kettle`
- `fan`
- `fridge`
- `iron`
- `mixer_grinder`
- `washing_machine`

Current capture summary:

| Appliance | Captures | Label |
|---|---:|---|
| Fridge normal | 1 | `fridge` |
| Washing machine normal wash | 3 | `washing_machine` |
| Washing machine super quick wash | 1 | `washing_machine` |
| Kettle boil | 3 | `electric_kettle` |
| Table fan speeds 1-3 | 6 | `fan` |
| Iron multi-cycle | 1 | `iron` |
| Mixer multi-cycle | 2 | `mixer_grinder` |
| Mixie normal | 1 | `mixer_grinder` |

Latest local dataset metrics:

| Metric | Value |
|---|---:|
| Raw rows | 7,911 |
| Feature windows | 2,092 |
| Classes | 6 |
| Feature set | `tapo_signature_v2` |

Class distribution by feature windows:

| Class | Windows |
|---|---:|
| `washing_machine` | 1,027 |
| `fridge` | 389 |
| `fan` | 374 |
| `mixer_grinder` | 142 |
| `iron` | 121 |
| `electric_kettle` | 39 |

## Current NILM Model Result

Latest local model:

| Metric | Value |
|---|---:|
| Train windows | 1,673 |
| Test windows | 419 |
| Test accuracy | 99.05% |
| CV mean accuracy | 99.52% |
| CV std deviation | 0.0034 |

Latest confusion matrix summary:

```text
electric_kettle -> correct: 8/8
fan             -> correct: 72/75, misread as iron: 3
fridge          -> correct: 78/78
iron            -> correct: 24/24
mixer_grinder   -> correct: 27/28, misread as washing_machine: 1
washing_machine -> correct: 206/206
```

Current main weakness:

```text
fan vs iron
```

Reason:

The newer fan captures are higher-power fan sessions, around 100-140 W. Some
of those windows overlap with lower-power/idle portions of iron behavior.

## Feature Set

Current feature set version:

```text
tapo_signature_v2
```

It uses 30-second time windows and includes:

- Mean/max/min/median power
- Power quantiles
- Power delta and standard deviation
- Active-power statistics
- On/off fraction
- High-power and very-high-power fractions
- Transition count
- Step-change features
- Rise time
- Estimated window energy
- Voltage/current summary features
- Cyclic behavior flag

Duration and sample interval are kept in feature CSVs for inspection, but they
are excluded from model training to avoid collection-setting leakage.

## Recent Dataset Improvements

Recently added local data:

- Washing-machine normal wash run 2
- Washing-machine normal wash run 3
- Washing-machine super quick wash, 15 minutes
- Table fan speed 1 repeat
- Table fan speed 2 repeat
- Table fan speed 3 repeat

Impact:

- Washing-machine windows increased strongly.
- Fan diversity improved.
- Model became more realistic.
- Overall accuracy stayed high, but fan-vs-iron confusion appeared.

## Current Local Git State Note

The Priority 1 NILM prediction implementation was pushed to the remote `dev`
branch up to commit:

```text
96181d8 Prepare the backend NILM runtime
```

The latest washing-machine and fan dataset/model refresh is currently local and
not yet committed or pushed unless explicitly done later.

## Important Commands

Run full demo:

```bash
make demo-up
make demo-down
```

Backend tests:

```bash
backend/.venv/bin/pytest backend/tests
```

Frontend build:

```bash
cd frontend
npm run build
```

ML compile check:

```bash
python -m py_compile \
  ml/feature_extraction.py \
  ml/train_nilm.py \
  ml/evaluate.py \
  ml/prediction.py \
  ml/predict_nilm.py \
  ml/data/merge_raw.py
```

NILM training:

```bash
cd ml
python data/merge_raw.py
python train_nilm.py --data data/appliance_data_real.csv
python evaluate.py --model models/nilm_v1.pkl --features data/features_extracted.csv
```

NILM prediction:

```bash
python ml/predict_nilm.py --csv ml/data/appliance_data_real.csv --limit 10
```

## Verified State

Latest verified checks from the recent implementation work:

- Backend tests: `12 passed`
- Frontend build: passed
- ML scripts: compile successfully
- NILM CLI prediction: passed
- Backend NILM service prediction: works locally after installing `libomp`

macOS note:

```bash
brew install libomp
```

This is needed for the PyPI XGBoost wheel in the backend virtualenv.

## Current Gaps And Risks

Important gaps:

- No true aggregate household NILM yet.
- No synchronized main-line aggregate readings yet.
- No induction cooker, geyser, AC, TV, microwave, or laptop charger data yet.
- Fridge has only one real capture, so it needs more long cyclic sessions.
- Iron has only one strong multi-cycle capture, and now overlaps with fan.
- Kettle has only 39 feature windows, so it should get more sessions later.
- Evaluation currently splits windows from the same captures, so it is a
  development baseline, not final real-home generalization proof.
- Model artifact `nilm_v1.pkl` is ignored by git and must be regenerated or
  provided separately in deployment.
- Loading old `.pkl` artifacts across different scikit-learn versions can emit
  warnings; retraining in a consistent environment is preferred.

## Best Next Data Collection

Highest-priority data for model improvement:

1. Induction cooker
   - 3 low-power sessions
   - 3 medium-power sessions
   - 3 high/boil sessions
   - 3 simmer/pulsing sessions
   - 3 real cooking sessions

2. Iron
   - 3-5 thermostat-cycle sessions
   - Capture heating ON/OFF cycles clearly
   - This directly targets fan-vs-iron confusion

3. Fridge
   - 5-8 long sessions
   - 1-2 hours each
   - Include compressor ON/OFF cycles

4. Washing machine
   - 2-3 more clean super quick sessions
   - 2-3 spin-only sessions
   - 2-3 rinse/spin sessions

5. Kettle
   - 5-8 more boil sessions
   - Different water levels

## Month 2 Direction

Recommended next implementation steps:

1. Commit and push the latest dataset/model refresh when ready.
2. Add induction cooker support to the merge map after data arrives.
3. Add an appliance prediction view in the dashboard using `nilmAPI.predict`.
4. Start collecting synchronized aggregate household readings.
5. Move from smart-plug signature classification toward aggregate NILM.
6. Add model/version reporting to the dashboard.
7. Add clearer model cards: class counts, confidence, and known limitations.

## Final Project Pitch

NeuralWatt is now more than a basic dashboard. It has a working full-stack
energy monitoring foundation and an early appliance-intelligence layer. The
backend can ingest secure IoT readings, store them, broadcast live updates,
calculate analytics, estimate bills, detect anomalies, and run NILM predictions.
The frontend gives a usable monitoring dashboard. The ML pipeline can merge real
Tapo P110 data, extract appliance signatures, train an XGBoost model, evaluate
it, and serve predictions through both CLI and API.

The next leap is moving from isolated smart-plug appliance signatures to real
aggregate household disaggregation.
