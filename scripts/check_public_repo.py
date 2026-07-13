#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = {
    "README.md",
    "AGENTS.md",
    "docs/architecture.md",
    "docs/proof-lanes.md",
    "docs/safety-and-ownership.md",
    ".agents/skills/how-i-engineer-omp-harness/SKILL.md",
    "examples/task-contract.md",
    "harness/README.md",
    "harness/bin/teachclaw-omp",
    "harness/lane.config.json",
    "harness/omp/teachclaw-extension.ts",
    "harness/omp/teachclaw.yml",
    "harness/scripts/lane-controller.mjs",
    "harness/scripts/destructive-guard.mjs",
    "harness/scripts/provider-readiness.mjs",
    "harness/scripts/fresh-run-verifier.mjs",
    "harness/tests/harness.test.mjs",
}

FORBIDDEN_PATH_PARTS = {"automations", "daily-automation", "drafts", "runs"}
SECRET_PATTERNS = {
    "secret-like token": re.compile(r"\b(?:sk-|gh[pousr]_)[A-Za-z0-9_-]{20,}\b"),
    "private home path": re.compile(r"/Users/[A-Za-z0-9._-]+/"),
    "private network address": re.compile(r"\b(?:10|127|192\.168)\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"),
}


def main() -> int:
    findings: list[str] = []

    for relative in sorted(REQUIRED):
        if not (ROOT / relative).is_file():
            findings.append(f"missing required file: {relative}")

    for path in sorted(ROOT.rglob("*")):
        relative = path.relative_to(ROOT)
        if ".git" in relative.parts or not path.is_file():
            continue
        if FORBIDDEN_PATH_PARTS.intersection(relative.parts):
            findings.append(f"stale daily-automation path: {relative}")
        if path.suffix.lower() not in {".json", ".md", ".mjs", ".py", ".ts", ".yml", ".yaml", ".txt"} and path.name not in {"AGENTS.md", "README.md", "Makefile", ".gitignore", "teachclaw-omp"}:
            continue
        text = path.read_text(encoding="utf-8")
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                findings.append(f"{label}: {relative}")

    if findings:
        print("PUBLIC REPO CHECK FAILED")
        for finding in findings:
            print(f"- {finding}")
        return 1

    print("PUBLIC REPO CHECK PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
