# Daily Automation Lane — Load First

You are building Anas's public daily AI automation engine.

Goal: one simple, effective, open-source automation per day. Not agent slop. Not a platform. A tiny tool with obvious usefulness and proof.

## Source of truth

- Workflow: `codex/daily-automation/WORKFLOW.md`
- Idea filter: `codex/daily-automation/IDEA-FILTER.md`
- Curated idea queue: `codex/daily-automation/CURATED-IDEA-QUEUE.md`
- Local web shell: `codex/daily-automation/LOCAL-WEB-SHELL.md`
- Public ship flow: `codex/daily-automation/PUBLIC-SHIP-FLOW.md`
- Ship checklist: `codex/daily-automation/SHIP-CHECKLIST.md`
- Posting rules: `codex/daily-automation/POSTING-RULES.md`
- Templates: `codex/daily-automation/PROMPT-TEMPLATES.md`
- Session record: `codex/daily-automation/WORK-DONE.md`

## Default command path

1. Pick one `ready` idea from `codex/daily-automation/CURATED-IDEA-QUEUE.md`, or use an explicit idea supplied by Anas in the current task.
2. Stop if there is no curated `ready` idea. Do not invent one.
3. Confirm it still passes the idea filter.
4. Prefer `python3 scripts/run_daily_automation_pipeline.py --idea "Idea name"` for scaffold + verification packet.
5. Build the smallest useful version inside the generated folder.
6. Re-run `python3 scripts/run_daily_automation_pipeline.py --path automations/day-XXX-slug`.
7. Stop unless approval exists for external actions.
8. If git push is approved, export a clean public repo first. Do not push the whole operator checkout.

## Definition of done

A day is done when the release packet says:

- README exists
- smoke command exists and passes
- local web form exists when useful and wraps the same CLI command
- sample input/output exists
- verification report exists
- X and LinkedIn drafts exist
- limitations are documented
- approval state is explicit
- public export/check passes before any public push
