#!/usr/bin/env node

import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { spawnSync } from "node:child_process";

function required(name) {
  const value = process.env[name]?.trim();
  if (!value) throw new Error(`${name} is required`);
  return value;
}

function git(root, args) {
  const result = spawnSync("git", args, { cwd: root, encoding: "utf8" });
  if (result.status !== 0) throw new Error(`git ${args.join(" ")} failed`);
  return String(result.stdout).trim();
}

const root = resolve(git(process.cwd(), ["rev-parse", "--show-toplevel"]));
const state = JSON.parse(readFileSync(join(root, ".teachclaw-lane", "lane-state.json"), "utf8"));
const baseUrl = required("PROVIDER_BASE_URL").replace(/\/$/, "");
const model = required("PROVIDER_MODEL");
const apiKey = required("PROVIDER_API_KEY");
const endpoint = `${baseUrl}/chat/completions`;
const started = Date.now();

const response = await fetch(endpoint, {
  method: "POST",
  headers: {
    authorization: `Bearer ${apiKey}`,
    "content-type": "application/json",
  },
  body: JSON.stringify({
    model,
    messages: [{ role: "user", content: "Reply with READY only." }],
    max_tokens: 8,
    temperature: 0,
  }),
  signal: AbortSignal.timeout(60_000),
});

const body = await response.json().catch(() => null);
const ready = response.ok && typeof body?.choices?.[0]?.message?.content === "string";
const evidence = {
  schema: "public-provider-readiness-v1",
  ready,
  model,
  endpointOrigin: new URL(baseUrl).origin,
  status: response.status,
  latencyMs: Date.now() - started,
  head: git(root, ["rev-parse", "HEAD"]),
  dirty: Boolean(git(root, ["status", "--porcelain"])),
  laneId: state.laneId,
  checkedAt: new Date().toISOString(),
};

const outputPath = join(state.paths.evidence, "provider-readiness.json");
mkdirSync(dirname(outputPath), { recursive: true });
writeFileSync(outputPath, `${JSON.stringify(evidence, null, 2)}\n`, { mode: 0o600 });
process.stdout.write(`${JSON.stringify({ ...evidence, outputPath }, null, 2)}\n`);
if (!ready) process.exitCode = 1;
