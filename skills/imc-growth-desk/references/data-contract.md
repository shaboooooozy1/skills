# Pipeline data contract

Supply UTF-8 CSV with exactly these 13 named columns. The order may differ. Include the header even for an empty pipeline. Dates are calendar dates, interpreted in the chosen business timezone before export.

| Column | Requirement / meaning |
|---|---|
| opportunity_id | Required, unique across all rows, including closed opportunities. |
| account | Required account name. Concentration matches case-insensitive exact names; normalize aliases explicitly before analysis. |
| stage | Required: prospect, discovery, qualified, proposal, negotiation, won, lost. Map source stages explicitly. |
| owner | Task owner; blank is reported as a quality gap. |
| annual_revenue | Optional annual agency revenue in the named currency. Nonnegative decimal, at most two decimal places and 1,000,000,000,000,000. No commas, currency symbols, negatives, or formulas. Blank means unknown. Zero means known zero. Never substitute premium, client revenue, total contract value, or an inferred commission. |
| currency | Three uppercase letters such as USD. Required when revenue is supplied. No currency conversion occurs. The script checks syntax, not the ISO currency registry; verify the code when mapping. |
| probability | Optional explicit value from 0 to 1, up to eight decimal places. 0.25 means 25%. Do not enter 25 or 25%. No stage-derived defaults. |
| next_action | Recorded action; blank is flagged. Do not present generated suggestions as source commitments. |
| due_date | Optional YYYY-MM-DD task date. Past/today flags refer to recorded tasks, not proof a reply is owed. |
| last_contact_date | Optional YYYY-MM-DD latest verified contact date. Must not be after as-of date. |
| renewal_date | Optional YYYY-MM-DD. A past date does not establish lapse, renewal, or loss. |
| source_url | Optional http(s) evidence link without embedded credentials. The script validates syntax, not accessibility or content. Never use private download tokens. |
| verified_at | Optional YYYY-MM-DD when the record was checked. Must not be after as-of date. Missing verification remains visible. |

## Calculation rules

- Open stages: prospect, discovery, qualified, proposal, negotiation. Won/lost are counted separately and excluded from open pipeline, task flags, and renewal buckets.
- Known revenue: sum only nonblank annual_revenue within each currency. If no amounts are known, report null/Unknown, not zero.
- Weighted scenario: sum revenue × explicit probability where both exist. Display included rows / all open rows in that currency, and known revenue covered / all known revenue. It is not a calibrated prediction.
- Account concentration: largest case-insensitive exact account-name total / all known open revenue, within one currency. A zero denominator yields no percentage. Unknown revenue can materially change the true concentration.
- Action queue: recorded overdue tasks, tasks due today, missing action, missing due date, contact at least 14 calendar days old, then missing contact date. A record may have multiple flags. Ties use due date, account, and ID. These operational priorities are defaults, not a statistical score.
- Renewal windows: past; 0–30, 31–60, 61–90, 91–120, and over 120 days. These cover open opportunities only, not a complete in-force book.
- Quality counts apply to open opportunities. Stage counts and total record count include closed rows.

## Import discipline

Preserve the original file. Make a mapping table from source columns to this contract. Remove duplicate source records only with a documented identity decision; never silently discard conflicting opportunities. All required columns must be present; unknown optional values are blank. Invalid values, duplicate IDs, malformed CSV, impossible dates, and future history dates fail the run before any report is written.

Normalize spreadsheet formula cells to verified values only when the intended result is known. Do not execute formulas or evaluate imported text. The tool does not export CSV values; if a future workflow exports user text to a spreadsheet, neutralize formula-injection characters appropriately.

## Demonstration

`assets/demo-pipeline.csv` contains five fictional records anchored to 2026-11-02. Expected: four open opportunities, one closed; USD 30,000 known annual agency revenue and USD 12,000 weighted scenario across two of the three USD records. One open record has no currency. These are test fixtures, not Will's book or production metrics.
