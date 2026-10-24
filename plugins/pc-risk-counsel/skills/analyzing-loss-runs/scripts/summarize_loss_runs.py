#!/usr/bin/env python3
"""Summarize normalized commercial P&C loss runs.

Reads claims.csv (schema: references/schema.md) and optional premium.csv, then writes
<out>.xlsx and <out>.json with totals by policy year and line, large losses, open claims,
top causes, and data-quality flags.

Usage:
  python summarize_loss_runs.py claims.csv [--premium premium.csv] [--large-loss 50000]
                                [--as-of YYYY-MM-DD] [--stale-days 90] [--out loss_summary]
"""
import argparse
import csv
import json
import math
import re
import sys
from datetime import date

import pandas as pd
from openpyxl.styles import Font

REQUIRED = ["carrier", "policy_year", "line", "claim_number", "loss_date", "status", "valuation_date"]
SPLIT = ["paid_loss", "paid_expense", "outstanding_loss", "outstanding_expense"]
MONEY = SPLIT + ["recoveries", "carrier_incurred"]
STATUSES = {"open", "closed", "reopened"}
LINE_CODES = {"WC", "GL", "AL", "APD", "PROP", "UMB", "PL", "EPL", "DO", "CYB", "CARGO", "IM", "OTHER"}  # schema.md
SAFE_EXPORT = ["carrier", "policy_number", "policy_year", "policy_effective", "line", "claim_number",
               "loss_date", "status", "claim_type", "cause", "paid_loss", "paid_expense",
               "outstanding_loss", "outstanding_expense", "recoveries", "carrier_incurred",
               "paid", "outstanding", "incurred", "incurred_source", "valuation_date"]
MISMATCH_TOL_ABS = 1.0      # dollars
MISMATCH_TOL_PCT = 0.005    # 0.5%


def read_table(path):
    """Read a CSV as text, stopping on repeated headers. pandas would rename a second
    'paid_loss' to 'paid_loss.1' and quietly ignore it."""
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))
    header = rows[0] if rows else []
    wide = [i + 1 for i, r in enumerate(rows[1:], start=1)
            if len(r) != len(header) and any(c.strip() for c in r)]
    if wide:
        sys.exit(f"{path}: row(s) {', '.join(map(str, wide[:10]))} have a different number of fields than the "
                 "header. Quote amounts with commas, e.g. \"1,000\".")
    norm = [h.strip().lower() for h in header]
    dupes = sorted({h for h in norm if h and norm.count(h) > 1})
    if dupes:
        sys.exit(f"{path}: column(s) {', '.join(dupes)} appear more than once. Keep one of each.")
    return pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")


def guard_outputs(inputs, out):
    """Stop before writing if --out would overwrite an input file (e.g. inputs.json with --out inputs)."""
    from pathlib import Path
    ins = {Path(p).resolve() for p in inputs if p}
    hit = [str(o) for o in (Path(f"{out}.xlsx").resolve(), Path(f"{out}.json").resolve()) if o in ins]
    if hit:
        sys.exit(f"--out {out} would overwrite the input {hit[0]}. Choose a different --out name.")


def valid_year(s):
    """Policy year as Int64: whole numbers from 1900 to 2100 only. 2024.5 or 20245 become unreadable."""
    y = pd.to_numeric(s, errors="coerce")
    return y.where(y.notna() & (y % 1 == 0) & y.between(1900, 2100)).astype("Int64")


def to_number(v):
    """'$1,250' -> 1250.0, '(1,250)' -> -1250.0, '' -> NaN."""
    if pd.isna(v):
        return float("nan")
    s = str(v).strip()
    if s == "" or s.lower() in {"n/a", "na", "-", "--"}:
        return float("nan")
    neg = s.startswith("(") and s.endswith(")")
    if neg:
        s = s[1:-1].strip()
    sign = ""
    if s[:1] in ("+", "-"):
        sign, s = s[0], s[1:].lstrip()
    if s.startswith("$"):
        s = s[1:].strip()
        if not sign and s[:1] in ("+", "-"):
            sign, s = s[0], s[1:]
    if neg and sign:
        return float("nan")  # "(-$1,000)" mixes two negative notations; never let them cancel out
    # Validate the whole format before dropping separators: "12,34" or "1(2)" is an OCR or typing
    # error, not 1234 or 12, so it stays unreadable and gets flagged.
    if re.search(r"[()$\s]", s):
        return float("nan")
    if "," in s:
        if not re.fullmatch(r"\d{1,3}(,\d{3})+(\.\d+)?", s):
            return float("nan")
        s = s.replace(",", "")
    try:
        n = float(sign + s)
    except ValueError:
        return float("nan")
    if not math.isfinite(n):
        return float("nan")  # "Infinity" and "nan" text count as unreadable
    return -n if neg else n


def load_claims(path):
    df = read_table(path)
    df.columns = [c.strip().lower() for c in df.columns]
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        sys.exit(f"claims.csv is missing required columns: {', '.join(missing)}")
    for c in MONEY:
        if c not in df.columns:
            df[c] = ""
    for c in ["policy_effective", "cause", "claim_type", "policy_number"]:
        if c not in df.columns:
            df[c] = ""
    df["_row"] = range(2, len(df) + 2)  # spreadsheet row number incl. header
    df["_unreadable"] = ""
    for c in MONEY:
        raw = df[c].astype(str).str.strip()
        df[c] = df[c].map(to_number)
        # Text that is present but not a number is not the same as a blank cell: remember it.
        bad = raw.ne("") & ~raw.str.lower().isin({"n/a", "na", "-", "--"}) & df[c].isna()
        df.loc[bad, "_unreadable"] = df.loc[bad, "_unreadable"] + c + " "
    for c in ["carrier", "line", "claim_number", "status", "cause"]:
        df[c] = df[c].astype(str).str.strip()
    df["line"] = df["line"].str.upper()
    df["status"] = df["status"].str.lower()
    df["policy_year"] = valid_year(df["policy_year"])
    eff_raw = df["policy_effective"].astype(str).str.strip()
    for c in ["loss_date", "valuation_date", "policy_effective"]:
        df[c] = pd.to_datetime(df[c].replace("", None), errors="coerce")
    df["_bad_effective"] = eff_raw.ne("") & df["policy_effective"].isna()  # supplied but unreadable
    return df


def flag(flags, row, kind, detail):
    flags.append({
        "row": int(row["_row"]) if row is not None else None,
        "carrier": row["carrier"] if row is not None else "",
        "claim_number": row["claim_number"] if row is not None else "",
        "flag": kind,
        "detail": detail,
    })


def dedupe(df, flags):
    """Keep the latest valuation per (carrier, claim_number). Flag true duplicates."""
    df = df.sort_values("valuation_date", kind="stable")  # stable: ties keep file order, first row wins
    no_id = df["claim_number"].str.strip().eq("") | df["carrier"].str.strip().eq("")
    keep = list(df.index[no_id])  # rows without a full key are kept as-is and flagged later
    for _, g in df[~no_id].groupby(["carrier", "claim_number"], sort=False):
        if len(g) == 1:
            keep.append(g.index[0])
            continue
        dated = g[g["valuation_date"].notna()]
        if dated.empty:
            # No readable valuation date on any row: keep the first, flag the rest. Never guess order.
            for _, r in g.iloc[1:].iterrows():
                flag(flags, r, "duplicate_claim",
                     f"Claim appears {len(g)} times with no readable valuation date. Kept row "
                     f"{int(g.iloc[0]['_row'])}. Confirm which report is current.")
            keep.append(g.index[0])
            continue
        latest_date = dated["valuation_date"].max()
        latest = dated[dated["valuation_date"] == latest_date]
        if len(latest) > 1:
            for _, r in latest.iloc[1:].iterrows():
                flag(flags, r, "duplicate_claim",
                     f"Same claim and valuation date appears {len(latest)} times. Kept row {int(latest.iloc[0]['_row'])}.")
        for i, r in g.drop(index=latest.index).iterrows():
            if pd.isna(r["valuation_date"]):
                flag(flags, r, "undated_duplicate",
                     f"Row has no readable valuation date. Kept the dated valuation {latest_date.date()}.")
            elif i not in latest.index:
                flag(flags, r, "superseded_valuation",
                     f"Older valuation dropped. Kept valuation {latest_date.date()}.")
        keep.append(latest.index[0])
    return df.loc[keep].sort_values(["policy_year", "line", "loss_date"])


def compute_amounts(df, flags):
    """Use the paid/outstanding split only when it is complete.

    Complete = paid_loss and outstanding_loss both present. Expense columns may be blank when the
    report does not separate expense (schema.md). A partial split falls back to carrier_incurred;
    with no carrier total it is computed from what is known and flagged as possibly understated.
    """
    any_split = df[SPLIT].notna().any(axis=1)
    complete = df["paid_loss"].notna() & df["outstanding_loss"].notna()
    partial = any_split & ~complete
    has_split = complete | (partial & df["carrier_incurred"].isna())
    rec = df["recoveries"].fillna(0)
    df["paid"] = df["paid_loss"].fillna(0) + df["paid_expense"].fillna(0)
    df["outstanding"] = df["outstanding_loss"].fillna(0) + df["outstanding_expense"].fillna(0)
    computed = df["paid"] + df["outstanding"] - rec
    df["incurred"] = computed.where(has_split, df["carrier_incurred"])
    df["incurred_source"] = has_split.map({True: "computed", False: "carrier"})
    df.loc[partial & has_split, "incurred_source"] = "computed_partial"  # known parts only, may understate
    # When incurred comes from the carrier total, keep whatever paid or reserve parts the report
    # did show (open-exposure totals need them); a part with nothing known stays unknown.
    known_paid = df[["paid_loss", "paid_expense"]].sum(axis=1, min_count=1)
    known_out = df[["outstanding_loss", "outstanding_expense"]].sum(axis=1, min_count=1)
    df.loc[~has_split, "paid"] = known_paid[~has_split]
    df.loc[~has_split, "outstanding"] = known_out[~has_split]
    # On any incomplete split, the side whose loss amount is blank stays unknown, never a reported zero,
    # so paid/outstanding totals know they are incomplete. Incurred above still uses the known parts.
    df.loc[partial & df["paid_loss"].isna(), "paid"] = float("nan")
    df.loc[partial & df["outstanding_loss"].isna(), "outstanding"] = float("nan")

    for i, r in df.iterrows():
        if partial[i]:
            if has_split[i]:
                flag(flags, r, "incomplete_split",
                     "Paid or outstanding loss is blank and there is no carrier incurred. Total uses known "
                     "amounts only and may be understated.")
            else:
                flag(flags, r, "incomplete_split",
                     "Paid or outstanding loss is blank. Used carrier incurred instead of a partial total.")
        if complete[i] and pd.notna(r["carrier_incurred"]):
            diff = abs(computed[i] - r["carrier_incurred"])
            if diff > max(MISMATCH_TOL_ABS, MISMATCH_TOL_PCT * abs(r["carrier_incurred"])):
                flag(flags, r, "incurred_mismatch",
                     f"paid + outstanding - recoveries = {computed[i]:,.0f} but carrier incurred = "
                     f"{r['carrier_incurred']:,.0f}. Computed value used.")
        if pd.notna(df.at[i, "incurred"]) and df.at[i, "incurred"] < 0:
            flag(flags, r, "net_negative_incurred",
                 f"Recoveries exceed paid + outstanding (net {df.at[i, 'incurred']:,.0f}). Counted as 0 here and in "
                 "the retention replay. Confirm the recovery with the carrier.")
            df.at[i, "incurred"] = 0.0
        if pd.isna(df.at[i, "incurred"]):
            flag(flags, r, "missing_amounts", "No paid/outstanding split and no carrier incurred. Counted as 0.")
            df.at[i, "incurred"] = 0.0
            df.at[i, "incurred_source"] = "missing"
    return df


def incurred_note(df):
    """Say plainly whether incurred is complete. Claims with no amount count as 0 and partial splits
    use known parts only, so either one makes the incurred total a floor, not a full figure."""
    parts = []
    if not df[["paid", "outstanding"]].notna().all().all():
        parts.append("Some claims show only a carrier incurred total, so paid and outstanding totals are unknown.")
    n_missing = int((df["incurred_source"] == "missing").sum())
    n_partial = int((df["incurred_source"] == "computed_partial").sum())
    if n_missing or n_partial:
        parts.append(f"Incurred is understated: {n_missing} claim(s) have no known amount (counted as 0) and "
                     f"{n_partial} use known parts of an incomplete split.")
    elif parts:
        parts.append("Incurred is complete.")
    return " ".join(parts) or None


def check_rows(df, flags):
    for _, r in df.iterrows():
        for c in REQUIRED:
            if pd.isna(r[c]) or str(r[c]).strip() in {"", "NaT", "<NA>"}:
                flag(flags, r, "missing_field", f"{c} is blank or unreadable.")
        if r["line"] and r["line"] not in LINE_CODES:
            flag(flags, r, "unknown_line", f"Line '{r['line']}' is not a schema code. Fix the typo, or use OTHER "
                 "and put the carrier's label in cause.")
        if r.get("_bad_effective"):
            flag(flags, r, "unreadable_date", "policy_effective is unreadable. Maturity assumes a Dec 1 start and "
                 "the policy-term check is skipped. Confirm the date.")
        if r["status"] and r["status"] not in STATUSES:
            flag(flags, r, "bad_status", f"Status '{r['status']}' is not open, closed, or reopened.")
        for c in MONEY:
            if pd.notna(r[c]) and r[c] < 0:  # recoveries too: the schema takes them as positive amounts
                flag(flags, r, "negative_amount", f"{c} = {r[c]:,.0f}.")
        if r["status"] in {"open", "reopened"} and pd.notna(r["outstanding"]) and r["outstanding"] == 0:
            flag(flags, r, "open_zero_reserve", "Open claim carries no reserve. Ask the carrier.")
        if r["status"] == "closed" and pd.notna(r["outstanding"]) and r["outstanding"] > 0:
            flag(flags, r, "closed_with_reserve", f"Closed claim still shows {r['outstanding']:,.0f} outstanding.")
        if pd.notna(r["loss_date"]):
            if pd.notna(r["policy_effective"]):
                start = r["policy_effective"]
                end = start + pd.DateOffset(years=1)
                if not (start <= r["loss_date"] < end):
                    flag(flags, r, "loss_date_outside_term",
                         f"Loss {r['loss_date'].date()} outside term {start.date()} to {end.date()}.")
            elif pd.notna(r["policy_year"]) and r["loss_date"].year not in (int(r["policy_year"]), int(r["policy_year"]) + 1):
                flag(flags, r, "loss_date_outside_term",
                     f"Loss year {r['loss_date'].year} does not fit policy year {int(r['policy_year'])}.")
        if str(r.get("_unreadable", "")).strip():
            flag(flags, r, "unreadable_amount",
                 f"Unreadable value in {', '.join(r['_unreadable'].split())}. Treated as unknown; "
                 "totals that use it may be wrong. Confirm with the carrier report.")
        if "UNREADABLE" in str(r["cause"]).upper():
            flag(flags, r, "unreadable_source", "Marked unreadable during extraction. Confirm with carrier report.")


def check_valuations(df, flags, as_of, stale_days):
    """One flag per carrier report (carrier + valuation date), not per claim."""
    for (carrier, vdate), g in df.dropna(subset=["valuation_date"]).groupby(["carrier", "valuation_date"]):
        age = (pd.Timestamp(as_of) - vdate).days
        if age < 0:
            flags.append({"row": None, "carrier": carrier, "claim_number": f"({len(g)} claims)",
                          "flag": "future_valuation",
                          "detail": f"Report valued {vdate.date()}, after --as-of {as_of}. Check the date or the "
                                    "--as-of value; maturity uses this date as given."})
        elif age > stale_days:
            flags.append({"row": None, "carrier": carrier, "claim_number": f"({len(g)} claims)",
                          "flag": "stale_valuation",
                          "detail": f"Report valued {vdate.date()}, {age} days before {as_of}. Request current loss runs."})


def summarize(df, group_cols, premium, large, ypremium=None):
    g = df.groupby(group_cols, dropna=False)
    out = pd.DataFrame({
        "claims": g.size(),
        "open_claims": g["status"].apply(lambda s: int(s.isin(["open", "reopened"]).sum())),
        # A group total is shown only when every claim's paid/outstanding is known. One carrier-total-only
        # claim makes the group's paid and outstanding unknown (incurred stays complete).
        "paid": g["paid"].agg(lambda s: s.sum() if s.notna().all() else float("nan")),
        "outstanding": g["outstanding"].agg(lambda s: s.sum() if s.notna().all() else float("nan")),
        "incurred": g["incurred"].sum(),
        "avg_incurred_per_claim": g["incurred"].mean(),
        "largest_claim": g["incurred"].max(),
        "claims_over_large_loss": g["incurred"].apply(lambda s: int((s >= large).sum())),
        "latest_valuation": g["valuation_date"].max().dt.date,
    }).reset_index()
    if premium is not None:
        out = attach_premium(out, group_cols, premium, ypremium)
    return out


def year_premium(df, premium, flags):
    """Premium per policy year, and whether it covers every line with claims that year.

    Coverage rules, per line with claims:
      - any premium row for that line is blank or unreadable -> not covered (premium partly unknown)
      - the line has known premium rows -> covered
      - the line is not listed -> covered only by a known ALL row (ALL = lines not listed separately)
    A year's loss ratio is computed only when every line with claims is covered and no premium
    amount that year is unknown (an unknown amount anywhere makes the denominator unknown).
    """
    def ylabel(py):
        return f"(policy year {int(py)})"

    rows = []
    claim_lines = df.groupby("policy_year")["line"].apply(set)
    for py in sorted(set(premium["policy_year"].dropna()) | set(claim_lines.index.dropna())):
        yr = premium[premium["policy_year"] == py]
        unknown_rows = yr[yr["earned_premium"].isna()]
        lines = yr[yr["line"] != "ALL"]
        listed = set(lines["line"])
        unknown_lines = set(lines.loc[lines["earned_premium"].isna(), "line"])
        known_lines = set(lines.loc[lines["earned_premium"].notna(), "line"]) - unknown_lines
        all_rows = yr[yr["line"] == "ALL"]
        all_known = len(all_rows) > 0 and all_rows["earned_premium"].notna().all()
        missing = sorted(
            ln for ln in claim_lines.get(py, set())
            if ln in unknown_lines or (ln not in known_lines and not (ln not in listed and all_known)))
        # Any unknown amount makes the year's premium unknown, never a partial sum.
        total = yr["earned_premium"].sum(min_count=1) if unknown_rows.empty else float("nan")
        if len(unknown_rows):
            flags.append({"row": None, "carrier": "", "claim_number": ylabel(py), "flag": "premium_unreadable",
                          "detail": f"Premium blank or unreadable for {', '.join(sorted(unknown_rows['line']))}. "
                                    "Those lines are treated as having unknown premium."})
        if len(all_rows) and listed:
            flags.append({"row": None, "carrier": "", "claim_number": ylabel(py), "flag": "premium_all_and_lines",
                          "detail": f"Premium has an ALL row and per-line rows ({', '.join(sorted(listed))}). "
                                    "They were added. Confirm ALL excludes the listed lines."})
        if missing:
            flags.append({"row": None, "carrier": "", "claim_number": ylabel(py), "flag": "premium_missing_lines",
                          "detail": f"Premium missing or unknown for {', '.join(missing)}. "
                                    "Year loss ratio not computed."})
        # Any unknown premium amount that year leaves the denominator unknown, even on a
        # claim-free line or an ALL row, so the year stays unrated.
        rows.append({"policy_year": py, "earned_premium": total,
                     "premium_complete": not missing and len(unknown_rows) == 0})
    out = pd.DataFrame(rows, columns=["policy_year", "earned_premium", "premium_complete"])  # may be empty
    out["policy_year"] = out["policy_year"].astype("Int64")
    return out


def attach_premium(out, group_cols, premium, ypremium=None):
    """Sum premium per group (several policies or carriers can share a year and line), then
    outer-join so a premium-only group (a zero-loss year or line) still appears with zero losses."""
    if group_cols == ["policy_year"]:
        p = ypremium
    elif group_cols == ["policy_year", "line"]:
        # Any blank row makes that year-line's premium unknown rather than a partial sum.
        p = (premium[premium["line"] != "ALL"]
             .groupby(group_cols, as_index=False)["earned_premium"]
             .agg(lambda s: s.sum() if s.notna().all() else float("nan")))
    else:
        return out
    out = out.merge(p, on=group_cols, how="outer")
    for c in ["claims", "open_claims", "incurred", "claims_over_large_loss"]:
        out[c] = out[c].fillna(0)
    for c in ["claims", "open_claims", "claims_over_large_loss"]:
        out[c] = out[c].astype(int)
    zero = out["claims"] == 0
    out.loc[zero, ["paid", "outstanding"]] = 0.0
    out = out.sort_values(group_cols).reset_index(drop=True)
    out["loss_ratio"] = out["incurred"] / out["earned_premium"]
    no_ratio = out["earned_premium"].isna() | (out["earned_premium"] <= 0)  # zero or negative: no ratio
    if "premium_complete" in out:
        no_ratio |= ~out["premium_complete"].fillna(False).astype(bool)
    out.loc[no_ratio, "loss_ratio"] = float("nan")
    return out


def line_ratios(by_line, by_year_line):
    """Line loss ratio over the policy years that have premium for that line only."""
    known = by_year_line[by_year_line["earned_premium"].notna()]
    rated = known[known["earned_premium"] > 0]  # a zero-premium year cannot be rated
    lines = pd.DataFrame({"line": pd.Series(sorted(set(known["line"])), dtype=object)})  # every premium line stays
    g = rated.groupby("line").agg(earned_premium=("earned_premium", "sum"),
                                  incurred_in_rated_years=("incurred", "sum"),
                                  rated_years=("policy_year", lambda s: ", ".join(str(int(y)) for y in sorted(s))))
    g = lines.merge(g.reset_index(), on="line", how="left")
    out = by_line.merge(g, on="line", how="outer")  # premium-only lines stay, at zero losses
    for c in ["claims", "open_claims", "incurred", "claims_over_large_loss"]:
        out[c] = out[c].fillna(0)
    for c in ["claims", "open_claims", "claims_over_large_loss"]:
        out[c] = out[c].astype(int)
    out.loc[out["claims"] == 0, ["paid", "outstanding"]] = 0.0
    out = out.sort_values("line").reset_index(drop=True)
    out["loss_ratio"] = out["incurred_in_rated_years"] / out["earned_premium"].where(out["earned_premium"] != 0)
    return out


def add_maturity(by_year, df):
    """Months of development per policy year, taken as the LEAST mature record in that year.

    Each policy (carrier + policy number + effective date) is measured on its own: from its term
    start to its latest valuation. The year gets the minimum, so one late-starting or early-valued
    policy keeps the year immature. Without a policy_effective date the start is assumed to be
    Dec 1 of the policy year (never overstates maturity). A policy with no readable valuation
    date makes the year unknown, and unknown counts as immature. A claim-free year is measured
    from Dec 1 (or its known start) to the latest loss-run report date.
    """
    report_date = df["valuation_date"].max()

    def months_between(start, val):
        # Completed months only: Jan 31 to Jan 1 two years later is 23, not 24.
        return (val.year - start.year) * 12 + (val.month - start.month) - (1 if val.day < start.day else 0)

    months_col, basis_col = [], []
    for _, r in by_year.iterrows():
        py = r["policy_year"]
        year_rows = df[df["policy_year"] == py] if pd.notna(py) else df.iloc[0:0]
        if pd.isna(py):
            months, basis = None, "unknown (no policy year)"
        elif year_rows.empty:
            start = pd.Timestamp(int(py), 12, 1)
            if pd.notna(report_date):
                months = months_between(start, report_date)
                basis = "assumed Dec 1 start; valued at latest report date (no claims this year)"
            else:
                months, basis = None, "unknown (no valuation date)"
        else:
            units = year_rows.groupby(["carrier", "policy_number", "policy_effective"], dropna=False)
            results = []
            for (_, _, eff), u in units:
                start = eff if pd.notna(eff) else pd.Timestamp(int(py), 12, 1)
                # any claim with an unknown valuation leaves the whole policy's maturity unknown
                val = pd.NaT if u["valuation_date"].isna().any() else u["valuation_date"].max()
                results.append((None if pd.isna(val) else months_between(start, val), pd.notna(eff)))
            if any(m is None for m, _ in results):
                months, basis = None, "unknown (a policy in this year has no valuation date)"
            else:
                months = min(m for m, _ in results)
                basis = ("least mature policy in the year"
                         + ("" if all(k for _, k in results) else "; Dec 1 start assumed where no policy_effective"))
        months_col.append(months)
        basis_col.append(basis)
    by_year["maturity_months"] = months_col
    by_year["maturity_basis"] = basis_col
    by_year["immature"] = by_year["maturity_months"].map(lambda m: bool(pd.isna(m) or m < 24))
    return by_year


def neutralize_formulas(ws):
    """Keep carrier text as text. openpyxl stores any string starting with '=' as a formula, so a
    claim number or cause printed that way would calculate when the workbook opens. These scripts
    write no intentional formulas, so every such cell is forced back to a plain string."""
    for row in ws.iter_rows():
        for cell in row:
            if isinstance(cell.value, str) and cell.value.startswith("="):
                cell.data_type = "s"


def write_xlsx(path, sheets):
    with pd.ExcelWriter(path, engine="openpyxl") as xw:
        for name, frame in sheets.items():
            frame.to_excel(xw, sheet_name=name, index=False)
            ws = xw.sheets[name]
            neutralize_formulas(ws)
            ws.freeze_panes = "A2"
            for cell in ws[1]:
                cell.font = Font(bold=True)
            for col in ws.columns:
                header = str(col[0].value or "")
                width = max([len(header)] + [len(str(c.value)) for c in col[1:200] if c.value is not None]) + 2
                ws.column_dimensions[col[0].column_letter].width = min(max(width, 10), 48)
                if header in {"paid", "outstanding", "incurred", "avg_incurred_per_claim", "largest_claim",
                              "earned_premium", "paid_loss", "paid_expense", "outstanding_loss",
                              "outstanding_expense", "recoveries", "carrier_incurred",
                              "written_premium", "mixed_premium", "incurred_in_rated_years"}:
                    for c in col[1:]:
                        c.number_format = '$#,##0;($#,##0)'
                elif header.startswith("loss_ratio") or header == "share_of_total_incurred":
                    for c in col[1:]:
                        c.number_format = "0.0%"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("claims")
    p.add_argument("--premium")
    p.add_argument("--large-loss", type=float, default=50000)
    p.add_argument("--as-of", default=date.today().isoformat())
    p.add_argument("--stale-days", type=int, default=90)
    p.add_argument("--out", default="loss_summary")
    a = p.parse_args()
    guard_outputs([a.claims, a.premium], a.out)
    try:
        a.as_of = date.fromisoformat(a.as_of).isoformat()
    except ValueError:
        sys.exit(f"--as-of must be a date like 2026-10-24, not {a.as_of!r}.")
    if a.stale_days < 0:
        sys.exit("--stale-days must be 0 or more.")
    if not math.isfinite(a.large_loss) or a.large_loss < 0:
        sys.exit("--large-loss must be a finite number of zero or more.")

    flags = []
    df = load_claims(a.claims)
    if df.empty:
        sys.exit("claims.csv has no rows. If there were no losses, say so in the narrative instead.")
    df = dedupe(df, flags)
    df = compute_amounts(df, flags)
    check_rows(df, flags)
    check_valuations(df, flags, a.as_of, a.stale_days)

    premium = None
    if a.premium:
        premium = read_table(a.premium)
        premium.columns = [c.strip().lower() for c in premium.columns]
        for c in ["policy_year", "line", "earned_premium"]:
            if c not in premium.columns:
                sys.exit(f"premium.csv is missing column: {c}")
        premium["policy_year"] = valid_year(premium["policy_year"])  # 2024.5 or 20245 -> premium_bad_year
        bad_year = premium[premium["policy_year"].isna()]
        if len(bad_year):
            flags.append({"row": None, "carrier": "", "claim_number": f"({len(bad_year)} premium rows)",
                          "flag": "premium_bad_year",
                          "detail": "Premium rows with a blank or unreadable policy_year were left out of every "
                                    "total and ratio. Fix the year to include them."})
            premium = premium[premium["policy_year"].notna()].copy()
        premium["line"] = premium["line"].str.strip().str.upper()
        no_line = premium[premium["line"] == ""]
        if len(no_line):
            flags.append({"row": None, "carrier": "", "claim_number": f"({len(no_line)} premium rows)",
                          "flag": "premium_no_line",
                          "detail": "Premium rows with a blank line code were left out of every total and ratio. "
                                    "Give each a line code or ALL."})
            premium = premium[premium["line"] != ""].copy()
        odd = premium[~premium["line"].isin(LINE_CODES | {"ALL"})]
        if len(odd):
            flags.append({"row": None, "carrier": "", "claim_number": f"({len(odd)} premium rows)",
                          "flag": "premium_unknown_line",
                          "detail": f"Premium line code(s) {', '.join(sorted(set(odd['line'])))} are not schema codes. "
                                    "Those rows were left out of every total and ratio. Fix the code or use OTHER."})
            premium = premium[premium["line"].isin(LINE_CODES | {"ALL"})].copy()
        premium["earned_premium"] = premium["earned_premium"].map(to_number).astype(float)  # float even if empty
        # A blank basis means earned (the default), also in a file where other rows say written.
        raw_basis = premium["premium_basis"] if "premium_basis" in premium else pd.Series([""] * len(premium))
        bases = set(raw_basis.str.strip().str.lower().replace("", "earned"))
        if bases - {"earned", "written"}:
            sys.exit(f"premium_basis must be earned, written, or blank. Found: {', '.join(sorted(bases - {'earned', 'written'}))}")
        basis = "earned" if bases <= {"earned"} else ("written" if bases == {"written"} else "mixed")

    ypremium = year_premium(df, premium, flags) if premium is not None else None
    by_year = add_maturity(summarize(df, ["policy_year"], premium, a.large_loss, ypremium), df)
    by_year_line = summarize(df, ["policy_year", "line"], premium, a.large_loss)
    by_line = summarize(df, ["line"], None, a.large_loss)
    if premium is not None:
        by_line = line_ratios(by_line, by_year_line)

    total_inc = df["incurred"].sum()
    cols = ["carrier", "policy_year", "line", "claim_number", "loss_date", "status", "cause",
            "paid", "outstanding", "incurred", "valuation_date"]
    large = df[df["incurred"] >= a.large_loss].sort_values("incurred", ascending=False)[cols].copy()
    large["share_of_total_incurred"] = large["incurred"] / total_inc if total_inc else float("nan")
    open_claims = df[df["status"].isin(["open", "reopened"])].sort_values("outstanding", ascending=False)[cols]
    causes = (df.assign(cause=df["cause"].replace("", "(not given)"))
                .groupby("cause").agg(claims=("claim_number", "size"), incurred=("incurred", "sum"))
                .sort_values(["claims", "incurred"], ascending=False).head(10).reset_index())
    flags_df = pd.DataFrame(flags, columns=["row", "carrier", "claim_number", "flag", "detail"])

    # Export only schema columns. Extra carrier-report columns (claimant names, notes) never leave.
    claims_out = df[[c for c in SAFE_EXPORT if c in df.columns]].copy()
    for c in ["loss_date", "valuation_date", "policy_effective"]:
        claims_out[c] = claims_out[c].dt.date
    for frame in (large, open_claims):
        for c in ["loss_date", "valuation_date"]:
            frame[c] = frame[c].dt.date

    totals = {
        "claims": int(len(df)),
        "open_claims": int(df["status"].isin(["open", "reopened"]).sum()),
        "paid": float(df["paid"].sum()) if df["paid"].notna().all() else None,
        "outstanding": float(df["outstanding"].sum()) if df["outstanding"].notna().all() else None,
        "paid_outstanding_note": incurred_note(df),
        "incurred": float(total_inc),
        "large_loss_threshold": a.large_loss,
        "claims_over_threshold": int(len(large)),
        "large_loss_share_of_incurred": float(large["incurred"].sum() / total_inc) if total_inc else None,
        "carriers": sorted(df["carrier"].unique().tolist()),
        "policy_years": [int(y) for y in sorted(df["policy_year"].dropna().unique())],
        "incurred_from_carrier_total_only": int((df["incurred_source"] == "carrier").sum()),
    }
    if premium is not None:
        # All-years ratio uses only the years whose premium covers every line with claims.
        rated = by_year[by_year["loss_ratio"].notna()]
        ep, inc = float(rated["earned_premium"].sum()), float(rated["incurred"].sum())
        totals["premium_basis"] = basis
        totals["earned_premium"] = (float(premium["earned_premium"].sum())
                                    if premium["earned_premium"].notna().all() else None)
        totals["loss_ratio"] = inc / ep if ep else None
        totals["loss_ratio_years"] = [int(y) for y in rated["policy_year"]]
        if basis != "earned":
            note = f"{basis} premium"
            totals["premium_note"] = (f"Premium basis is {note}. Loss ratios use {note}, not earned premium. "
                                      "Label them that way in any narrative.")
            ren = {"earned_premium": f"{basis}_premium", "loss_ratio": f"loss_ratio_{basis}"}
            by_year, by_year_line, by_line = (f.rename(columns=ren) for f in (by_year, by_year_line, by_line))
            totals = {ren.get(k, k): v for k, v in totals.items()}

    write_xlsx(f"{a.out}.xlsx", {
        "Summary_by_Year": by_year,
        "Summary_by_Year_Line": by_year_line,
        "Summary_by_Line": by_line,
        "Large_Losses": large,
        "Open_Claims": open_claims,
        "Top_Causes": causes,
        "Data_Flags": flags_df,
        "Claims": claims_out,
    })

    def records(frame):
        return json.loads(frame.to_json(orient="records", date_format="iso"))

    report = {
        "as_of": a.as_of,
        "totals": totals,
        "by_year": records(by_year),
        "by_line": records(by_line),
        "by_year_line": records(by_year_line),
        "open_claims": records(open_claims),
        "large_losses": records(large),
        "top_causes": records(causes),
        "flag_counts": flags_df["flag"].value_counts().to_dict(),
        "flags": records(flags_df),
        "review_gate": ("Draft for licensed-professional review. Based on carrier loss runs as valued on the "
                        "dates shown. Not an actuarial analysis or coverage determination."),
    }
    with open(f"{a.out}.json", "w") as f:
        json.dump(report, f, indent=2, default=str)

    print(f"Claims: {totals['claims']} ({totals['open_claims']} open) | Incurred: ${totals['incurred']:,.0f} "
          f"| Large losses >= ${a.large_loss:,.0f}: {totals['claims_over_threshold']}")
    lr_key = next((k for k in totals if k.startswith("loss_ratio") and k != "loss_ratio_years"), None)
    if lr_key and totals[lr_key] is not None:
        print(f"Loss ratio ({lr_key}, years {totals['loss_ratio_years']}): {totals[lr_key]:.1%}")
    print(f"Data flags: {len(flags_df)} {dict(report['flag_counts'])}")
    print(f"Wrote {a.out}.xlsx and {a.out}.json")


if __name__ == "__main__":
    main()
