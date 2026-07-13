# How I Engineer Now: The OMP Harness

The important change in my engineering system is not a new model. It is a
cleaner allocation of responsibility between models and software.

My earlier system already treated agents as an engineering team rather than one
magic prompt. It started with a conversation, turned context into a brief, split
work into lanes, used deterministic scripts, added evals, and separated proof
surfaces.

That was directionally right. The problem was that the operational layer kept
growing sideways. Launchers, test runners, cleanup helpers, fixed-port scripts,
review roles, persona drivers, and runtime sync tools overlapped. An agent could
complete the same job through several plausible paths, and no one path was
clearly authoritative.

The current design centralises those responsibilities without collapsing all
behaviour into one monolith.

## The Five-Layer Model

```text
OMP             planning, roles, delegation, handoffs
lane controller environment and lifecycle mechanics
driver          realistic user interaction
verifier        deterministic outcome assertions
product         actual behaviour under development
```

These boundaries are the architecture.

## OMP Is The Coordination Shell

[oh-my-pi](https://github.com/can1357/oh-my-pi) provides the lightweight harness:
role-based model routing, task agents, shared task state, explicit handoffs, and
custom tools.

The planner gets the brief and proof contract. It decides whether the job needs
one agent or several, splits only independent outcomes, sequences shared mutable
runtime phases, and integrates the evidence.

A task agent does not receive the entire project history. It receives:

- one outcome
- allowed and forbidden scope
- the smallest relevant skill and current files
- supported controller operations
- required evidence
- cleanup responsibility
- a stop condition

The task result is structured evidence, not a transcript dump.

## Model Roles Are Resource Allocation

The harness uses stable roles even when the underlying models change:

- **plan:** strongest reasoning for decomposition and proof design
- **task:** capable execution for bounded implementation or operation
- **slow:** strong reasoning for genuinely ambiguous diagnosis
- **commit:** cheaper precise work for mechanical closeout
- **tiny:** the cheapest reliable option for small deterministic edits
- **default:** balanced interactive work

This is not about always choosing the cheapest model. It is about spending the
least total reasoning needed to reach a trustworthy result.

Using a premium reasoning model to allocate a port, mirror a directory, check a
process, or clean an owned path is waste. Normal software can do those things
more reliably and return exact state.

## The Lane Controller Is The Source Of Operational Truth

The controller owns:

- isolated ports and runtime directories
- local app, worker, and gateway lifecycle
- worktree-specific data
- committed-code mirroring
- shared-resource locks
- runtime or tester synchronisation
- provenance and evidence locations
- process and path ownership
- guarded cleanup

The controller may be a substantial file. That is acceptable when it replaces
several competing systems. The risk is not raw line count; it is a second control
plane.

The tripwire is simple:

> If a new wrapper starts allocating ports, syncing code, launching services,
> acquiring locks, collecting lifecycle evidence, or deleting runtime paths, it
> is probably duplicating the controller.

Extend the controller contract or remove the wrapper.

## Why The Driver And Verifier Are Separate

Realistic user flows are variable. A driver may need to click, type, upload,
wait for visible state, download an artifact, or respond to a clarification.
That is a reasonable place for an agent.

Correctness is different. A verifier should assert exact outcomes independently:
records exist, statuses changed, identifiers are new, files match the contract,
provenance points at the current commit, and owned processes were cleaned up.

The model performs the story. Software checks the facts.

That separation avoids the weakest form of agent evaluation: asking the same
agent that performed the work whether it thinks the work succeeded.

## Worktree Isolation Without Worktree Proliferation

Isolation does not mean creating a fresh checkout for every proof surface.

- If work starts on main, create an isolated worktree.
- If it is already on a non-main worktree, keep UI, runtime, evidence, and
  cleanup attached to that worktree.

The controller creates isolation through owned ports, data, paths, services,
locks, and leases. The commit lineage stays coherent and there is no artificial
integration step between UI proof and the code being proved.

## The Proof Surfaces

Different product risks need different proof.

### UI

Start the local app from the current worktree, seed a fake session with fake
data, use the exact returned login URL, and inspect desktop and mobile browser
states. This is intentionally lightweight.

### Generated artifacts

Mirror the committed worktree into an owned local runtime, make a realistic
request, then render and inspect the artifact the user actually receives. A
successful tool call or extracted text does not prove a slide deck is usable.

### Cross-boundary workflows

Acquire the shared tester, sync the committed worktree, start owned local
services, run one committed realistic replay, capture evidence, invoke the
independent verifier, then stop and release everything owned by the lane.

The model drives the workflow. The controller establishes provenance. The
verifier decides whether the outcome met the contract.

## Context Is A Budget

The old system often loaded broad development docs, historical plans, proof
instructions, and previous results into one session. That made an agent look
informed while blurring what was current and what mattered.

The current hierarchy is:

```text
root rules -> one task route -> current code and evidence
```

History is queryable when required; it is not startup truth. Current code and
runtime state beat prose describing what used to be true.

Smaller context improves the system in several ways:

- less token use per agent
- fewer irrelevant constraints competing for attention
- clearer ownership and stop conditions
- less sibling-transcript duplication
- fewer model calls spent rediscovering environmental facts
- lower chance that stale instructions revive a retired flow

## Evals Are Targeted, Not Ceremonial

Evals still matter when the change affects output quality, routing, confidence,
fallback, or user trust.

```text
scenario pack -> candidates -> rubric -> mechanical gates -> targeted judgement
```

Mechanical gates run first. A judge model is called only for dimensions that
need language or visual judgement. Unchanged surfaces are not re-evaluated, and
high-cost reasoning is concentrated on uncertain or high-risk cases.

An eval does not automatically require a separate eval agent. A deterministic
verifier can settle deterministic questions more cheaply and with less variance.

## Failure Handling Is Bounded

The older instinct was to add another reviewer or loop until every concern
disappeared. That can consume unlimited tokens while expanding the scope on each
pass.

The current rule is:

1. preserve the evidence
2. diagnose the proven failure once
3. repair the narrow cause
4. rerun the affected proof
5. stop if the remaining issue needs judgement or a new scope decision

No infinite autoreview loop. Safety comes primarily from deterministic
invariants, ownership guards, typed evidence, and explicit proof contracts.

## Before And After

| Earlier | Now |
| --- | --- |
| Overlapping launch, sync, proof, and cleanup scripts | One lane controller |
| Broad shared context | Need-to-know task context |
| Generic workers carrying the whole workflow | OMP planner and bounded tasks |
| Review loops as the default control | Mechanical gates and one diagnosis |
| Similar model posture for most work | Role-based reasoning budget |
| Success inferred from commands or model replies | Typed surface-specific evidence |
| Cleanup as shell convention | Ownership-checked path and process cleanup |

## The Deeper Point

Centralisation is not the same as putting everything into one giant agent or one
giant prompt.

The operational complexity still exists: ports must be allocated, services must
start, runtimes must match the worktree, shared resources must be locked,
evidence must be captured, and cleanup must be safe.

The improvement is that these responsibilities are encoded once behind an
explicit interface. Agents no longer negotiate the environment from scratch.
They can spend their limited context and reasoning on the user problem,
implementation trade-offs, realistic interaction, and the parts of quality that
actually require judgement.

That is the system I want as my main runner: less magical, less chatty, more
deterministic, and more capable because its boundaries are stricter.
