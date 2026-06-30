---
name: daily-ai-automation-ship
description: "Build, verify, and package one tiny runnable daily AI automation."
---

# Daily AI Automation Ship

Use when building an automation under `automations/day-XXX-slug/`.

## Workflow

1. Read `codex/daily-automation/LOAD-FIRST.md`, `CURATED-IDEA-QUEUE.md`, `LOCAL-WEB-SHELL.md`, `PUBLIC-SHIP-FLOW.md`, and `SHIP-CHECKLIST.md`.
2. Pick only a `ready` curated idea, or an explicit idea supplied by Anas in the current task. Stop if none exists.
3. Create a folder with `python3 scripts/new_daily_automation.py "Idea"` unless one already exists.
4. Build the smallest useful CLI/local tool.
5. Add sample input and generated output.
6. Add or update `web_config.json` and `make web` when a local form helps parse inputs or download outputs.
7. Make `make smoke` pass.
8. Run `python3 scripts/verify_daily_automation.py automations/day-XXX-slug`.
9. Run `python3 scripts/draft_social_post.py automations/day-XXX-slug`.
10. Run `python3 scripts/release_packet.py automations/day-XXX-slug`.
11. Stop at the approval gate for push/post actions.
12. If Anas explicitly approves public git push, configure `Anas Abdi <abdianas919@gmail.com>`, export with `scripts/export_public_daily_automation_repo.py`, run `scripts/public_release_check.py` on the export, then push the exported repo.

## Hard rules

- Do not touch unrelated career assets.
- Do not invent or research a new idea during a build run.
- Do not include secrets or private data.
- Do not build a platform.
- Do not push the whole operator checkout as the public repo.
- Do not claim live posting or pushing unless approval gate passes and the action actually happened.
