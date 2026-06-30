# Ship Checklist

A daily automation is shippable when all of this is true:

## Project

- [ ] Folder is `automations/day-XXX-slug/`
- [ ] `README.md` explains problem, setup, run, output, limits
- [ ] `IDEA.md` captures user, pain, input, output, score
- [ ] `web_config.json` exists when a local form helps input/output
- [ ] `.env.example` exists if config is needed
- [ ] sample input exists under `data/`
- [ ] sample output is generated under `output/`

## Code

- [ ] one obvious entrypoint exists
- [ ] local web form wraps the same CLI command when included
- [ ] `make smoke` or equivalent works
- [ ] missing config fails with a clear message
- [ ] no secrets or private data
- [ ] dependencies are minimal

## Proof

- [ ] `python3 scripts/verify_daily_automation.py automations/day-XXX-slug` passes
- [ ] `VERIFY.md` includes commands run and result
- [ ] limitations are honest

## Distribution packet

- [ ] X draft exists
- [ ] LinkedIn draft exists
- [ ] release packet exists
- [ ] approval state is explicit
- [ ] no live push/post without approval manifest

## Public repo

- [ ] git identity is `Anas Abdi <abdianas919@gmail.com>` before commit/push
- [ ] public release uses a clean export folder, not the private operator checkout
- [ ] `python3 scripts/public_release_check.py <export-folder>` passes
- [ ] public repo contains only daily automation lane files
