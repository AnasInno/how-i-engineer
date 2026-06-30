# Daily automation template

Do not copy this manually unless needed. Prefer:

```bash
python3 scripts/new_daily_automation.py "Idea name"
```

Or run the full local packet flow:

```bash
python3 scripts/run_daily_automation_pipeline.py --idea "Idea name"
```

Each generated automation should include:

- README
- IDEA.md
- Makefile
- `.env.example`
- sample input under `data/`
- generated sample output under `output/`
- smoke/test path
- VERIFY.md
- X + LinkedIn drafts
- release packet
