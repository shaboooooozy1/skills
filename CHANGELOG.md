# Changelog

## 2026-10-24 — marketplace 2.0.0

### Fixed in review (PR #17)
- Loss runs: blank claim numbers are no longer merged as one claim; a partial paid/outstanding split falls back to carrier incurred instead of counting unknowns as zero; duplicate premium rows for a year and line are summed; premium-only years and lines appear with zero losses; maturity no longer assumes a January 1 start; JSON now includes year-by-line totals and open claims; the Claims sheet exports schema columns only, so claimant names and notes never leave.
- Retention replay: same blank-claim and partial-split rules as the loss-run script.
- Loss runs: year and all-years loss ratios only use years whose premium covers every line with claims; ALL premium is defined as lines not listed separately; written premium is labeled as written; duplicate rows with no readable valuation date no longer crash the script.
- Retention replay: policy years with no claims in the selected lines count as zero retained (new `--years` flag); an undated row never wins over a dated valuation.
- Charts: negative values are no longer clipped at zero; blank cells show as gaps, not zeros; stacked charts put negative parts below zero; duplicate column names are rejected.
- Loss runs: year maturity uses the least mature policy in the year; reserve flags check any known reserve; zero-premium years are not counted as rated; premium rows with an unreadable year are flagged and excluded from totals.
- Retention replay: options with the same retention but different aggregates stay separate; claims with no known amount and undated duplicates are named in the notes.
- TCOR: missing premiums stop the run; any other component left out or blank is listed in `open_items`, including a blank collateral amount or rate; the exposure divisor must be positive; counts such as vehicles or headcount are no longer formatted as dollars.
- Input checks: the retention replay stops on any negative amount, notes split-vs-carrier mismatches, and rejects ambiguous comma lists such as `25,500` (use `25500` or semicolons); `--large-loss` must be finite and non-negative; each skill ZIP now carries its plugin's MIT LICENSE.
- Input checks: "Infinity" and similar text count as unreadable amounts; years whose summed premium is zero or negative get no ratio; the retention replay stops on unreadable amounts or negative recoveries and rejects $ or thousands separators in options; charts reject non-finite values.
- Input checks: chart `--benchmark` must be finite; `--stale-days` cannot be negative; semicolon retention lists reject misplaced separators such as `25,00`; a TCOR period with every premium blank stops; the replay names every claim with no readable valuation date; the validator rejects symlinks in upstream skills too.
- Input checks: amounts with malformed separators such as `12,34` or `1(2)` are flagged as unreadable instead of being read as 1234 or 12; a fractional policy year is treated as unreadable instead of crashing; the retention replay only stops on bad amounts in rows it will actually use (latest valuation, selected lines and years); without `--immature-years` the replay withholds the mature-years average.
- Input checks: unreadable amounts (text where a number belongs) are flagged as unreadable_amount; premium_basis must be earned, written, or blank; retention options must be finite; README separates fork-added skills from upstream ones.
- Input checks: negative collateral amounts and non-finite TCOR numbers are rejected; negative recoveries are flagged; a TCOR period with no source is an open item; the TCOR JSON review gate matches SKILL.md; maturity counts completed months only; zero-premium lines stay in the line summary; retention piercing claims name their option.
- Input checks: negative collateral rates are rejected; premium rows with no line code are flagged and excluded; a year's premium is unknown when any of its rows is unknown; blank premium_basis counts as earned in mixed files; the retention replay trims claim keys like the loss-run script.
- Input checks: negative retentions, aggregates, and exposures are rejected; tied latest valuations and future valuation dates are flagged; near-equal retention options stay separate; the validator reports malformed frontmatter instead of crashing.
- Loss runs: paid, outstanding, and premium totals are reported as unknown (not a partial sum) when any part is unknown; written and mixed loss-ratio columns are formatted as percentages.
- `m365-email-command-center` description narrowed to inbox-level work.
- Security: workbook writers in all three risk scripts force any text starting with `=` to a plain string, so carrier-supplied text can never open as a live Excel formula. The text itself is kept exactly as printed.
- Security: the `skill-zips` install artifact is uploaded only from pushes to `main`, never from pull request runs.
- Security: skills may not contain symlinks (validator and packager both fail), the packager archives only regular files inside the skill folder, and CI checkout no longer persists the job token. Published ZIPs are built in a separate job that installs nothing from PyPI and runs the standard-library packager in isolated mode; the workflow is read-only.
- README: upstream install section now adds this repository's marketplace.

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
