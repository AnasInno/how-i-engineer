#!/usr/bin/env python3
"""Sample local automation entrypoint. Replace with the real daily tool."""
from __future__ import annotations

import argparse
from pathlib import Path


def convert(text: str) -> str:
    # Deterministic placeholder: turns messy notes into simple action bullets.
    parts = [p.strip().strip(".") for p in text.replace("\n", " ").split(".") if p.strip()]
    lines = ["# Action Draft", ""]
    for part in parts:
        lines.append(f"- {part}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/sample_input.txt")
    parser.add_argument("--output", default="output/sample_output.md")
    args = parser.parse_args()

    src = Path(args.input)
    dst = Path(args.output)
    if not src.exists():
        raise SystemExit(f"Input file not found: {src}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(convert(src.read_text(encoding="utf-8")), encoding="utf-8")
    print(f"Wrote {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
