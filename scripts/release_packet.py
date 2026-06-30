#!/usr/bin/env python3
"""Create a release-readiness packet for a daily automation."""
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def approval_state(slug: str) -> str:
    path = ROOT / "approvals" / f"{slug}.release.json"
    if not path.exists():
        return "missing"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return f"invalid: {exc}"
    if data.get("approved") is True:
        return "approved for: " + ", ".join(data.get("allow") or [])
    return "present but not approved"


def git_state(slug: str, automation_rel: str) -> str:
    paths = [
        automation_rel,
        f"drafts/daily-automation/{slug}",
        f"runs/daily-automation/{slug}",
        "codex/daily-automation",
        ".agents/skills/daily-ai-automation-posting",
        ".agents/skills/daily-ai-automation-research",
        ".agents/skills/daily-ai-automation-ship",
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
    proc = subprocess.run(
        ["git", "status", "--short", "--", *paths],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    self_prefix = f"runs/daily-automation/{slug}/release-packet"
    lines = [line for line in proc.stdout.splitlines() if self_prefix not in line]
    return "\n".join(lines).strip() or "clean"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path")
    args = parser.parse_args()

    folder = Path(args.path).resolve()
    slug = folder.name
    verify = folder / "VERIFY.md"
    drafts = ROOT / "drafts" / "daily-automation" / slug
    packet_dir = ROOT / "runs" / "daily-automation" / slug
    packet_dir.mkdir(parents=True, exist_ok=True)

    verify_text = verify.read_text(encoding="utf-8") if verify.exists() else ""
    verify_pass = "Status: **PASS**" in verify_text
    x = drafts / "x.md"
    linkedin = drafts / "linkedin.md"

    automation_rel = str(folder.relative_to(ROOT))
    packet = {
        "slug": slug,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "automation_path": automation_rel,
        "verify_pass": verify_pass,
        "x_draft": str(x.relative_to(ROOT)) if x.exists() else None,
        "linkedin_draft": str(linkedin.relative_to(ROOT)) if linkedin.exists() else None,
        "approval_state": approval_state(slug),
        "external_actions_blocked_without_approval": True,
        "git_status_scope": "daily automation lane only",
    }
    (packet_dir / "release-packet.json").write_text(json.dumps(packet, indent=2) + "\n", encoding="utf-8")

    md = [
        f"# Release Packet — {slug}",
        "",
        f"Created: {packet['created_at']}",
        "",
        "## Readiness",
        "",
        f"- Verification pass: {'yes' if verify_pass else 'no'}",
        f"- X draft: `{packet['x_draft']}`" if packet["x_draft"] else "- X draft: missing",
        f"- LinkedIn draft: `{packet['linkedin_draft']}`" if packet["linkedin_draft"] else "- LinkedIn draft: missing",
        f"- Approval state: {packet['approval_state']}",
        "",
        "## External action rule",
        "",
        "Push/post actions are blocked unless `scripts/check_approval.py <slug> <action>` passes.",
        "",
        "## Git status at packet time",
        "",
        "Scope: daily automation lane only.",
        "",
        "```text",
        git_state(slug, automation_rel),
        "```",
        "",
    ]
    (packet_dir / "release-packet.md").write_text("\n".join(md), encoding="utf-8")
    print(packet_dir.relative_to(ROOT))
    return 0 if verify_pass and x.exists() and linkedin.exists() else 1


if __name__ == "__main__":
    raise SystemExit(main())
