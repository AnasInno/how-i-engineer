import assert from "node:assert/strict";
import { cpSync, existsSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { execFileSync, spawn } from "node:child_process";
import { createServer } from "node:http";
import { fileURLToPath } from "node:url";
import test from "node:test";

import {
  acquireTesterLock,
  assertSafeLaneRoot,
  cleanupLane,
  deterministicPorts,
  initialiseLane,
  isStrictDescendant,
  ownedProcessStatus,
  prepareRuntimeMirror,
  releaseTesterLock,
  seedUiFixture,
  startOwnedProcess,
  stopOwnedProcess,
  testerOwner,
} from "../scripts/lane-controller.mjs";
import { verifyFreshRun } from "../scripts/fresh-run-verifier.mjs";
import { isDestructiveCommand } from "../scripts/destructive-guard.mjs";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../..");

function fixtureRepo() {
  const root = mkdtempSync(join(tmpdir(), "public-teachclaw-harness-"));
  cpSync(join(ROOT, "harness"), join(root, "harness"), { recursive: true });
  writeFileSync(join(root, "README.md"), "fixture\n");
  writeFileSync(join(root, ".gitignore"), ".teachclaw-lane/\n");
  execFileSync("git", ["init", "-b", "feature/test"], { cwd: root, stdio: "ignore" });
  execFileSync("git", ["config", "user.email", "test@example.com"], { cwd: root });
  execFileSync("git", ["config", "user.name", "Harness Test"], { cwd: root });
  execFileSync("git", ["add", "."], { cwd: root });
  execFileSync("git", ["commit", "-m", "fixture"], { cwd: root, stdio: "ignore" });
  return root;
}

function runChild(command, args, options) {
  return new Promise((resolvePromise, rejectPromise) => {
    const child = spawn(command, args, { ...options, stdio: ["ignore", "pipe", "pipe"] });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (chunk) => { stdout += String(chunk); });
    child.stderr.on("data", (chunk) => { stderr += String(chunk); });
    child.once("error", rejectPromise);
    child.once("exit", (code) => resolvePromise({ code, stdout, stderr }));
  });
}

test("ports are stable per worktree", () => {
  assert.deepEqual(deterministicPorts("/tmp/worktree-a"), deterministicPorts("/tmp/worktree-a"));
  assert.notDeepEqual(deterministicPorts("/tmp/worktree-a"), deterministicPorts("/tmp/worktree-b"));
});

test("cleanup target must be the owned lane descendant", () => {
  assert.equal(isStrictDescendant("/tmp/repo", "/tmp/repo/.teachclaw-lane"), true);
  assert.equal(isStrictDescendant("/tmp/repo", "/tmp/other"), false);
  assert.throws(() => assertSafeLaneRoot("/tmp/repo", "/tmp/repo"), /protected cleanup target/);
  assert.throws(() => assertSafeLaneRoot("/tmp/repo", "/tmp/other"), /not owned/);
});

test("catastrophic recursive deletion is blocked before shell execution", () => {
  const root = "/tmp/example-repo";
  assert.equal(isDestructiveCommand("rm -rf /", [root, "/tmp/home"], root), true);
  assert.equal(isDestructiveCommand(`rm -rf ${root}`, [root, "/tmp/home"], root), true);
  assert.equal(isDestructiveCommand(`rm -rf '${root}/*'`, [root, "/tmp/home"], root), true);
  assert.equal(isDestructiveCommand("sudo rm --recursive --force .git", [root], root), true);
  assert.equal(isDestructiveCommand("rm -rf $HOME", [root, "/tmp/home"], root), true);
  assert.equal(isDestructiveCommand("rm -rf .teachclaw-lane/evidence", [root], root), false);
});

test("lane lifecycle records ownership, health and explicit tester release", async () => {
  const root = fixtureRepo();
  try {
    const state = initialiseLane(root);
    assert.equal(state.branch, "feature/test");
    assert.equal(initialiseLane(root).laneId, state.laneId);
    assert.equal(seedUiFixture(root).loginUrl.includes(String(state.ports.app)), true);
    assert.equal(prepareRuntimeMirror(root).files.length, 3);

    const started = await startOwnedProcess(root, "app");
    assert.equal(started.owned, true);
    assert.throws(() => initialiseLane(root), /recorded process ownership/);
    assert.equal(ownedProcessStatus(root, "app").running, true);
    await stopOwnedProcess(root, "app");
    assert.equal(ownedProcessStatus(root, "app").running, false);

    acquireTesterLock(root);
    assert.equal(testerOwner(root).laneId, state.laneId);
    assert.throws(() => cleanupLane(root), /release it explicitly/);
    assert.equal(releaseTesterLock(root).released, true);
    assert.equal(cleanupLane(root).cleaned, true);
    assert.equal(existsSync(join(root, ".teachclaw-lane")), false);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("runtime mirror refuses an uncommitted worktree", () => {
  const root = fixtureRepo();
  try {
    initialiseLane(root);
    writeFileSync(join(root, "uncommitted.txt"), "drift\n");
    assert.throws(() => prepareRuntimeMirror(root), /clean committed worktree/);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("fresh-run verifier rejects stale evidence and accepts a matching new run", () => {
  const baseline = {
    messages: [{ id: "old-user", role: "user" }],
    runs: [{ runId: "old-run", status: "complete", sourceFileCount: 6, frameTotal: 50 }],
  };
  const scenario = { expected: { status: "complete", sourceFileCount: 16, frameTotal: 80, requireNoActiveJobs: true } };
  const stale = verifyFreshRun(baseline, { ...baseline, activeJobs: [] }, scenario);
  assert.equal(stale.passed, false);

  const fresh = verifyFreshRun(baseline, {
    messages: [...baseline.messages, { id: "new-user", role: "user" }, { id: "new-assistant", role: "assistant" }],
    runs: [{ runId: "new-run", status: "complete", sourceFileCount: 16, frameTotal: 80 }, ...baseline.runs],
    activeJobs: [],
  }, scenario);
  assert.equal(fresh.passed, true);
  assert.equal(fresh.selectedRun.runId, "new-run");
});

test("provider readiness records redacted evidence without persisting the credential", async () => {
  const root = fixtureRepo();
  const server = createServer((request, response) => {
    assert.equal(request.headers.authorization, "Bearer placeholder-credential");
    response.setHeader("content-type", "application/json");
    response.end(JSON.stringify({ choices: [{ message: { content: "READY" } }] }));
  });
  await new Promise((resolvePromise) => server.listen(0, "localhost", resolvePromise));
  try {
    initialiseLane(root);
    const address = server.address();
    assert.equal(typeof address, "object");
    const result = await runChild(process.execPath, [join(root, "harness/scripts/provider-readiness.mjs")], {
      cwd: root,
      env: {
        ...process.env,
        PROVIDER_BASE_URL: `http://localhost:${address.port}`,
        PROVIDER_MODEL: "fixture-model",
        PROVIDER_API_KEY: "placeholder-credential",
      },
    });
    assert.equal(result.code, 0, result.stderr);
    assert.equal(result.stdout.includes("placeholder-credential"), false);
    const evidence = readFileSync(join(root, ".teachclaw-lane/evidence/provider-readiness.json"), "utf8");
    assert.equal(evidence.includes("placeholder-credential"), false);
    assert.equal(JSON.parse(evidence).ready, true);
    cleanupLane(root);
  } finally {
    await new Promise((resolvePromise) => server.close(resolvePromise));
    rmSync(root, { recursive: true, force: true });
  }
});
