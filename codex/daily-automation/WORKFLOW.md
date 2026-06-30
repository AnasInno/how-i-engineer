# Daily Automation Workflow

## 0. Start clean

Inspect repo state first. Do not overwrite unrelated dirty files.

```bash
git status --short
```

## 1. Select one curated pain

Read `codex/daily-automation/CURATED-IDEA-QUEUE.md`.

Use the highest-priority `ready` idea, or an explicit idea supplied by Anas in
the current task. Do not invent a fresh idea during the build run.

Stop if no curated idea is ready.

Capture the selected idea in `IDEA.md`:

- user/persona
- boring pain
- current manual workflow
- input
- output
- why this is small enough for one day
- rejection risks

Use web research only when Anas explicitly asks for more research in the current
task. The default builder role is implementation, not idea curation.

## 2. Create project folder

Preferred full local pipeline:

```bash
python3 scripts/run_daily_automation_pipeline.py --idea "Voice note action item extractor"
```

Scaffold only:

```bash
python3 scripts/new_daily_automation.py "Voice note action item extractor"
```

This creates:

```text
automations/day-XXX-slug/
  README.md
  IDEA.md
  Makefile
  pyproject.toml
  .env.example
  web_config.json
  data/sample_input.txt
  output/.gitkeep
  scripts/run.py
  tests/test_smoke.py
  VERIFY.md
```

## 3. Build the smallest useful tool

The tool should have a direct command like:

```bash
make smoke
```

Add a tiny local web form when it helps the operator enter filters, paste data,
or download outputs:

```bash
make web
```

The web form must wrap the same local automation command. Do not turn it into a
hosted app, database-backed product, or separate frontend project.

## 4. Verify

```bash
python3 scripts/verify_daily_automation.py automations/day-XXX-slug
```

This writes `VERIFY.md` and returns non-zero for missing proof.

## 5. Draft public posts

```bash
python3 scripts/draft_social_post.py automations/day-XXX-slug
```

This writes drafts under `drafts/daily-automation/day-XXX-slug/`.

## 6. Build release packet

```bash
python3 scripts/release_packet.py automations/day-XXX-slug
```

The packet states readiness, verification status, post draft paths, and approval gate state.

## 7. Approval-gated external actions

Do not push or post live unless:

```bash
python3 scripts/check_approval.py day-XXX-slug git-push
python3 scripts/check_approval.py day-XXX-slug x-post
python3 scripts/check_approval.py day-XXX-slug linkedin-post
```

passes for the exact action.

## 8. Public open-source release

When Anas approves a public git push, do not push the whole operator checkout.
This workspace can contain private career/application material that is unrelated
to the automation lane.

Use the clean export flow:

```bash
git config user.name "Anas Abdi"
git config user.email "abdianas919@gmail.com"
python3 scripts/export_public_daily_automation_repo.py --dest ../daily-ai-automation-kit --force --init-git --commit "Initial public daily automation kit"
python3 scripts/public_release_check.py ../daily-ai-automation-kit
```

Then create or update the public GitHub repo from the exported folder.

See `codex/daily-automation/PUBLIC-SHIP-FLOW.md` for the exact push commands.
