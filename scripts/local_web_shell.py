#!/usr/bin/env python3
"""Tiny reusable local web shell for daily automations."""
from __future__ import annotations

import argparse
import html
import json
import mimetypes
import subprocess
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, urlparse


def load_config(app_root: Path) -> dict:
    config_path = app_root / "web_config.json"
    if not config_path.exists():
        raise SystemExit(f"Missing web_config.json in {app_root}")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(config.get("fields"), list):
        raise SystemExit("web_config.json must include a fields list")
    if not isinstance(config.get("run", {}).get("command"), list):
        raise SystemExit("web_config.json must include run.command as a list")
    return config


def validate_config(app_root: Path, config: dict) -> None:
    for field in config["fields"]:
        if "name" not in field:
            raise SystemExit("Every field in web_config.json must include a name")
        for key in ("save_to", "default_file"):
            if field.get(key):
                safe_path(app_root, str(field[key]))
    for output in config.get("outputs", []):
        if output.get("path"):
            safe_path(app_root, str(output["path"]))


def safe_path(app_root: Path, rel_path: str) -> Path:
    path = (app_root / rel_path).resolve()
    if not path.is_relative_to(app_root.resolve()):
        raise ValueError(f"Path escapes app root: {rel_path}")
    return path


def read_default(app_root: Path, field: dict) -> str:
    for key in ("save_to", "default_file"):
        rel = field.get(key)
        if rel:
            path = safe_path(app_root, rel)
            if path.exists():
                return path.read_text(encoding="utf-8")
    return str(field.get("default", ""))


def render_field(app_root: Path, field: dict) -> str:
    name = str(field["name"])
    label = html.escape(str(field.get("label", name)))
    help_text = html.escape(str(field.get("help", "")))
    value = html.escape(read_default(app_root, field))
    field_type = str(field.get("type", "text"))

    if field_type == "textarea":
        rows = int(field.get("rows", 10))
        control = f'<textarea name="{html.escape(name)}" rows="{rows}">{value}</textarea>'
    elif field_type == "select":
        options = []
        selected = read_default(app_root, field)
        for option in field.get("options", []):
            option_value = str(option)
            attr = " selected" if option_value == selected else ""
            options.append(f'<option value="{html.escape(option_value)}"{attr}>{html.escape(option_value)}</option>')
        control = f'<select name="{html.escape(name)}">{"".join(options)}</select>'
    else:
        input_type = "number" if field_type == "number" else "text"
        control = f'<input type="{input_type}" name="{html.escape(name)}" value="{value}">'

    help_html = f'<p class="help">{help_text}</p>' if help_text else ""
    return f'<label><span>{label}</span>{control}{help_html}</label>'


def render_outputs(app_root: Path, config: dict) -> str:
    rows = []
    for output in config.get("outputs", []):
        rel_path = str(output.get("path", ""))
        if not rel_path:
            continue
        path = safe_path(app_root, rel_path)
        label = html.escape(str(output.get("label", rel_path)))
        exists = path.exists()
        status = "ready" if exists else "not generated yet"
        link = ""
        if exists:
            href = "/download?path=" + quote(rel_path)
            link = f'<a class="button secondary" href="{href}">Download</a>'
        rows.append(
            "<tr>"
            f"<td>{label}</td>"
            f"<td><code>{html.escape(rel_path)}</code></td>"
            f"<td>{status}</td>"
            f"<td>{link}</td>"
            "</tr>"
        )
    if not rows:
        return "<p>No outputs configured.</p>"
    return (
        "<table><thead><tr><th>Output</th><th>Path</th><th>Status</th><th></th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
    )


def render_page(app_root: Path, config: dict, state: dict) -> bytes:
    title = html.escape(str(config.get("title", app_root.name)))
    description = html.escape(str(config.get("description", "")))
    button_label = html.escape(str(config.get("run", {}).get("button_label", "Run automation")))
    fields = "\n".join(render_field(app_root, field) for field in config["fields"])
    outputs = render_outputs(app_root, config)

    run_html = ""
    if state.get("last_command"):
        code = int(state.get("last_returncode", 0))
        status = "passed" if code == 0 else f"failed with exit code {code}"
        log = html.escape(str(state.get("last_log", ""))[-6000:])
        command = html.escape(" ".join(state["last_command"]))
        run_html = (
            '<section class="panel">'
            "<h2>Last Run</h2>"
            f"<p>Status: <strong>{status}</strong></p>"
            f"<p><code>{command}</code></p>"
            f"<pre>{log or 'No output.'}</pre>"
            "</section>"
        )

    body = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f7f7f5;
      --text: #1f2328;
      --muted: #606873;
      --line: #d8dadd;
      --panel: #ffffff;
      --accent: #146c5f;
      --accent-dark: #0d5147;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font: 15px/1.45 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    main {{
      width: min(1080px, calc(100% - 32px));
      margin: 24px auto 48px;
      display: grid;
      gap: 18px;
    }}
    header {{
      border-bottom: 1px solid var(--line);
      padding: 0 0 16px;
    }}
    h1 {{ margin: 0 0 6px; font-size: 28px; font-weight: 650; letter-spacing: 0; }}
    h2 {{ margin: 0 0 12px; font-size: 18px; font-weight: 650; letter-spacing: 0; }}
    p {{ margin: 0 0 10px; }}
    .muted, .help {{ color: var(--muted); }}
    .grid {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(320px, 0.8fr);
      gap: 18px;
      align-items: start;
    }}
    .panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
    }}
    form {{ display: grid; gap: 14px; }}
    label {{ display: grid; gap: 7px; font-weight: 600; }}
    label span {{ display: block; }}
    input, textarea, select {{
      width: 100%;
      border: 1px solid #bfc4ca;
      border-radius: 6px;
      background: #fff;
      color: var(--text);
      padding: 10px 11px;
      font: inherit;
    }}
    textarea {{
      min-height: 180px;
      resize: vertical;
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 13px;
    }}
    .help {{ margin: -2px 0 0; font-size: 13px; font-weight: 400; }}
    .button, button {{
      appearance: none;
      border: 0;
      border-radius: 6px;
      background: var(--accent);
      color: #fff;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 40px;
      padding: 0 14px;
      font: inherit;
      font-weight: 650;
      text-decoration: none;
    }}
    .button:hover, button:hover {{ background: var(--accent-dark); }}
    .secondary {{
      background: #eef2f1;
      color: var(--accent-dark);
      border: 1px solid #c8d8d4;
    }}
    .secondary:hover {{ background: #dfe9e6; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
    }}
    th, td {{
      border-bottom: 1px solid var(--line);
      padding: 10px 8px;
      text-align: left;
      vertical-align: middle;
    }}
    th {{ color: var(--muted); font-weight: 650; }}
    code, pre {{
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 13px;
    }}
    pre {{
      background: #111827;
      color: #f9fafb;
      overflow: auto;
      padding: 12px;
      border-radius: 6px;
      max-height: 340px;
    }}
    @media (max-width: 760px) {{
      main {{ width: min(100% - 20px, 1080px); margin-top: 14px; }}
      .grid {{ grid-template-columns: 1fr; }}
      h1 {{ font-size: 23px; }}
      .panel {{ padding: 14px; }}
      table {{ display: block; overflow-x: auto; }}
    }}
  </style>
</head>
<body>
  <main>
    <header>
      <h1>{title}</h1>
      <p class="muted">{description}</p>
    </header>
    <div class="grid">
      <section class="panel">
        <h2>Inputs</h2>
        <form method="post" action="/run">
          {fields}
          <button type="submit">{button_label}</button>
        </form>
      </section>
      <section class="panel">
        <h2>Outputs</h2>
        {outputs}
      </section>
    </div>
    {run_html}
  </main>
</body>
</html>"""
    return body.encode("utf-8")


def write_form_fields(app_root: Path, config: dict, values: dict[str, list[str]]) -> None:
    for field in config["fields"]:
        save_to = field.get("save_to")
        if not save_to:
            continue
        name = str(field["name"])
        value = values.get(name, [""])[0]
        path = safe_path(app_root, str(save_to))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")


def run_command(app_root: Path, config: dict, state: dict) -> None:
    command = [str(part) for part in config["run"]["command"]]
    timeout = int(config.get("run", {}).get("timeout_seconds", 120))
    proc = subprocess.run(command, cwd=app_root, text=True, capture_output=True, check=False, timeout=timeout)
    state["last_command"] = command
    state["last_returncode"] = proc.returncode
    state["last_log"] = (proc.stdout + proc.stderr).strip()


def make_handler(app_root: Path, config: dict, state: dict):
    allowed_downloads = {
        safe_path(app_root, str(output["path"]))
        for output in config.get("outputs", [])
        if output.get("path")
    }

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            if parsed.path == "/download":
                self._serve_download(parsed.query)
                return
            self._serve_page()

        def do_POST(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            if parsed.path != "/run":
                self.send_error(404)
                return
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length).decode("utf-8")
            values = parse_qs(raw, keep_blank_values=True)
            try:
                write_form_fields(app_root, config, values)
                run_command(app_root, config, state)
            except Exception as exc:
                state["last_command"] = config.get("run", {}).get("command", [])
                state["last_returncode"] = 1
                state["last_log"] = str(exc)
            self._serve_page()

        def _serve_page(self) -> None:
            body = render_page(app_root, config, state)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _serve_download(self, query: str) -> None:
            params = parse_qs(query)
            rel_path = params.get("path", [""])[0]
            try:
                path = safe_path(app_root, rel_path)
            except ValueError as exc:
                self.send_error(400, str(exc))
                return
            if path not in allowed_downloads:
                self.send_error(403, "Path is not configured as an output")
                return
            if not path.exists() or not path.is_file():
                self.send_error(404, "Output not found")
                return
            data = path.read_bytes()
            content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Disposition", f'attachment; filename="{path.name}"')
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, format: str, *args) -> None:  # noqa: A002
            return

    return Handler


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app-root", default=".", help="Automation folder containing web_config.json")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-open", action="store_true", help="Do not open the browser automatically")
    parser.add_argument("--check", action="store_true", help="Validate web_config.json and exit")
    args = parser.parse_args()

    app_root = Path(args.app_root).resolve()
    config = load_config(app_root)
    validate_config(app_root, config)
    if args.check:
        print(f"OK: {app_root / 'web_config.json'}")
        return 0

    state: dict = {}
    server = ThreadingHTTPServer((args.host, args.port), make_handler(app_root, config, state))
    url = f"http://{args.host}:{server.server_port}"
    print(f"Serving {app_root.name} at {url}")
    if not args.no_open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
