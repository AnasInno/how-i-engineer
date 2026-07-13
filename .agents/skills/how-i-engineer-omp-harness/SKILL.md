---
name: how-i-engineer-omp-harness
description: "Use when documenting or applying the OMP planner, bounded task, canonical lane-controller, driver, and verifier architecture."
---

# How I Engineer OMP Harness

Load `docs/how-i-engineer-omp.md` and only the current files required by the
task. Do not preload the daily-automation cockpit for architecture-only work.

## Use This For

- designing an OMP plan with several bounded outcomes
- defining planner and task model roles
- adding a controller-backed OMP tool
- separating realistic drivers from deterministic verifiers
- deciding whether work needs one agent or several
- documenting proof and cleanup boundaries

## Rules

1. Reuse the current non-main worktree; create one only when starting on main.
2. Give the planner one outcome and an explicit proof contract.
3. Use one task agent by default; add more only for independent outcomes.
4. Give each task one scope, one evidence contract, and one stop condition.
5. Keep ports, paths, services, sync, locks, provenance, and cleanup in the
   canonical lane controller.
6. Keep realistic interaction in a driver and deterministic assertions in a
   verifier.
7. Use stronger reasoning only where ambiguity earns it.
8. Preserve typed evidence and return summaries, not full transcripts.
9. Diagnose each failure once and rerun only the affected proof.
10. Clean only state whose ownership the controller can prove.

## Return

- topology used
- context loaded per role
- controller operations used
- evidence per proof surface
- deterministic verifier result
- judgement that still required a model or human
- cleanup state
- residual risk
