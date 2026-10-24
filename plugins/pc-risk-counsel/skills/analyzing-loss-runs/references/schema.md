# Normalized Loss Run Schema

## claims.csv

One row per claim. Header row required. Column order does not matter. Unknown columns are kept but ignored.

| Column | Required | Format | Notes |
|---|---|---|---|
| carrier | yes | text | As printed on the report |
| policy_number | no | text | |
| policy_year | yes | YYYY | Year the policy term **starts**. A 7/1/2024–7/1/2025 term is 2024. |
| policy_effective | no | YYYY-MM-DD | Enables the loss-date-in-term check |
| line | yes | code | See line codes below |
| claim_number | yes | text | Exactly as printed, including leading zeros |
| loss_date | yes | YYYY-MM-DD | Date of loss, not report date |
| status | yes | open / closed / reopened | |
| paid_loss | * | number | Indemnity or medical paid to date |
| paid_expense | * | number | ALAE / expense paid |
| outstanding_loss | * | number | Case reserve, loss |
| outstanding_expense | * | number | Case reserve, expense |
| recoveries | no | number | Subrogation, salvage, deductible reimbursement received. Positive number. |
| carrier_incurred | * | number | Total incurred as printed by the carrier |
| valuation_date | yes | YYYY-MM-DD | "Valued as of" date on that report |
| cause | no | text | Short cause or claim type ("rear-end," "slip and fall," "strain - lifting") |
| claim_type | no | text | WC: medical-only / indemnity. Others: BI / PD / other. |

\* Supply the paid and outstanding split when the report shows it. `paid_loss` and `outstanding_loss` must both be filled for the split to count. If the report does not separate expense, put the totals in `paid_loss` and `outstanding_loss` and leave both expense columns blank. If the report shows only a total, fill `carrier_incurred` and leave the four split columns blank. The script uses carrier_incurred when the split is missing.

Number formatting: strip `$` and commas. Parentheses mean negative: `(1,250)` → `-1250`. Blank means unknown, not zero.

## Line codes

| Code | Line |
|---|---|
| WC | Workers compensation |
| GL | General liability |
| AL | Commercial auto liability |
| APD | Auto physical damage |
| PROP | Property |
| UMB | Umbrella / excess |
| PL | Professional / E&O |
| EPL | Employment practices |
| DO | Directors and officers |
| CYB | Cyber |
| CARGO | Motor truck cargo / inland marine cargo |
| IM | Other inland marine |
| OTHER | Anything else. Put the carrier's label in `cause`. |

## premium.csv (optional)

| Column | Required | Notes |
|---|---|---|
| policy_year | yes | Same convention as claims.csv |
| line | yes | Same codes. Use ALL for a package premium that cannot be split. ALL means premium for every line **not** listed separately that year, so ALL and per-line rows add together. |
| earned_premium | yes | Earned, not written, when available |
| premium_basis | no | `earned` or `written`. When any row says `written`, outputs rename the columns to `written_premium` and `loss_ratio_written` (or `mixed_…`) and the JSON totals carry a `premium_note`. |

Loss ratios are computed only where premium covers the losses: per year and line when that line has premium; per year when every line with claims that year has premium or an ALL row exists. The all-years ratio uses only those covered years and lists them in `loss_ratio_years`. Years left out get a `premium_missing_lines` flag.

## Extraction tips

- Multi-carrier: one report per carrier per valuation. When two valuations of the same carrier exist, keep only the latest per claim.
- Claims marked "record only," "incident," or "first report only" with zero dollars: keep them. They count toward frequency. Set amounts to 0 and status as printed.
- WC reports often split medical and indemnity. Add them into `paid_loss` and `outstanding_loss`. Note medical-only vs. indemnity in `claim_type`.
- If a page is unreadable, add the row with what is readable and put `UNREADABLE` in `cause`. The script will flag it.
