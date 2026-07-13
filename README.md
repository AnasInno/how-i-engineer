# How I Engineer TeachClaw with OMP

This repo is the public-safe architecture of the agentic engineering system I
use to develop and prove TeachClaw.

It is not a generic prompt collection. It documents the real operating pattern:
one isolated worktree, stock OMP for coordination, a thin TeachClaw extension,
one deterministic lane controller,
realistic drivers, independent verifiers, and proof that matches the product
surface.

```text
conversation
    ↓
tight brief + proof contract
    ↓
current isolated worktree
    ↓
OMP planner → bounded task agents → explicit handoffs
    ↓
typed TeachClaw extension
    ↓
canonical lane controller
    ↓
driver → product → verifier
    ↓
surface-specific evidence + merge judgement
```

## Run the Real Public Harness

The `harness/` directory contains executable control-plane code extracted from
the system. It uses a disposable demo server instead of TeachClaw product code,
but the worktree, state, ownership, mirror, lock, verifier and cleanup mechanics
are real.

```bash
make check
```

That command syntax-checks the launcher, runs the complete lane lifecycle in a
temporary Git repo, starts and health-checks an owned process, proves explicit
tester-lock release, exercises guarded cleanup, and verifies that stale evidence
cannot satisfy a new run contract.

Try the controller directly from a non-main branch:

```bash
node harness/scripts/lane-controller.mjs init
node harness/scripts/lane-controller.mjs ui-seed
node harness/scripts/lane-controller.mjs runtime-prepare
node harness/scripts/lane-controller.mjs process-up app
node harness/scripts/lane-controller.mjs process-status app
node harness/scripts/lane-controller.mjs process-down app
node harness/scripts/lane-controller.mjs cleanup
```

See [`harness/README.md`](harness/README.md) for the launcher, extension, provider
preflight and independent verifier commands.

## The Core Boundary

| Layer | Owns |
| --- | --- |
| OMP | Conversation, planning, model routing, task agents, coordination and steering |
| TeachClaw extension | Typed lane actions, approval tiers, main-branch mutation refusal and destructive-command guards |
| Lane controller | Worktree identity, ports, paths, databases, services, runtime mirrors, locks, evidence and owned cleanup |
| Driver | Realistic teacher interaction through the actual surface |
| Verifier | Deterministic assertions over saved evidence |
| Product code | TeachClaw behaviour, pedagogy, marking, artifacts and UI |

The model performs the story. Software checks the facts.

## One Worktree Is the Lane

The harness does not create a new worktree for every UI or proof task.

- When launched from clean primary `main`, it creates a linked feature
  worktree automatically.
- When already inside a linked or non-main worktree, it stays there.
- UI, app, worker, gateway, database, browser profile, logs and evidence all
  belong to that same lane.
- OMP's own task isolation remains off because the TeachClaw worktree and lane
  controller already own isolation.

Task agents in one OMP session receive non-overlapping ownership. If a worker
needs independent mutable state, it gets another linked TeachClaw worktree and
another harness session.

## Deterministic Bootstrap

The real launcher does six things before OMP starts:

1. verifies the supported OMP and Node runtime;
2. chooses or creates the correct worktree;
3. installs dependencies only when missing or unusable;
4. initialises worktree-owned lane state;
5. loads the checked-in OMP config and TeachClaw extension;
6. stores OMP session evidence inside the lane.

Ambient skills and rule packs are disabled. Agents load TeachClaw development
context on a need-to-know basis rather than inheriting every skill, runbook and
historical result.

## Model Routing

The checked-in role shape is deliberate:

```yaml
default:  gpt-5.6-sol low
plan:     gpt-5.6-sol xhigh
task:     gpt-5.6-luna xhigh
slow:     gpt-5.6-sol xhigh
commit:   gpt-5.6-luna low
tiny:     gpt-5.6-luna low
```

Planning and ambiguous diagnosis receive the strongest reasoning. Bounded task
execution gets a capable worker model. Commit-shaped and tiny mechanical work
uses cheaper roles. Setup, synchronisation, assertions and cleanup remain
deterministic code rather than model work.

The default topology is one planner and one task agent. Parallel workers are
used only for genuinely independent outcomes; shared runtime phases are
serialised with explicit handoffs.

## Typed Tool Surface

OMP does not receive a collection of overlapping shell wrappers. The extension
exposes the canonical controller's vocabulary:

```text
lane state      status, init
UI              ui-seed, app-up, app-status, app-down
gateway         gateway-prepare, gateway-up, gateway-status, gateway-down
marking         marking-prepare, marking-local-up/down, direct-check/run
tester          acquire, owner, sync, browser car, verify, release
cleanup         cleanup
```

Scenario drivers such as provider readiness or a committed marking replay are
typed separately from lifecycle actions. This prevents product-specific proof
logic from turning the controller into a scenario engine.

## The Three Proof Lanes

### UI

Seed a fake session, start the local app, use the exact returned login URL,
inspect desktop and mobile states, then stop the owned app. UI proof is light
and stays in the current worktree.

### PowerPoint

Check the exact provider/model route, mirror the current committed worktree into
an isolated local gateway, make the realistic teacher request, render the
actual PPTX, inspect the slides, then stop the owned gateway. A successful model
reply is not artifact proof.

### Marking

Run the deterministic direct check first. For cross-boundary proof, acquire the
pinned tester, sync the committed worktree, start the lane-owned local app and
worker, drive the committed teacher replay through the real browser, save
structured state, run the independent verifier, then stop and release every
owned resource.

The driver baselines old chat messages and marking runs. Only a new run matching
the committed scenario can pass.

## Hard Guardrails

- Mutating lane actions are refused on `main`.
- Worktree cleanup can stop or remove only state whose ownership is recorded.
- Recursive deletion targeting the repo, worktree root, `.git`, `/`, `/Users`,
  the home directory or unresolved variable paths is rejected.
- Tester ownership is exclusive and released explicitly.
- Secrets are hydrated into owned child processes from ignored trusted sources;
  they are never copied into prompts, config, evidence or commits.
- A controller command proves environment state, not product quality.
- Browser, artifact, tester and live proof remain separate claims.

## The Expansion Tripwire

The lane controller is allowed to be substantial because it replaces several
competing launch, sync, lock, provenance and cleanup systems. Its size is not
permission to absorb product behaviour or scenario judgement.

If a new script starts allocating ports, mirroring code, launching services,
acquiring locks, collecting lifecycle evidence or cleaning runtime paths, a
second control plane is forming. Extend the controller contract instead of
adding another wrapper.

## Repo Map

```text
AGENTS.md                         public agent rules
docs/architecture.md             full ownership and execution model
docs/proof-lanes.md              UI, PowerPoint and marking proof contracts
docs/safety-and-ownership.md     worktree, process, path and secret guardrails
examples/task-contract.md        bounded worker handoff format
harness/bin/teachclaw-omp        worktree-aware OMP launcher
harness/omp/                     real role config and typed extension
harness/scripts/                 lane controller and proof verifiers
harness/tests/                   executable lifecycle and safety tests
scripts/check_public_repo.py     deterministic public-safety/structure check
```

Run the public repository check:

```bash
make check
```

## What This Repo Does Not Publish

TeachClaw product source, private prompts, teacher or pupil data, credentials,
runtime identities, infrastructure addresses, live evidence, browser sessions
and exact private fixtures remain private.

The useful part to open source is the engineering system: who owns what, how
agents receive context, how environments become deterministic, how proof is
separated, and where the system refuses to improvise.
