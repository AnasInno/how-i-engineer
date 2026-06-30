#!/usr/bin/env python3
"""Create a new day-XXX daily automation scaffold."""
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTOMATIONS = ROOT / "automations"


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-") or "automation"


def next_day() -> int:
    AUTOMATIONS.mkdir(exist_ok=True)
    nums = []
    for p in AUTOMATIONS.iterdir():
        if not p.is_dir():
            continue
        m = re.match(r"day-(\d{3})-", p.name)
        if m:
            nums.append(int(m.group(1)))
    return (max(nums) + 1) if nums else 1


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("idea", help="Short idea/title for the automation")
    parser.add_argument("--day", type=int, help="Explicit day number")
    parser.add_argument("--force", action="store_true", help="Allow writing into existing folder")
    args = parser.parse_args()

    day = args.day or next_day()
    base_slug = slugify(args.idea)
    slug = f"day-{day:03d}-{base_slug}"
    target = AUTOMATIONS / slug
    if target.exists() and not args.force:
        raise SystemExit(f"Refusing to overwrite existing folder: {target}")

    title = args.idea.strip()
    write(target / "IDEA.md", f"""# {title}

## Persona

Who has this boring problem?

## Pain

What manual workflow is annoying today?

## Current workflow

What do they do without this automation?

## Input

`data/sample_input.txt`

## Output

`output/sample_output.md`

## One-day scope

Why this can be built and understood quickly.

## Idea filter score

- Pain is boring and common: 0/2
- Input/output are obvious: 0/2
- Demo can run in under 2 minutes: 0/2
- Saves real manual effort: 0/2
- Post/story is clear without hype: 0/2

Total: 0/10

## Rejection risks

What would make this too vague, too broad, or too dependent on private data?
""")

    write(target / "README.md", f"""# {title}

Tiny daily AI automation scaffold.

## Problem

Describe the boring workflow pain in one sentence.

## What it does

Describe the exact input -> output transformation.

## Quick start

```bash
cd {target.relative_to(ROOT)}
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
make smoke
```

Or use the local web form:

```bash
make web
```

## Input

See `data/sample_input.txt`.

## Output

Smoke run writes `output/sample_output.md`.

## Local web form

`make web` opens a small local form for entering inputs and downloading outputs.
It is only a friendly wrapper around the same CLI command.

## Configuration

Copy `.env.example` to `.env` only if you add optional API-backed behaviour.
The default scaffold runs locally without secrets.

## Limitations

- This is a tiny daily automation, not a production platform.
- Replace scaffold logic with the real workflow before publishing.
- Do not use private or sensitive data in samples.

## Verification

```bash
python3 ../../scripts/verify_daily_automation.py .
```
""")

    write(target / ".env.example", "# Optional config only. Keep the sample runnable without secrets.\n# OPENAI_API_KEY=\n")
    write(target / "data/sample_input.txt", "Messy note: Follow up with Sam tomorrow about the proposal. Send invoice draft by Friday. Check the contract wording.\n")
    write(target / "output/.gitkeep", "")
    write(target / "web_config.json", f'''{{
  "title": "{title}",
  "description": "Paste or edit sample input, run the automation locally, then download the generated output.",
  "fields": [
    {{
      "name": "input_text",
      "label": "Input text",
      "type": "textarea",
      "rows": 12,
      "default_file": "data/sample_input.txt",
      "save_to": "data/web_input.txt",
      "help": "This local form writes to data/web_input.txt and runs the same CLI command as the smoke test."
    }}
  ],
  "run": {{
    "button_label": "Run automation",
    "command": ["python3", "scripts/run.py", "--input", "data/web_input.txt", "--output", "output/sample_output.md"],
    "timeout_seconds": 120
  }},
  "outputs": [
    {{
      "label": "Markdown output",
      "path": "output/sample_output.md"
    }}
  ]
}}
''')
    write(target / "scripts/run.py", '#!/usr/bin/env python3\n"""Sample local automation entrypoint. Replace with the real daily tool."""\nfrom __future__ import annotations\n\nimport argparse\nfrom pathlib import Path\n\n\ndef convert(text: str) -> str:\n    # Deterministic placeholder: turns messy notes into simple action bullets.\n    parts = [p.strip().strip(".") for p in text.replace("\\n", " ").split(".") if p.strip()]\n    lines = ["# Action Draft", ""]\n    for part in parts:\n        lines.append(f"- {part}")\n    lines.append("")\n    return "\\n".join(lines)\n\n\ndef main() -> int:\n    parser = argparse.ArgumentParser()\n    parser.add_argument("--input", default="data/sample_input.txt")\n    parser.add_argument("--output", default="output/sample_output.md")\n    args = parser.parse_args()\n\n    src = Path(args.input)\n    dst = Path(args.output)\n    if not src.exists():\n        raise SystemExit(f"Input file not found: {src}")\n    dst.parent.mkdir(parents=True, exist_ok=True)\n    dst.write_text(convert(src.read_text(encoding="utf-8")), encoding="utf-8")\n    print(f"Wrote {dst}")\n    return 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n')
    (target / "scripts/run.py").chmod(0o755)

    write(target / "tests/test_smoke.py", '''from pathlib import Path
import subprocess
import sys


def test_smoke_command_generates_output():
    root = Path(__file__).resolve().parents[1]
    out = root / "output" / "sample_output.md"
    if out.exists():
        out.unlink()
    result = subprocess.run(
        [sys.executable, "scripts/run.py", "--input", "data/sample_input.txt", "--output", "output/sample_output.md"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert out.exists()
    assert "# Action Draft" in out.read_text()
''')

    write(target / "pyproject.toml", f'''[project]
name = "{slug.replace('-', '_')}"
version = "0.1.0"
description = "Daily AI automation: {title}"
requires-python = ">=3.10"
dependencies = []

[project.optional-dependencies]
dev = ["pytest>=8"]

[tool.pytest.ini_options]
testpaths = ["tests"]
''')

    write(target / "Makefile", '''.PHONY: smoke web test clean

smoke:
	python3 scripts/run.py --input data/sample_input.txt --output output/sample_output.md

web:
	python3 ../../scripts/local_web_shell.py --app-root .

test:
	python3 -m pytest -q

clean:
	rm -f output/sample_output.md data/web_input.txt
''')

    write(target / "VERIFY.md", "# Verification\n\nNot run yet.\n")
    print(target.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
