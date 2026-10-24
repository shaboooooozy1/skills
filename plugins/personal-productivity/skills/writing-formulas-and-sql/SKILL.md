---
name: writing-formulas-and-sql
description: >-
  Writes exact Excel, Google Sheets, and SQL from plain-English descriptions of a data layout and the
  result wanted, then explains the logic in one or two sentences. Use when the user asks for a formula
  or query, names a function (SUMIFS, XLOOKUP, VLOOKUP, INDEX/MATCH, FILTER, UNIQUE, LET, pivot,
  conditional formatting rule) or a SQL task (join, group by, window function, CTE, dedupe), or pastes
  a broken formula or query and asks why it fails. Do NOT use for building whole spreadsheet files,
  charts, or loss-run analysis.
license: MIT
metadata:
  version: 1.1.0
  author: Will Bloomstine
---

# Writing Formulas and SQL

Translate intent into a formula or query that works the first time. Speed matters. Correctness matters more.

## Workflow

1. **Pin the layout.** Restate columns, header row, sheet names, and the key in one line. If a fact that changes the answer is missing (which column holds the key, whether there is a header), state the assumption and proceed. Ask only when two readings give different results and no default is sensible.
2. **Pin the platform.** Default to Excel for Microsoft 365. If the user says Google Sheets, older Excel, or a SQL dialect, follow it. Note when a function is unavailable (XLOOKUP, LET, FILTER need Excel 2021 or 365).
3. **Write it.** Output the formula or query in a code block, ready to paste.
4. **Explain it.** One or two sentences, so the user can adapt it.
5. **Edge cases.** One line on what breaks it (blank keys, text-formatted numbers, duplicates), only when likely.

## Formula rules

- Prefer `SUMIFS`/`COUNTIFS` over nested `IF`. Prefer `XLOOKUP` or `INDEX/MATCH` over `VLOOKUP`.
- Anchor references the user will fill down (`$B4`, `$C:$C`).
- Wrap lookups that can miss in an explicit not-found value, not a blanket `IFERROR` that hides real errors.
- For a formula over 2 lines, use `LET` and name the parts.
- Debugging a pasted formula: name the error, the cause, and the corrected formula.

## SQL rules

- Default to ANSI SQL. Name the dialect when you use dialect features.
- Filter dates with half-open ranges, never functions on the column. `sale_date >= '2023-01-01' AND sale_date < '2024-01-01'` keeps indexes usable and handles timestamps.
- Use explicit `JOIN ... ON`. Never comma joins.
- Prefer CTEs over nested subqueries when there are more than two steps.
- Warn when a join can fan out and inflate a `SUM`.

## Examples

**"SUMIF with values in F, match in $B4, shared key in C"**
```excel
=SUMIFS($F:$F, $C:$C, $B4)
```
Sums column F where column C equals B4. Fill down to repeat for each key in column B.

**"Loss ratio by policy year from a sheet with Year in A, Incurred in D, Earned Premium in E; the year to match is in H2"**
```excel
=LET(inc, SUMIFS($D:$D, $A:$A, H2), ep, SUMIFS($E:$E, $A:$A, H2), IF(ep=0, "n/a", inc/ep))
```
Totals incurred and earned premium for the year, then divides. Returns "n/a" instead of a divide-by-zero error.

**"Total revenue per customer for 2023, only customers over $1,000"**
```sql
SELECT customer_id,
       SUM(revenue) AS total_revenue
FROM sales
WHERE sale_date >= DATE '2023-01-01'
  AND sale_date <  DATE '2024-01-01'
GROUP BY customer_id
HAVING SUM(revenue) > 1000
ORDER BY total_revenue DESC;
```
Filters to 2023 with an index-friendly date range, totals revenue per customer, and keeps totals over $1,000.

**"Latest row per account"**
```sql
WITH ranked AS (
  SELECT a.*,
         ROW_NUMBER() OVER (PARTITION BY account_id ORDER BY updated_at DESC) AS rn
  FROM accounts a
)
SELECT * FROM ranked WHERE rn = 1;
```
Numbers each account's rows newest first and keeps the first.
