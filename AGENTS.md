## Project Specific Rules

- Perform test-driven-development. When creating new functionality, always start by creating end to end test cases for the function. The function is only 
deemed completed when it passes the test case.
- Keep file modularised. Each `.py` file should serve to do 1 specific thing.
- After changes are implemented, add them to the CHANGELOG.md

## Agent skills

### Issue tracker

Issues are tracked as local markdown files under `.scratch/<feature>/`. See `docs/agents/issue-tracker.md`.

### Triage labels

The five canonical triage labels: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context layout: one shared `CONTEXT.md` at the repo root. See `docs/agents/domain.md`.