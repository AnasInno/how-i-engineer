#!/usr/bin/env python3
"""Export the daily automation lane into a clean public repo folder."""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PUBLIC_PATHS = [
    ".agents/skills/daily-ai-automation-posting/SKILL.md",
    ".agents/skills/daily-ai-automation-research/SKILL.md",
    ".agents/skills/daily-ai-automation-ship/SKILL.md",
    "AGENTS.md",
    "approvals/README.md",
    "automations/_template/README.md",
    "automations/day-001-messy-notes-to-action-draft",
    "automations/day-002-recall-radar",
    "codex/daily-automation",
    "drafts/daily-automation/day-001-messy-notes-to-action-draft",
    "drafts/daily-automation/day-002-recall-radar",
    "runs/daily-automation/day-001-messy-notes-to-action-draft",
    "runs/daily-automation/day-002-recall-radar",
    "scripts/check_approval.py",
    "scripts/draft_social_post.py",
    "scripts/export_public_daily_automation_repo.py",
    "scripts/local_web_shell.py",
    "scripts/new_daily_automation.py",
    "scripts/public_release_check.py",
    "scripts/release_packet.py",
    "scripts/run_daily_automation_pipeline.py",
    "scripts/verify_daily_automation.py",
]

EXCLUDE_DIRS = {".git", ".venv", "__pycache__", ".pytest_cache"}
EXCLUDE_FILES = {"data/web_input.txt"}

PUBLIC_GITIGNORE = """.DS_Store
.venv/
__pycache__/
.pytest_cache/
*.pyc
.env
.env.*
!.env.example
*.sqlite
*.db
automations/day-*/.venv/
automations/day-*/data/web_input.txt
"""


def should_skip(path: Path, source: Path) -> bool:
    rel = path.relative_to(source).as_posix()
    if rel in EXCLUDE_FILES:
        return True
    return any(part in EXCLUDE_DIRS for part in path.relative_to(source).parts)


def copy_path(source: Path, dest: Path) -> None:
    if source.is_dir():
        for path in source.rglob("*"):
            if should_skip(path, source):
                continue
            target = dest / path.relative_to(source)
            if path.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)
    else:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)


def run(cmd: list[str], cwd: Path) -> None:
    print("$ " + " ".join(cmd))
    subprocess.run(cmd, cwd=cwd, text=True, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dest", required=True, help="Destination folder for the public repo export")
    parser.add_argument("--force", action="store_true", help="Delete destination before exporting")
    parser.add_argument("--init-git", action="store_true", help="Initialise git in the exported folder")
    parser.add_argument("--commit", default="", help="Commit message to create after export when --init-git is set")
    args = parser.parse_args()

    dest = Path(args.dest).expanduser().resolve()
    if dest.exists():
        if not args.force:
            raise SystemExit(f"Destination exists. Re-run with --force to replace: {dest}")
        shutil.rmtree(dest)
    dest.mkdir(parents=True)

    for rel in PUBLIC_PATHS:
        source = ROOT / rel
        if not source.exists():
            raise SystemExit(f"Missing public export path: {rel}")
        copy_path(source, dest / rel)

    readme_source = ROOT / "codex/daily-automation/PUBLIC-README.md"
    if readme_source.exists():
        shutil.copy2(readme_source, dest / "README.md")
    license_source = ROOT / "codex/daily-automation/PUBLIC-LICENSE-MIT.txt"
    if license_source.exists():
        shutil.copy2(license_source, dest / "LICENSE")
    (dest / ".gitignore").write_text(PUBLIC_GITIGNORE, encoding="utf-8")

    run([sys.executable, "scripts/public_release_check.py", str(dest)], ROOT)

    if args.init_git:
        run(["git", "init"], dest)
        run(["git", "config", "user.name", "Anas Abdi"], dest)
        run(["git", "config", "user.email", "abdianas919@gmail.com"], dest)
        run(["git", "add", "-A"], dest)
        if args.commit:
            run(["git", "commit", "-m", args.commit], dest)

    print(dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
