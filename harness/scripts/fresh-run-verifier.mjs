#!/usr/bin/env node

import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";

function parseArgs(argv) {
  const result = {};
  for (let index = 0; index < argv.length; index += 2) {
    const key = argv[index];
    const value = argv[index + 1];
    if (!key?.startsWith("--") || value === undefined) throw new Error("arguments must be --name value pairs");
    result[key.slice(2)] = value;
  }
  return result;
}

export function selectFreshRun(baseline, finalState, scenario) {
  const baselineIds = new Set((baseline.runs || []).map((run) => run.runId));
  return (finalState.runs || []).find((run) => (
    run.runId
    && !baselineIds.has(run.runId)
    && run.status === scenario.expected.status
    && run.sourceFileCount === scenario.expected.sourceFileCount
    && run.frameTotal === scenario.expected.frameTotal
  ));
}

export function verifyFreshRun(baseline, finalState, scenario) {
  const run = selectFreshRun(baseline, finalState, scenario);
  const baselineMessageIds = new Set((baseline.messages || []).map((message) => message.id));
  const freshMessages = (finalState.messages || []).filter((message) => message.id && !baselineMessageIds.has(message.id));
  const checks = {
    fresh_run_present: Boolean(run),
    fresh_teacher_turn_present: freshMessages.some((message) => message.role === "user"),
    fresh_assistant_turn_present: freshMessages.some((message) => message.role === "assistant"),
    no_active_jobs: scenario.expected.requireNoActiveJobs ? (finalState.activeJobs || []).length === 0 : true,
  };
  const passed = Object.values(checks).every(Boolean);
  return {
    schema: "public-fresh-run-verifier-v1",
    passed,
    checks,
    selectedRun: run || null,
    baselineRunCount: (baseline.runs || []).length,
    finalRunCount: (finalState.runs || []).length,
    freshMessageCount: freshMessages.length,
  };
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  for (const name of ["baseline", "final", "scenario", "out"]) {
    if (!args[name]) throw new Error(`--${name} is required`);
  }
  const baseline = JSON.parse(readFileSync(resolve(args.baseline), "utf8"));
  const finalState = JSON.parse(readFileSync(resolve(args.final), "utf8"));
  const scenario = JSON.parse(readFileSync(resolve(args.scenario), "utf8"));
  const result = verifyFreshRun(baseline, finalState, scenario);
  const outputPath = resolve(args.out);
  mkdirSync(dirname(outputPath), { recursive: true });
  writeFileSync(outputPath, `${JSON.stringify(result, null, 2)}\n`, { mode: 0o600 });
  process.stdout.write(`${JSON.stringify({ ...result, outputPath }, null, 2)}\n`);
  if (!result.passed) process.exitCode = 1;
}

if (resolve(process.argv[1] || "") === resolve(new URL(import.meta.url).pathname)) {
  main().catch((error) => {
    process.stderr.write(`${error instanceof Error ? error.message : String(error)}\n`);
    process.exitCode = 1;
  });
}
