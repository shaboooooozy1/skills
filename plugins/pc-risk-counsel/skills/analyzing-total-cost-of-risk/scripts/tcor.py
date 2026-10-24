#!/usr/bin/env python3
"""Compute Total Cost of Risk (TCOR) for one or more periods or program scenarios.

TCOR = premiums (incl. taxes and fees) + retained losses + administration
       + risk control spend + collateral cost

Input is a JSON file (schema: references/tcor-inputs.md). Every figure comes from the user,
a carrier quote, or the client's books. This script adds and divides. It never estimates.

Usage:
  python tcor.py inputs.json [--out tcor_summary]
"""
import argparse
import json
import math
import re
import sys

import pandas as pd
from openpyxl.styles import Font

COMPONENTS = ["premiums", "retained_losses", "admin", "risk_control", "collateral_cost"]
LABELS = {
    "premiums": "Premiums, taxes and fees",
    "retained_losses": "Retained losses",
    "admin": "Administration",
    "risk_control": "Risk control",
    "collateral_cost": "Collateral cost",
}


MONEY_RE = re.compile(r"[+-]?\$?[+-]?(\d{1,3}(,\d{3})+|\d+)?(\.\d+)?")


def parse_money(s):
    """Strict money text: '$1,250.50', '-1250', '(1,000)'. Malformed separators ('1,00', '1$00') -> None."""
    s = s.strip()
    neg = s.startswith("(") and s.endswith(")")
    if neg:
        s = s[1:-1].strip()
    if not s or not MONEY_RE.fullmatch(s) or not any(ch.isdigit() for ch in s):
        return None
    if neg and ("-" in s or "+" in s):
        return None  # "(-$1,000)" mixes two negative notations; never let them cancel out
    n = float(s.replace("$", "").replace(",", ""))
    return -n if neg else n


def num(v, where):
    if v is None or v == "":
        return 0.0
    try:
        if isinstance(v, bool):
            raise ValueError  # JSON true/false is not an amount
        n = float(v) if isinstance(v, (int, float)) else parse_money(str(v))
    except ValueError:
        n = None
    if n is None:
        sys.exit(f"Not a number at {where}: {v!r}. Check commas and $ signs, e.g. 1,000 or 1000.")
    if not math.isfinite(n):
        sys.exit(f"Not a finite number at {where}: {v!r}")
    return n


def sum_block(block, where):
    if block is None:
        return 0.0, {}
    if isinstance(block, (bool, int, float, str)):
        n = num(block, where)
        return n, {"(single amount)": n}  # keep scalar inputs in the Detail sheet's audit trail
    items = {k: num(v, f"{where}.{k}") for k, v in block.items()}
    return sum(items.values()), items


def compute_period(p, i):
    label = str(p.get("label") or f"period_{i + 1}")  # a year like 2025 is a valid label
    row = {"label": label, "kind": p.get("kind", "actual")}
    detail, open_items = [], []
    if p.get("premiums") in (None, "", {}, []):
        sys.exit(f"{label}: premiums are missing. TCOR cannot be computed without them.")
    if isinstance(p["premiums"], dict) and all(v in (None, "") for v in p["premiums"].values()):
        sys.exit(f"{label}: every premium is blank. TCOR cannot be computed without at least one premium.")
    for comp in ["premiums", "retained_losses", "admin", "risk_control"]:
        block = p.get(comp)
        if block in (None, "", {}):
            open_items.append(f"{LABELS[comp]} not supplied (counted as 0)")
        elif isinstance(block, dict):
            open_items += [f"{LABELS[comp]}: {k} blank (counted as 0)" for k, v in block.items() if v in (None, "")]
        total, items = sum_block(block, f"{label}.{comp}")
        row[comp] = total
        for k, v in items.items():
            detail.append({"label": label, "component": LABELS[comp], "item": k, "amount": v})
    col = p.get("collateral") or {}
    if col:
        open_items += [f"{LABELS['collateral_cost']}: {k} blank (counted as 0)"
                       for k in ("amount", "cost_rate") if col.get(k) in (None, "")]
    amount = num(col.get("amount"), f"{label}.collateral.amount")
    rate = num(col.get("cost_rate"), f"{label}.collateral.cost_rate")
    fees = num(col.get("fees"), f"{label}.collateral.fees")
    if amount < 0 or fees < 0:
        sys.exit(f"{label}.collateral amount and fees cannot be negative.")
    if rate < 0:
        sys.exit(f"{label}.collateral.cost_rate cannot be negative ({rate}).")
    if rate > 1:
        sys.exit(f"{label}.collateral.cost_rate looks like a percent ({rate}). Use a decimal: 0.015 for 1.5%.")
    row["collateral_cost"] = amount * rate + fees
    if amount or fees:
        detail.append({"label": label, "component": LABELS["collateral_cost"],
                       "item": f"{amount:,.0f} x {rate:.4f} + fees {fees:,.0f}", "amount": row["collateral_cost"]})
    if not p.get("collateral"):
        open_items.append(f"{LABELS['collateral_cost']} not supplied (counted as 0)")
    row["tcor"] = sum(row[c] for c in COMPONENTS)
    row["open_items"] = "; ".join(open_items)
    exp = p.get("exposure")
    row["exposure"] = num(exp, f"{label}.exposure") if exp not in (None, "") else None
    if row["exposure"] is not None and row["exposure"] <= 0:
        sys.exit(f"{label}.exposure must be positive. Leave it out if it is unknown.")
    row["notes"] = p.get("notes", "")
    row["source"] = p.get("source", "")
    if not str(row["source"]).strip():
        open_items.append("No source given for this period's figures")
        row["open_items"] = "; ".join(open_items)
    return row, detail


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
    ap.add_argument("inputs")
    ap.add_argument("--out", default="tcor_summary")
    a = ap.parse_args()

    with open(a.inputs) as f:
        cfg = json.load(f)
    periods = cfg.get("periods") or []
    if not periods:
        sys.exit("inputs.json needs a non-empty 'periods' list.")
    base = cfg.get("exposure_base", {})
    base_name = base.get("name", "exposure")
    per = num(base.get("per", 1000), "exposure_base.per")
    if per <= 0:
        sys.exit("exposure_base.per must be a positive number, e.g. 1000 for per $1,000 or 1 for per unit.")
    money_base = base_name.lower() in {"revenue", "payroll", "sales", "receipts", "tiv", "property values"}

    rows, detail = [], []
    for i, p in enumerate(periods):
        r, d = compute_period(p, i)
        rows.append(r)
        detail.extend(d)
    df = pd.DataFrame(rows)
    df["tcor_per_unit"] = df.apply(
        lambda r: r["tcor"] / (r["exposure"] / per) if r["exposure"] else None, axis=1)
    for c in COMPONENTS:
        df[f"{c}_share"] = df[c] / df["tcor"].where(df["tcor"] != 0)
    first = df.iloc[0]
    df["tcor_change_vs_first"] = df["tcor"] - first["tcor"]
    df["tcor_change_pct_vs_first"] = df["tcor_change_vs_first"] / first["tcor"] if first["tcor"] else None

    unit = f"TCOR per {per:,.0f} {base_name}"
    out = df.rename(columns={**LABELS, "tcor": "TCOR", "tcor_per_unit": unit})

    with pd.ExcelWriter(f"{a.out}.xlsx", engine="openpyxl") as xw:
        out.to_excel(xw, sheet_name="TCOR", index=False)
        pd.DataFrame(detail).to_excel(xw, sheet_name="Detail", index=False)
        for ws in xw.sheets.values():
            neutralize_formulas(ws)
            ws.freeze_panes = "B2"
            for cell in ws[1]:
                cell.font = Font(bold=True)
            for col in ws.columns:
                h = str(col[0].value or "")
                ws.column_dimensions[col[0].column_letter].width = min(max(len(h) + 2, 12), 40)
                if "share" in h or "pct" in h:
                    fmt = "0.0%"
                elif "per " in h:
                    fmt = '$#,##0.00'
                elif h == "exposure" and not money_base:
                    fmt = '#,##0'  # headcount, vehicles and other counts are not dollars
                else:
                    fmt = '$#,##0;($#,##0)'
                if h not in {"label", "kind", "notes", "source", "component", "item", "open_items"}:
                    for c in col[1:]:
                        c.number_format = fmt

    result = {
        "client": cfg.get("client", ""),
        "exposure_base": {"name": base_name, "per": per},
        "periods": json.loads(out.to_json(orient="records")),
        # Must match the review gate in analyzing-total-cost-of-risk/SKILL.md.
        "review_gate": ("Draft for licensed-professional review. Figures are as supplied; scenario retained "
                        "losses are historical replays, not actuarial projections. Alternative premiums come "
                        "from carrier quotes."),
    }
    with open(f"{a.out}.json", "w") as f:
        json.dump(result, f, indent=2)

    w = max(len(r["label"]) for r in rows)
    print(f"{'Period':<{w}}  {'TCOR':>12}  {unit:>22}  Premium share  Retained share")
    for _, r in df.iterrows():
        pu = f"${r['tcor_per_unit']:,.2f}" if pd.notna(r["tcor_per_unit"]) else "n/a"
        print(f"{r['label']:<{w}}  ${r['tcor']:>11,.0f}  {pu:>22}  {r['premiums_share']:>12.1%}  "
              f"{r['retained_losses_share']:>13.1%}")
    for r in rows:
        if r["open_items"]:
            print(f"Open items, {r['label']}: {r['open_items']}")
    print(f"Wrote {a.out}.xlsx and {a.out}.json")


if __name__ == "__main__":
    main()
