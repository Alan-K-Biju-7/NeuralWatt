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

## Target Appliance Classes

1. `fridge`
2. `washing_machine`
3. `geyser`
4. `iron`
5. `microwave`
6. `mixer_grinder`
7. `tv`
8. `fan`
9. `laptop_charger`

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

## Target Metrics

| Metric | Target |
|---|---|
| Test accuracy | `>= 80%` |
| Precision per class | `>= 75%` |
| Recall per class | `>= 80%` |

## Tapo P110 Integration TODO

When real plug data arrives, update `load_csv()` in `feature_extraction.py`:

```python
df = df.rename(columns={
    "current_power": "power_w",
    "device_alias": "appliance_label",
})
```
