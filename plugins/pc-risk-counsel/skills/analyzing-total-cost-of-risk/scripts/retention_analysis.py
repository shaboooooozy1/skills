#!/usr/bin/env python3
"""Replay historical claims against per-occurrence retention options.

Answers: "Had this client carried a $X deductible or SIR, how much of each year's losses
would it have kept?" Reads the normalized claims.csv produced for analyzing-loss-runs.

Retained per claim = min(claim amount, retention). If an annual aggregate is given, retained
per year is capped at the aggregate. Everything above is ceded to the insurer.

This is a historical replay at current valuations. It is not a projection. Recent years are
immature, and inflation and exposure changes are not adjusted unless the user supplies factors.

Usage:
  python retention_analysis.py claims.csv --retentions 25000,50000,100000 \
      [--aggregate 250000] [--lines AL,GL] [--basis incurred|loss_only] \
      --immature-years 2024,2025|none [--out retention]
"""
import argparse
import json
import math
import re
import sys

import pandas as pd
from openpyxl.styles import Font

SPLIT = ["paid_loss", "paid_expense", "outstanding_loss", "outstanding_expense"]


def to_number(v):
    if pd.isna(v):
        return float("nan")
    s = str(v).strip()
    if s in {"", "-", "--"} or s.lower() in {"n/a", "na"}:
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


def money_list(s, name):
    """Options are separated by commas, or by semicolons when the numbers use thousands separators.

    '25000,50000' -> [25000, 50000]; '25,000;50,000' -> [25000, 50000].
    A comma list that also reads as one thousands-formatted number (e.g. '25,500') is ambiguous
    and rejected.
    """
    s = s.strip()
    if "$" in s:
        sys.exit(f"--{name}: leave out the $ sign, e.g. 25000,50000")
    if ";" in s:
        parts = [x.strip() for x in s.split(";") if x.strip()]
        for x in parts:
            if "," in x and not re.fullmatch(r"\d{1,3}(,\d{3})+(\.\d+)?", x):
                sys.exit(f"--{name}: '{x}' has misplaced thousands separators. Use 25,000 or 25000.")
        parts = [x.replace(",", "") for x in parts]
    else:
        if re.fullmatch(r"\d{1,3}(,\d{3})+", s):
            sys.exit(f"--{name} '{s}' could be one number with thousands separators or several options. "
                     "Write plain numbers (25500 or 25,500 as 25500) and separate options with commas, "
                     "or use semicolons: 25,500;50,000")
        parts = [x.strip() for x in s.split(",") if x.strip()]
    try:
        vals = [float(x) for x in parts]
    except ValueError:
        sys.exit(f"--{name} must be numbers separated by commas, e.g. 25000,50000")
    if not vals:
        sys.exit(f"--{name} needs at least one number, e.g. 25000,50000")
    if not all(math.isfinite(v) for v in vals):
        sys.exit(f"--{name} values must be finite numbers.")
    return vals


def load(path, basis, notes):
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    df.columns = [c.strip().lower() for c in df.columns]
    for c in ["carrier", "claim_number", "policy_year", "line"]:
        if c not in df.columns:
            sys.exit(f"claims.csv missing column: {c}")
    # Bad amounts are recorded per row and checked in main() after dedupe and the --years/--lines
    # filters, so a superseded valuation or an excluded line never blocks an otherwise valid replay.
    df["_bad"] = ""
    for c in SPLIT + ["recoveries", "carrier_incurred"]:
        if c not in df.columns:
            df[c] = float("nan")
            continue
        raw = df[c].astype(str).str.strip()
        df[c] = df[c].map(to_number)
        bad = raw.ne("") & ~raw.str.lower().isin({"n/a", "na", "-", "--"}) & df[c].isna()
        df.loc[bad, "_bad"] += c + " "
        df.loc[df[c] < 0, "_bad"] += f"negative {c} "
    df["valuation_date"] = pd.to_datetime(df.get("valuation_date", ""), errors="coerce")
    df["line"] = df["line"].str.strip().str.upper()
    df["carrier"] = df["carrier"].str.strip()
    df["claim_number"] = df["claim_number"].str.strip()  # same keys as summarize_loss_runs.py
    py = pd.to_numeric(df["policy_year"], errors="coerce")
    df["policy_year"] = py.where(py.notna() & (py % 1 == 0)).astype("Int64")  # 2024.5 counts as unreadable
    # latest valuation per claim; rows missing carrier or claim number are never merged together
    df = df.sort_values("valuation_date", na_position="first")  # undated rows never win over dated ones
    no_id = df["claim_number"].str.strip().eq("") | df["carrier"].str.strip().eq("")
    keyed = df[~no_id]
    undated_dups = keyed[keyed["valuation_date"].isna()
                         & keyed.duplicated(subset=["carrier", "claim_number"], keep=False)]
    ambiguous = (undated_dups.groupby(["carrier", "claim_number"]).size().index
                 .difference(keyed[keyed["valuation_date"].notna()].set_index(["carrier", "claim_number"]).index))
    if len(ambiguous):
        notes.append(f"{len(ambiguous)} claim(s) appear more than once with no readable valuation date "
                     f"({', '.join(c for _, c in ambiguous)}). Kept one row each without knowing which is "
                     "current. Confirm against the carrier reports.")
    dated = keyed[keyed["valuation_date"].notna()]
    latest = dated[dated["valuation_date"] == dated.groupby(["carrier", "claim_number"])["valuation_date"].transform("max")]
    tied = latest[latest.duplicated(subset=["carrier", "claim_number"], keep=False)]
    if len(tied):
        names = sorted(set(tied["claim_number"]))
        notes.append(f"{len(names)} claim(s) have two rows with the same latest valuation date "
                     f"({', '.join(names)}). Kept one without knowing which is right. Confirm with the carrier.")
    df = pd.concat([df[no_id], keyed.drop_duplicates(subset=["carrier", "claim_number"], keep="last")])
    amb = {(c, n) for c, n in ambiguous}
    undated = [n or "(no claim number)"
               for c, n, d in zip(df["carrier"], df["claim_number"], df["valuation_date"])
               if pd.isna(d) and (c, n) not in amb]  # ambiguous duplicates already have their own note
    if undated:
        notes.append(f"{len(undated)} claim(s) have no readable valuation date ({', '.join(undated)}). "
                     "Their amounts may be older than the rest of the data. Confirm the valuation with the carrier.")
    if no_id.any():
        notes.append(f"{int(no_id.sum())} row(s) lack a carrier or claim number and were kept as separate claims.")
    # Same rule as summarize_loss_runs.py: the split is complete when paid_loss and outstanding_loss
    # are both known. A partial split falls back to carrier_incurred when present.
    any_split = df[SPLIT].notna().any(axis=1)
    complete = df["paid_loss"].notna() & df["outstanding_loss"].notna()
    partial = any_split & ~complete
    has_split = complete | (partial & df["carrier_incurred"].isna())
    if partial.any():
        notes.append(f"{int(partial.sum())} claim(s) had an incomplete paid/outstanding split. Used carrier "
                     "incurred where given; otherwise known amounts only (may understate).")
    rec = df["recoveries"].fillna(0)
    if basis == "loss_only":
        amt = df["paid_loss"].fillna(0) + df["outstanding_loss"].fillna(0) - rec
    else:
        amt = df[SPLIT].fillna(0).sum(axis=1) - rec
    n_fallback = int((~has_split & df["carrier_incurred"].notna()).sum())
    if n_fallback:
        notes.append(f"{n_fallback} claim(s) had only a carrier incurred total. Used it as the claim amount"
                     + (" (includes expense, overstates loss-only basis)." if basis == "loss_only" else "."))
    no_amount = ~has_split & df["carrier_incurred"].isna()
    if no_amount.any():
        notes.append(f"{int(no_amount.sum())} claim(s) have no known amount at all "
                     f"({', '.join(df.loc[no_amount, 'claim_number'].replace('', '(blank)'))}). Counted as 0, "
                     "so every scenario's retained losses are understated until they are filled in.")
    # Same tolerance as summarize_loss_runs.py: name claims whose split disagrees with the carrier total.
    total_split = df[SPLIT].fillna(0).sum(axis=1) - rec
    mismatch = complete & df["carrier_incurred"].notna() & (
        (total_split - df["carrier_incurred"]).abs()
        > (0.005 * df["carrier_incurred"].abs()).clip(lower=1.0))
    if mismatch.any():
        notes.append(f"{int(mismatch.sum())} claim(s) have a paid/outstanding split that disagrees with the "
                     f"carrier incurred total ({', '.join(df.loc[mismatch, 'claim_number'])}). The split was "
                     "used. Resolve with the carrier before relying on these scenarios.")
    df["amount"] = amt.where(has_split, df["carrier_incurred"]).fillna(0).clip(lower=0)
    return df


def neutralize_formulas(ws):
    """Keep carrier text as text. openpyxl stores any string starting with '=' as a formula, so a
    claim number or cause printed that way would calculate when the workbook opens. These scripts
    write no intentional formulas, so every such cell is forced back to a plain string."""
    for row in ws.iter_rows():
        for cell in row:
            if isinstance(cell.value, str) and cell.value.startswith("="):
                cell.data_type = "s"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("claims")
    ap.add_argument("--retentions", required=True, help="Per-occurrence options, e.g. 25000,50000,100000")
    ap.add_argument("--aggregate", help="Annual aggregate cap. One value for all options, or one per option.")
    ap.add_argument("--lines", help="Comma-separated line codes to include, e.g. AL,GL. Default all.")
    ap.add_argument("--basis", choices=["incurred", "loss_only"], default="incurred",
                    help="incurred = loss + expense less recoveries; loss_only excludes ALAE")
    ap.add_argument("--years", help="Policy years the loss runs cover, e.g. 2021-2025. Default: every year in "
                    "claims.csv before the line filter. Years with no claims count as zero retained.")
    ap.add_argument("--immature-years", help="Comma-separated policy years to mark immature, e.g. 2024,2025, "
                    "or 'none'. Without it the mature-years average is withheld.")
    ap.add_argument("--out", default="retention")
    a = ap.parse_args()

    notes = []
    rets = money_list(a.retentions, "retentions")
    aggs = money_list(a.aggregate, "aggregate") if a.aggregate else []
    if aggs and len(aggs) not in (1, len(rets)):
        sys.exit("--aggregate needs one value, or one per retention option.")
    if len(aggs) == 1:
        aggs = aggs * len(rets)
    if any(v < 0 for v in rets + aggs):
        sys.exit("Retentions and aggregates must be zero or positive.")
    pairs = list(zip(rets, aggs or [None] * len(rets)))
    if len(set(pairs)) != len(pairs):
        sys.exit("The same retention and aggregate pair is listed twice. List each option once.")
    maturity_known = a.immature_years is not None
    if not maturity_known or a.immature_years.strip().lower() == "none":
        immature = set()
    else:
        try:
            immature = {int(y) for y in a.immature_years.split(",") if y.strip()}
        except ValueError:
            sys.exit("--immature-years must be policy years like 2024,2025, or 'none'.")
    if not maturity_known:
        notes.append("No --immature-years given, so the mature-years average is withheld. Recent years are "
                     "still developing. Rerun with --immature-years (or 'none' if every year is mature).")

    df = load(a.claims, a.basis, notes)
    # Year range comes from the whole file (or --years), before the line filter, so a year
    # with no claims in the selected lines still counts as a zero-retained year.
    if a.years:
        try:
            lo, _, hi = a.years.partition("-")
            years = list(range(int(lo), int(hi or lo) + 1))
        except ValueError:
            sys.exit("--years must look like 2021-2025 or 2024")
    else:
        years = sorted(int(y) for y in df["policy_year"].dropna().unique())
    outside = df[~df["policy_year"].isin(years)]
    if len(outside):
        notes.append(f"{len(outside)} claim(s) fall outside --years and were left out.")
        df = df[df["policy_year"].isin(years)]
    if a.lines:
        keep = {x.strip().upper() for x in a.lines.split(",")}
        df = df[df["line"].isin(keep)]
        notes.append(f"Lines included: {', '.join(sorted(keep))}.")
    if not years:
        sys.exit("No policy years found.")
    bad = df[df["_bad"].str.strip().ne("")]
    if len(bad):
        sys.exit("Fix these amounts before replaying (run summarize_loss_runs.py to see every data flag): "
                 + ", ".join(f"{n or '(no claim number)'} ({b.strip()})" for n, b in zip(bad["claim_number"], bad["_bad"])))
    stray = sorted(immature - set(years))
    if stray:
        sys.exit(f"--immature-years {', '.join(map(str, stray))} not in the replay years "
                 f"({years[0]}-{years[-1]}). Check for a typo.")
    empty_years = [y for y in years if not (df["policy_year"] == y).any()]
    if empty_years:
        notes.append(f"No claims in {', '.join(map(str, empty_years))} for the selected lines. Counted as zero "
                     "retained. Confirm the loss runs cover those years.")

    rows, piercing = [], []
    for i, ret in enumerate(rets):
        agg = aggs[i] if aggs else None
        option = f"${ret:,.0f}" + (f" / ${agg:,.0f} agg" if agg is not None else "")
        for y in years:
            g = df[df["policy_year"] == y]
            per_claim = g["amount"].clip(upper=ret)
            retained = float(per_claim.sum())
            capped = bool(agg is not None and retained >= agg)  # reaching the cap exactly exhausts it
            if agg is not None and retained > agg:
                retained = agg
            total = float(g["amount"].sum())
            over = g[g["amount"] > ret]
            rows.append({
                "option": option, "retention": ret, "aggregate": agg, "policy_year": y,
                "immature": (y in immature) if maturity_known else None, "claims": int(len(g)), "total_losses": total,
                "retained": retained, "ceded": total - retained,
                "retained_pct": retained / total if total else None,
                "claims_piercing_retention": int(len(over)), "aggregate_hit": capped,
            })
            for _, c in over.iterrows():
                piercing.append({"option": option, "retention": ret, "aggregate": agg, "policy_year": y,
                                 "line": c["line"],
                                 "claim_number": c["claim_number"], "amount": float(c["amount"]),
                                 "excess_over_retention": float(c["amount"] - ret)})
    detail = pd.DataFrame(rows)

    summ = []
    # One row per retention+aggregate option, grouped on the raw numbers (labels are rounded).
    for _, g in detail.groupby(["retention", "aggregate"], dropna=False, sort=False):
        mature = g[g["immature"].eq(False)]  # unknown maturity counts as not mature
        summ.append({
            "option": g["option"].iloc[0], "retention": g["retention"].iloc[0], "aggregate": g["aggregate"].iloc[0],
            "years": len(g), "avg_annual_retained_all_years": g["retained"].mean(),
            "avg_annual_retained_mature_years": mature["retained"].mean() if len(mature) and maturity_known else None,
            "worst_year_retained": g["retained"].max(),
            "worst_year": int(g.loc[g["retained"].idxmax(), "policy_year"]),
            "total_retained": g["retained"].sum(), "total_ceded": g["ceded"].sum(),
            "years_aggregate_hit": int(g["aggregate_hit"].sum()),
        })
    summary = pd.DataFrame(summ)

    with pd.ExcelWriter(f"{a.out}.xlsx", engine="openpyxl") as xw:
        summary.to_excel(xw, sheet_name="Summary", index=False)
        detail.to_excel(xw, sheet_name="By_Year", index=False)
        pd.DataFrame(piercing).to_excel(xw, sheet_name="Claims_Over_Retention", index=False)
        pd.DataFrame({"note": notes or ["None"]}).to_excel(xw, sheet_name="Notes", index=False)
        for ws in xw.sheets.values():
            neutralize_formulas(ws)
            ws.freeze_panes = "A2"
            for cell in ws[1]:
                cell.font = Font(bold=True)
            for col in ws.columns:
                h = str(col[0].value or "")
                ws.column_dimensions[col[0].column_letter].width = min(max(len(h) + 2, 12), 60)
                if h.endswith("_pct"):
                    for c in col[1:]:
                        c.number_format = "0.0%"
                elif any(k in h for k in ["retention", "aggregate", "losses", "retained", "ceded", "amount", "excess"]) \
                        and "hit" not in h and "piercing" not in h:
                    for c in col[1:]:
                        c.number_format = '$#,##0'

    out = {
        "basis": a.basis, "notes": notes,
        "summary": json.loads(summary.to_json(orient="records")),
        "by_year": json.loads(detail.to_json(orient="records")),
        "caveat": ("Historical replay at current valuations. Not a projection. Immature years understate "
                   "retained losses. No trend, inflation, or exposure adjustment applied."),
    }
    with open(f"{a.out}.json", "w") as f:
        json.dump(out, f, indent=2)

    print(f"Basis: {a.basis} | Years: {years[0]}-{years[-1]} | Claims: {len(df)}")
    print(f"{'Retention':>11} {'Agg':>11} {'Avg/yr (all)':>14} {'Avg/yr (mature)':>16} {'Worst yr':>12}")
    for _, s in summary.iterrows():
        agg = f"${s['aggregate']:,.0f}" if pd.notna(s["aggregate"]) else "none"
        mat = f"${s['avg_annual_retained_mature_years']:,.0f}" if pd.notna(s["avg_annual_retained_mature_years"]) else "n/a"
        print(f"${s['retention']:>10,.0f} {agg:>11} ${s['avg_annual_retained_all_years']:>13,.0f} {mat:>16} "
              f"${s['worst_year_retained']:>11,.0f}")
    for n in notes:
        print("Note:", n)
    print(f"Wrote {a.out}.xlsx and {a.out}.json")


if __name__ == "__main__":
    main()
