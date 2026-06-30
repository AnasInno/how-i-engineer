# Recall Radar

## Persona

Small clinic, ecommerce, facilities, or office operators who keep local stock and need to notice public recalls quickly.

## Pain

They have to open public recall pages and manually compare product names, brands, models, barcodes, GTINs, and batches against stock lists.

## Current workflow

Someone scans OPSS/GOV.UK and MHRA alerts, copies details into a spreadsheet, searches inventory row by row, and escalates possible matches.

## Input

`data/sample_inventory.csv`

## Output

- `output/sample_recall_report.md`
- `output/sample_recall_matches.csv`

## One-day scope

Recall Radar stays narrow: local CSV in, public recall alerts in, deterministic match report out. The demo runs from sample data in under two minutes and the live path only adds public-page extraction.

## Idea filter score

- Boring/common pain: 2/2
- Obvious I/O: 2/2
- Demo under two minutes: 2/2
- Saves manual review effort: 2/2
- Clear post story: 2/2

Total: 10/10

## Rationale

The story is easy to explain: reduce all alert-by-stock comparisons to the few rows a human should review, without pretending to certify safety decisions.

## Rejection risks

Too much scope would turn this into compliance software. The daily automation version must remain a triage assistant with public sources, fictional samples, and human review.
