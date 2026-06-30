# Messy notes to action draft

Turn a rough dump of notes into a clean action draft.

## Problem

People capture useful notes quickly, then waste time later converting the mess into actual follow-up tasks.

## What it does

Reads `data/sample_input.txt`, extracts sentence-like note fragments, and writes a simple Markdown action draft to `output/sample_output.md`.

## Quick start

```bash
cd automations/day-001-messy-notes-to-action-draft
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
make smoke
```

Or use the local web form:

```bash
make web
```

No API key is needed for the sample version.

## Input

See `data/sample_input.txt`.

## Output

Smoke run writes `output/sample_output.md`.

## Local web form

`make web` opens a small local form for pasting notes and downloading the
generated action draft. It is only a friendly wrapper around the same CLI
command.

## Configuration

Copy `.env.example` to `.env` only if you add optional API-backed behaviour later.
The default sample runs locally without secrets.

## Limitations

- This is a tiny daily automation, not a production task manager.
- It does not infer dates or owners yet.
- It uses sample data only; do not publish private notes.

## Verification

```bash
python3 ../../scripts/verify_daily_automation.py .
```
