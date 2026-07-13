# How I Engineer

A public, evolving record of how I ship AI-assisted products and small
automations.

The current system is built around a simple idea:

> Agents become more reliable when the system asks them to reason less about
> mechanics and more about the parts that genuinely need judgement.

My first version had the right ingredients—conversation, briefs, workers,
deterministic scripts, evals, browser proof, and release gates—but too many of
those ingredients grew their own runner, helper, context pack, and review loop.

The newer design is smaller and stricter:

```text
conversation -> brief -> isolated worktree -> OMP plan -> bounded tasks
             -> lane controller -> driver -> verifier -> ship
```

Read the detailed architecture and the reasoning behind it in
[`docs/how-i-engineer-omp.md`](docs/how-i-engineer-omp.md).

## What Changed

- **Less startup context.** Agents load root rules, one compact task route, and
  current code/evidence—not the whole repository and its history.
- **OMP as the coordinator.** Planning, role routing, task delegation, and
  handoffs live in one lightweight harness.
- **One canonical lane controller.** Ports, runtime paths, local services, sync,
  locks, provenance, evidence, and cleanup have one owner.
- **Stricter role boundaries.** Drivers perform realistic user actions;
  deterministic verifiers decide whether state and contracts are correct.
- **Less LLM usage.** Strong reasoning is spent on planning and ambiguity. Tiny
  edits and mechanics use cheaper roles or normal code.
- **No default reviewer loop.** Mechanical gates run first. A failure gets one
  evidence-based diagnosis and one bounded repair.
- **Proof stays surface-specific.** Tests, browser state, rendered artifacts,
  runtime replay, evals, and release checks prove different things.

## The Boundary That Keeps It Clean

- **OMP:** environment-aware planning and coordination
- **Lane controller:** deterministic environment and lifecycle mechanics
- **Driver:** realistic user interaction
- **Verifier:** deterministic outcome assertions
- **Product code:** actual behaviour being built and tested

The controller can be large because it replaces several competing systems. The
tripwire is not line count; it is ownership. If another script starts allocating
ports, syncing runtimes, launching services, or cleaning directories, a second
control plane is forming.

## Why It Uses Fewer Tokens

The old failure mode was context clogging: every agent inherited broad docs,
historical plans, proof instructions, and sibling output. More context looked
like more intelligence, but it made the task boundary harder to see.

Now:

- the planner gets the outcome and proof contract
- each task agent gets one lane and the smallest relevant context
- deterministic tools return typed state instead of terminal archaeology
- workers return evidence summaries instead of full transcripts
- judge models run only after mechanical gates pass
- unchanged proof surfaces are not re-evaluated

This reduces prompt size, repeated discovery, coordination chatter, and model
calls spent checking facts that software can assert exactly.

## Daily Automation Examples

The repo also contains tiny, local-first automation examples. They are the small
end of the same engineering philosophy:

- obvious input
- useful output
- deterministic CLI source of truth
- runnable locally in minutes
- sample data included
- no private account required for the demo
- optional local web form as a thin wrapper

### Quick Start

```bash
cd automations/day-001-messy-notes-to-action-draft
make smoke
```

Open its local form:

```bash
make web
```

The current automation lane is documented in:

- `codex/daily-automation/LOAD-FIRST.md`
- `codex/daily-automation/WORKFLOW.md`
- `codex/daily-automation/PUBLIC-SHIP-FLOW.md`
- `.agents/skills/daily-ai-automation-ship/SKILL.md`

Builders use a curated ready idea or an explicit idea from Anas. They do not
invent a new automation during the build run.

## Safety

This repo publishes the operating design, not private machinery. It excludes
credentials, customer data, private prompts, local paths, runtime identities,
browser sessions, and live traces.

Daily automation public exports are checked with:

```bash
python3 scripts/export_public_daily_automation_repo.py --dest ../daily-ai-automation-kit --force
python3 scripts/public_release_check.py ../daily-ai-automation-kit
```

The point is not that agents can do everything. The point is that clear
boundaries make the useful parts repeatable, inspectable, and cheap enough to run
every day.
