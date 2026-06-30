# AGENTS.md — AI Deployment Engineer Kit

This repo is Anas Abdi's public AI Deployment/FDE proof kit. It now also contains the daily AI automation shipping lane.

## Load first

For any daily automation / public shipping task, read:

1. `codex/daily-automation/LOAD-FIRST.md`
2. `codex/daily-automation/WORKFLOW.md`
3. `codex/daily-automation/SHIP-CHECKLIST.md`
4. `codex/daily-automation/CURATED-IDEA-QUEUE.md`
5. `codex/daily-automation/LOCAL-WEB-SHELL.md`
6. `codex/daily-automation/PUBLIC-SHIP-FLOW.md`

Then use the repo-local skills in `.agents/skills/` when they match the task.

## Daily automation mission

Ship one tiny, boring, useful AI automation at a time.

Anas owns research and idea curation. Automation builders must pick from
`codex/daily-automation/CURATED-IDEA-QUEUE.md` or from an explicit user-provided
idea in the current task. Do not invent the daily idea from scratch.

A valid daily automation:
- solves one clear workflow pain
- is runnable locally in minutes
- includes sample input/output
- has a smoke test or deterministic verification
- includes a tiny local web form when inputs/outputs benefit from it
- has a README with limits and setup
- produces X + LinkedIn drafts
- does not post live or push externally unless the approval gate passes
- uses a clean public export repo for open-source publishing

## Hard boundaries

- No secrets, private IPs, teacher data, DMs, personal inbox contents, or real customer data in public artifacts.
- Do not modify unrelated career assets unless asked.
- Do not use TeachClaw private source as sample code.
- Do not push this whole operator checkout as the public repo. Export the daily automation lane with `scripts/export_public_daily_automation_repo.py`, then run `scripts/public_release_check.py` on the export.
- Keep automations in `automations/day-XXX-slug/`.
- Keep generated release/post drafts in `drafts/daily-automation/` unless the automation README needs them.
- External actions are approval-gated. Build/draft/verify freely; pushing/posting needs an approval manifest.

## Approval gate

Live release actions must be blocked unless a matching file exists:

`approvals/day-XXX-slug.release.json`

Required shape:

```json
{
  "approved": true,
  "slug": "day-001-example",
  "allow": ["git-push", "x-post", "linkedin-post"],
  "approved_by": "Anas",
  "notes": "Manual approval after review"
}
```

If approval is missing, still create the release packet and explain exactly what is ready.
