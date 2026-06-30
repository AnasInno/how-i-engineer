# Recall Radar

Recall Radar is a local stock-to-alert triage automation for checking inventory CSV rows against public recall and safety alert pages.

## Problem

Small operators can miss recalls because checking every product safety or medicines alert against local stock is repetitive manual work.

## What it does

The CLI reads a local inventory CSV, loads sample or live public recall alerts, extracts structured identifiers, matches stock rows to alerts, and writes a Markdown action report plus a CSV review queue.

Live sources are:

- OPSS/GOV.UK product safety alerts, reports, and recalls.
- MHRA drug and device alerts.

## Quick start

```bash
cd automations/day-002-recall-radar
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
make smoke
```

The smoke run uses fictional sample inventory and sample recall records, so it does not need secrets or network access.

## Input

Default input: `data/sample_inventory.csv`.

Required columns:

```text
sku,name,brand,model,barcode,gtin,batch,expiry_date,location,quantity
```

The local web form saves edited inventory CSV to `data/web_inventory.csv`.

## Output

The sample run writes:

- `output/sample_recall_report.md`
- `output/sample_recall_matches.csv`

Live proof runs write:

- `output/live_recall_report.md`
- `output/live_recall_matches.csv`
- `output/alert_cache.json`

## Local web form

```bash
make web
```

The web form is a local wrapper around the same sample-mode CLI. Paste or edit inventory CSV, run Recall Radar, then download the generated report and matches CSV.

## Configuration

Copy `.env.example` to `.env` only for local live LLM extraction.

`--use-llm` uses OpenRouter model `qwen/qwen3.7-plus` only for structured extraction from public recall pages. Deterministic exact identifier matching remains the source of match confidence.

Supported private environment variables are:

- `OPENROUTER_API_KEY`
- `OPENROUTER_MODEL`
- `OPENROUTER_BASE_URL`

## Limitations

- Recall Radar is stock-to-alert triage, not legal, clinical, or safety certification.
- A human must review matched rows before taking operational action.
- Live recall pages can change format; deterministic identifiers are preferred over generated text.
- Sample inventory is fictional and safe to publish.

## Verification

```bash
make smoke
python3 ../../scripts/verify_daily_automation.py .
```

For live proof, provide a private env file path at runtime instead of committing secrets:

```bash
OPENROUTER_ENV_FILE=<private env file> OPENROUTER_MODEL=qwen/qwen3.7-plus make live-smoke
```
