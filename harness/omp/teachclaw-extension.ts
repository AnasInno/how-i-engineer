import { existsSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, join, resolve } from "node:path";
import type { ExtensionAPI } from "@oh-my-pi/pi-coding-agent";
import { isDestructiveCommand } from "../scripts/destructive-guard.mjs";

export const ACTIONS = [
  "status",
  "init",
  "ui-seed",
  "app-up",
  "app-status",
  "app-down",
  "gateway-prepare",
  "gateway-up",
  "gateway-status",
  "gateway-down",
  "tester-acquire",
  "tester-owner",
  "tester-release",
  "cleanup",
] as const;

export type LaneAction = (typeof ACTIONS)[number];
export type ActionTier = "read" | "write" | "exec";

const COMMANDS: Record<LaneAction, string[]> = {
  status: ["status"],
  init: ["init"],
  "ui-seed": ["ui-seed"],
  "app-up": ["process-up", "app"],
  "app-status": ["process-status", "app"],
  "app-down": ["process-down", "app"],
  "gateway-prepare": ["runtime-prepare"],
  "gateway-up": ["process-up", "gateway"],
  "gateway-status": ["process-status", "gateway"],
  "gateway-down": ["process-down", "gateway"],
  "tester-acquire": ["tester-acquire"],
  "tester-owner": ["tester-owner"],
  "tester-release": ["tester-release"],
  cleanup: ["cleanup"],
};

const READ_ACTIONS = new Set<LaneAction>(["status", "app-status", "gateway-status", "tester-owner"]);
const EXEC_ACTIONS = new Set<LaneAction>([
  "app-down",
  "gateway-down",
  "tester-acquire",
  "tester-release",
  "cleanup",
]);

export function classifyAction(action: LaneAction): ActionTier {
  if (READ_ACTIONS.has(action)) return "read";
  if (EXEC_ACTIONS.has(action)) return "exec";
  return "write";
}

export function resolveGitRoot(cwd: string, hasPath: (path: string) => boolean): string | undefined {
  let current = resolve(cwd);
  while (true) {
    if (hasPath(join(current, ".git"))) return current;
    const parent = dirname(current);
    if (parent === current) return undefined;
    current = parent;
  }
}

function redact(value: string) {
  return value
    .replace(/\bBearer\s+[A-Za-z0-9._~+/=-]+/gi, "Bearer <redacted>")
    .replace(/\b[A-Z][A-Z0-9_]*(?:KEY|TOKEN|SECRET|PASSWORD)\s*=\s*[^\s,;]+/g, "<redacted environment assignment>");
}

async function branch(pi: ExtensionAPI, root: string, signal: AbortSignal) {
  const result = await pi.exec("git", ["branch", "--show-current"], { cwd: root, timeout: 30_000, signal });
  return result.stdout.trim();
}

async function runLane(pi: ExtensionAPI, cwd: string, action: LaneAction, signal: AbortSignal) {
  const root = resolveGitRoot(cwd, existsSync);
  if (!root) throw new Error("TeachClaw harness root not found");
  const currentBranch = await branch(pi, root, signal);
  if (classifyAction(action) !== "read" && (!currentBranch || currentBranch === "main")) {
    throw new Error(`mutating lane action '${action}' is refused on main or detached HEAD`);
  }
  const result = await pi.exec("node", ["harness/scripts/lane-controller.mjs", ...COMMANDS[action]], {
    cwd: root,
    timeout: classifyAction(action) === "exec" ? 900_000 : 300_000,
    signal,
  });
  return {
    content: [{ type: "text" as const, text: redact(result.stdout || result.stderr) }],
    details: { action, root, branch: currentBranch, exitCode: result.code },
    isError: result.code !== 0,
  };
}

async function runProof(pi: ExtensionAPI, cwd: string, action: "provider-readiness" | "fresh-run-verifier", args: string[], signal: AbortSignal) {
  const root = resolveGitRoot(cwd, existsSync);
  if (!root) throw new Error("TeachClaw harness root not found");
  const currentBranch = await branch(pi, root, signal);
  if (!currentBranch || currentBranch === "main") throw new Error(`proof '${action}' is refused on main`);
  const command = action === "provider-readiness"
    ? ["harness/scripts/provider-readiness.mjs"]
    : ["harness/scripts/fresh-run-verifier.mjs", ...args];
  const result = await pi.exec("node", command, { cwd: root, timeout: 300_000, signal });
  return {
    content: [{ type: "text" as const, text: redact(result.stdout || result.stderr) }],
    details: { action, root, branch: currentBranch, exitCode: result.code },
    isError: result.code !== 0,
  };
}

function actionFromUnknown(value: unknown): LaneAction | undefined {
  const action = value && typeof value === "object" ? (value as { action?: unknown }).action : undefined;
  return typeof action === "string" && (ACTIONS as readonly string[]).includes(action) ? action as LaneAction : undefined;
}

export default function teachClawHarness(pi: ExtensionAPI) {
  const { z } = pi.zod;

  pi.on("before_agent_start", async () => ({
    systemPromptAppend: [
      "TeachClaw harness contract:",
      "- Use one generic task worker by default; parallelise only independent outcomes.",
      "- Use typed lane actions for lifecycle mechanics; do not invent launch, sync, lock, evidence, or cleanup wrappers.",
      "- Keep realistic interaction in the driver and deterministic assertions in the verifier.",
      "- After ui-seed, use the exact returned loginUrl.",
    ].join("\n"),
  }));

  pi.registerTool({
    name: "teachclaw_lane",
    label: "TeachClaw Lane",
    description: "Run one worktree-owned deterministic lane action.",
    approval: (params) => {
      const action = actionFromUnknown(params);
      if (!action) return { tier: "exec", reason: "action could not be classified safely" };
      const tier = classifyAction(action);
      return tier === "exec" ? { tier, reason: `external or destructive lane action: ${action}` } : tier;
    },
    parameters: z.object({ action: z.enum(ACTIONS) }),
    async execute(_id, params, signal, _update, ctx) {
      return runLane(pi, ctx.cwd, params.action, signal ?? new AbortController().signal);
    },
  });

  pi.registerTool({
    name: "teachclaw_proof",
    label: "TeachClaw Proof",
    description: "Run a bounded deterministic proof driver.",
    approval: "exec",
    parameters: z.object({
      action: z.enum(["provider-readiness", "fresh-run-verifier"] as const),
      args: z.array(z.string()).optional(),
    }),
    async execute(_id, params, signal, _update, ctx) {
      return runProof(pi, ctx.cwd, params.action, params.args ?? [], signal ?? new AbortController().signal);
    },
  });

  pi.on("tool_call", async (event, ctx) => {
    if (event.toolName !== "bash") return;
    const input = event.input as { command?: unknown; cwd?: unknown };
    if (typeof input.command !== "string") return;
    const commandCwd = typeof input.cwd === "string" ? resolve(ctx.cwd, input.cwd) : resolve(ctx.cwd);
    const root = resolveGitRoot(commandCwd, existsSync) ?? commandCwd;
    if (isDestructiveCommand(input.command, [root, homedir()], commandCwd)) {
      return { block: true, reason: "blocked recursive deletion targeting a protected path" };
    }
  });
}
