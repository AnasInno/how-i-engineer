---
name: how-i-engineer-omp-harness
description: "Use when documenting or applying the real TeachClaw OMP, lane-controller, driver and verifier architecture."
---

# TeachClaw OMP Harness

Load `docs/architecture.md` and only the topic doc and current files required by
the task.

## Procedure

1. Start with the user outcome and required proof surface.
2. Reuse the current non-main worktree; create one only when starting on main.
3. Choose the minimum topology: one planner and one task agent by default.
4. Give each task one outcome, scope, tool surface, evidence contract and stop
   condition.
5. Use the typed extension and canonical controller for all environment and
   lifecycle work.
6. Keep realistic interaction in a driver and assertions in a verifier.
7. Serialise shared mutable runtime phases with explicit handoffs.
8. Return typed evidence and concise findings rather than transcript dumps.
9. Clean only recorded owned state and release shared resources explicitly.

## Tripwire

Do not add a new launcher, synchroniser, port allocator, lock convention,
evidence collector or cleanup path. If the controller cannot express a valid
requirement, extend its contract while preserving one state and ownership model.

## Return

- topology and role routing
- worktree and lane identity
- controller actions used
- proof per surface
- verifier result
- cleanup state
- residual risk
