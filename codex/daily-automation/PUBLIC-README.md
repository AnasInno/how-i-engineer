# Daily AI Automation Kit

Tiny, local-first AI automation examples for boring business workflows.

The goal is one simple automation at a time:

- obvious input
- useful output
- runnable locally in minutes
- sample data included
- no private accounts required for the demo
- optional tiny local web form for friendlier inputs and downloads

## Quick Start

Run the first shipped example:

```bash
cd automations/day-001-messy-notes-to-action-draft
make smoke
```

Open the local form:

```bash
make web
```

## Current Automation

`automations/day-001-messy-notes-to-action-draft`

Paste messy notes and generate a simple action draft. It is intentionally small:
the project shows the shape of the daily automation lane rather than pretending
to be a full product.

## Build Pattern

Each automation keeps the CLI as the source of truth.

The local web shell is only a friendly wrapper for:

- entering inputs
- running the same local command
- downloading outputs

See `codex/daily-automation/LOCAL-WEB-SHELL.md`.

## Agent Workflow

The operating contract is in:

- `AGENTS.md`
- `codex/daily-automation/LOAD-FIRST.md`
- `codex/daily-automation/WORKFLOW.md`
- `codex/daily-automation/PUBLIC-SHIP-FLOW.md`
- `.agents/skills/daily-ai-automation-ship/SKILL.md`

Builders must use a curated ready idea or an explicit idea from Anas. They must
not invent a new automation idea during a build run.

## Safety

This public repo is exported from a private operator workspace using:

```bash
python3 scripts/export_public_daily_automation_repo.py --dest ../daily-ai-automation-kit --force
python3 scripts/public_release_check.py ../daily-ai-automation-kit
```

No private career assets, inbox contents, browser profiles, secrets, or customer
data belong here.
