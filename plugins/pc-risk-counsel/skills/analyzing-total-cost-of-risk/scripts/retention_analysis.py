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
      [--aggregate 250000] [--lines AL,GL] [--basis incurred|loss_only] [--out retention]
"""
import argparse
import json
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
    s = re.sub(r"[,$()\s]", "", s)
    try:
        n = float(s)
    except ValueError:
        return float("nan")
    return -n if neg else n


def money_list(s, name):
    try:
        return [float(x.replace(",", "").replace("$", "")) for x in s.split(",") if x.strip()]
    except ValueError:
        sys.exit(f"--{name} must be comma-separated numbers, e.g. 25000,50000")


def load(path, basis, notes):
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    df.columns = [c.strip().lower() for c in df.columns]
    for c in ["carrier", "claim_number", "policy_year", "line"]:
        if c not in df.columns:
            sys.exit(f"claims.csv missing column: {c}")
    for c in SPLIT + ["recoveries", "carrier_incurred"]:
        df[c] = df[c].map(to_number) if c in df.columns else float("nan")
    df["valuation_date"] = pd.to_datetime(df.get("valuation_date", ""), errors="coerce")
    df["line"] = df["line"].str.strip().str.upper()
    df["policy_year"] = pd.to_numeric(df["policy_year"], errors="coerce").astype("Int64")
    # latest valuation per claim, one row per claim
    df = (df.sort_values("valuation_date")
            .drop_duplicates(subset=["carrier", "claim_number"], keep="last"))
    has_split = df[SPLIT].notna().any(axis=1)
    rec = df["recoveries"].fillna(0)
    if basis == "loss_only":
        amt = df["paid_loss"].fillna(0) + df["outstanding_loss"].fillna(0) - rec
    else:
        amt = df[SPLIT].fillna(0).sum(axis=1) - rec
    n_fallback = int((~has_split).sum())
    if n_fallback:
        notes.append(f"{n_fallback} claim(s) had only a carrier incurred total. Used it as the claim amount"
                     + (" (includes expense, overstates loss-only basis)." if basis == "loss_only" else "."))
    df["amount"] = amt.where(has_split, df["carrier_incurred"]).fillna(0).clip(lower=0)
    return df


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("claims")
    ap.add_argument("--retentions", required=True, help="Per-occurrence options, e.g. 25000,50000,100000")
    ap.add_argument("--aggregate", help="Annual aggregate cap. One value for all options, or one per option.")
    ap.add_argument("--lines", help="Comma-separated line codes to include, e.g. AL,GL. Default all.")
    ap.add_argument("--basis", choices=["incurred", "loss_only"], default="incurred",
                    help="incurred = loss + expense less recoveries; loss_only excludes ALAE")
    ap.add_argument("--immature-years", help="Comma-separated policy years to mark immature, e.g. 2024,2025")
    ap.add_argument("--out", default="retention")
    a = ap.parse_args()

    notes = []
    rets = money_list(a.retentions, "retentions")
    aggs = money_list(a.aggregate, "aggregate") if a.aggregate else []
    if aggs and len(aggs) not in (1, len(rets)):
        sys.exit("--aggregate needs one value, or one per retention option.")
    if len(aggs) == 1:
        aggs = aggs * len(rets)
    immature = {int(y) for y in a.immature_years.split(",")} if a.immature_years else set()

    df = load(a.claims, a.basis, notes)
    if a.lines:
        keep = {x.strip().upper() for x in a.lines.split(",")}
        df = df[df["line"].isin(keep)]
        notes.append(f"Lines included: {', '.join(sorted(keep))}.")
    if df.empty:
        sys.exit("No claims left after filtering.")
    years = sorted(int(y) for y in df["policy_year"].dropna().unique())

    rows, piercing = [], []
    for i, ret in enumerate(rets):
        agg = aggs[i] if aggs else None
        for y in years:
            g = df[df["policy_year"] == y]
            per_claim = g["amount"].clip(upper=ret)
            retained = float(per_claim.sum())
            capped = bool(agg is not None and retained > agg)
            if capped:
                retained = agg
            total = float(g["amount"].sum())
            over = g[g["amount"] > ret]
            rows.append({
                "retention": ret, "aggregate": agg, "policy_year": y,
                "immature": y in immature, "claims": int(len(g)), "total_losses": total,
                "retained": retained, "ceded": total - retained,
                "retained_pct": retained / total if total else None,
                "claims_piercing_retention": int(len(over)), "aggregate_hit": capped,
            })
            for _, c in over.iterrows():
                piercing.append({"retention": ret, "policy_year": y, "line": c["line"],
                                 "claim_number": c["claim_number"], "amount": float(c["amount"]),
                                 "excess_over_retention": float(c["amount"] - ret)})
    detail = pd.DataFrame(rows)

    summ = []
    for ret, g in detail.groupby("retention", sort=False):
        mature = g[~g["immature"]]
        summ.append({
            "retention": ret, "aggregate": g["aggregate"].iloc[0],
            "years": len(g), "avg_annual_retained_all_years": g["retained"].mean(),
            "avg_annual_retained_mature_years": mature["retained"].mean() if len(mature) else None,
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
