# Curated Idea Queue

Anas owns research and idea curation.

The build automation may only ship ideas from this queue, or from an explicit
idea supplied by Anas in the current task. If there is no `ready` idea, the
builder must stop and ask for a curated option instead of inventing one.

## Builder Rules

- Do not generate fresh ideas.
- Do not browse for ideas unless Anas asks for research in the current task.
- Prefer the highest-priority `ready` idea.
- Reject ideas here if the concrete input/output, sample data, or demo path is missing.
- After shipping, update the chosen item to `shipped` with the automation path and commit hash.

## Idea Template

Copy this block into `Ready Ideas` when an idea is ready for a build agent.

```md
### IDEA-YYYY-MM-DD-01: Specific task title

Status: ready
Priority: 1
Score: 0/10
Persona:
Pain:
Current manual workflow:
Input:
Output:
One-day scope:
Sample data plan:
Optional LLM use:
Forbidden dependencies:
First smoke test:
Post angle:
Notes:
```

## Ready Ideas

No ready ideas yet.

## Active Shortlist

These are strong candidates, but they are not build-ready until Anas changes
`Status` to `ready`.

### IDEA-2026-06-22-01: Local Planning Lead Scout

Status: candidate-review
Priority: 1
Score: 10/10

Persona:
Small builders, roofers, window fitters, electricians, architects, surveyors,
and specialist trades who want local project leads before competitors reach the
homeowner.

Research signal:
- The official Planning Data API exposes planning and housing datasets for England:
  https://www.planning.data.gov.uk/docs
- A UK small builder described checking local planning applications for
  extensions and sending letters to applicants:
  https://www.reddit.com/r/smallbusinessuk/comments/1owqoz2/how_can_i_get_more_sales_as_a_small_builder/
- Commercial planning-lead products exist, which suggests market pull:
  https://www.planningpipe.co.uk/planning-leads/

Pain:
Trades manually search council/planning portals, hear about projects late, and
keep potential jobs in spreadsheets, notebooks, WhatsApp, or email.

Meet-them-where-they-are version:
A CLI or tiny local app that takes an area and trade profile, pulls or loads
planning applications, and exports a spreadsheet of scored leads. No CRM setup
required.

Custom inputs:
- postcode, local authority, town, or radius
- trade keywords such as loft, extension, roof, windows, solar, EV charger,
  kitchen, drainage, landscaping
- planning status filter such as submitted, validated, approved, refused,
  appeal, withdrawn
- application type filter such as householder, extension, commercial,
  conversion, new build
- date window such as last 7 days or last 30 days
- minimum/maximum project value if available
- exclude keywords such as tree works, signage, telecoms, discharge condition
- output format: CSV, Markdown, or CRM import CSV

Output:
- scored leads CSV
- address or site description
- planning reference and source link
- likely trade category
- status and decision date
- reason it matched
- suggested outreach angle
- confidence score

Solution variants:
- Trade Lead Scout: trade profile in, local planning leads out.
- Approved But Not Started Watch: only approved applications that likely now
  need contractors.
- Extension Opportunity Finder: only homeowner extensions, lofts, garages,
  and conversions.
- Competitor/Area Watch: monitor named streets, postcodes, or local authority
  areas for fresh activity.

One-day scope:
Use sample planning records first, plus an adapter shaped for the public API.
Build deterministic keyword scoring and CSV export.

Sample data plan:
Create 10 fake planning records with varied descriptions, statuses, dates,
and council links. Include at least 3 obvious matches and 3 false positives.

Optional LLM use:
Small OpenRouter call can summarize the application description and suggest an
outreach angle. The core scoring must work without the LLM.

Forbidden dependencies:
No email sending, no live CRM write, no scraping private portals, no homeowner
personal data beyond public planning data.

First smoke test:
Run with `--area "Manchester" --trade "roofer" --days 30` against sample data.
Assert that loft/roof/extension records rank above unrelated tree/signage
records and that a CSV is produced.

Post angle:
"A local trade should not spend Monday morning opening council tabs. This turns
public planning data into a short list of nearby jobs worth checking."

Open questions for Anas:
- Which first persona: builder, roofer, architect, or electrician?
- Should first version use official Planning Data API live, or sample-first with
  API adapter?
- Should outreach angle be included, or keep it as pure lead triage?

### IDEA-2026-06-22-02: Tender Fit Scout

Status: candidate-review
Priority: 2
Score: 10/10

Persona:
Small suppliers such as cleaning companies, security firms, maintenance teams,
training providers, IT support shops, caterers, and local service businesses
that want public-sector work but do not have a bid team.

Research signal:
- Contracts Finder is the official UK public contract opportunity search:
  https://www.gov.uk/contracts-finder
- Contracts Finder has API documentation:
  https://www.contractsfinder.service.gov.uk/apidocumentation
- SME procurement barriers include admin burden and resource-heavy
  prequalification:
  https://www.achilles.com/industry-insights/removing-barriers-for-smes-to-bid-for-tenders/
- Small UK business owners ask how to start with low-value tenders:
  https://www.reddit.com/r/smallbusinessuk/comments/1fcoes6/tenders_for_1st_time_small_business/

Pain:
Owners skim tender emails and portals, open too many irrelevant opportunities,
and waste time reading tenders they were never a fit for.

Meet-them-where-they-are version:
The owner fills in a short company profile once, then drops in a tender export
or uses a public feed. The tool returns "apply", "maybe", or "ignore" with
plain-English reasons.

Custom inputs:
- company profile: services, regions, certifications, insurance level, company
  size, case-study keywords
- contract value range
- region/postcode radius
- deadline window
- CPV/service keywords
- excluded sectors or buyers
- risk tolerance: low admin only, include framework bids, include long shots
- required accreditations to detect, such as ISO, DBS, Cyber Essentials,
  CHAS, SafeContractor
- output format: bid/no-bid CSV, Markdown shortlist, or CRM import CSV

Output:
- ranked tender shortlist
- apply/maybe/ignore recommendation
- fit score
- deadline and urgency
- value and buyer
- location
- missing requirements
- reason to ignore if poor fit
- next action checklist

Solution variants:
- Micro Tender Finder: only small, low-value contracts suitable for tiny teams.
- Deadline Risk Filter: surfaces tenders closing soon or missing key docs.
- Framework Avoider: removes complex framework-heavy opportunities.
- Renewal Watch: spots expiring or recurring contracts worth preparing for.

One-day scope:
Use sample tender JSON/CSV shaped like Contracts Finder results. Build scoring,
filters, and a Markdown/CSV output.

Sample data plan:
Create 8 fake tenders across cleaning, IT, catering, security, and training.
Include deadline, value, location, requirements, and buyer.

Optional LLM use:
Small OpenRouter call can summarize tender text and explain fit. Deterministic
rules must still produce a usable shortlist without LLM.

Forbidden dependencies:
No live submission, no bid writing as the core product, no account login, no
claiming eligibility without evidence.

First smoke test:
Run with a sample cleaning-company profile and assert that local cleaning
tenders rank above national IT/framework tenders.

Post angle:
"A small supplier should know in two minutes whether a tender is worth reading."

Open questions for Anas:
- First niche: cleaning, maintenance, IT support, training, or catering?
- Should output be owner-friendly "why/next action", or procurement-style
  scoring table?
- Should live API be included in v1, or sample/export-first?

### IDEA-2026-06-22-03: Restaurant Supplier Price Change Watcher

Status: candidate-review
Priority: 3
Score: 9/10

Persona:
Independent restaurant owners, cafe operators, chefs, caterers, and food-truck
owners who buy from suppliers and manage margins in spreadsheets or invoices.

Research signal:
- Restaurant operators describe the manual method as a weekly "Price Book"
  spreadsheet updated from invoices:
  https://www.reddit.com/r/restaurantowners/comments/1op4fi6/how_are_you_keeping_track_of_vendor_price_changes/
- One operator said distributor price comparison is time-consuming and sometimes
  skipped:
  https://www.reddit.com/r/restaurant/comments/1r6mrj5/restaurant_owners_how_bad_have_food_costs_gotten/
- Restaurant costing products emphasize supplier price changes and margin
  tracking:
  https://www.restaurant365.com/blog/menu-cost-calculator-a-restaurant-owners-guide/

Pain:
Supplier prices move, but menu prices and recipe cost sheets lag behind. Owners
only notice margin loss after the week/month is already gone.

Meet-them-where-they-are version:
Drop in last week's supplier CSV and this week's supplier CSV. The tool outputs
what changed, what rose most, and which items need a menu/margin review.

Custom inputs:
- previous supplier file
- current supplier file
- supplier name
- item matching column such as SKU, item name, or description
- threshold percentage or amount change
- category filters such as meat, dairy, dry goods, drinks, packaging
- ignore list for seasonal items
- optional recipe/menu CSV with ingredient quantities
- optional target food-cost percentage
- output format: CSV, Markdown, or printable kitchen/admin report

Output:
- price-change report
- biggest increases and decreases
- new or missing items
- potential duplicate item names
- optional affected menu items
- optional margin warning
- suggested action: review, switch supplier, update menu price, ignore

Solution variants:
- Vendor CSV Diff: compare two price lists and flag changes.
- Invoice Price Book Updater: update an existing price-book CSV from a new
  invoice export.
- Menu Margin Watch: connect ingredient price changes to recipe/menu costs.
- Supplier Comparison Sheet: compare the same item across two suppliers.

One-day scope:
Start with CSV only. Build item matching, percentage changes, threshold filters,
and Markdown/CSV outputs.

Sample data plan:
Create two fake supplier CSV files plus an optional menu recipe CSV. Include
eggs, beef, chicken, flour, oil, cheese, packaging, and drinks.

Optional LLM use:
Not needed for v1. A tiny LLM call could explain the report in owner-friendly
language, but deterministic output is enough.

Forbidden dependencies:
No POS integration, no accounting integration, no invoice OCR in the first
version, no live supplier portal scraping.

First smoke test:
Run with `previous.csv`, `current.csv`, and `--threshold 8`. Assert that items
over threshold appear, unchanged items are suppressed, and optional menu rows
show affected dishes.

Post angle:
"Restaurants already have the price lists. This just tells them what changed
before the margin disappears."

Open questions for Anas:
- Should v1 be pure CSV diff, or include recipe/menu impact?
- Which is more compelling: chef/admin report or owner margin report?
- Should it output suggested menu price changes, or just flag risks?

## Backlog Candidates

These are worth keeping, but not the immediate top-three focus.

### IDEA-2026-06-22-04: Contractor Change Order Pack Builder

Status: candidate-review
Priority: 4
Score: 9/10
Persona: builders, subcontractors, trades, small contractors
Pain: verbal extras and messy site notes turn into unpaid work or disputed
invoices.
Research signal:
- Change order admin described as time-consuming:
  https://www.reddit.com/r/ConstructionManagers/comments/1ij9g2g/change_order_management/
- Contractors discuss losing money on verbal change orders:
  https://www.reddit.com/r/GeneralContractor/comments/1qsp5u8/honest_question_is_losing_money_on_verbal_change/
Meet-them-where-they-are version:
Paste messy site notes and cost lines. Output a change-order draft, approval
wording, and invoice CSV.
Custom inputs:
job name, client name, site notes, labour lines, material lines, markup,
approval terms, output format.
First smoke test:
Messy site note text -> clean change-order Markdown and invoice rows.

### IDEA-2026-06-22-05: Companies House Trigger Scout

Status: candidate-review
Priority: 5
Score: 8/10
Persona: accountants, recruiters, B2B agencies, compliance shops, local service
providers
Pain: useful company events exist publicly, but discovery and monitoring are
manual.
Research signal:
- Companies House public API:
  https://developer.company-information.service.gov.uk/
- Filing history endpoint:
  https://developer-specs.company-information.service.gov.uk/companies-house-public-data-api/reference/filing-history
Meet-them-where-they-are version:
SIC/location/watchlist input -> trigger CSV with company, event, why it matters,
and next action.
Custom inputs:
SIC codes, location/postcode, company age, event types, watchlist, exclusion
keywords, output format.
First smoke test:
Sample company events -> scored trigger list.

### IDEA-2026-06-22-06: Agency Weekly Client Proof Digest

Status: candidate-review
Priority: 6
Score: 8/10
Persona: SEO, PPC, content, and local marketing agencies
Pain: reporting narrative and weekly updates take too much manual stitching.
Research signal:
- Reporting narrative described as time-consuming:
  https://www.reddit.com/r/SEO/comments/1pwyhfb/anybody_else_hate_writing_monthly_client_reports/
- Client reporting pain includes pulling data from too many platforms:
  https://www.reddit.com/r/PPC/comments/1myo7la/client_reporting_feels_way_more_manual_than_it/
Meet-them-where-they-are version:
Work-log CSV plus metrics CSV -> client-ready weekly Markdown update.
Custom inputs:
client name, reporting period, work log, metrics export, tone, KPI focus,
known risks, output format.
First smoke test:
Sample work log and metrics CSV -> concise client update.

### IDEA-2026-06-22-07: Ecommerce Order Reply Drafts

Status: candidate-review
Priority: 7
Score: 7/10
Persona: Shopify/ecommerce operators handling support through email or a
helpdesk
Pain: repetitive order tracking, returns, shipping, and refund emails take time.
Research signal:
- Shopify store owners complain about repetitive "where is my order" emails:
  https://www.reddit.com/r/shopify/comments/1k7k3zf/curious_how_others_are_handling_repetitive/
- E-commerce support teams spend hours on tracking questions:
  https://www.reddit.com/r/ecommerce/comments/1p3n48i/manual_order_tracking_emails_are_eating_3_hours/
Meet-them-where-they-are version:
Exported emails plus orders CSV -> reply drafts and human-needed flags. Real
value likely needs Gmail, Shopify, or Gorgias integration later.
Custom inputs:
orders CSV, support messages export, policy text, tone, allowed actions,
escalation rules, output format.
First smoke test:
Sample order data plus 10 support messages -> categorized reply drafts.

## Shipped Ideas

- day-001-messy-notes-to-action-draft
