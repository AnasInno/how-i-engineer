I'm building TeachClaw as the serious product, and shipping tiny practical AI automations on the side.

Today: Recall Radar.

Small operators should not have to open every public recall alert and compare it row-by-row against local stock.

What I built:
- inventory CSV in
- live OPSS/GOV.UK product safety + MHRA drug/device alert pages in
- Markdown action report + CSV review queue out

Live proof:
- fetched 13 public OPSS/MHRA alert pages
- ran Qwen3.7 Plus structured extraction through OpenRouter
- deterministic barcode/GTIN matching reduced 52 alert × stock comparisons to 2 rows needing human review

Limit: this is triage, not legal, clinical, or safety certification. A human still checks the matched rows before action.

Repo: https://github.com/AnasInno/how-i-engineer
