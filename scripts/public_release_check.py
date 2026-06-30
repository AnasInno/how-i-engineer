#!/usr/bin/env python3
"""Fail fast if a folder is not safe to push as the public daily automation repo."""
from __future__ import annotations

import argparse
import re
from pathlib import Path

SKIP_DIR_PARTS = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
}

BLOCKED_DIR_PARTS = {
    ".job-application-browser",
    ".job-apply-chrome-profile",
    ".job-apply-google-profile-2",
    ".job-apply-robotics-profile",
    ".job-apply-robotics-profile-3",
    ".job-apply-single-profile",
    ".job-apply-two-profile",
    "docs/applications",
    "docs/career-assets",
    "inbox",
    "tmp",
}

BLOCKED_SUFFIXES = {
    ".docx",
    ".pdf",
    ".xlsx",
    ".sqlite",
    ".db",
}

TEXT_SUFFIXES = {
    ".css",
    ".html",
    ".js",
    ".json",
    ".md",
    ".mmd",
    ".py",
    ".sh",
    ".toml",
    ".txt",
    ".yml",
    ".yaml",
}

CONTENT_PATTERNS = [
    ("OpenAI/OpenRouter style secret", re.compile(r"\b(sk-[A-Za-z0-9_-]{20,}|sk-or-[A-Za-z0-9_-]{20,})\b")),
    ("GitHub token", re.compile(r"\bgh[oprsu]_[A-Za-z0-9_]{20,}\b")),
    ("private phone number", re.compile(r"\+44\s?7\d{3}\s?\d{6}|\+44\s?7\d{2,4}\s?\d{3}\s?\d{3,4}")),
    ("private workspace path reference", re.compile(r"(docs/career-assets|docs/applications|\.job-apply|inbox/|tmp/)")),
    ("non-placeholder API assignment", re.compile(r"(?i)(api[_-]?key|access[_-]?token|secret|password)\s*[:=]\s*['\"]?(?!$|<|your-|test-|example|placeholder)[A-Za-z0-9_.:/+=-]{12,}")),
]


def rel_parts(path: Path, root: Path) -> set[str]:
    rel = path.relative_to(root).as_posix()
    parts = set(path.relative_to(root).parts)
    for blocked in BLOCKED_DIR_PARTS:
        if "/" in blocked and rel.startswith(blocked + "/"):
            parts.add(blocked)
    return parts


def blocked_dir_label(path: Path, root: Path) -> str | None:
    rel = path.relative_to(root).as_posix()
    parts = set(path.relative_to(root).parts)
    for blocked in BLOCKED_DIR_PARTS:
        if "/" in blocked:
            if rel == blocked or rel.startswith(blocked + "/"):
                return blocked
        elif blocked in parts:
            return blocked
    return None


def is_text(path: Path) -> bool:
    return path.suffix.lower() in TEXT_SUFFIXES or path.name in {".gitignore", "Makefile", "LICENSE"}


def check(root: Path) -> list[str]:
    findings: list[str] = []
    reported_blocked_dirs: set[str] = set()
    for path in sorted(root.rglob("*")):
        rel_path = path.relative_to(root)
        if any(part in SKIP_DIR_PARTS for part in rel_path.parts):
            continue
        blocked_dir = blocked_dir_label(path, root)
        if blocked_dir:
            if blocked_dir not in reported_blocked_dirs:
                findings.append(f"blocked private path: {blocked_dir}/")
                reported_blocked_dirs.add(blocked_dir)
            continue
        if not path.is_file():
            continue
        rel = rel_path
        name = path.name.lower()
        if name.startswith(".env") and name != ".env.example":
            findings.append(f"blocked env file: {rel}")
        if "private" in name or "secret" in name or "token" in name:
            findings.append(f"blocked sensitive filename: {rel}")
        if path.suffix.lower() in BLOCKED_SUFFIXES:
            findings.append(f"blocked binary/private suffix: {rel}")
        if is_text(path):
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                findings.append(f"not utf-8 text: {rel}")
                continue
            for label, pattern in CONTENT_PATTERNS:
                if rel.as_posix() == "scripts/public_release_check.py" and label == "private workspace path reference":
                    continue
                if pattern.search(text):
                    findings.append(f"{label}: {rel}")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="Folder to check before public push")
    args = parser.parse_args()

    root = Path(args.path).resolve()
    if not root.exists() or not root.is_dir():
        raise SystemExit(f"Not a directory: {root}")

    findings = check(root)
    if findings:
        print("PUBLIC RELEASE CHECK FAILED")
        for finding in findings:
            print(f"- {finding}")
        return 1
    print(f"PUBLIC RELEASE CHECK PASSED: {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
