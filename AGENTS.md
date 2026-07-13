# AGENTS.md — How I Engineer TeachClaw with OMP

This is a public-safe architecture repo. It documents the TeachClaw development
harness without publishing product source, private prompts, data, credentials,
runtime identities or live evidence.

## Load First

For non-trivial work, read only:

1. `docs/architecture.md`
2. the single relevant topic doc
3. the current files being changed

Do not load the whole repo or historical Git state as startup context.

## Topic Router

- OMP, model roles or task topology: `docs/architecture.md`
- UI, PowerPoint or marking evidence: `docs/proof-lanes.md`
- worktrees, cleanup, secrets or destructive guards:
  `docs/safety-and-ownership.md`
- agent procedure: `.agents/skills/how-i-engineer-omp-harness/SKILL.md`

## Architecture Rules

- OMP owns planning, model routing, task agents and handoffs.
- The extension exposes typed controller actions and safety gates.
- One lane controller owns environment and lifecycle mechanics.
- Drivers own realistic interaction.
- Verifiers own deterministic outcome assertions.
- Product code owns product behaviour.
- Reuse the current isolated worktree; create one only when starting on main.
- Use one task agent by default and parallelise only independent outcomes.
- Do not add a parallel launcher, sync path, lock convention, evidence collector
  or cleanup system.
- Never weaken ownership or destructive-path guards for convenience.

## Public Boundary

Use generic or scrubbed examples. Do not add local absolute paths, secrets,
private instance names, network addresses, customer data, private fixtures,
screenshots, logs or transcripts.

## Validation

```bash
make check
```
