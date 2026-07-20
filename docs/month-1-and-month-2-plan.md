# NeuralWatt Progress And Next Plan

Last updated: 2026-06-11

## Project Overview

NeuralWatt is an AI-based smart household energy platform. It monitors live
electricity usage, stores readings, displays usage through a web dashboard,
detects abnormal energy patterns, estimates electricity cost, and now includes
an early appliance-intelligence layer using labelled smart-plug data.

The long-term target is a system that can:

- Monitor real-time power usage.
- Estimate appliance-level usage.
- Detect abnormal energy behavior.
- Forecast electricity bills.
- Recommend better appliance usage times.
- Support solar-aware scheduling later.
- Explain model decisions and confidence clearly.

## Completed Foundation

The core monitoring system is implemented.

- FastAPI backend.
- MongoDB storage.
- React dashboard.
- JWT user authentication.
- Household and device management.
- Device-key based ingestion with `X-Device-Key`.
- Canonical reading fields such as `power_w`, `voltage_v`, and `current_a`.
- Backward compatibility for older fields such as `watts`, `voltage`, and
  `current`.
- Simulator for safe local demos.
- WebSocket live updates.
- Daily and hourly analytics.
- Usage summary and peak-hour views.
- KSEB-style cost and bill estimation.
- Basic Z-score anomaly detection.
- Alert configuration foundation.
- API and architecture documentation.
- Backend tests and frontend production build path.

## Completed Appliance Intelligence

The early NILM layer is implemented as a smart-plug appliance signature
classifier.

- Tapo smart-plug CSV merge pipeline.
- Raw data quality report.
- Canonical appliance training CSV.
- Feature extraction with time windows.
- XGBoost training pipeline.
- Evaluation pipeline with confusion matrix and classification report.
- Model metadata export.
- CLI prediction script.
- Backend NILM prediction API.
- Frontend API helper for future dashboard integration.

Current NILM classes:

- `electric_kettle`
- `fan`
- `fridge`
- `iron`
- `mixer_grinder`
- `washing_machine`

Latest local model summary:

| Metric | Value |
|---|---:|
| Raw rows | 22,723 |
| Active feature windows | 4,877 |
| Classes | 6 |
| Feature set | `tapo_signature_v3` |
| Grouped holdout accuracy | 86.16% |
| GroupKFold CV mean accuracy | 71.89% |
| GroupKFold CV std deviation | 0.2688 |

Current known model weakness:

```text
transfer to unseen capture sessions
```

The v3 model no longer trains on voltage/current-derived features, and it uses
GroupKFold by `capture_id`/`session_id` instead of random window splits. The
lower CV score is more honest because it measures generalization to unseen
capture sessions.

## Important Limitation

The current model is not yet true aggregate household NILM.

Current model:

```text
single appliance smart-plug readings -> appliance class prediction
```

Future target:

```text
aggregate household mains readings -> appliance-level disaggregation
```

To reach true NILM, the project still needs synchronized aggregate household
main-line readings plus Tapo appliance-level labels collected on the same clock.

## Current Demonstration Flow

A strong demo can show:

1. Start MongoDB, backend, frontend, and simulator.
2. Log in to the dashboard.
3. Show live power readings.
4. Show usage charts and KPIs.
5. Show KSEB-style bill estimate.
6. Show anomaly detection.
7. Show the real Tapo appliance dataset.
8. Run feature extraction and training.
9. Run NILM prediction from CLI.
10. Show model evaluation and confusion matrix.
11. Explain that full aggregate disaggregation is the next research step.

## Next Development Priorities

Highest priority:

- Collect induction cooker data at low, medium, high, simmer, and real cooking
  modes.
- Collect more iron thermostat-cycle sessions to reduce fan-vs-iron confusion.
- Collect longer fridge sessions with compressor cycles.
- Add a dashboard appliance prediction view using the existing NILM API.
- Start synchronized aggregate household reading collection.

Useful additional data:

- More kettle boil sessions with different water levels.
- Washing-machine spin-only and rinse-spin modes.
- Extra clean super-quick washing-machine sessions.
- More low-power appliance classes after the core classes are stable.

## Success Measure For The Current Stage

The current stage is successful because the project has moved from only
monitoring to early appliance intelligence:

- The monitoring system works.
- Real appliance data is collected.
- Features are extracted.
- A baseline model trains successfully.
- Evaluation reports are generated.
- Predictions work through CLI and backend API.
- Limitations are documented honestly.

The next major success measure is true aggregate NILM using synchronized
main-line and appliance-level readings.
