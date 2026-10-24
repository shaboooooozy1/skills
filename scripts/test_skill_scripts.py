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

if failures:
    print("FAILED")
    for f in failures:
        print(" -", f)
    sys.exit(1)
print("All script tests passed.")
