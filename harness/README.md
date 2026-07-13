# Runnable Harness

This directory is a public extraction of the real TeachClaw development harness.
Product code and private infrastructure adapters are deliberately absent; the
deterministic control-plane mechanics are runnable.

## Files

- `bin/teachclaw-omp` — worktree-aware OMP launcher.
- `omp/teachclaw.yml` — real role-routing and task-isolation shape.
- `omp/teachclaw-extension.ts` — typed OMP tools, approval tiers, main refusal
  and catastrophic deletion guard.
- `scripts/lane-controller.mjs` — deterministic ports, lane state, process
  ownership, runtime mirroring, UI fixture seed, tester lock and safe cleanup.
- `scripts/destructive-guard.mjs` — pre-shell refusal for catastrophic recursive
  deletion targets.
- `scripts/provider-readiness.mjs` — minimal redacted provider proof.
- `scripts/fresh-run-verifier.mjs` — rejects stale messages/runs and selects only
  a new scenario-matching result.
- `examples/demo-server.mjs` — disposable local process for exercising the
  controller without TeachClaw product source.
- `tests/harness.test.mjs` — executable ownership, cleanup and verifier tests.

## Run the deterministic core

From a non-main branch:

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

Run the stale-evidence verifier:

```bash
node harness/scripts/fresh-run-verifier.mjs \
  --baseline harness/examples/evidence-baseline.json \
  --final harness/examples/evidence-final.json \
  --scenario harness/examples/scenario.json \
  --out /tmp/public-teachclaw-verification.json
```

Run the tests:

```bash
make check
```

## Connect it to a product

Edit `lane.config.json` so each process command starts the real local app or
gateway. Keep commands argument-based—never shell strings—and keep credentials
in the parent process environment. Add private sync/browser adapters behind the
typed extension without moving their scenario logic into the controller.
