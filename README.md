# How I Engineer TeachClaw with OMP

This repo is a public, runnable extraction of the agentic engineering harness I
use to develop TeachClaw.

The main lesson is simple: the system improved when I asked language models to
do less. Models plan, implement, navigate and judge. Deterministic software owns
ports, paths, process lifecycle, runtime synchronisation, locks, provenance,
assertions and cleanup.

TeachClaw product code, private prompts, teacher data, fixtures, credentials and
infrastructure remain private. The control-plane mechanics are real and
executable.

## Architecture

```text
conversation
    ↓
brief + proof contract
    ↓
isolated worktree
    ↓
OMP planner → bounded task agents → explicit handoffs
    ↓
typed extension
    ↓
canonical lane controller
    ↓
driver → product → independent verifier
    ↓
surface-specific evidence + merge judgement
```

Each layer has one owner:

| Layer | Responsibility |
| --- | --- |
| OMP | Planning, model routing, task agents, coordination and steering |
| Extension | Typed tools, approval tiers, branch rules and catastrophic command guards |
| Lane controller | Worktree identity, ports, state, processes, mirrors, locks, evidence and cleanup |
| Driver | Realistic user interaction |
| Verifier | Deterministic assertions over saved evidence |
| Product | Actual TeachClaw behaviour |

The model performs the story. Software checks the facts.

## One Worktree Is the Lane

The launcher reuses the current isolated worktree. When started from clean
primary `main`, it creates a linked feature worktree automatically. It does not
create another checkout for UI, PowerPoint or marking proof.

The worktree owns its `.teachclaw-lane/` directory, including:

- stable ports derived from the worktree path;
- atomic lane state;
- local app and gateway process records;
- runtime mirrors and provenance manifests;
- fake UI fixtures;
- logs, evidence and OMP sessions.

OMP task isolation is disabled because the worktree and lane controller already
own isolation. One task agent is the default. Parallel workers are used only for
independent outcomes, and shared runtime phases use explicit handoffs.

## Model Routing

The checked-in OMP roles match the type of work:

```yaml
default: openai-codex/gpt-5.6-sol:low
plan:    openai-codex/gpt-5.6-sol:xhigh
task:    openai-codex/gpt-5.6-luna:xhigh
slow:    openai-codex/gpt-5.6-sol:xhigh
commit:  openai-codex/gpt-5.6-luna:low
tiny:    openai-codex/gpt-5.6-luna:low
```

Strong reasoning is reserved for planning and ambiguous diagnosis. Bounded
implementation uses the task role. Commit-shaped and tiny mechanical work uses
cheaper roles. Setup, sync, assertions and cleanup stay deterministic.

The launcher disables ambient skills and rule packs. Agents receive the smallest
relevant task context instead of the entire repo history and every sibling
transcript.

## What the Code Actually Does

### Launcher

[`harness/bin/teachclaw-omp`](harness/bin/teachclaw-omp) verifies Git, Node and
OMP; selects or creates the correct worktree; initialises lane state; then starts
stock OMP with the checked-in config, extension and worktree-local session path.

`workflowz` starts the parent through the plan role unless the user explicitly
selects another model. Generic workers resolve through the task role.

### Typed OMP extension

[`harness/omp/teachclaw-extension.ts`](harness/omp/teachclaw-extension.ts)
registers two tool families:

- `teachclaw_lane` for environment and lifecycle actions;
- `teachclaw_proof` for bounded proof drivers.

It classifies actions as read, write or exec; refuses mutation on `main`;
redacts output; and blocks catastrophic recursive deletion before the shell runs.

### Lane controller

[`harness/scripts/lane-controller.mjs`](harness/scripts/lane-controller.mjs) is
the single operational state machine. It implements:

- deterministic worktree-derived ports;
- atomic state writes;
- idempotent initialisation that refuses to orphan process ownership;
- argument-based process startup with isolated environment values;
- PID plus process-signature ownership checks;
- health checks and owned shutdown;
- clean-commit runtime mirroring with SHA-256 manifests;
- fake UI session seeding with an exact login URL;
- exclusive tester locks shared across worktrees;
- explicit tester release;
- cleanup restricted to the owned lane directory.

If another script starts allocating ports, launching services, syncing runtimes,
acquiring locks or cleaning directories, a second control plane is forming. The
controller should be extended instead.

### Destructive-command guard

[`harness/scripts/destructive-guard.mjs`](harness/scripts/destructive-guard.mjs)
parses shell segments before execution. Recursive deletion is blocked when the
target is empty, variable-expanded, `.git`, the repo, worktree root, filesystem
root, user root or home directory.

The controller also validates its own cleanup target independently. A prompt
rule is not treated as a filesystem safety boundary.

### Provider preflight

[`harness/scripts/provider-readiness.mjs`](harness/scripts/provider-readiness.mjs)
makes one minimal request to the configured endpoint before an expensive runtime
starts. It records model, endpoint origin, HTTP status, latency, commit, dirty
state and lane identity. The credential and response content are never written
to evidence.

### Independent verifier

[`harness/scripts/fresh-run-verifier.mjs`](harness/scripts/fresh-run-verifier.mjs)
baselines old message and run IDs, then accepts only a new run matching the
scenario's status, file count and assessment frame. It also checks for fresh
teacher and assistant turns and the absence of active jobs.

This prevents a convincing screenshot or stale successful run from passing a
new proof.

## Proof Shapes

The private product adapters follow three public contracts:

```text
UI
seed fake session → exact login URL → local app → desktop/mobile inspection → app down

PowerPoint
provider preflight → committed runtime mirror → local gateway → real request
→ render actual PPTX → inspect slides → gateway down

Marking
direct check → acquire tester → sync committed worktree → local app/worker
→ committed browser replay → save state → independent verifier
→ local services down → tester release
```

A controller command proves environment state, not product quality. Tests,
browser state, rendered artifacts, runtime provenance and verifier output remain
separate evidence.

## Run It

Requirements: Git, Node 22+, and OMP 16.4.8+ for the full launcher. The
deterministic controller and tests need only Git and Node.

```bash
make check
```

This runs:

- the public secret/path scanner;
- launcher syntax validation;
- a real temporary Git worktree lane;
- process startup, health, ownership and shutdown;
- clean-runtime mirror and dirty-worktree refusal;
- tester lock acquisition and explicit release;
- destructive-command guard tests;
- local provider-preflight proof without credential persistence;
- fresh-run acceptance and stale-run rejection.

Try the controller directly from a non-main branch:

```bash
node harness/scripts/lane-controller.mjs init
node harness/scripts/lane-controller.mjs ui-seed
node harness/scripts/lane-controller.mjs runtime-prepare
node harness/scripts/lane-controller.mjs process-up app
node harness/scripts/lane-controller.mjs process-status app
node harness/scripts/lane-controller.mjs process-down app
node harness/scripts/lane-controller.mjs tester-acquire
node harness/scripts/lane-controller.mjs tester-owner
node harness/scripts/lane-controller.mjs tester-release
node harness/scripts/lane-controller.mjs cleanup
```

Run the verifier against the included fixtures:

```bash
node harness/scripts/fresh-run-verifier.mjs \
  --baseline harness/examples/evidence-baseline.json \
  --final harness/examples/evidence-final.json \
  --scenario harness/examples/scenario.json \
  --out /tmp/public-teachclaw-verification.json
```

## Repository Shape

```text
README.md                           architecture, reasoning and usage
harness/bin/teachclaw-omp           worktree-aware launcher
harness/omp/teachclaw.yml           OMP roles and task settings
harness/omp/teachclaw-extension.ts  typed tools and safety gates
harness/scripts/                    controller, guard and verifiers
harness/examples/                   disposable runtime and evidence fixtures
harness/tests/harness.test.mjs      deterministic integration tests
scripts/check_public_repo.py        public boundary check
```

That is the whole public system: one explanation, one launcher, one extension,
one controller and focused proof scripts.
