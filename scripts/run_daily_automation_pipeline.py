#!/usr/bin/env python3
"""Run the daily automation local pipeline: scaffold/existing -> verify -> drafts -> release packet."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str], *, allow_fail: bool = False) -> int:
    print("$ " + " ".join(cmd))
    proc = subprocess.run(cmd, cwd=ROOT, text=True, check=False)
    if proc.returncode and not allow_fail:
        raise SystemExit(proc.returncode)
    return proc.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--idea", help="Create a new automation from this idea/title")
    group.add_argument("--path", help="Use an existing automation folder")
    parser.add_argument("--day", type=int, help="Explicit day number when using --idea")
    args = parser.parse_args()

    if args.idea:
        cmd = [sys.executable, "scripts/new_daily_automation.py", args.idea]
        if args.day:
            cmd += ["--day", str(args.day)]
        proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, check=False)
        print("$ " + " ".join(cmd))
        print(proc.stdout, end="")
        if proc.stderr:
            print(proc.stderr, end="", file=sys.stderr)
        if proc.returncode:
            return proc.returncode
        rel = proc.stdout.strip().splitlines()[-1]
        path = ROOT / rel
    else:
        path = Path(args.path).resolve()

    rel_path = str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
    run([sys.executable, "scripts/verify_daily_automation.py", rel_path])
    run([sys.executable, "scripts/draft_social_post.py", rel_path])
    run([sys.executable, "scripts/release_packet.py", rel_path])
    print("\nLocal pipeline complete. External push/post remains approval-gated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
