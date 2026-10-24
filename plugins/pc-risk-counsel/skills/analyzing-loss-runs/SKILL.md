---
name: analyzing-loss-runs
description: >-
  Normalizes commercial P&C loss runs from one or more carriers into a single claims table, totals paid,
  outstanding, and incurred by policy year and line, flags data problems and large losses, builds an
  Excel workbook, and drafts a producer-facing loss summary. Use when the user uploads or pastes loss
  runs, loss history, claims reports, or "currently valued" carrier reports (PDF, XLSX, CSV), or asks
  about loss trends, loss ratios, frequency vs. severity, large losses, or how a renewal's claims look.
  Output feeds TCOR, retention, renewal, and submission work. Not for benefits claims experience.
license: MIT
metadata:
  version: 1.0.0
  author: Will Bloomstine
---

# Analyzing Loss Runs

Turn messy carrier loss runs into one clean table, exact totals, and a short story the producer can defend in front of an underwriter or a CFO.

The math is done by script. Never total claims by hand.

## Workflow

Copy this checklist and tick it off:

```
- [ ] 1. Extract every claim into claims.csv (schema in references/schema.md)
- [ ] 2. Capture earned premium into premium.csv if the user has it (optional)
- [ ] 3. Run scripts/summarize_loss_runs.py
- [ ] 4. Read the data flags. Fix extraction errors, rerun. Report true source problems.
- [ ] 5. Draft the narrative (references/narrative-guide.md)
- [ ] 6. Deliver workbook + narrative with the review gate
```

### 1. Extract

Read `references/schema.md` before extracting. One row per claim, per valuation. Keep the carrier's claim number exactly as printed. Record each report's valuation date. If a carrier report shows only incurred, put it in `carrier_incurred` and leave paid and outstanding blank rather than guessing a split.

Record "no losses" years explicitly. A policy year with zero claims is evidence, not a gap. Add a row to `premium.csv` for it, or tell the user which years the loss runs cover.

### 2. Run the script

```bash
python scripts/summarize_loss_runs.py claims.csv \
  --premium premium.csv \
  --large-loss 100000 \
  --as-of 2026-10-24 \
  --out loss_summary
```

- `--large-loss`: individual claim threshold for the large-loss list. Default 50,000. Use the user's number if given.
- `--as-of`: the date used to judge stale valuations. Default today.
- Writes `loss_summary.xlsx` (sheets: Summary_by_Year, Summary_by_Year_Line, Summary_by_Line, Large_Losses, Open_Claims, Top_Causes, Data_Flags, Claims) and `loss_summary.json` with the same tables. Loss ratios appear wherever premium was supplied, and a premium-only year or line shows with zero losses.
- The Claims sheet carries schema columns only. Any extra columns in claims.csv (claimant names, notes) are dropped from every output.

### 3. Read the flags

The script flags: duplicate claim numbers, blank claim numbers, incomplete paid/outstanding splits, incurred that does not equal paid plus outstanding less recoveries, negative amounts, open claims with zero reserve, closed claims with reserves, loss dates outside the policy year, and valuations more than 90 days old. Fix anything caused by your own extraction and rerun. Report the rest to the user as questions for the carrier.

### 4. Narrative

Follow `references/narrative-guide.md`. Lead with the one finding that matters most. Use only numbers from the script output.

## Hard rules

- Never invent a claim, amount, premium, or valuation date. If a number is unreadable, mark the row and flag it.
- Never state reserve adequacy, project ultimate losses, or apply loss development factors unless the user supplies the factors. Recent years are immature. Say so.
- Never state whether a claim is covered.
- Strip claimant names and medical details from anything leaving the analysis. Use claim numbers.
- End every deliverable with: "Draft for licensed-professional review. Based on carrier loss runs as valued on the dates shown. Not an actuarial analysis or coverage determination."

## Hand-offs

- Retention or deductible questions: pass `claims.csv` to `analyzing-total-cost-of-risk` (its retention script reads this file directly).
- Client email about the results: hand the narrative to `churchill-hemingway-engine`.
- Chart of the trend: `building-quick-charts` with Summary_by_Year.
