# Prompt Templates

## Daily ship prompt

```text
Read AGENTS.md and codex/daily-automation/LOAD-FIRST.md.

Ship one daily AI automation.

Idea source: codex/daily-automation/CURATED-IDEA-QUEUE.md
Constraints:
- pick only a `ready` curated idea, or an explicit idea from Anas
- stop if no curated idea is ready
- do not invent, research, or score fresh ideas during the build run
- simple, boring, useful
- local-first
- runnable in under 2 minutes
- include a basic local web form with `make web` when it helps parse inputs/download outputs
- include sample input/output
- include README, IDEA.md, VERIFY.md
- run verification
- draft X + LinkedIn posts
- build release packet
- do not push or post live unless approval gate passes
- if public git push is approved, export a clean public repo and run the public release check before pushing
```

## Curation prompt for Anas

```text
Use the daily automation idea filter. Give me 10 tiny automation ideas scored out of 10. Reject anything vague or platform-shaped. For the top 3, include persona, input, output, and demo path.

I will choose which one becomes `ready` in codex/daily-automation/CURATED-IDEA-QUEUE.md.
```

## Repair prompt

```text
A daily automation failed verification. Inspect VERIFY.md and the smoke command. Fix the smallest thing needed to pass. Do not broaden scope.
```

## Posting prompt

```text
Draft founder-led X and LinkedIn posts for this automation. Keep it concrete and non-hype. Use problem -> build -> proof -> link placeholder.
```

## Public push prompt

```text
Open-source the daily automation lane. Do not push the whole operator checkout.
Configure git as Anas Abdi <abdianas919@gmail.com>, export the clean public repo,
run scripts/public_release_check.py on the export, then push the exported repo publicly.
Report the repo URL, commit hash, and checks.
```
