#!/usr/bin/env python3
"""Draft X and LinkedIn posts for a daily automation."""
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def first_heading(readme: str, fallback: str) -> str:
    for line in readme.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def section(text: str, name: str) -> str:
    pattern = rf"## {re.escape(name)}\n\n(?P<body>.*?)(?=\n## |\Z)"
    m = re.search(pattern, text, re.S)
    return re.sub(r"\s+", " ", m.group("body")).strip() if m else ""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path")
    args = parser.parse_args()

    folder = Path(args.path).resolve()
    slug = folder.name
    readme_path = folder / "README.md"
    idea_path = folder / "IDEA.md"
    verify_path = folder / "VERIFY.md"
    if not readme_path.exists():
        raise SystemExit(f"Missing README: {readme_path}")

    readme = readme_path.read_text(encoding="utf-8")
    title = first_heading(readme, slug)
    problem = section(readme, "Problem") or "A boring workflow had too many manual steps."
    does = section(readme, "What it does") or "I built a tiny local automation for it."
    verified = "PASS" in verify_path.read_text(encoding="utf-8") if verify_path.exists() else False
    proof = "Smoke test passes with sample input/output." if verified else "Verification pending."

    outdir = ROOT / "drafts" / "daily-automation" / slug
    outdir.mkdir(parents=True, exist_ok=True)

    x = f"""Day {slug[4:7]} of tiny practical AI automations.\n\nProblem: {problem}\n\nBuilt: {title} — {does}\n\nProof: {proof}\n\nRepo: {{{{REPO_URL}}}}\n"""
    linkedin = f"""I'm building TeachClaw as the serious product, and shipping tiny practical AI automations on the side.\n\nToday: {title}\n\nThe boring problem:\n{problem}\n\nWhat I built:\n{does}\n\nProof:\n{proof}\n\nI like this lane because the tools stay small: one input, one useful output, honest limits, runnable sample.\n\nRepo: {{{{REPO_URL}}}}\n"""

    (outdir / "x.md").write_text(x, encoding="utf-8")
    (outdir / "linkedin.md").write_text(linkedin, encoding="utf-8")
    (outdir / "metadata.json").write_text('''{
  "status": "drafted",
  "live_posted": false,
  "requires_approval_for_live_posting": true
}
''', encoding="utf-8")
    print(outdir.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
