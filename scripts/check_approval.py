#!/usr/bin/env python3
"""Check approval manifest for a release action."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALID = {"git-push", "x-post", "linkedin-post", "publish-release"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("slug")
    parser.add_argument("action", choices=sorted(VALID))
    args = parser.parse_args()

    path = ROOT / "approvals" / f"{args.slug}.release.json"
    if not path.exists():
        raise SystemExit(f"BLOCKED: missing approval manifest {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("approved") is not True:
        raise SystemExit("BLOCKED: approval manifest does not set approved=true")
    if data.get("slug") != args.slug:
        raise SystemExit(f"BLOCKED: approval slug mismatch: {data.get('slug')} != {args.slug}")
    allowed = set(data.get("allow") or [])
    if args.action not in allowed:
        raise SystemExit(f"BLOCKED: action {args.action} not in allow list {sorted(allowed)}")
    print(f"APPROVED: {args.action} for {args.slug}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
