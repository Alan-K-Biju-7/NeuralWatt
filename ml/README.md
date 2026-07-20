# NeuralWatt ML Pipeline

NILM appliance classification pipeline for the NeuralWatt energy monitoring
system.

## Current Stage

Phase 1: appliance signature learning from labelled Tapo P110 smart plug data.

## Folder Structure

```text
ml/
|-- data/
|   |-- raw/                       # Drop Tapo P110 CSV exports here
|   `-- sample_appliance_data.csv  # Smoke test data
|-- models/                        # Trained artifacts saved here
|-- results/                       # Evaluation outputs
|-- feature_extraction.py
|-- train_nilm.py
|-- evaluate.py
`-- requirements.txt
```

## Input CSV Format

| Column | Type | Example |
|---|---|---|
| `timestamp` | ISO8601 datetime | `2026-05-20 06:00:00` |
| `power_w` | float, watts | `1450.0` |
| `appliance_label` | string | `geyser` |

Optional columns such as `capture_id` or `session_id` are allowed. The feature
extractor uses them to avoid mixing windows across separate appliance captures.

## Target Appliance Classes

1. `fridge`
2. `washing_machine`
3. `geyser`
4. `iron`
5. `microwave`
6. `mixer_grinder`
7. `tv`
8. `fan`
9. `electric_kettle`
10. `laptop_charger`

## Quick Start

```bash
cd ml
python -m pip install -r requirements.txt

# Smoke test
python feature_extraction.py data/sample_appliance_data.csv

# Train
python train_nilm.py --data data/sample_appliance_data.csv

# Evaluate
python evaluate.py --model models/nilm_v1.pkl --features data/features_extracted.csv

# Predict
python predict_nilm.py --csv data/appliance_data_real.csv --limit 10
```

## Real Tapo P110 Exports

Real Tapo P110 captures copied into `data/raw/` can be merged and trained with:

```bash
cd ml
python data/merge_raw.py
python feature_extraction.py data/appliance_data_real.csv
python train_nilm.py --data data/appliance_data_real.csv
python evaluate.py --model models/nilm_v1.pkl --features data/features_extracted.csv
python predict_nilm.py --csv data/appliance_data_real.csv --limit 10
```

The current real dataset contains:

| Appliance | Captures | Label |
|---|---:|---|
| fridge normal | 1 | `fridge` |
| washing machine normal wash | 3 | `washing_machine` |
| washing machine super quick wash | 1 | `washing_machine` |
| kettle boil | 3 | `electric_kettle` |
| table fan speeds 1-3 | 6 | `fan` |
| iron multi-cycle | 1 | `iron` |
| mixer multi-cycle | 2 | `mixer_grinder` |
| mixie normal | 1 | `mixer_grinder` |

`data/raw_quality_report.csv` records row counts, max power, missing timing
gaps, and outlier counts for each raw capture. The current files have no power
outliers. The fridge, washing-machine, and mixer captures have timing gaps, so
prefer collecting additional sessions before making final accuracy claims.

Current baseline:

| Metric | Value |
|---|---:|
| Classes | 6 |
| Raw rows | 22,723 |
| Active feature windows | 4,877 |
| Raw feature windows before inactive filtering | 5,743 |
| Feature set | `tapo_signature_v3` |
| Grouped holdout accuracy | `86.16%` |
| GroupKFold CV mean accuracy | `71.89%` |
| GroupKFold CV std deviation | `0.2688` |

The `tapo_signature_v3` feature set uses 30-second time windows and trains on
steady-state power, quantiles, active-power statistics, on/off transitions, step
changes, estimated window energy, cyclic behavior, and normalized shape
features: peak-to-mean ratio, coefficient of variation, duty cycle, and delta
versus rolling baseline. Voltage/current-derived features are intentionally
excluded to reduce location and sensor-transfer leakage.

Duration and sample interval are kept in the feature CSV for inspection but are
excluded from model training to avoid collection-setting leakage. `capture_id`
and `session_id` are also kept in the feature CSV so training and evaluation can
use `GroupKFold` by capture/session instead of random window splits.

The current grouped holdout uses `capture_id`, 26 total capture groups, and 8
held-out groups covering 513 windows across 5 appliance classes. The GroupKFold
CV mean is lower than the older random-window score because it measures
generalization to unseen capture sessions.

## Prediction

After training creates `models/nilm_v1.pkl`, run:

```bash
python predict_nilm.py --csv data/appliance_data_real.csv --limit 10
```

The predictor accepts canonical readings (`timestamp`, `power_w`) and common
Tapo-style columns normalized by the feature extractor. It uses the same
30-second windows as training and returns `predicted_appliance`, `confidence`,
and per-class probabilities when output is written to CSV:

```bash
python predict_nilm.py \
  --csv data/appliance_data_real.csv \
  --output results/predictions.csv
```

## Tapo P110 Screenshot-Derived NILM Data

Screenshot-derived appliance captures are stored in training and provenance
forms:

```text
data/tapo_p110_iron_box_nilm.csv          # NILM training schema
data/raw/tapo_p110_iron_box_2026-05-24.csv # source/provenance with metadata
data/tapo_p110_iron_box_2026-05-27_nilm.csv # second screenshot-derived capture
data/raw/tapo_p110_iron_box_2026-05-27.csv  # source/provenance rows
data/raw/tapo_p110_iron_box_2026-05-27_metadata.json
data/tapo_p110_washing_machine_2026-05-27_nilm.csv
data/raw/tapo_p110_washing_machine_2026-05-27.csv
data/raw/tapo_p110_washing_machine_2026-05-27_metadata.json
```

Use the `*_nilm.csv` files with the feature extractor. They contain the
training columns `timestamp`, `power_w`, and `appliance_label`, plus optional
capture metadata.

Observed values:

| Capture | Label | Runtime | Energy used today | Current power |
|---|---|---:|---:|---:|
| `2026-05-24` | `iron` | `0.6 h` | `0.089 kWh` | `<1 W` |
| `2026-05-27` | `iron` | `0.5 h` | `0.119 kWh` | `<1 W` |
| `2026-05-27` | `washing_machine` | `8.0 h` | `0.102 kWh` | `<1 W` |

The CSVs use one-minute derived readings whose interval energy sums to the
observed screenshot totals. Treat them as screenshot-derived labelled data, not
raw Tapo export. Once CSV/API exports are available, replace this approximation
with meter-level samples.

Example:

```bash
python feature_extraction.py data/tapo_p110_iron_box_nilm.csv
```

For model training, combine labelled appliance captures before running
`train_nilm.py`. Keep `capture_id` when combining multiple capture sessions.

## Target Metrics

| Metric | Target |
|---|---|
| Test accuracy | `>= 80%` |
| Precision per class | `>= 75%` |
| Recall per class | `>= 80%` |

## True Aggregate NILM Data Collection

The current model is still a smart-plug appliance signature classifier, not true
household aggregate disaggregation. To move to true NILM, collect synchronized
readings like this:

| Stream | Required fields | Purpose |
|---|---|---|
| Main-line sensor | `timestamp`, `aggregate_power_w`, `voltage_v`, `current_a`, `power_factor` | Household mains signal to disaggregate |
| Tapo P110 labels | `timestamp`, `appliance_label`, `power_w`, `capture_id` or `session_id` | Ground-truth appliance activity |
| Sync metadata | timezone, sample interval, clock source, household id | Align mains and appliance labels safely |

Run appliance-labelled sessions while the main-line sensor records continuously.
Keep the same clock source or record clock drift so aggregate readings and Tapo
labels can be joined by timestamp.

## Tapo P110 Integration

`feature_extraction.load_tapo_csv()` normalizes common Tapo/API fields such as
`timestamp_utc`, `current_power`, `appliance`, and `state` into the canonical
`timestamp`, `power_w`, `appliance_label`, and `relay_state` schema. It also
maps raw names such as `kettle`, `table_fan`, `fridge`, `iron`,
`washing_machine`, `mixie`, and `mixer` into stable training labels.
