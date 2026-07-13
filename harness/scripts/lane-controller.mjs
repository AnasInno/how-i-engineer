#!/usr/bin/env node

import {
  closeSync,
  copyFileSync,
  existsSync,
  lstatSync,
  mkdirSync,
  openSync,
  readFileSync,
  renameSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import { createHash, randomUUID } from "node:crypto";
import { homedir, tmpdir } from "node:os";
import { basename, dirname, isAbsolute, join, relative, resolve, sep } from "node:path";
import { spawn, spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const THIS_FILE = fileURLToPath(import.meta.url);
export const HARNESS_ROOT = resolve(dirname(THIS_FILE), "..");
export const DEFAULT_REPO_ROOT = resolve(HARNESS_ROOT, "..");
export const LANE_DIRNAME = ".teachclaw-lane";
const STATE_SCHEMA = "public-teachclaw-lane-v1";

function sha256(value) {
  return createHash("sha256").update(value).digest("hex");
}

function git(root, args) {
  const result = spawnSync("git", args, { cwd: root, encoding: "utf8" });
  if (result.status !== 0) {
    throw new Error(`git ${args.join(" ")} failed: ${String(result.stderr).trim()}`);
  }
  return String(result.stdout).trim();
}

export function resolveRepoRoot(cwd = process.cwd()) {
  return resolve(git(cwd, ["rev-parse", "--show-toplevel"]));
}

export function deterministicPorts(root) {
  const seed = Number.parseInt(sha256(resolve(root)).slice(0, 8), 16);
  return {
    app: 3200 + (seed % 400),
    worker: 4200 + (seed % 400),
    gateway: 18000 + (seed % 1000),
  };
}

export function isStrictDescendant(parent, candidate) {
  const rel = relative(resolve(parent), resolve(candidate));
  return Boolean(rel) && rel !== ".." && !rel.startsWith(`..${sep}`) && !isAbsolute(rel);
}

export function assertSafeLaneRoot(repoRoot, laneRoot) {
  const root = resolve(repoRoot);
  const target = resolve(laneRoot);
  const protectedPaths = new Set([
    "/",
    "/Users",
    resolve(homedir()),
    root,
    resolve(root, ".git"),
  ]);
  if (protectedPaths.has(target)) throw new Error(`refusing protected cleanup target: ${target}`);
  if (!isStrictDescendant(root, target)) throw new Error(`lane root is not owned by this worktree: ${target}`);
  if (basename(target) !== LANE_DIRNAME) throw new Error(`unexpected lane directory name: ${target}`);
  if (existsSync(target) && lstatSync(target).isSymbolicLink()) throw new Error(`refusing symlink lane root: ${target}`);
  return target;
}

function statePath(root) {
  return join(root, LANE_DIRNAME, "lane-state.json");
}

function loadConfig(root) {
  return JSON.parse(readFileSync(join(root, "harness", "lane.config.json"), "utf8"));
}

function atomicWriteJson(path, value) {
  mkdirSync(dirname(path), { recursive: true });
  const temporary = `${path}.${process.pid}.${randomUUID()}.tmp`;
  writeFileSync(temporary, `${JSON.stringify(value, null, 2)}\n`, { mode: 0o600 });
  renameSync(temporary, path);
}

function readState(root) {
  const path = statePath(root);
  if (!existsSync(path)) throw new Error("lane is not initialised; run init first");
  const state = JSON.parse(readFileSync(path, "utf8"));
  if (state.schema !== STATE_SCHEMA || resolve(state.repoRoot) !== resolve(root)) {
    throw new Error("lane state does not belong to this worktree");
  }
  return state;
}

function writeState(root, state) {
  atomicWriteJson(statePath(root), state);
}

function assertMutableBranch(root) {
  const branch = git(root, ["branch", "--show-current"]);
  if (!branch || branch === "main") throw new Error("mutating lane actions are refused on main or detached HEAD");
  return branch;
}

export function initialiseLane(root = resolveRepoRoot()) {
  const branch = assertMutableBranch(root);
  const head = git(root, ["rev-parse", "HEAD"]);
  const laneRoot = assertSafeLaneRoot(root, join(root, LANE_DIRNAME));
  const laneId = sha256(resolve(root)).slice(0, 16);
  if (existsSync(statePath(root))) {
    const existing = readState(root);
    if (Object.keys(existing.processes).length) {
      throw new Error("refusing to reinitialise a lane with recorded process ownership; stop or inspect those processes first");
    }
    existing.branch = branch;
    existing.head = head;
    existing.ports = deterministicPorts(root);
    existing.updatedAt = new Date().toISOString();
    writeState(root, existing);
    return existing;
  }
  const state = {
    schema: STATE_SCHEMA,
    laneId,
    repoRoot: resolve(root),
    laneRoot,
    branch,
    head,
    ports: deterministicPorts(root),
    paths: {
      evidence: join(laneRoot, "evidence"),
      fixtures: join(laneRoot, "fixtures"),
      logs: join(laneRoot, "logs"),
      runtime: join(laneRoot, "runtime"),
      sessions: join(laneRoot, "omp-sessions"),
    },
    processes: {},
    updatedAt: new Date().toISOString(),
  };
  for (const path of Object.values(state.paths)) mkdirSync(path, { recursive: true });
  writeState(root, state);
  return state;
}

function processSignature(pid) {
  const result = spawnSync("ps", ["-p", String(pid), "-o", "lstart=,command="], { encoding: "utf8" });
  const output = String(result.stdout || "").trim();
  return result.status === 0 && output ? sha256(output) : null;
}

function processIsOwned(record) {
  if (!record || !Number.isSafeInteger(record.pid) || record.pid <= 1) return false;
  const current = processSignature(record.pid);
  return Boolean(current && current === record.signature);
}

function expandCommand(words, state) {
  const replacements = {
    "{appPort}": String(state.ports.app),
    "{gatewayPort}": String(state.ports.gateway),
    "{workerPort}": String(state.ports.worker),
    "{laneId}": state.laneId,
    "{laneRoot}": state.laneRoot,
  };
  return words.map((word) => replacements[word] ?? word);
}

async function waitForHealth(port, healthPath, timeoutMs = 8000) {
  const deadline = Date.now() + timeoutMs;
  let lastError = "health check did not run";
  while (Date.now() < deadline) {
    try {
      const response = await fetch(`http://localhost:${port}${healthPath}`, {
        signal: AbortSignal.timeout(750),
      });
      if (response.ok) return;
      lastError = `HTTP ${response.status}`;
    } catch (error) {
      lastError = error instanceof Error ? error.message : String(error);
    }
    await new Promise((resolvePromise) => setTimeout(resolvePromise, 100));
  }
  throw new Error(`process health check failed: ${lastError}`);
}

export async function startOwnedProcess(root, name) {
  assertMutableBranch(root);
  const state = readState(root);
  const existing = state.processes[name];
  if (existing && processIsOwned(existing)) throw new Error(`${name} is already running as owned pid ${existing.pid}`);
  if (existing) throw new Error(`${name} has stale or mismatched process state; inspect before replacing it`);

  const definition = loadConfig(root).processes?.[name];
  if (!definition || !Array.isArray(definition.command) || !definition.portRole) {
    throw new Error(`unknown configured process: ${name}`);
  }
  const command = expandCommand(definition.command, state);
  const logPath = join(state.paths.logs, `${name}.log`);
  const logFd = openSync(logPath, "a", 0o600);
  const child = spawn(command[0], command.slice(1), {
    cwd: root,
    detached: true,
    env: {
      ...process.env,
      LANE_ID: state.laneId,
      LANE_ROOT: state.laneRoot,
      PORT: String(state.ports[definition.portRole]),
      PROCESS_NAME: name,
    },
    stdio: ["ignore", logFd, logFd],
  });
  child.unref();
  closeSync(logFd);

  await new Promise((resolvePromise) => setTimeout(resolvePromise, 80));
  const signature = processSignature(child.pid);
  if (!signature) throw new Error(`${name} exited before ownership could be recorded`);
  const record = {
    pid: child.pid,
    signature,
    port: state.ports[definition.portRole],
    logPath,
    startedAt: new Date().toISOString(),
  };
  state.processes[name] = record;
  state.updatedAt = new Date().toISOString();
  writeState(root, state);

  try {
    await waitForHealth(record.port, definition.healthPath || "/health");
  } catch (error) {
    await stopOwnedProcess(root, name);
    throw error;
  }
  return { name, running: true, owned: true, ...record };
}

async function waitForExit(pid, timeoutMs) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      process.kill(pid, 0);
    } catch {
      return true;
    }
    await new Promise((resolvePromise) => setTimeout(resolvePromise, 50));
  }
  return false;
}

export async function stopOwnedProcess(root, name) {
  assertMutableBranch(root);
  const state = readState(root);
  const record = state.processes[name];
  if (!record) return { name, stopped: false, reason: "not recorded" };
  if (!processIsOwned(record)) throw new Error(`refusing to stop ${name}; pid ownership cannot be proven`);

  process.kill(-record.pid, "SIGTERM");
  if (!(await waitForExit(record.pid, 3000))) {
    if (!processIsOwned(record)) throw new Error(`refusing SIGKILL for ${name}; ownership changed after SIGTERM`);
    process.kill(-record.pid, "SIGKILL");
    await waitForExit(record.pid, 1000);
  }
  delete state.processes[name];
  state.updatedAt = new Date().toISOString();
  writeState(root, state);
  return { name, stopped: true };
}

export function ownedProcessStatus(root, name) {
  const state = readState(root);
  const record = state.processes[name] || null;
  return { name, running: processIsOwned(record), owned: processIsOwned(record), record };
}

export function prepareRuntimeMirror(root) {
  assertMutableBranch(root);
  const state = readState(root);
  const config = loadConfig(root);
  const dirty = Boolean(git(root, ["status", "--porcelain"]));
  if (config.requireCleanRuntimeMirror && dirty) {
    throw new Error("runtime mirroring requires a clean committed worktree");
  }
  const mirrorRoot = join(state.paths.runtime, "mirror");
  const stagingRoot = join(state.paths.runtime, `mirror.next-${randomUUID()}`);
  const files = [];
  for (const relativePath of config.runtimeFiles || []) {
    const source = resolve(root, relativePath);
    if (!isStrictDescendant(root, source) || !existsSync(source)) throw new Error(`invalid runtime source: ${relativePath}`);
    const destination = resolve(stagingRoot, relativePath);
    if (!isStrictDescendant(stagingRoot, destination)) throw new Error(`invalid runtime destination: ${relativePath}`);
    mkdirSync(dirname(destination), { recursive: true });
    copyFileSync(source, destination);
    const digest = sha256(readFileSync(source));
    files.push({ path: relativePath, sha256: digest });
  }
  if (existsSync(mirrorRoot)) {
    if (!isStrictDescendant(state.paths.runtime, mirrorRoot) || lstatSync(mirrorRoot).isSymbolicLink()) {
      throw new Error("refusing to replace an unowned or symlinked runtime mirror");
    }
    rmSync(mirrorRoot, { recursive: true, force: false });
  }
  renameSync(stagingRoot, mirrorRoot);
  const manifest = {
    schema: "public-runtime-mirror-v1",
    laneId: state.laneId,
    head: git(root, ["rev-parse", "HEAD"]),
    dirty,
    files,
    createdAt: new Date().toISOString(),
  };
  atomicWriteJson(join(state.paths.evidence, "runtime-mirror.json"), manifest);
  return manifest;
}

export function seedUiFixture(root) {
  assertMutableBranch(root);
  const state = readState(root);
  const sessionId = `demo-${state.laneId}`;
  const fixture = {
    schema: "public-ui-fixture-v1",
    fake: true,
    sessionId,
    teacher: { name: "Demo Teacher" },
    createdAt: new Date().toISOString(),
  };
  atomicWriteJson(join(state.paths.fixtures, "ui-session.json"), fixture);
  return {
    fixturePath: join(state.paths.fixtures, "ui-session.json"),
    loginUrl: `http://localhost:${state.ports.app}/dev-login?session=${sessionId}`,
  };
}

function sharedLockPath(root) {
  const commonDir = git(root, ["rev-parse", "--git-common-dir"]);
  const repoKey = sha256(resolve(root, commonDir)).slice(0, 16);
  return join(tmpdir(), "public-teachclaw-locks", repoKey, "tester.json");
}

export function acquireTesterLock(root) {
  assertMutableBranch(root);
  const state = readState(root);
  const path = sharedLockPath(root);
  mkdirSync(dirname(path), { recursive: true });
  const owner = { laneId: state.laneId, repoRoot: state.repoRoot, acquiredAt: new Date().toISOString() };
  try {
    const fd = openSync(path, "wx", 0o600);
    writeFileSync(fd, `${JSON.stringify(owner, null, 2)}\n`);
    closeSync(fd);
  } catch (error) {
    if (existsSync(path)) throw new Error(`tester is already owned: ${readFileSync(path, "utf8").trim()}`);
    throw error;
  }
  return owner;
}

export function testerOwner(root) {
  const path = sharedLockPath(root);
  return existsSync(path) ? JSON.parse(readFileSync(path, "utf8")) : null;
}

export function releaseTesterLock(root) {
  assertMutableBranch(root);
  const state = readState(root);
  const path = sharedLockPath(root);
  if (!existsSync(path)) return { released: false, reason: "not locked" };
  const owner = JSON.parse(readFileSync(path, "utf8"));
  if (owner.laneId !== state.laneId || resolve(owner.repoRoot) !== resolve(root)) {
    throw new Error("refusing to release tester lock owned by another lane");
  }
  rmSync(path);
  return { released: true };
}

export function cleanupLane(root) {
  assertMutableBranch(root);
  const state = readState(root);
  const running = Object.entries(state.processes).filter(([, record]) => processIsOwned(record));
  if (running.length) throw new Error(`refusing cleanup while owned processes run: ${running.map(([name]) => name).join(", ")}`);
  const owner = testerOwner(root);
  if (owner?.laneId === state.laneId) throw new Error("refusing cleanup while this lane owns the tester lock; release it explicitly");
  const laneRoot = assertSafeLaneRoot(root, state.laneRoot);
  rmSync(laneRoot, { recursive: true, force: false });
  return { cleaned: true, laneRoot };
}

function output(value) {
  process.stdout.write(`${JSON.stringify(value, null, 2)}\n`);
}

async function main() {
  const root = resolveRepoRoot();
  const [action, name] = process.argv.slice(2);
  if (action === "init") return output(initialiseLane(root));
  if (action === "status") {
    const state = readState(root);
    return output({ ...state, processes: Object.fromEntries(Object.keys(state.processes).map((key) => [key, ownedProcessStatus(root, key)])) });
  }
  if (action === "ui-seed") return output(seedUiFixture(root));
  if (action === "runtime-prepare") return output(prepareRuntimeMirror(root));
  if (action === "process-up" && name) return output(await startOwnedProcess(root, name));
  if (action === "process-status" && name) return output(ownedProcessStatus(root, name));
  if (action === "process-down" && name) return output(await stopOwnedProcess(root, name));
  if (action === "tester-acquire") return output(acquireTesterLock(root));
  if (action === "tester-owner") return output(testerOwner(root));
  if (action === "tester-release") return output(releaseTesterLock(root));
  if (action === "cleanup") return output(cleanupLane(root));
  throw new Error("usage: lane-controller.mjs init|status|ui-seed|runtime-prepare|process-up NAME|process-status NAME|process-down NAME|tester-acquire|tester-owner|tester-release|cleanup");
}

if (resolve(process.argv[1] || "") === resolve(THIS_FILE)) {
  main().catch((error) => {
    process.stderr.write(`${error instanceof Error ? error.message : String(error)}\n`);
    process.exitCode = 1;
  });
}
