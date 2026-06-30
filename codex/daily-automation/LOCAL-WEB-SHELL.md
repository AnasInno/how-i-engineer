# Local Web Shell

Each daily automation should stay automation-first:

- CLI remains the source of truth.
- The local web form is only a friendlier way to enter inputs and download outputs.
- No auth, database, hosted app, React, or product-specific frontend unless Anas asks.

## Default Shape

```text
automations/day-XXX-slug/
  scripts/run.py
  web_config.json
  data/sample_input.txt
  output/.gitkeep
  Makefile
```

The shared runner is:

```bash
python3 ../../scripts/local_web_shell.py --app-root .
```

The automation's `Makefile` should expose:

```bash
make smoke
make web
```

## What The Web Form Should Do

- show only the fields the operator needs
- accept pasted text or CSV-shaped text for the first version
- run the same local command as the CLI
- display the command result
- provide download links for generated CSV, Markdown, or HTML outputs

## What It Should Not Do

- become a SaaS app
- require login or live accounts
- hide the CLI
- write to CRMs, inboxes, or public sites without approval
- add a custom frontend stack per automation

## Customization Pattern

Edit `web_config.json`:

```json
{
  "title": "Example Automation",
  "description": "Paste input, run locally, download outputs.",
  "fields": [
    {
      "name": "input_text",
      "label": "Input text",
      "type": "textarea",
      "default_file": "data/sample_input.txt",
      "save_to": "data/web_input.txt"
    }
  ],
  "run": {
    "button_label": "Run automation",
    "command": ["python3", "scripts/run.py", "--input", "data/web_input.txt", "--output", "output/sample_output.md"]
  },
  "outputs": [
    {
      "label": "Markdown output",
      "path": "output/sample_output.md"
    }
  ]
}
```

For CSV-heavy automations, start with pasted CSV textareas and write them to
files under `data/`. Add actual file upload only after the workflow proves useful.
