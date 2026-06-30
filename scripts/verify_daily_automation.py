#!/usr/bin/env python3
"""Verify a daily automation folder and write VERIFY.md."""
from __future__ import annotations

import argparse
import subprocess
from datetime import datetime, timezone
from pathlib import Path

REQUIRED = ["README.md", "IDEA.md", "Makefile", "web_config.json", "data/sample_input.txt", "scripts/run.py"]


def run(cmd: list[str], cwd: Path) -> tuple[int, str]:
    proc = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=False, timeout=120)
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="Automation folder")
    args = parser.parse_args()

    root = Path(args.path).resolve()
    failures: list[str] = []
    notes: list[str] = []

    if not root.exists() or not root.is_dir():
        raise SystemExit(f"Not a directory: {root}")

    for rel in REQUIRED:
        if not (root / rel).exists():
            failures.append(f"missing {rel}")

    readme = (root / "README.md").read_text(encoding="utf-8") if (root / "README.md").exists() else ""
    for phrase in ["Problem", "Quick start", "Limitations", "Verification"]:
        if phrase not in readme:
            failures.append(f"README missing section marker: {phrase}")

    smoke_code = None
    smoke_log = ""
    if (root / "Makefile").exists():
        smoke_code, smoke_log = run(["make", "smoke"], root)
        if smoke_code != 0:
            failures.append("make smoke failed")
        else:
            notes.append("make smoke passed")
    else:
        failures.append("cannot run smoke without Makefile")

    web_log = ""
    if (root / "web_config.json").exists():
        web_code, web_log = run(["python3", "../../scripts/local_web_shell.py", "--app-root", ".", "--check"], root)
        if web_code != 0:
            failures.append("web_config.json failed local web shell check")
        else:
            notes.append("local web shell config passed")

    output_files = [p for p in (root / "output").glob("*.*") if p.name != ".gitkeep"] if (root / "output").exists() else []
    if not output_files:
        failures.append("no generated sample output under output/")
    else:
        notes.append("sample output exists: " + ", ".join(p.name for p in output_files))

    status = "PASS" if not failures else "FAIL"
    report = [
        "# Verification",
        "",
        f"Status: **{status}**",
        f"Checked: {datetime.now(timezone.utc).isoformat()}",
        f"Folder: `{root.name}`",
        "",
        "## Checks",
        "",
    ]
    if notes:
        report.extend(f"- ✅ {n}" for n in notes)
    if failures:
        report.extend(f"- ❌ {f}" for f in failures)
    report.extend(["", "## Smoke log", "", "```text", smoke_log or "No smoke log.", "```", ""])
    report.extend(["", "## Web shell check", "", "```text", web_log or "No web shell check.", "```", ""])
    (root / "VERIFY.md").write_text("\n".join(report), encoding="utf-8")
    print(f"{status}: {root / 'VERIFY.md'}")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
