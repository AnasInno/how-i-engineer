# Public Ship Flow

This is the exact daily automation release flow.

## 1. Build Locally

Use only a curated `ready` idea or an explicit idea from Anas.

```bash
python3 scripts/run_daily_automation_pipeline.py --idea "Idea name"
```

or for an existing automation:

```bash
python3 scripts/run_daily_automation_pipeline.py --path automations/day-XXX-slug
```

The local build must produce:

- runnable CLI
- `make smoke`
- `make web` when a friendly input/download form helps
- sample input and output
- `VERIFY.md`
- X and LinkedIn drafts
- release packet

## 2. Stop At The Gate

External actions need explicit approval. Build, verify, draft, and package are
local. Public push and live social posting are external.

```bash
python3 scripts/check_approval.py day-XXX-slug git-push
```

If approval is missing, stop and report what is ready.

## 3. Do Not Push The Operator Repo

The working `ai-deployment-engineer-kit` checkout can contain private career
assets, application notes, browser profiles, or local-only evidence. Do not push
that whole checkout as the public daily automation repo.

Publish from a clean export folder instead.

## 4. Configure Git Identity

Use Anas's public author identity before committing or pushing:

```bash
git config user.name "Anas Abdi"
git config user.email "abdianas919@gmail.com"
```

If the last local commit was made with the wrong identity and has not been
pushed, amend it:

```bash
git commit --amend --reset-author --no-edit
```

## 5. Export The Public Repo

```bash
python3 scripts/export_public_daily_automation_repo.py \
  --dest ../daily-ai-automation-kit \
  --force \
  --init-git \
  --commit "Initial public daily automation kit"
```

The export includes only the daily automation lane:

- daily automation docs
- repo-local daily automation skills
- reusable scripts
- shipped automations
- public post drafts and release packets

It excludes career assets, inbox material, browser profiles, private profiles,
temporary files, and private workspace history.

## 6. Run Public Safety Check

```bash
python3 scripts/public_release_check.py ../daily-ai-automation-kit
```

Do not push unless this passes.

## 7. Push Publicly

Create the public repo once:

```bash
gh repo create AnasInno/daily-ai-automation-kit \
  --public \
  --source ../daily-ai-automation-kit \
  --remote origin \
  --push
```

For later updates:

```bash
cd ../daily-ai-automation-kit
git push origin main
```

## 8. Report Back

Report:

- public repo URL
- commit hash
- checks run
- what shipped
- whether social drafts are ready
