# Verification

Status: **PASS**
Checked: 2026-06-30T01:12:53.495753+00:00
Folder: `day-002-recall-radar`

## Checks

- ✅ make smoke passed
- ✅ local web shell config passed
- ✅ sample output exists: live_recall_matches.csv, sample_recall_report.md, alert_cache.json, live_recall_report.md, sample_recall_matches.csv

## Smoke log

```text
python3 scripts/run.py --input data/sample_inventory.csv --output output/sample_recall_report.md --csv-output output/sample_recall_matches.csv --source sample
Wrote output/sample_recall_report.md
Wrote output/sample_recall_matches.csv
```


## Web shell check

```text
OK: web_config.json
```

## Live OpenRouter run

Command:

```text
OPENROUTER_ENV_FILE=<private env file> OPENROUTER_MODEL=qwen/qwen3.7-plus make live-smoke
```

Model: `qwen/qwen3.7-plus`

Source feeds and extra URLs:

- `https://www.gov.uk/product-safety-alerts-reports-recalls.atom`
- `https://www.gov.uk/drug-device-alerts.atom`
- `https://www.gov.uk/product-safety-alerts-reports-recalls/product-recall-azara-travel-adaptor-2601-0270`
- `https://www.gov.uk/drug-device-alerts/class-2-medicines-recall-becton-dickinson-uk-ltd-chloraprep-2-percent-1ml-and-chloraprep-frepp-2-percent-1-dot-5ml-applicators-el-26-a-slash-26`

Outputs:

- `output/live_recall_report.md`
- `output/live_recall_matches.csv`

Observed live metrics:

- Alerts reviewed: 13
- Inventory rows checked: 4
- Candidate manual comparisons avoided = alerts * inventory rows: 52
- Rows needing human review: 2

Result status: PASS. The live report and live CSV exist, and the live CSV matched `ADP-001` and `MED-001`.
