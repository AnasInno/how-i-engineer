# Proof Lanes

Environment setup, product behaviour and quality are different claims. Each
surface has its own driver, evidence and cleanup contract.

## UI

```text
initialise lane
→ seed fake session and fake data
→ capture exact login URL
→ start owned local app
→ inspect desktop and mobile browser states
→ stop owned app
```

UI proof uses the current isolated worktree. It does not require a new
integration worktree when the code is already isolated.

## PowerPoint

```text
provider readiness
→ prepare committed runtime mirror
→ start owned local gateway
→ submit realistic teacher request
→ locate generated PPTX
→ render every slide
→ inspect actual output
→ stop owned gateway
```

Provider readiness proves only that the configured route answers. Gateway
readiness proves only that the runtime matches the worktree. The PowerPoint claim
requires the artifact to exist and the rendered slides to be inspected.

## Marking

The direct deterministic lane runs first. Cross-boundary proof then uses the
smallest approved sequence:

```text
direct check
→ acquire exclusive tester ownership
→ sync the clean committed worktree
→ start lane-owned local app and worker
→ open the real teacher chat
→ attach the approved committed fixture
→ perform the committed teacher exchange
→ wait for a new matching marking run
→ save chat, dashboard and structured state
→ run the independent verifier
→ stop local services
→ release tester ownership
```

The replay records baseline message and run IDs before acting. A valid result
must be new and match the scenario's file partition, assessment frame, status,
reports and feedback contract.

## Evidence Meanings

| Evidence | Proves |
| --- | --- |
| controller status | owned environment state |
| focused tests | code behaviour in the test boundary |
| browser screenshots | visible state at a moment in the real path |
| rendered slides | actual artifact layout and readability |
| runtime provenance | mirror and commit agreement |
| verifier JSON | deterministic scenario assertions |
| cleanup status | absence of recorded owned processes |

Do not collapse these into a single `tested` label.
