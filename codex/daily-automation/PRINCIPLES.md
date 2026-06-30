# Daily Automation Principles

## Taste

- Boring beats clever.
- Useful beats impressive.
- One job beats a platform.
- Local-first beats SaaS dependency.
- Sample data beats screenshots-only proof.
- Honest limitations beat fake polish.

## Public identity

This lane supports founder-led distribution:

> Building TeachClaw as the serious product, and shipping one tiny practical AI automation every day.

TeachClaw stays the flagship. Daily automations are public proof of speed, taste, and applied AI deployment instincts.

## Scope rules

Good projects:
- turn messy input into useful output
- save 10-30 minutes of admin work
- work with files, folders, public pages, email exports, notes, PDFs, CSVs, transcripts, or screenshots
- are understandable from the title alone

Bad projects:
- generic chatbots
- "AI agent for X" with no concrete workflow
- tools needing private accounts to see value
- multi-day platforms disguised as daily automations
- anything that depends on private TeachClaw internals

## Engineering standard

- Prefer Python or TypeScript, whichever makes the automation simplest.
- Keep dependencies small.
- Provide `.env.example` if API keys are optional/needed.
- Include `make smoke` or an equivalent one-command smoke path.
- Include deterministic sample data.
- Fail clearly when config is missing.
