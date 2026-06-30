# Recall Radar Report

## Summary

Generated: 2026-06-30T01:13:24+00:00
Inventory rows checked: 4
Alerts reviewed: 13
Matched inventory rows: 2
Rows needing human review: 2

## Action required

- `ADP-001` — Universal Travel Adaptor at Stockroom (qty 3)
  - Alert: Product Recall: Azara Travel Adaptor (2601-0270)
  - Match: exact_barcode (99) via barcode
  - Action: The local authority is requiring the recall of the product from end users. Consumers who own the product are advised to stop using it immediately and contact the distributor they purchased from for redress.
  - Human next step: Open the alert URL and verify identifiers, batch, and quantity before taking stock action.
  - Source: https://www.gov.uk/product-safety-alerts-reports-recalls/product-recall-azara-travel-adaptor-2601-0270

- `MED-001` — ChloraPrep 1mL applicators at Treatment Room (qty 60)
  - Alert: Class 2 Medicines Recall: Becton Dickinson UK Ltd, ChloraPrep 2% 1mL and ChloraPrep Frepp 2% 1.5mL applicators, EL(26)A/26
  - Match: exact_gtin (99) via gtin
  - Action: Stop supplying the affected batches. Quarantine all remaining stock and return it to your supplier using your supplier’s approved process.
  - Human next step: Open the alert URL and verify identifiers, batch, and quantity before taking stock action.
  - Source: https://www.gov.uk/drug-device-alerts/class-2-medicines-recall-becton-dickinson-uk-ltd-chloraprep-2-percent-1ml-and-chloraprep-frepp-2-percent-1-dot-5ml-applicators-el-26-a-slash-26

## Review queue

No fuzzy review matches found.

## No-match inventory count

Inventory rows without a likely alert match: 2

## Time saved proxy

Alerts reviewed: 13
Inventory rows checked: 4
Candidate manual comparisons avoided = alerts * inventory rows: 52
Rows needing human review: 2
Automation runtime seconds: 578.40

The operator now reviews only the matched/review rows instead of opening every alert against every stock row.

## Source notes

- MHRA/GOV.UK drug and device alerts
- OPSS/GOV.UK product safety alerts

Output CSV: output/live_recall_matches.csv

## Limitations

Recall Radar is a stock-to-alert triage aid, not legal, clinical, or safety certification.
Exact identifier matches are strongest; fuzzy name matches must be checked by a person before action.
Public pages can change structure, so live extraction may miss fields that are visible to a human.
