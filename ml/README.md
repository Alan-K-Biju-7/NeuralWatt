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
```

## Real Tapo P110 Exports

Real Tapo P110 captures copied into `data/raw/` can be merged and trained with:

```bash
cd ml
python data/merge_raw.py
python feature_extraction.py data/appliance_data_real.csv
python train_nilm.py --data data/appliance_data_real.csv
python evaluate.py --model models/nilm_v1.pkl --features data/features_extracted.csv
```

The current real dataset contains:

| Appliance | Captures | Label |
|---|---:|---|
| kettle boil | 3 | `electric_kettle` |
| table fan speeds 1-3 | 3 | `fan` |
| mixer multi-cycle | 1 | `mixer_grinder` |

`data/raw_quality_report.csv` records row counts, max power, missing timing
gaps, and outlier counts for each raw capture. The current files have no power
outliers. The mixer capture has timing gaps, so treat mixer metrics as early
baseline results until more mixer sessions are collected.

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

## Tapo P110 Integration

`feature_extraction.load_tapo_csv()` normalizes common Tapo/API fields such as
`timestamp_utc`, `current_power`, `appliance`, and `state` into the canonical
`timestamp`, `power_w`, `appliance_label`, and `relay_state` schema. It also
maps `kettle`, `table_fan`, and `mixer` into the training labels
`electric_kettle`, `fan`, and `mixer_grinder`.
