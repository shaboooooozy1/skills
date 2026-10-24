Synthetic test data. Fictional carriers and claims. No client data.

Planted issues the script must catch:
- A-1210: two valuations (2025-12-31 and 2026-03-31) -> superseded_valuation, keep 2026-03-31
- A-1302: exact duplicate row -> duplicate_claim
- A-1102: split totals 9,800 but carrier incurred 10,500 -> incurred_mismatch
- W23-002: open with zero reserve -> open_zero_reserve
- W23-003: closed with 1,500 outstanding -> closed_with_reserve
- A-1255: loss 2026-01-14 outside 2024-07-01 term -> loss_date_outside_term
- All Sample Casualty rows valued 2026-03-31 -> stale_valuation when --as-of 2026-10-24
- A-1301: carrier incurred only (no split) -> incurred_source=carrier, no flag
- 2025 policy year: immature
Expected: 21 claims after dedupe, 9 open.
