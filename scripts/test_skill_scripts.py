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
    check(years[2024]["immature"] is True and "Dec 31" in years[2024]["maturity_basis"],
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

    # Codex round on 41a7ea9: partial totals, unknown premium total, formats, TCOR inputs.
    check(t["paid"] is None and t["outstanding"] is None and t["paid_outstanding_note"],
          f"paid/outstanding must be unknown with a carrier-total-only claim: {t}")
    check(bp["totals"]["earned_premium"] is None, f"premium total must be unknown: {bp['totals']}")
    cws = openpyxl.load_workbook(tp / "cov.xlsx")["Summary_by_Year"]
    hdr = {c.value: c.column for c in cws[1]}
    check(cws.cell(row=2, column=hdr["loss_ratio_written"]).number_format == "0.0%",
          "renamed loss ratio not formatted as percent")
    (tp / "tc_bad.json").write_text(json.dumps({"exposure_base": {"name": "vehicles", "per": 0},
                                                "periods": [{"label": "z", "premiums": 1}]}))
    r = subprocess.run([sys.executable, "-I", str(TCOR), "tc_bad.json"], cwd=tmp, capture_output=True, text=True)
    check(r.returncode != 0 and "positive" in r.stderr, "non-positive exposure divisor not rejected")
    (tp / "tc_col_in.json").write_text(json.dumps({"exposure_base": {"name": "vehicles", "per": 1},
                                                   "periods": [{"label": "z", "premiums": 100, "exposure": 25,
                                                                "collateral": {"amount": 50000, "cost_rate": ""}}]}))
    run([TCOR, "tc_col_in.json", "--out", "tc_col"], tmp)
    col_items = json.loads((tp / "tc_col.json").read_text())["periods"][0]["open_items"]
    check("cost_rate blank" in col_items, f"blank collateral rate not an open item: {col_items!r}")
    tws = openpyxl.load_workbook(tp / "tc_col.xlsx")["TCOR"]
    th = {c.value: c.column for c in tws[1]}
    check(not tws.cell(row=2, column=th["exposure"]).number_format.startswith("$"),
          "vehicle count formatted as currency")

    # Codex round on 43abac2: input validation.
    def fails(args, needle):
        r = subprocess.run([sys.executable, "-I", *map(str, args)], cwd=tmp, capture_output=True, text=True)
        return r.returncode != 0 and needle in r.stderr
    check(fails([RET, EV / "analyzing-loss-runs/claims.csv", "--retentions", "-5000"], "zero or positive"),
          "negative retention not rejected")
    (tp / "tc_neg.json").write_text(json.dumps({"periods": [{"label": "n", "premiums": 1, "exposure": -5}]}))
    check(fails([TCOR, "tc_neg.json"], "must be positive"), "negative exposure not rejected")
    (tp / "tie.csv").write_text(
        "carrier,policy_year,line,claim_number,loss_date,status,paid_loss,outstanding_loss,valuation_date\n"
        "T,2024,GL,G1,2024-03-01,closed,100,0,2026-09-30\nT,2024,GL,G1,2024-03-01,closed,900,0,2026-09-30\n")
    run([RET, "tie.csv", "--retentions", "5000.1,5000.2", "--out", "tie"], tmp)
    tie = json.loads((tp / "tie.json").read_text())
    check("same latest valuation date" in " ".join(tie["notes"]), f"tied valuations not noted: {tie['notes']}")
    check(len(tie["summary"]) == 2 and all(s["years"] == 1 for s in tie["summary"]),
          f"near-equal options merged: {tie['summary']}")
    run([LR, "tie.csv", "--as-of", "2026-01-01", "--out", "fut"], tmp)
    check(json.loads((tp / "fut.json").read_text())["flag_counts"].get("future_valuation") == 1,
          "future valuation not flagged")

    # Codex round on 43ee7a9.
    check(bp["by_year"][0]["earned_premium"] is None, f"partial year premium shown: {bp['by_year'][0]}")
    (tp / "mx.csv").write_text(
        "carrier,policy_year,line,claim_number,loss_date,status,paid_loss,outstanding_loss,valuation_date\n"
        "T,2024,WC,W1,2024-03-01,closed,1000,0,2026-09-30\n"
        " T ,2024,WC, W1 ,2024-03-01,closed,1000,0,2026-06-30\n")
    (tp / "mx_prem.csv").write_text(
        "policy_year,line,earned_premium,premium_basis\n2024,WC,10000,written\n2024,GL,5000,\n2024,,5000,\n")
    run([LR, "mx.csv", "--premium", "mx_prem.csv", "--as-of", "2026-10-24", "--out", "mx"], tmp)
    mx = json.loads((tp / "mx.json").read_text())
    check(mx["totals"]["premium_basis"] == "mixed", f"blank basis must count as earned: {mx['totals']}")
    check(mx["flag_counts"].get("premium_no_line") == 1 and round(mx["totals"]["mixed_premium"]) == 15000,
          f"blank-line premium not excluded: {mx['totals']} {mx['flag_counts']}")
    run([RET, "mx.csv", "--retentions", "500", "--out", "mx_ret"], tmp)
    check(json.loads((tp / "mx_ret.json").read_text())["by_year"][0]["claims"] == 1,
          "whitespace-padded keys counted the claim twice")
    (tp / "tc_negrate.json").write_text(json.dumps({"periods": [{"label": "q", "premiums": 1,
                                                                 "collateral": {"amount": 50000, "cost_rate": -0.02}}]}))
    check(fails([TCOR, "tc_negrate.json"], "cannot be negative"), "negative collateral rate not rejected")

    # Codex round on f1c8d83.
    (tp / "f8.csv").write_text(
        "carrier,policy_year,policy_effective,line,claim_number,loss_date,status,paid_loss,outstanding_loss,"
        "recoveries,valuation_date\n"
        "T,2024,2024-01-31,GL,G1,2024-03-01,closed,9000,0,(1000),2026-01-01\n")
    (tp / "f8_prem.csv").write_text("policy_year,line,earned_premium\n2024,GL,5000\n2024,UMB,0\n")
    run([LR, "f8.csv", "--premium", "f8_prem.csv", "--as-of", "2026-02-01", "--out", "f8"], tmp)
    f8 = json.loads((tp / "f8.json").read_text())
    check(f8["by_year"][0]["maturity_months"] == 23, f"partial month counted: {f8['by_year'][0]}")
    check(f8["flag_counts"].get("negative_amount") == 1, f"negative recovery not flagged: {f8['flag_counts']}")
    check(any(r["line"] == "UMB" for r in f8["by_line"]), "zero-premium-only line dropped from by_line")
    (tp / "f8r.csv").write_text(
        "carrier,policy_year,line,claim_number,loss_date,status,paid_loss,outstanding_loss,valuation_date\n"
        "T,2024,GL,G1,2024-03-01,closed,9000,0,2026-01-01\n")
    run([RET, "f8r.csv", "--retentions", "1000,1000", "--aggregate", "5000,9000", "--out", "f8r"], tmp)
    pw = openpyxl.load_workbook(tp / "f8r.xlsx")["Claims_Over_Retention"]
    check("aggregate" in [c.value for c in pw[1]], "piercing claims do not identify the option")
    (tp / "tc_nan.json").write_text('{"periods": [{"label": "n", "premiums": "NaN", "source": "s"}]}')
    check(fails([TCOR, "tc_nan.json"], "'NaN'"), "non-finite TCOR input not rejected")
    (tp / "tc_negamt.json").write_text(json.dumps({"periods": [{"label": "n", "premiums": 1, "source": "s",
                                                                "collateral": {"amount": -1, "cost_rate": 0.01}}]}))
    check(fails([TCOR, "tc_negamt.json"], "cannot be negative"), "negative collateral amount not rejected")
    nosrc = json.loads((tp / "tc_open.json").read_text())
    check("No source" in nosrc["periods"][0]["open_items"], "missing source not an open item")
    check("historical replays" in nosrc["review_gate"], "TCOR review gate wording differs from SKILL.md")

    # Codex round on c304d80.
    (tp / "ur.csv").write_text(
        "carrier,policy_year,line,claim_number,loss_date,status,paid_loss,outstanding_loss,recoveries,valuation_date\n"
        "T,2024,GL,G1,2024-03-01,closed,1000,0,UNREADABLE,2026-09-30\n")
    run([LR, "ur.csv", "--as-of", "2026-10-24", "--out", "ur"], tmp)
    check(json.loads((tp / "ur.json").read_text())["flag_counts"].get("unreadable_amount") == 1,
          "unreadable recovery not flagged")
    (tp / "ur_prem.csv").write_text("policy_year,line,earned_premium,premium_basis\n2024,GL,5000,writen\n")
    check(fails([LR, "ur.csv", "--premium", "ur_prem.csv"], "premium_basis must be"), "bad premium basis accepted")
    check(fails([RET, "ur.csv", "--retentions", "1000", "--aggregate", "nan"], "finite"), "non-finite aggregate accepted")

    # Codex round on 2515636.
    check(fails([RET, "f8.csv", "--retentions", "1000"], "negative recoveries"), "negative recovery replayed")
    check(fails([RET, "f8r.csv", "--retentions", "$25,000"], "$ sign"), "dollar sign accepted")
    check(fails([RET, "f8r.csv", "--retentions", "25,000"], "thousands separators"), "split thousands accepted")
    check(fails([RET, "f8r.csv", "--retentions", "25,500"], "thousands separators"), "25,500 split into two options")
    run([RET, "f8r.csv", "--retentions", "25,500;50,000", "--out", "semi"], tmp)
    semi = [s["retention"] for s in json.loads((tp / "semi.json").read_text())["summary"]]
    check(semi == [25500, 50000], f"semicolon-separated options misparsed: {semi}")
    (tp / "negl.csv").write_text(
        "carrier,policy_year,line,claim_number,loss_date,status,paid_loss,outstanding_loss,carrier_incurred,valuation_date\n"
        "T,2024,GL,G1,2024-03-01,open,-1000,5000,,2026-09-30\nT,2024,GL,G2,2024-03-01,closed,100,0,900,2026-09-30\n")
    check(fails([RET, "negl.csv", "--retentions", "1000"], "negative paid_loss"), "negative paid loss replayed")
    (tp / "mm.csv").write_text(
        "carrier,policy_year,line,claim_number,loss_date,status,paid_loss,outstanding_loss,carrier_incurred,valuation_date\n"
        "T,2024,GL,G2,2024-03-01,closed,100,0,900,2026-09-30\n")
    run([RET, "mm.csv", "--retentions", "1000", "--out", "mm"], tmp)
    check("disagrees with the carrier incurred" in " ".join(json.loads((tp / "mm.json").read_text())["notes"]),
          "split/carrier mismatch not noted in replay")
    check(fails([LR, "mm.csv", "--large-loss", "nan"], "--large-loss"), "non-finite large-loss threshold accepted")
    (tp / "inf.csv").write_text("Year,Premium\n2024,Infinity\n")
    check(fails([CHART, "inf.csv", "--title", "x"], "'Infinity'"), "non-finite chart value accepted")
    (tp / "inf2.csv").write_text(
        "carrier,policy_year,line,claim_number,loss_date,status,paid_loss,outstanding_loss,valuation_date\n"
        "T,2024,GL,G1,2024-03-01,closed,Infinity,0,2026-09-30\n")
    (tp / "negp.csv").write_text("policy_year,line,earned_premium\n2024,GL,1000\n2024,GL,-3000\n")
    run([LR, "inf2.csv", "--premium", "negp.csv", "--as-of", "2026-10-24", "--out", "inf2"], tmp)
    i2 = json.loads((tp / "inf2.json").read_text())
    check(i2["flag_counts"].get("unreadable_amount") == 1, f"Infinity not flagged: {i2['flag_counts']}")
    check(i2["by_year"][0]["loss_ratio"] is None and i2["totals"]["loss_ratio_years"] == [],
          f"negative premium year rated: {i2['by_year'][0]}")

    # Codex round on d52eef7.
    (tp / "bm.csv").write_text("Year,Ratio\n2024,0.5\n")
    check(fails([CHART, "bm.csv", "--title", "x", "--benchmark", "nan"], "--benchmark"), "non-finite benchmark accepted")
    check(fails([LR, "mm.csv", "--stale-days", "-1"], "--stale-days"), "negative stale-days accepted")
    check(fails([RET, "f8r.csv", "--retentions", "25,00;50,000"], "thousands separators"),
          "mistyped thousands separator silently changed the amount")
    (tp / "tc_blank.json").write_text(json.dumps({"periods": [{"label": "P", "premiums": {"WC": "", "GL": None}}]}))
    check(fails([TCOR, "tc_blank.json"], "every premium is blank"), "all-blank premiums produced a TCOR")
    (tp / "nodate.csv").write_text(
        "carrier,policy_year,line,claim_number,loss_date,status,paid_loss,outstanding_loss,valuation_date\n"
        "T,2024,GL,G1,2024-03-01,closed,500,0,\nT,2024,GL,G2,2024-03-01,closed,700,0,2026-09-30\n")
    run([RET, "nodate.csv", "--retentions", "1000", "--out", "nodate"], tmp)
    nd = " ".join(json.loads((tp / "nodate.json").read_text())["notes"])
    check("no readable valuation date (G1)" in nd, f"unique undated claim not noted: {nd}")
    vs = tp / "vs"
    (vs / "scripts").mkdir(parents=True)
    (vs / "skills/skill-creator/scripts").mkdir(parents=True)
    (vs / "skills/demo").mkdir(parents=True)
    (vs / "scripts/validate_skills.py").write_text((ROOT / "scripts/validate_skills.py").read_text())
    (vs / "skills/skill-creator/scripts/quick_validate.py").write_text(
        (ROOT / "skills/skill-creator/scripts/quick_validate.py").read_text())
    (vs / "skills/demo/SKILL.md").write_text("---\nname: demo\ndescription: Demo skill. Use when testing.\n---\nBody\n")
    (vs / "skills/demo/link").symlink_to("/etc/hostname")
    r = subprocess.run([sys.executable, "-I", str(vs / "scripts/validate_skills.py"), "--only", "skills"],
                       capture_output=True, text=True)
    check(r.returncode != 0 and "symlinks are not allowed" in r.stdout, f"upstream symlink accepted: {r.stdout[-300:]}")

    # Codex round on 2d0df70.
    (tp / "frac.csv").write_text("carrier,policy_year,line,claim_number,loss_date,status,paid_loss,outstanding_loss,valuation_date\n"
        "T,2024.5,GL,G1,2024-03-01,closed,100,0,2026-09-30\nT,2024,GL,G2,2024-03-01,closed,200,0,2026-09-30\n")
    run([LR, "frac.csv", "--as-of", "2026-10-24", "--out", "frac"], tmp)
    check((tp / "frac.json").exists(), "fractional policy year crashed the loss-run script")
    run([RET, "frac.csv", "--retentions", "1000", "--immature-years", "none", "--out", "frac_ret"], tmp)
    check((tp / "frac_ret.json").exists(), "fractional policy year crashed the replay")
    (tp / "sep.csv").write_text("carrier,policy_year,line,claim_number,loss_date,status,paid_loss,outstanding_loss,valuation_date\n"
        'T,2024,GL,G1,2024-03-01,closed,"12,34",0,2026-09-30\nT,2024,GL,G2,2024-03-01,closed,1(2),0,2026-09-30\n'
        'T,2024,GL,G3,2024-03-01,closed,"$1,250.50",(0),2026-09-30\nT,2024,GL,G4,2024-03-01,closed,"($1,000)",0,2026-09-30\n')
    run([LR, "sep.csv", "--as-of", "2026-10-24", "--out", "sep"], tmp)
    sp = json.loads((tp / "sep.json").read_text())
    check(sp["flag_counts"].get("unreadable_amount") == 2, f"malformed separators not flagged: {sp['flag_counts']}")
    check(fails([RET, "sep.csv", "--retentions", "1000"], "G1 (paid_loss)"), "replay accepted 12,34 as 1234")
    (tp / "scope.csv").write_text("carrier,policy_year,line,claim_number,loss_date,status,paid_loss,outstanding_loss,valuation_date\n"
        "T,2024,WC,W1,2024-03-01,closed,abc,0,2026-09-30\n"
        "T,2024,AL,A1,2024-03-01,closed,-5,0,2026-06-30\nT,2024,AL,A1,2024-03-01,closed,500,0,2026-09-30\n")
    run([RET, "scope.csv", "--retentions", "1000", "--lines", "AL", "--immature-years", "none", "--out", "scope"], tmp)
    check((tp / "scope.json").exists(), "bad WC row or superseded AL valuation blocked an AL replay")
    check(fails([RET, "scope.csv", "--retentions", "1000"], "W1 (paid_loss)"), "bad in-scope amount not caught")
    run([RET, "scope.csv", "--retentions", "1000", "--lines", "AL", "--out", "nomat"], tmp)
    nm = json.loads((tp / "nomat.json").read_text()) if (tp / "nomat.json").exists() else {"summary": [{}], "notes": []}
    check(nm["summary"][0].get("avg_annual_retained_mature_years", 0) is None
          and "mature-years average is withheld" in " ".join(nm["notes"]),
          f"mature average published without --immature-years: {nm['summary'][0]}")

    # Codex round on 168f624.
    (tp / "mat.csv").write_text("carrier,policy_year,line,claim_number,loss_date,status,paid_loss,outstanding_loss,valuation_date\n"
        "T,2020,GL,M1,2020-03-01,closed,100,0,2026-09-30\nT,2020,GL,M2,2020-04-01,closed,100,0,\n")
    run([LR, "mat.csv", "--as-of", "2026-10-24", "--out", "mat"], tmp)
    m20 = json.loads((tp / "mat.json").read_text())["by_year"][0]
    check(m20["immature"] is True and m20["maturity_months"] is None,
          f"policy with an undated claim marked mature: {m20}")
    (tp / "fracp.csv").write_text("policy_year,line,earned_premium\n2024.5,GL,1000\n2024,GL,2000\n")
    run([LR, "mm.csv", "--premium", "fracp.csv", "--as-of", "2026-10-24", "--out", "fracp"], tmp)
    fp = json.loads((tp / "fracp.json").read_text()) if (tp / "fracp.json").exists() else {"flag_counts": {}}
    check(fp["flag_counts"].get("premium_bad_year") == 1, f"fractional premium year not flagged: {fp['flag_counts']}")
    for bad in ("1,00", "1$00"):
        (tp / "tc_sep.json").write_text(json.dumps({"periods": [{"label": "P", "premiums": bad}]}))
        check(fails([TCOR, "tc_sep.json"], "Not a number"), f"TCOR accepted malformed premium {bad}")
    (tp / "tc_scalar.json").write_text(json.dumps({"periods": [{"label": "P", "premiums": "$1,250", "admin": 300}]}))
    run([TCOR, "tc_scalar.json", "--out", "tc_scalar_out"], tmp)
    det = [c.value for row in openpyxl.load_workbook(tp / "tc_scalar_out.xlsx")["Detail"].iter_rows() for c in row]
    check(1250 in det and 300 in det, f"scalar components missing from Detail sheet: {det}")
    (tp / "wide.csv").write_text("Year,Revenue\n2024,1,000\n")
    check(fails([CHART, "wide.csv", "--title", "x"], "more fields than the header"), "unquoted 1,000 charted as 1")
    (tp / "badsep.csv").write_text('Year,Revenue\n2024,"1,00"\n')
    check(fails([CHART, "badsep.csv", "--title", "x"], "Non-numeric"), "chart accepted 1,00 as 100")
    (tp / "pos.csv").write_text("Year,Change\n2024,5\n2025,8\n")
    probe = ("import runpy, sys, matplotlib.figure as F\n"
             "orig = F.Figure.savefig\n"
             "def save(self, *a, **k):\n"
             "    print('YLIM', self.axes[0].get_ylim()[0]); return orig(self, *a, **k)\n"
             "F.Figure.savefig = save\n"
             f"sys.argv = [{str(CHART)!r}, 'pos.csv', '--title', 'x', '--benchmark', '-3', '--out', 'negbm']\n"
             f"runpy.run_path({str(CHART)!r}, run_name='__main__')\n")
    out = subprocess.run([sys.executable, "-I", "-c", probe], cwd=tmp, capture_output=True, text=True).stdout
    ylo = [float(x.split()[1]) for x in out.splitlines() if x.startswith("YLIM")]
    check(bool(ylo) and ylo[0] <= -3, f"negative benchmark clipped by the axis: {ylo}")

    # Codex round on d3e68aa.
    (tp / "par.csv").write_text("carrier,policy_year,line,claim_number,loss_date,status,paid_loss,outstanding_loss,valuation_date\n"
        'T,2024,GL,P1,2024-03-01,closed,"(-$1,000)",0,2026-09-30\nT,2024,GL,P2,2024-03-01,closed,"($-1,000)",0,2026-09-30\n')
    run([LR, "par.csv", "--as-of", "2026-10-24", "--out", "par"], tmp)
    pr = json.loads((tp / "par.json").read_text())
    check(pr["flag_counts"].get("unreadable_amount") == 2, f"(-$1,000) read as positive: {pr['flag_counts']}")
    check(fails([RET, "par.csv", "--retentions", "1000"], "P1 (paid_loss)"), "replay read (-$1,000) as positive")
    (tp / "tc_par.json").write_text(json.dumps({"periods": [{"label": "P", "premiums": "(-$1,000)"}]}))
    check(fails([TCOR, "tc_par.json"], "Not a number"), "TCOR read (-$1,000) as positive")
    for empty in ("", ",", ";"):
        check(fails([RET, "mm.csv", "--retentions", empty], "at least one number"), f"empty retentions {empty!r} accepted")
    (tp / "eq.csv").write_text("carrier,policy_year,line,claim_number,loss_date,status,paid_loss,outstanding_loss,valuation_date\n"
        "T,2024,GL,E1,2024-03-01,closed,600,0,2026-09-30\nT,2024,GL,E2,2024-03-01,closed,400,0,2026-09-30\n")
    run([RET, "eq.csv", "--retentions", "1000", "--aggregate", "1000", "--immature-years", "none", "--out", "eq"], tmp)
    eq = json.loads((tp / "eq.json").read_text())["summary"][0]
    check(eq["years_aggregate_hit"] == 1 and eq["total_retained"] == 1000,
          f"aggregate reached exactly not counted as hit: {eq}")
    check(fails([RET, "eq.csv", "--retentions", "1000", "--immature-years", "20245"], "not in the replay years"),
          "mistyped immature year accepted")
    (tp / "tc_bool.json").write_text(json.dumps({"periods": [{"label": "P", "premiums": True}]}))
    check(fails([TCOR, "tc_bool.json"], "Not a number"), "JSON true accepted as a premium")
    (tp / "tc_lbl.json").write_text(json.dumps({"periods": [{"label": 2025, "premiums": 1000}]}))
    run([TCOR, "tc_lbl.json", "--out", "tc_lbl_out"], tmp)
    check((tp / "tc_lbl_out.xlsx").exists(), "numeric period label crashed TCOR")
    pz = tp / "pz"
    (pz / "scripts").mkdir(parents=True)
    (pz / "plugins/p/skills/s").mkdir(parents=True)
    (pz / "scripts/package_zips.py").write_text((ROOT / "scripts/package_zips.py").read_text())
    (pz / "plugins/p/skills/s/SKILL.md").write_text("---\nname: s\ndescription: x\n---\n")
    (pz / "plugins/p/LICENSE").symlink_to("/etc/hostname")
    r = subprocess.run([sys.executable, "-I", str(pz / "scripts/package_zips.py")], capture_output=True, text=True)
    check(r.returncode != 0 and "symlink" in r.stderr and not (pz / "dist/s.zip").exists(),
          f"symlinked plugin LICENSE packaged: {r.stderr[-200:]}")

    # Codex round on 351f0af.
    (tp / "tc_null.json").write_text(json.dumps({"periods": [{"label": "P", "premiums": 1000, "source": None}]}))
    run([TCOR, "tc_null.json", "--out", "tc_null_out"], tmp)
    tn = json.loads((tp / "tc_null_out.json").read_text())["periods"][0]
    check("No source" in str(tn.get("open_items")), f"null source treated as sourced: {tn}")
    (tp / "nomt.csv").write_text("carrier,policy_year,line,claim_number,loss_date,status,paid_loss,outstanding_loss,"
        "carrier_incurred,valuation_date\nT,2024,GL,N1,2024-03-01,open,,,,2026-09-30\n"
        "T,2024,GL,N2,2024-03-01,closed,,,900,2026-09-30\n")
    run([LR, "nomt.csv", "--as-of", "2026-10-24", "--out", "nomt"], tmp)
    note = json.loads((tp / "nomt.json").read_text())["totals"]["paid_outstanding_note"] or ""
    check("understated" in note and "complete" not in note.replace("incomplete", ""),
          f"missing amounts described as complete incurred: {note}")
    (tp / "noyr.csv").write_text("carrier,policy_year,line,claim_number,loss_date,status,paid_loss,outstanding_loss,valuation_date\nT,,GL,Y1,2024-03-01,closed,100,0,2026-09-30\n")
    (tp / "noyr_p.csv").write_text("policy_year,line,earned_premium\nabc,GL,1000\n")
    run([LR, "noyr.csv", "--premium", "noyr_p.csv", "--as-of", "2026-10-24", "--out", "noyr"], tmp)
    check((tp / "noyr.json").exists(), "report with no readable policy year crashed")
    (tp / "dup.csv").write_text("carrier,policy_year,line,claim_number,loss_date,status,paid_loss,Paid_Loss ,"
        "outstanding_loss,valuation_date\nT,2024,GL,D1,2024-03-01,closed,100,5000,0,2026-09-30\n")
    check(fails([LR, "dup.csv"], "more than once"), "duplicate paid_loss column silently dropped")
    check(fails([RET, "dup.csv", "--retentions", "1000"], "more than once"), "replay accepted duplicate column")
    (tp / "eff.csv").write_text("carrier,policy_year,policy_effective,line,claim_number,loss_date,status,paid_loss,"
        "outstanding_loss,valuation_date\nT,2024,2024-13-45,WCC,F1,2024-03-01,closed,100,0,2026-09-30\n")
    run([LR, "eff.csv", "--as-of", "2026-10-24", "--out", "eff"], tmp)
    ef = json.loads((tp / "eff.json").read_text())["flag_counts"]
    check(ef.get("unreadable_date") == 1, f"unreadable policy_effective not flagged: {ef}")
    check(ef.get("unknown_line") == 1, f"line typo WCC not flagged: {ef}")
    (tp / "scn.csv").write_text("carrier,policy_year,line,claim_number,loss_date,status,paid_loss,outstanding_loss,"
        "carrier_incurred,valuation_date\nT,2024,WC,W9,2024-03-01,open,,,,\n"
        "T,2024,AL,A9,2024-03-01,closed,500,0,,2026-09-30\n")
    run([RET, "scn.csv", "--retentions", "1000", "--lines", "AL", "--immature-years", "none", "--out", "scn"], tmp)
    sn = " ".join(json.loads((tp / "scn.json").read_text())["notes"])
    check("W9" not in sn, f"AL-only replay carries notes about an excluded WC claim: {sn}")

    # Codex round on 004928f.
    (tp / "keep.json").write_text(json.dumps({"periods": [{"label": "P", "premiums": 1000, "source": "s"}]}))
    before = (tp / "keep.json").read_text()
    check(fails([TCOR, "keep.json", "--out", "keep"], "would overwrite") and (tp / "keep.json").read_text() == before,
          "TCOR overwrote its own input JSON")
    check(fails([LR, "mm.csv", "--as-of", "2026-13-45"], "--as-of"), "malformed --as-of accepted")
    check(fails([LR, "noyr.csv", "--as-of", "yesterday"], "--as-of"), "malformed --as-of accepted on undated file")

    # Codex round on a0903ea.
    (tp / "tie2.csv").write_text("carrier,policy_year,line,claim_number,loss_date,status,paid_loss,outstanding_loss,valuation_date\n"
        "T,2024,GL,K1,2024-03-01,closed,300,0,2026-09-30\nT,2024,GL,K1,2024-03-01,closed,900,0,2026-09-30\n"
        "T,2024,GL,K2,2024-03-01,closed,111,0,\nT,2024,GL,K2,2024-03-01,closed,999,0,\n")
    run([LR, "tie2.csv", "--as-of", "2026-10-24", "--out", "tie2"], tmp)
    run([RET, "tie2.csv", "--retentions", "100000", "--immature-years", "none", "--out", "tie2_ret"], tmp)
    lr_inc = json.loads((tp / "tie2.json").read_text())["totals"]["incurred"]
    ret_tot = json.loads((tp / "tie2_ret.json").read_text())["summary"][0]["total_retained"]
    check(lr_inc == ret_tot == 411, f"summary ({lr_inc}) and replay ({ret_tot}) kept different duplicate rows")
    (tp / "shift.csv").write_text("carrier,policy_year,line,claim_number,loss_date,status,paid_loss,outstanding_loss,valuation_date\nT,2024,GL,S1,2024-03-01,closed,1,000,0,2026-09-30\n")
    check(fails([LR, "shift.csv"], "different number of fields"), "unquoted 1,000 shifted claim columns")
    check(fails([RET, "shift.csv", "--retentions", "1000"], "different number of fields"), "replay accepted shifted row")
    (tp / "yr5.csv").write_text("carrier,policy_year,line,claim_number,loss_date,status,paid_loss,outstanding_loss,valuation_date\n"
        "T,20245,GL,Y5,2024-03-01,closed,100,0,2026-09-30\nT,2024,GL,Y6,2024-03-01,closed,200,0,2026-09-30\n")
    run([RET, "yr5.csv", "--retentions", "1000", "--immature-years", "none", "--out", "yr5"], tmp)
    yrs = [r["policy_year"] for r in json.loads((tp / "yr5.json").read_text())["by_year"]]
    check(yrs == [2024], f"policy year 20245 became a replay year: {yrs}")
    run([LR, "yr5.csv", "--as-of", "2026-10-24", "--out", "yr5_lr"], tmp)
    y5 = json.loads((tp / "yr5_lr.json").read_text()) if (tp / "yr5_lr.json").exists() else {"flag_counts": {}}
    check(y5["flag_counts"].get("missing_field") == 1,
          "policy year 20245 not flagged by the loss-run script")
    (tp / "tc_list.json").write_text(json.dumps({"periods": [{"label": "P", "premiums": 1000, "admin": []}]}))
    run([TCOR, "tc_list.json", "--out", "tc_list_out"], tmp)
    tl = json.loads((tp / "tc_list_out.json").read_text())["periods"][0] if (tp / "tc_list_out.json").exists() else {}
    check("Administration not supplied" in str(tl.get("open_items")), f"empty list component crashed TCOR: {tl}")
    (tp / "tc_list2.json").write_text(json.dumps({"periods": [{"label": "P", "premiums": 1000, "admin": [5]}]}))
    check(fails([TCOR, "tc_list2.json"], "not a list"), "list component accepted")

    # Codex round on 850eaa4.
    (tp / "tc_dupk.json").write_text('{"periods": [{"label": "P", "premiums": {"WC": 1000, "WC": 50}}]}')
    check(fails([TCOR, "tc_dupk.json"], "repeats the key"), "duplicate JSON key silently dropped a premium")
    (tp / "pl_prem.csv").write_text("policy_year,line,earned_premium\n2024,GL,10000\n2024,GLL,5000\n")
    run([LR, "mm.csv", "--premium", "pl_prem.csv", "--as-of", "2026-10-24", "--out", "pl"], tmp)
    pl = json.loads((tp / "pl.json").read_text())
    check(pl["flag_counts"].get("premium_unknown_line") == 1 and pl["totals"]["earned_premium"] == 10000,
          f"premium line typo summed into the denominator: {pl['flag_counts']}, {pl['totals'].get('earned_premium')}")
    check(fails([RET, "mm.csv", "--retentions", "1000", "--years", "20245"], "four-digit"), "--years 20245 accepted")
    for flag_name in ("--lines", "--aggregate", "--immature-years"):
        for empty in ("", ","):
            check(fails([RET, "mm.csv", "--retentions", "1000", flag_name, empty], "is empty"),
                  f"empty {flag_name} {empty!r} accepted")

    # Codex round on 55645aa.
    (tp / "half.csv").write_text("carrier,policy_year,line,claim_number,loss_date,status,paid_loss,outstanding_loss,valuation_date\nT,2024,GL,H1,2024-03-01,open,100,,2026-09-30\n")
    run([LR, "half.csv", "--as-of", "2026-10-24", "--out", "half"], tmp)
    ht = json.loads((tp / "half.json").read_text())["totals"]
    check(ht["outstanding"] is None and ht["paid"] == 100 and ht["incurred"] == 100,
          f"blank outstanding reported as zero: {ht}")
    check(fails([RET, "mm.csv", "--retentions", "1000", "--lines", "WCC"], "schema line code"), "--lines WCC accepted")
    sl = tp / "sl"
    (sl / "scripts").mkdir(parents=True)
    (sl / "outside/real").mkdir(parents=True)
    (sl / "plugins/p/skills").mkdir(parents=True)
    (sl / "scripts/package_zips.py").write_text((ROOT / "scripts/package_zips.py").read_text())
    (sl / "outside/real/SKILL.md").write_text("---\nname: real\ndescription: x\n---\n")
    (sl / "outside/real/secret.txt").write_text("not for packaging")
    (sl / "plugins/p/skills/s").symlink_to(sl / "outside/real", target_is_directory=True)
    r = subprocess.run([sys.executable, "-I", str(sl / "scripts/package_zips.py")], capture_output=True, text=True)
    check(r.returncode != 0 and "symlink" in r.stderr and not (sl / "dist/s.zip").exists(),
          f"symlinked skill folder packaged: {r.stderr[-200:]}")

    # Codex round on f8994dc.
    al = tp / "al"
    (al / "scripts").mkdir(parents=True)
    (al / "outside/skills/leak").mkdir(parents=True)
    (al / "plugins").mkdir(parents=True)
    (al / "scripts/package_zips.py").write_text((ROOT / "scripts/package_zips.py").read_text())
    (al / "outside/skills/leak/SKILL.md").write_text("---\nname: leak\ndescription: x\n---\n")
    (al / "outside/skills/leak/secret.txt").write_text("not for packaging")
    (al / "plugins/p").symlink_to(al / "outside", target_is_directory=True)
    r = subprocess.run([sys.executable, "-I", str(al / "scripts/package_zips.py")], capture_output=True, text=True)
    check(r.returncode != 0 and "symlink" in r.stderr and not (al / "dist/leak.zip").exists(),
          f"symlinked plugin folder packaged: {r.stderr[-200:]}")
    (tp / "wcc.csv").write_text("carrier,policy_year,line,claim_number,loss_date,status,paid_loss,outstanding_loss,valuation_date\n"
        "T,2024,WCC,C1,2024-03-01,closed,5000,0,2026-09-30\nT,2024,WC,C2,2024-03-01,closed,100,0,2026-09-30\n")
    check(fails([RET, "wcc.csv", "--retentions", "1000", "--lines", "WC"], "not schema codes"),
          "claim line typo vanished from a WC replay")
    (tp / "rec.csv").write_text("carrier,policy_year,line,claim_number,loss_date,status,paid_loss,outstanding_loss,"
        "recoveries,valuation_date\nT,2024,GL,R1,2024-03-01,closed,100,0,500,2026-09-30\n"
        "T,2024,GL,R2,2024-03-01,closed,300,0,0,2026-09-30\n")
    run([LR, "rec.csv", "--as-of", "2026-10-24", "--out", "rec"], tmp)
    run([RET, "rec.csv", "--retentions", "100000", "--immature-years", "none", "--out", "rec_ret"], tmp)
    rc = json.loads((tp / "rec.json").read_text())
    rr = json.loads((tp / "rec_ret.json").read_text())
    check(rc["flag_counts"].get("net_negative_incurred") == 1 and rc["totals"]["incurred"] == 300
          == rr["summary"][0]["total_retained"],
          f"net-negative claim: summary {rc['totals']['incurred']} vs replay {rr['summary'][0]['total_retained']}")

    # Codex round on 9c33941.
    (tp / "blank.csv").write_text("carrier,policy_year,line,claim_number,loss_date,status,paid_loss,outstanding_loss,valuation_date\nT,2024,GL,B1,2024-03-01,closed,100,0,2026-09-30\n\n\n"
        "T,2024,GL,B2,2024-03-01,bogus,100,0,2026-09-30\n")
    run([LR, "blank.csv", "--as-of", "2026-10-24", "--out", "blank"], tmp)
    bf = openpyxl.load_workbook(tp / "blank.xlsx")["Data_Flags"]
    hdr = [c.value for c in bf[1]]
    rows_flagged = [r[hdr.index("row")] for r in bf.iter_rows(min_row=2, values_only=True) if r[hdr.index("flag")] == "bad_status"]
    check(rows_flagged == [5], f"data flag points at the wrong line after blank lines: {rows_flagged}")
    check(fails([RET, "mm.csv", "--retentions", "25,000.50"], "thousands separators"), "25,000.50 split into $25 and $0.50")

    # Codex round on 4620519.
    for bad_col in ([1000], 1000):
        (tp / "tc_col2.json").write_text(json.dumps({"periods": [{"label": "P", "premiums": 1000, "collateral": bad_col}]}))
        check(fails([TCOR, "tc_col2.json"], "collateral must be an object"), f"collateral {bad_col!r} crashed TCOR")
    (tp / "effy.csv").write_text("carrier,policy_year,policy_effective,policy_number,line,claim_number,loss_date,status,"
        "paid_loss,outstanding_loss,valuation_date\nT,2024,2023-01-01,P1,GL,E1,2023-06-01,closed,100,0,2026-09-30\n")
    run([LR, "effy.csv", "--as-of", "2026-10-24", "--out", "effy"], tmp)
    ey = json.loads((tp / "effy.json").read_text())["flag_counts"]
    check(ey.get("effective_year_mismatch") == 1, f"effective date in the wrong year not flagged: {ey}")
    (tp / "oldv.csv").write_text("carrier,policy_year,policy_effective,policy_number,line,claim_number,loss_date,status,"
        "paid_loss,outstanding_loss,valuation_date\n"
        "T,2024,2024-01-01,P1,GL,O1,2024-03-01,closed,100,0,2025-12-31\n"
        "T,2024,2024-01-01,P1,GL,O2,2024-04-01,closed,100,0,2026-02-28\n")
    run([LR, "oldv.csv", "--as-of", "2026-03-01", "--out", "oldv"], tmp)
    ov = json.loads((tp / "oldv.json").read_text())["by_year"][0]
    check(ov["maturity_months"] == 23 and ov["immature"] is True,
          f"policy maturity used the newest valuation instead of the oldest: {ov['maturity_months']}")
    dz = tp / "dz"
    (dz / "scripts").mkdir(parents=True)
    for plug in ("a", "b"):
        (dz / f"plugins/{plug}/skills/same").mkdir(parents=True)
        (dz / f"plugins/{plug}/skills/same/SKILL.md").write_text(f"---\nname: same\ndescription: {plug}\n---\n")
    (dz / "scripts/package_zips.py").write_text((ROOT / "scripts/package_zips.py").read_text())
    r = subprocess.run([sys.executable, "-I", str(dz / "scripts/package_zips.py")], capture_output=True, text=True)
    check(r.returncode != 0 and "more than one plugin" in r.stderr, f"duplicate skill names overwrote a ZIP: {r.stderr[-200:]}")

    # Codex round on 8ad2f26.
    (tp / "dec.csv").write_text("carrier,policy_year,line,claim_number,loss_date,status,paid_loss,outstanding_loss,valuation_date\nT,2024,GL,D9,2024-12-20,closed,100,0,2026-12-15\n")
    run([LR, "dec.csv", "--as-of", "2026-12-16", "--out", "dec"], tmp)
    dy = json.loads((tp / "dec.json").read_text())["by_year"][0]
    check(dy["immature"] is True and dy["maturity_months"] == 23,
          f"unknown December start overstated maturity: {dy['maturity_months']}")
    for bad in ('{"periods": {"label": "P", "premiums": 1}}', '{"periods": ["P"]}', '[1]'):
        (tp / "tc_shape.json").write_text(bad)
        check(fails([TCOR, "tc_shape.json"], "list of objects"), f"malformed periods accepted: {bad}")
    run([LR, "mm.csv", "--as-of", "2026-10-24", "--out", "norec"], tmp)
    check(json.loads((tp / "norec.json").read_text())["totals"].get("recoveries_note"),
          "missing recoveries column not mentioned")

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
