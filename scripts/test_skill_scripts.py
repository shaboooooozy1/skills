#!/usr/bin/env python3
"""Regression tests for bundled skill scripts, using synthetic data in evals/.

Usage: python scripts/test_skill_scripts.py   (exit 1 on any failure)
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LR = ROOT / "plugins/pc-risk-counsel/skills/analyzing-loss-runs/scripts/summarize_loss_runs.py"
RET = ROOT / "plugins/pc-risk-counsel/skills/analyzing-total-cost-of-risk/scripts/retention_analysis.py"
TCOR = ROOT / "plugins/pc-risk-counsel/skills/analyzing-total-cost-of-risk/scripts/tcor.py"
CHART = ROOT / "plugins/personal-productivity/skills/building-quick-charts/scripts/make_chart.py"
EV = ROOT / "evals"
failures = []


def run(args, cwd):
    r = subprocess.run([sys.executable, "-I", *map(str, args)], cwd=cwd, capture_output=True, text=True)
    if r.returncode:
        failures.append(f"{Path(args[0]).name} exited {r.returncode}: {r.stderr[-400:]}")
    return r


def check(cond, msg):
    if not cond:
        failures.append(msg)


with tempfile.TemporaryDirectory() as tmp:
    run([LR, EV / "analyzing-loss-runs/claims.csv", "--premium", EV / "analyzing-loss-runs/premium.csv",
         "--large-loss", "100000", "--as-of", "2026-10-24", "--out", "ls"], tmp)
    r = json.loads((Path(tmp) / "ls.json").read_text())
    t = r["totals"]
    check(t["claims"] == 21, f"claims {t['claims']} != 21")
    check(t["open_claims"] == 9, f"open {t['open_claims']} != 9")
    check(round(t["incurred"]) == 802080, f"incurred {t['incurred']} != 802080")
    check(t["claims_over_threshold"] == 3, "large-loss count != 3")
    expected_flags = {"superseded_valuation": 1, "duplicate_claim": 1, "incurred_mismatch": 1,
                      "open_zero_reserve": 2, "closed_with_reserve": 1, "loss_date_outside_term": 1,
                      "stale_valuation": 1}
    check(r["flag_counts"] == expected_flags, f"flags {r['flag_counts']} != {expected_flags}")
    y2025 = [y for y in r["by_year"] if y["policy_year"] == 2025][0]
    check(y2025["immature"] is True, "2025 should be immature")

    run([RET, EV / "analyzing-loss-runs/claims.csv", "--retentions", "25000,50000,100000",
         "--aggregate", "250000", "--lines", "AL", "--immature-years", "2024,2025", "--out", "ret"], tmp)
    s = {row["retention"]: row for row in json.loads((Path(tmp) / "ret.json").read_text())["summary"]}
    check(round(s[100000]["avg_annual_retained_all_years"]) == 61760, "100K avg all years != 61,760")
    check(round(s[100000]["avg_annual_retained_mature_years"]) == 73667, "100K avg mature != 73,667")
    check(round(s[100000]["worst_year_retained"]) == 109800, "100K worst year != 109,800")

    run([TCOR, EV / "analyzing-total-cost-of-risk/inputs.json", "--out", "tc"], tmp)
    p = json.loads((Path(tmp) / "tc.json").read_text())["periods"]
    check(round(p[0]["TCOR"]) == 531200, f"current TCOR {p[0]['TCOR']} != 531,200")
    check(round(p[1]["TCOR"]) == 533050, f"scenario TCOR {p[1]['TCOR']} != 533,050")

    (Path(tmp) / "c.csv").write_text("Year,Loss ratio\n2022,0.71\n2023,0.64\n2024,0.52\n2025,0.48\n")
    run([CHART, "c.csv", "--title", "Loss ratio fell 3 straight years", "--format", "percent",
         "--benchmark", "0.6", "--benchmark-label", "Target 60%", "--labels", "--out", "c"], tmp)
    check((Path(tmp) / "c.png").stat().st_size > 10_000, "chart PNG missing or empty")

    # Edge cases from PR #17 review: blank claim numbers, partial splits, extra PII columns,
    # duplicate premium rows, premium-only years, missing effective dates.
    tp = Path(tmp)
    (tp / "edge.csv").write_text(
        "carrier,policy_year,line,claim_number,loss_date,status,paid_loss,outstanding_loss,"
        "carrier_incurred,valuation_date,cause,claimant_name\n"
        "Test Co,2024,GL,,2024-03-01,closed,1000,0,,2026-09-30,UNREADABLE,Jane Roe\n"
        "Test Co,2024,GL,,2024-05-01,closed,2000,0,,2026-09-30,UNREADABLE,John Doe\n"
        "Test Co,2024,GL,C-3,2024-06-01,open,5000,,12000,2026-09-30,slip,Pat Poe\n"
        "Test Co,2024,GL,C-4,2024-07-01,open,,3000,,2026-09-30,slip,Sam Soe\n")
    (tp / "edge_prem.csv").write_text(
        "policy_year,line,earned_premium\n2024,GL,10000\n2024,GL,15000\n2025,GL,20000\n")
    run([LR, "edge.csv", "--premium", "edge_prem.csv", "--as-of", "2026-10-24", "--out", "edge"], tmp)
    e = json.loads((tp / "edge.json").read_text())
    check(e["totals"]["claims"] == 4, f"blank claim numbers merged: {e['totals']['claims']} claims, want 4")
    check(round(e["totals"]["incurred"]) == 1000 + 2000 + 12000 + 3000,
          f"partial split handling wrong: incurred {e['totals']['incurred']}, want 18000")
    check(e["flag_counts"].get("incomplete_split") == 2, f"incomplete_split flags {e['flag_counts']}")
    years = {y["policy_year"]: y for y in e["by_year"]}
    check(2025 in years and years[2025]["claims"] == 0, "premium-only year 2025 missing from by_year")
    yl = [r for r in e["by_year_line"] if r["policy_year"] == 2024 and r["line"] == "GL"]
    check(len(yl) == 1 and round(yl[0]["earned_premium"]) == 25000,
          f"duplicate premium rows not summed: {yl}")
    check(abs(yl[0]["loss_ratio"] - 18000 / 25000) < 1e-9 if yl else False, "2024 GL loss ratio wrong")
    check("open_claims" in e and len(e["open_claims"]) == 2, "open_claims missing from JSON")
    check(years[2024]["immature"] is True and "Dec 1" in years[2024]["maturity_basis"],
          f"maturity fallback should be conservative: {years[2024]}")
    import openpyxl
    hdr = [c.value for c in openpyxl.load_workbook(tp / "edge.xlsx")["Claims"][1]]
    check("claimant_name" not in hdr, "claimant_name leaked into Claims sheet")

    run([RET, "edge.csv", "--retentions", "10000", "--out", "edge_ret"], tmp)
    er = json.loads((tp / "edge_ret.json").read_text())
    check(round(er["summary"][0]["total_retained"]) == 1000 + 2000 + 10000 + 3000,
          f"retention replay partial/blank handling wrong: {er['summary'][0]['total_retained']}")

    # Second review round: premium coverage, written basis, undated duplicates, zero-claim years.
    (tp / "cov.csv").write_text(
        "carrier,policy_year,line,claim_number,loss_date,status,paid_loss,outstanding_loss,valuation_date\n"
        "T,2022,WC,W1,2022-05-01,closed,1000,0,2026-09-30\n"
        "T,2022,AL,A1,2022-06-01,closed,4000,0,2026-09-30\n"
        "T,2023,WC,W2,2023-05-01,closed,2000,0,2026-09-30\n"
        "T,2023,AL,A2,2023-06-01,closed,3000,0,\n"
        "T,2023,AL,A2,2023-06-01,closed,3500,0,\n"
        "T,2024,AL,A3,2024-06-01,closed,9000,0,2026-09-30\n")
    (tp / "cov_prem.csv").write_text(
        "policy_year,line,earned_premium,premium_basis\n"
        "2022,WC,10000,written\n"            # AL missing -> no 2022 year ratio
        "2023,ALL,20000,written\n"           # package covers all lines -> 2023 ratio
        "2024,AL,30000,written\n")
    run([LR, "cov.csv", "--premium", "cov_prem.csv", "--as-of", "2026-10-24", "--out", "cov"], tmp)
    c = json.loads((tp / "cov.json").read_text())
    ct, cy = c["totals"], {y["policy_year"]: y for y in c["by_year"]}
    check(cy[2022].get("loss_ratio_written") is None, f"2022 ratio should be withheld: {cy[2022]}")
    check(abs(cy[2023]["loss_ratio_written"] - 5000 / 20000) < 1e-9, f"2023 ALL ratio wrong: {cy[2023]}")
    check(ct["loss_ratio_years"] == [2023, 2024], f"rated years {ct.get('loss_ratio_years')}")
    check(abs(ct["loss_ratio_written"] - (5000 + 9000) / 50000) < 1e-9, f"all-years ratio {ct}")
    check(ct["premium_basis"] == "written" and "premium_note" in ct, "written basis not labeled")
    check(c["flag_counts"].get("premium_missing_lines") == 1, f"flags {c['flag_counts']}")
    check(ct["claims"] == 5 and c["flag_counts"].get("duplicate_claim") == 1,
          "undated duplicate not handled without crashing")

    run([RET, "cov.csv", "--retentions", "5000", "--lines", "WC", "--out", "cov_ret"], tmp)
    cr = json.loads((tp / "cov_ret.json").read_text())["summary"][0]
    check(cr["years"] == 3 and round(cr["avg_annual_retained_all_years"]) == 1000,
          f"zero-claim year not counted: {cr}")

    (tp / "blank.csv").write_text("Year,Loss ratio\n2022,0.5\n2023,\n2024,0.4\n")
    run([CHART, "blank.csv", "--title", "Gap for unknown", "--format", "percent", "--labels",
         "--out", "blank"], tmp)
    check((tp / "blank.png").exists(), "blank-cell chart failed")

    # Third review round: an old claim-free year is mature; by-line ratio uses rated years only.
    (tp / "old.csv").write_text(
        "carrier,policy_year,policy_effective,line,claim_number,loss_date,status,paid_loss,outstanding_loss,valuation_date\n"
        "T,2021,2021-07-01,GL,G1,2021-08-01,closed,5000,0,2026-09-30\n"
        "T,2023,2023-07-01,GL,G2,2023-08-01,closed,7000,0,2026-09-30\n")
    (tp / "old_prem.csv").write_text("policy_year,line,earned_premium\n2022,GL,10000\n2023,GL,10000\n")
    run([LR, "old.csv", "--premium", "old_prem.csv", "--as-of", "2026-10-24", "--out", "old"], tmp)
    o = json.loads((tp / "old.json").read_text())
    oy = {y["policy_year"]: y for y in o["by_year"]}
    check(oy[2022]["immature"] is False, f"claim-free 2022 should be mature: {oy[2022]}")
    gl = [r for r in o["by_line"] if r["line"] == "GL"][0]
    check(abs(gl["loss_ratio"] - 7000 / 20000) < 1e-9, f"by-line ratio should use rated years only: {gl}")

    # Fourth round: reported reserves kept on partial splits; undated claim years stay immature;
    # premium-only lines stay in by_line.
    (tp / "r4.csv").write_text(
        "carrier,policy_year,line,claim_number,loss_date,status,paid_loss,outstanding_loss,carrier_incurred,valuation_date\n"
        "T,2021,GL,G1,2021-08-01,open,,4000,9000,2026-09-30\n"
        "U,2023,AL,A1,2023-08-01,closed,500,0,,\n")
    (tp / "r4_prem.csv").write_text("policy_year,line,earned_premium\n2021,GL,1000\n2023,AL,1000\n2022,UMB,500\n")
    run([LR, "r4.csv", "--premium", "r4_prem.csv", "--as-of", "2026-10-24", "--out", "r4"], tmp)
    r4 = json.loads((tp / "r4.json").read_text())
    check(round(r4["totals"]["outstanding"]) == 4000, f"reported reserve dropped: {r4['totals']}")
    check(round(r4["totals"]["incurred"]) == 9500, f"incurred wrong: {r4['totals']['incurred']}")
    y23 = [y for y in r4["by_year"] if y["policy_year"] == 2023][0]
    check(y23["immature"] is True and "unknown" in y23["maturity_basis"],
          f"undated claim year must stay immature: {y23}")
    umb = [r for r in r4["by_line"] if r["line"] == "UMB"]
    check(len(umb) == 1 and umb[0]["claims"] == 0, f"premium-only line missing: {r4['by_line']}")

    # A blank premium cell must not count as coverage for its line.
    (tp / "bp.csv").write_text(
        "carrier,policy_year,line,claim_number,loss_date,status,paid_loss,outstanding_loss,valuation_date\n"
        "T,2024,WC,W1,2024-08-01,closed,1000,0,2026-09-30\n"
        "T,2024,AL,A1,2024-08-01,closed,2000,0,2026-09-30\n")
    (tp / "bp_prem.csv").write_text("policy_year,line,earned_premium\n2024,WC,10000\n2024,AL,\n")
    run([LR, "bp.csv", "--premium", "bp_prem.csv", "--as-of", "2026-10-24", "--out", "bp"], tmp)
    bp = json.loads((tp / "bp.json").read_text())
    check(bp["by_year"][0]["loss_ratio"] is None and bp["totals"]["loss_ratio_years"] == [],
          f"blank premium treated as coverage: {bp['by_year'][0]}")
    check(bp["flag_counts"].get("premium_unreadable") == 1 and bp["flag_counts"].get("premium_missing_lines") == 1,
          f"flags {bp['flag_counts']}")

    # ALL row plus a blank listed line, and a line with one known and one blank row: both unrated.
    (tp / "al.csv").write_text(
        "carrier,policy_year,line,claim_number,loss_date,status,paid_loss,outstanding_loss,valuation_date\n"
        "T,2024,WC,W1,2024-08-01,closed,30000,0,2026-09-30\n"
        "T,2024,GL,G1,2024-08-01,closed,20000,0,2026-09-30\n"
        "T,2025,AL,A1,2025-08-01,closed,5000,0,2026-09-30\n")
    (tp / "al_prem.csv").write_text(
        "policy_year,line,earned_premium\n2024,ALL,50000\n2024,WC,\n2025,AL,10000\n2025,AL,\n")
    run([LR, "al.csv", "--premium", "al_prem.csv", "--as-of", "2026-10-24", "--out", "al"], tmp)
    al = json.loads((tp / "al.json").read_text())
    ay = {y["policy_year"]: y for y in al["by_year"]}
    check(ay[2024]["loss_ratio"] is None and ay[2025]["loss_ratio"] is None,
          f"partly unknown premium must leave years unrated: {ay}")
    check(al["totals"]["loss_ratio_years"] == [], f"rated years {al['totals']['loss_ratio_years']}")
    al25 = [r for r in al["by_year_line"] if r["policy_year"] == 2025 and r["line"] == "AL"][0]
    check(al25["loss_ratio"] is None, f"year-line with a blank row must be unrated: {al25}")
    check(al["flag_counts"].get("premium_all_and_lines") == 1, f"flags {al['flag_counts']}")

    # A blank premium on a claim-free line (or ALL row) leaves the year unrated too.
    (tp / "cf.csv").write_text(
        "carrier,policy_year,line,claim_number,loss_date,status,paid_loss,outstanding_loss,valuation_date\n"
        "T,2024,WC,W1,2024-08-01,closed,5000,0,2026-09-30\n")
    (tp / "cf_prem.csv").write_text("policy_year,line,earned_premium\n2024,WC,10000\n2024,UMB,\n")
    run([LR, "cf.csv", "--premium", "cf_prem.csv", "--as-of", "2026-10-24", "--out", "cf"], tmp)
    cf = json.loads((tp / "cf.json").read_text())
    check(cf["by_year"][0]["loss_ratio"] is None and cf["totals"]["loss_ratio_years"] == [],
          f"unknown premium on a claim-free line must leave the year unrated: {cf['by_year'][0]}")

    # Codex round on 9f9b6b1: retention options, unknown amounts, undated dups, reserve flags,
    # least-mature policy, zero premium, bad premium years, TCOR open items, chart stacking.
    (tp / "cx.csv").write_text(
        "carrier,policy_number,policy_year,policy_effective,line,claim_number,loss_date,status,paid_loss,"
        "outstanding_loss,carrier_incurred,valuation_date\n"
        "T,P1,2023,2023-01-01,GL,G1,2023-03-01,closed,,500,4000,2026-09-30\n"
        "U,P2,2023,2023-12-01,GL,G2,2024-01-15,open,100,0,,2024-12-31\n"
        "T,P1,2023,2023-01-01,GL,G3,2023-04-01,closed,,,,2026-09-30\n"
        "V,P3,2024,,AL,A1,2024-06-01,closed,1000,0,,\n"
        "V,P3,2024,,AL,A1,2024-06-01,closed,9000,0,,\n")
    (tp / "cx_prem.csv").write_text("policy_year,line,earned_premium\n2023,GL,0\n2024,GL,10000\n,GL,999\n")
    run([LR, "cx.csv", "--premium", "cx_prem.csv", "--as-of", "2026-10-24", "--out", "cx"], tmp)
    cx = json.loads((tp / "cx.json").read_text())
    fc = cx["flag_counts"]
    check(fc.get("closed_with_reserve") == 1, f"reserve on carrier-total claim not flagged: {fc}")
    check(fc.get("open_zero_reserve") == 1 and fc.get("premium_bad_year") == 1, f"flags {fc}")
    y23 = [y for y in cx["by_year"] if y["policy_year"] == 2023][0]
    check(y23["maturity_months"] == 12 and y23["immature"] is True,
          f"maturity must use the least mature policy: {y23}")
    gl = [r for r in cx["by_line"] if r["line"] == "GL"][0]
    check(gl["loss_ratio"] is None or gl["rated_years"] != "2023",
          f"zero-premium year counted as rated: {gl}")
    check(round(cx["totals"]["earned_premium"]) == 10000, f"bad-year premium kept in total: {cx['totals']}")

    run([RET, "cx.csv", "--retentions", "5000,5000", "--aggregate", "10000,20000", "--out", "cx_ret"], tmp)
    cxr = json.loads((tp / "cx_ret.json").read_text())
    check(len(cxr["summary"]) == 2 and all(s["years"] == 2 for s in cxr["summary"]),
          f"retention options merged: {cxr['summary']}")
    notes = " ".join(cxr["notes"])
    check("no known amount" in notes and "no readable valuation date" in notes, f"notes {cxr['notes']}")

    (tp / "tc_open_in.json").write_text(json.dumps({"periods": [{"label": "x", "premiums": {"WC": 100, "GL": ""}}]}))
    run([TCOR, "tc_open_in.json", "--out", "tc_open"], tmp)
    oi = json.loads((tp / "tc_open.json").read_text())["periods"][0]["open_items"]
    check("GL blank" in oi and "Retained losses not supplied" in oi, f"TCOR open items missing: {oi!r}")
    (tp / "tc_none.json").write_text(json.dumps({"periods": [{"label": "y"}]}))
    r = subprocess.run([sys.executable, "-I", str(TCOR), "tc_none.json"], cwd=tmp, capture_output=True, text=True)
    check(r.returncode != 0 and "premiums are missing" in r.stderr, "missing premiums not rejected")

    (tp / "dup.csv").write_text("Year,Premium,Premium\n2024,1,2\n")
    r = subprocess.run([sys.executable, "-I", str(CHART), "dup.csv", "--title", "x", "--out", "dup"],
                       cwd=tmp, capture_output=True, text=True)
    check(r.returncode != 0 and "Duplicate column" in r.stderr, "duplicate chart headers not rejected")
    (tp / "stk.csv").write_text("Year,Premium,Credit\n2024,100,-40\n")
    run([CHART, "stk.csv", "--type", "stacked", "--title", "x", "--labels", "--out", "stk"], tmp)

    # Security review: carrier text starting with '=' must stay text, never a live formula.
    (tp / "inj.csv").write_text(
        "carrier,policy_year,line,claim_number,loss_date,status,paid_loss,outstanding_loss,valuation_date,cause\n"
        'T,2024,GL,"=HYPERLINK(""http://x.test"",""ok"")",2024-06-01,closed,100,0,2026-09-30,=1+1\n')
    run([LR, "inj.csv", "--as-of", "2026-10-24", "--out", "inj"], tmp)
    run([RET, "inj.csv", "--retentions", "50", "--out", "inj_ret"], tmp)
    (tp / "inj_in.json").write_text(json.dumps({"periods": [{"label": "=2+2", "premiums": 1, "source": "=A1"}]}))
    run([TCOR, "inj_in.json", "--out", "inj_tc"], tmp)
    for book in ("inj.xlsx", "inj_ret.xlsx", "inj_tc.xlsx"):
        live = [f"{ws.title}!{c.coordinate}" for ws in openpyxl.load_workbook(tp / book).worksheets
                for row in ws.iter_rows() for c in row if c.data_type == "f"]
        check(not live, f"{book} has live formula cells: {live}")
    claims_ws = openpyxl.load_workbook(tp / "inj.xlsx")["Claims"]
    vals = [c.value for row in claims_ws.iter_rows(min_row=2) for c in row]
    check('=HYPERLINK("http://x.test","ok")' in vals, "claim number text not preserved exactly")

    (tp / "neg.csv").write_text("Item,Change\nA,500\nB,-300\nC,200\n")
    run([CHART, "neg.csv", "--title", "Credits shown", "--out", "neg"], tmp)
    check((tp / "neg.png").exists(), "negative-value chart failed")

if failures:
    print("FAILED")
    for f in failures:
        print(" -", f)
    sys.exit(1)
print("All script tests passed.")
