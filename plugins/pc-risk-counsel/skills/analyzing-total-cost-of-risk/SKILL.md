---
name: analyzing-total-cost-of-risk
description: >-
  Builds a Total Cost of Risk (TCOR) worksheet from premiums, retained losses, administration, risk
  control, and collateral costs, expresses it per $1,000 of revenue or payroll, compares years or
  program structures, and replays loss history against deductible or SIR options. Use when the user
  mentions TCOR, cost of risk, total cost of insurance, "what are we really spending," higher
  deductibles, retentions, self-insured retention, large deductible vs. guaranteed cost, or moving
  along the risk financing continuum, even if they only ask "should we take more risk." Not for
  benefits funding or stop-loss.
license: MIT
metadata:
  requires: Python 3.10+ with pandas and openpyxl (pip install pandas openpyxl)
  version: 1.0.0
  author: Will Bloomstine
---

# Analyzing Total Cost of Risk

Premium is the visible cost. TCOR is the real one. This skill shows a CFO the whole number and how it moves under different program structures.

All arithmetic runs in scripts. Never add components or replay claims by hand.

## TCOR components

| Component | Includes |
|---|---|
| Premiums, taxes and fees | All lines, surplus lines taxes, policy fees, broker fees billed with premium |
| Retained losses | Deductible and SIR losses paid by the client, uninsured losses, losses below a self-insured layer |
| Administration | Broker fees not in premium, TPA fees, internal risk and claims staff time, claims-handling charges |
| Risk control | Safety programs, consultants, training, telematics, loss-control equipment |
| Collateral cost | Letter-of-credit fees and cost of capital on collateral posted for retentions |

Full field list and an example: `references/tcor-inputs.md`.

## Workflow

```
- [ ] 1. Pick the frame: year-over-year actuals, or current program vs. alternative structures
- [ ] 2. Collect every input and its source (see "Where numbers come from")
- [ ] 3. If comparing retentions, run scripts/retention_analysis.py on the loss-run claims.csv
- [ ] 4. Build inputs.json and run scripts/tcor.py
- [ ] 5. Write the findings (structure below)
- [ ] 6. Deliver workbook + findings with the review gate
```

### Step 3: retention replay

```bash
python scripts/retention_analysis.py claims.csv --retentions 25000,50000,100000 \
  --aggregate 250000 --lines AL --immature-years 2024,2025 --out retention
```

Write options as plain numbers separated by commas (`25000,50000`), or use semicolons if you keep thousands separators (`25,000;50,000`). The script stops on unreadable or negative amounts and names claims whose split disagrees with the carrier total. Add `--years 2021-2025` with the years the loss runs cover. Years with no claims in the selected lines count as zero retained. Without the flag, the range is every year in claims.csv before the line filter. `claims.csv` is the normalized file from `analyzing-loss-runs`. If it does not exist yet, run that skill first. The replay shows, for each retention, what the client would have kept each year and the worst year. Always pass `--immature-years` (or `none`). Without it the script withholds the mature-years average, because recent years are still developing. Use the **mature-years average** as the starting estimate of retained losses for a scenario, and show the worst year beside it. Name the basis: incurred (loss plus expense) or loss only, matching how the quoted deductible applies.

### Step 4: TCOR

```bash
python scripts/tcor.py inputs.json --out tcor_summary
```

Writes `tcor_summary.xlsx` (TCOR and Detail sheets) and `tcor_summary.json`. A period without premiums stops the run. Any other component left out or blank is counted as 0 and listed in that period's `open_items`; carry those into the findings' open items.

## Where numbers come from

| Input | Source | If missing |
|---|---|---|
| Current premiums | Policies, invoices, or the client's books | Ask |
| Alternative-program premiums | Carrier quotes or indications only | Leave the scenario out. Never estimate a deductible credit. |
| Retained losses, actual | Client's deductible invoices or loss runs | Ask, or run the replay |
| Retained losses, scenario | `retention_analysis.py` mature-years average | Label "estimate" |
| Admin and risk control | Client | Use 0 and list it as an open item |
| Collateral amount and rate | Carrier quote and client's bank or CFO | Use 0 and list as open item |

Every figure in `inputs.json` gets a `source`. If a number came from the replay, the period's `kind` is `scenario`.

## Findings structure

1. **The number.** TCOR, and TCOR per $1,000 of the exposure base.
2. **What drives it.** Component shares. Premium is rarely the only lever.
3. **The comparison.** Each scenario's TCOR against current, with the worst-year retained loss beside it. A cheaper expected TCOR with a worst year the balance sheet cannot absorb is not a recommendation.
4. **Questions to test.** Two to four, framed for the CFO. Examples: "Can the balance sheet absorb a $[worst year] retained year?" "Will the carrier require collateral, and at what cost?" "Is claims handling for the retained layer staffed?"
5. **Open items.** Every input that was 0 or estimated.
6. **Review gate**: "Draft for licensed-professional review. Figures are as supplied; scenario retained losses are historical replays, not actuarial projections. Alternative premiums come from carrier quotes."

## Risk financing continuum

Guaranteed cost → loss-sensitive (large deductible, retro) → SIR → captive → full self-retention. Each step right trades premium for retained volatility, admin, and collateral. TCOR is how to show that trade in one number per step. Present the step the data supports, and the condition for taking the next one (loss stability, balance-sheet capacity, claims infrastructure). Captive feasibility needs an actuarial study. Say so instead of modeling it.

## Hard rules

- Never invent premiums, deductible credits, collateral requirements, LOC rates, or industry TCOR benchmarks.
- Never present a replay average as a forecast. Always show the worst year.
- Never recommend a structure as suitable. Recommend what to test, and who decides.
- Tax, accounting, and legal treatment of retentions or captives: recommend the client's CPA and attorney.
