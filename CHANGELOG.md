# Changelog

## 2026-10-24 — marketplace 2.0.0

### Added
- `pc-risk-counsel` plugin 1.0.0
  - `analyzing-loss-runs`: normalized claims schema, `summarize_loss_runs.py` (totals by year and line, loss ratio, maturity, large losses, open claims, top causes, eight data-quality flags), narrative guide.
  - `analyzing-total-cost-of-risk`: `tcor.py` (TCOR and per-$1,000 rate across years or scenarios) and `retention_analysis.py` (historical replay against per-occurrence retentions with optional aggregate).
- `broker-voice` plugin 1.1.0 with `churchill-hemingway-engine`.
- `personal-productivity` plugin 1.1.0.
- `scripts/validate_skills.py`, `scripts/test_skill_scripts.py`, `scripts/package_zips.py`, and a GitHub Actions workflow running all three.
- Synthetic test data and trigger-eval query sets in `evals/`.
- MIT license per plugin. `SECURITY.md`.

### Changed
- Marketplace renamed `anthropic-agent-skills` → `bloomstine-skills` and owner set to Will Bloomstine. The old name collided with Anthropic's official marketplace. Re-add with `/plugin marketplace add shaboooooozy1/skills`.
- `churchill-hemingway-engine` 1.1.0: third-person description with edit triggers, new edit mode (`references/edit-mode.md`), compliance guardrails, signature block aligned to house standard. BOR template rewritten to describe the letter accurately. Removed a banned phrase ("reached out") from the referral template.
- `claude-setup-architect` → `setup-architect` 1.1.0. Moved from repo root into `personal-productivity`. Reserved word removed from the name. Unclosed code fences repaired so the Project and Skill templates render.
- `excel-and-sql-helper` → `writing-formulas-and-sql` 1.1.0. Fixed the SQL example (non-standard `YEAR()` on an indexed column replaced with a half-open date range). Added Sheets, dialect, `LET`, and debugging guidance.
- `quick-charts` → `building-quick-charts` 1.1.0. Now renders PNG and SVG with `make_chart.py` instead of an artifact that could not be pasted into slides.
- `email-command-center`: fixed invalid YAML frontmatter (unquoted colon) that blocked upload. Narrowed its trigger and `m365-email-command-center`'s to avoid colliding with the voice engine.

### Merged or retired
- `simple-prototyper` + `claude-design-personal` → `prototyping-ui-concepts` 1.1.0. Dropped UI troubleshooting tips tied to one product version.
- `email-tone-editor` retired. Its jobs (tighten, tone check, subject lines) live in the voice engine's edit mode. Its "softer phrasing" advice contradicted the house voice, and its triggers competed with the engine.
