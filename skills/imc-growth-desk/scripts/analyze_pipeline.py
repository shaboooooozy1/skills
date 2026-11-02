#!/usr/bin/env python3
"""Validate an opportunity CSV and produce deterministic, evidence-aware metrics.

Uses only the Python standard library. No network calls or input file mutations.
Money in JSON is represented as decimal strings to avoid binary float rounding.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
from collections import Counter
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlsplit

FIELDS = (
    "opportunity_id", "account", "stage", "owner", "annual_revenue", "currency",
    "probability", "next_action", "due_date", "last_contact_date", "renewal_date",
    "source_url", "verified_at",
)
STAGES = ("prospect", "discovery", "qualified", "proposal", "negotiation", "won", "lost")
CLOSED = {"won", "lost"}
RANKS = {"overdue": 0, "due_today": 1, "missing_next_action": 2,
         "missing_due_date": 3, "stale_contact": 4, "missing_contact_date": 5}


class ValidationError(ValueError):
    """A rejected input; no partial report should be relied upon."""


def parse_date(value: str, field: str, row: int | None = None) -> date | None:
    if not value:
        return None
    prefix = f"row {row}: " if row else ""
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValidationError(f"{prefix}{field} must use YYYY-MM-DD")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValidationError(f"{prefix}{field} is not a real calendar date") from exc


def decimal_value(value: str, field: str, row: int) -> Decimal | None:
    if not value:
        return None
    # Bound input magnitude/length as well as requiring a conventional number.
    if len(value) > 50 or not re.fullmatch(r"\+?\d+(?:\.\d+)?", value):
        raise ValidationError(f"row {row}: {field} must be a finite nonnegative decimal number")
    try:
        number = Decimal(value)
    except InvalidOperation as exc:
        raise ValidationError(f"row {row}: invalid {field}") from exc
    if not number.is_finite() or number < 0:
        raise ValidationError(f"row {row}: {field} must be finite and nonnegative")
    if field == "probability" and number > 1:
        raise ValidationError(f"row {row}: probability must be between 0 and 1")
    if field == "annual_revenue" and (number > Decimal("1000000000000000") or number.as_tuple().exponent < -2):
        raise ValidationError(f"row {row}: annual_revenue must be at most 1000000000000000 with at most two decimal places")
    if field == "probability" and number.as_tuple().exponent < -8:
        raise ValidationError(f"row {row}: probability must have at most eight decimal places")
    return number


def money(value: Decimal | None) -> str | None:
    return format(value, "f") if value is not None else None


def percentage(numerator: Decimal | int, denominator: Decimal | int) -> str | None:
    if not denominator:
        return None
    return format(Decimal(numerator) * Decimal(100) / Decimal(denominator), ".2f")


def read_opportunities(text: str, as_of: date) -> list[dict]:
    reader = csv.DictReader(io.StringIO(text.lstrip("\ufeff")), strict=True)
    if reader.fieldnames is None:
        raise ValidationError("CSV is empty; supply a header with all required columns")
    if len(reader.fieldnames) != len(set(reader.fieldnames)):
        raise ValidationError("CSV contains duplicate column names")
    missing = sorted(set(FIELDS) - set(reader.fieldnames))
    extra = sorted(set(reader.fieldnames) - set(FIELDS))
    if missing or extra:
        detail = []
        if missing:
            detail.append("missing columns: " + ", ".join(missing))
        if extra:
            detail.append("unexpected columns: " + ", ".join(extra))
        raise ValidationError("; ".join(detail))
    records = []
    seen = set()
    for raw in reader:
        row_number = reader.line_num
        if None in raw or any(value is None for value in raw.values()):
            raise ValidationError(f"row {row_number}: incorrect number of CSV fields")
        row = {key: value.strip() for key, value in raw.items()}
        if not any(row.values()):
            continue
        for key in ("opportunity_id", "account", "stage"):
            if not row[key]:
                raise ValidationError(f"row {row_number}: {key} is required")
        if row["opportunity_id"] in seen:
            raise ValidationError(f"row {row_number}: duplicate opportunity_id {row['opportunity_id']!r}")
        seen.add(row["opportunity_id"])
        if row["stage"] not in STAGES:
            raise ValidationError(f"row {row_number}: unknown stage {row['stage']!r}")
        row["annual_revenue"] = decimal_value(row["annual_revenue"], "annual_revenue", row_number)
        row["probability"] = decimal_value(row["probability"], "probability", row_number)
        if row["currency"] and not re.fullmatch(r"[A-Z]{3}", row["currency"]):
            raise ValidationError(f"row {row_number}: currency must be a three-letter uppercase currency code")
        if row["annual_revenue"] is not None and not row["currency"]:
            raise ValidationError(f"row {row_number}: known annual_revenue requires currency")
        for key in ("due_date", "last_contact_date", "renewal_date", "verified_at"):
            row[key] = parse_date(row[key], key, row_number)
        for key in ("last_contact_date", "verified_at"):
            if row[key] is not None and row[key] > as_of:
                raise ValidationError(f"row {row_number}: {key} is after as-of date")
        if row["source_url"]:
            url = urlsplit(row["source_url"])
            if url.scheme not in {"http", "https"} or not url.netloc or url.username or url.password:
                raise ValidationError(f"row {row_number}: source_url must be an http(s) URL without credentials")
        records.append(row)
    return records


def record_identity(row: dict) -> dict:
    return {key: row[key] for key in ("opportunity_id", "account", "stage", "owner", "source_url")}


def analyze(records: list[dict], as_of: date) -> dict:
    open_rows = [row for row in records if row["stage"] not in CLOSED]
    counts = Counter(row["stage"] for row in records)
    currencies = sorted({row["currency"] for row in open_rows if row["currency"]})
    totals = []
    for currency in currencies:
        rows = [row for row in open_rows if row["currency"] == currency]
        known = [row for row in rows if row["annual_revenue"] is not None]
        weighted = [row for row in known if row["probability"] is not None]
        amount = sum((row["annual_revenue"] for row in known), Decimal(0)) if known else None
        weighted_amount = sum((row["annual_revenue"] * row["probability"] for row in weighted), Decimal(0)) if weighted else None
        weighted_base = sum((row["annual_revenue"] for row in weighted), Decimal(0)) if weighted else None
        accounts = {}
        for row in known:
            key = row["account"].casefold()
            if key not in accounts:
                accounts[key] = {"account": row["account"], "known_annual_revenue": Decimal(0), "opportunities": 0}
            accounts[key]["known_annual_revenue"] += row["annual_revenue"]
            accounts[key]["opportunities"] += 1
        ranked = sorted(accounts.values(), key=lambda x: (-x["known_annual_revenue"], x["account"].casefold()))
        top = ranked[0] if ranked else None
        totals.append({
            "currency": currency, "open_opportunities": len(rows),
            "known_revenue_opportunities": len(known), "unknown_revenue_opportunities": len(rows) - len(known),
            "known_annual_revenue": money(amount),
            "weighted_annual_revenue": money(weighted_amount),
            "weighted_opportunities": len(weighted),
            "weighted_opportunity_coverage_percent": percentage(len(weighted), len(rows)),
            "known_revenue_with_explicit_probability": money(weighted_base),
            "weighted_revenue_coverage_percent": percentage(weighted_base or Decimal(0), amount or Decimal(0)),
            "top_account": ({"account": top["account"], "known_annual_revenue": money(top["known_annual_revenue"]),
                             "known_revenue_share_percent": percentage(top["known_annual_revenue"], amount or Decimal(0)),
                             "opportunities": top["opportunities"]} if top else None),
        })
    actions = []
    renewal_windows = {"past": [], "0_30_days": [], "31_60_days": [], "61_90_days": [], "91_120_days": [], "over_120_days": []}
    quality = {"missing_owner": 0, "missing_source_url": 0, "missing_verified_at": 0,
               "missing_next_action": 0, "missing_due_date": 0, "missing_contact_date": 0,
               "missing_renewal_date": 0, "unknown_revenue": 0, "missing_probability": 0,
               "missing_currency": 0}
    for row in open_rows:
        flags = []
        due = row["due_date"]
        if due is not None:
            if due < as_of:
                flags.append("overdue")
            elif due == as_of:
                flags.append("due_today")
        for field, flag in (("next_action", "missing_next_action"), ("due_date", "missing_due_date"),
                            ("last_contact_date", "missing_contact_date")):
            if not row[field]:
                flags.append(flag)
        contact_age = (as_of - row["last_contact_date"]).days if row["last_contact_date"] else None
        if contact_age is not None and contact_age >= 14:
            flags.append("stale_contact")
        if flags:
            flags.sort(key=lambda x: RANKS[x])
            actions.append({**record_identity(row), "priority": flags[0], "flags": flags,
                            "next_action": row["next_action"] or None, "due_date": due.isoformat() if due else None,
                            "days_overdue": max(0, (as_of - due).days) if due else None,
                            "days_since_contact": contact_age,
                            "verified_at": row["verified_at"].isoformat() if row["verified_at"] else None})
        for field, key in (("owner", "missing_owner"), ("source_url", "missing_source_url"),
                           ("verified_at", "missing_verified_at"), ("next_action", "missing_next_action"),
                           ("due_date", "missing_due_date"), ("last_contact_date", "missing_contact_date"),
                           ("renewal_date", "missing_renewal_date"), ("currency", "missing_currency")):
            quality[key] += int(not row[field])
        quality["unknown_revenue"] += int(row["annual_revenue"] is None)
        quality["missing_probability"] += int(row["probability"] is None)
        if row["renewal_date"]:
            days = (row["renewal_date"] - as_of).days
            bucket = ("past" if days < 0 else "0_30_days" if days <= 30 else "31_60_days" if days <= 60
                      else "61_90_days" if days <= 90 else "91_120_days" if days <= 120 else "over_120_days")
            renewal_windows[bucket].append({**record_identity(row), "renewal_date": row["renewal_date"].isoformat(), "days_until_renewal": days})
    actions.sort(key=lambda x: (RANKS[x["priority"]], x["due_date"] or "9999-12-31", x["account"].casefold(), x["opportunity_id"]))
    for rows in renewal_windows.values():
        rows.sort(key=lambda x: (x["days_until_renewal"], x["account"].casefold(), x["opportunity_id"]))
    return {
        "schema_version": 1, "as_of": as_of.isoformat(), "record_count": len(records),
        "open_opportunities": len(open_rows), "closed_opportunities": len(records) - len(open_rows),
        "stage_counts": {stage: counts[stage] for stage in STAGES}, "currency_totals": totals,
        "action_queue": actions, "renewal_windows": renewal_windows, "data_quality": quality,
        "methodology": [
            "Only prospect, discovery, qualified, proposal and negotiation stages contribute to open-pipeline metrics.",
            "Annual revenue means supplied annual agency revenue, not insurance premium. No commission rate is inferred.",
            "Money is represented as exact decimal strings. Unknown amounts remain null; currencies are never combined.",
            "Weighted revenue uses only explicit annual_revenue and probability; it is a scenario estimate, not a calibrated forecast.",
            "Coverage counts use all open opportunities in the currency as denominator; revenue coverage uses known revenue only.",
            "Account concentration uses case-insensitive exact account names and known annual revenue only, within each currency.",
            "Action priorities are operational rules, not likelihood scores. Stale contact means at least 14 calendar days.",
            "Provided dates are calendar dates. An overdue date is a recorded task date, not proof a reply remains unanswered.",
            "Renewal windows include open opportunities only. Past dates are reported without assuming that policies renewed.",
            "Missing evidence remains a data-quality gap. The tool does not verify source content or contact anyone.",
        ],
    }


def markdown_text(value: object) -> str:
    return str(value).replace("\\", "\\\\").replace("|", "\\|").replace("\r", " ").replace("\n", " ").replace("<", "&lt;").replace(">", "&gt;")


def render_markdown(report: dict) -> str:
    lines = ["# IMC Growth Desk", "", f"As of **{report['as_of']}**. Supplied opportunity data; not a verified mailbox scan.", "",
             f"**{report['open_opportunities']} open opportunities** · {report['closed_opportunities']} closed · {report['record_count']} total", "",
             "## Pipeline by currency", "", "| Currency | Known annual revenue | Weighted scenario | Weighted rows / open rows |", "|---|---:|---:|---:|"]
    for total in report["currency_totals"]:
        lines.append(f"| {total['currency']} | {total['known_annual_revenue'] if total['known_annual_revenue'] is not None else 'Unknown'} | {total['weighted_annual_revenue'] if total['weighted_annual_revenue'] is not None else 'Unknown'} | {total['weighted_opportunities']} / {total['open_opportunities']} |")
    unknown_currency = report["data_quality"]["missing_currency"]
    if unknown_currency:
        lines.append(f"| Currency not recorded | Unknown | Unknown | 0 / {unknown_currency} |")
    elif not report["currency_totals"]:
        lines.append("| No open opportunities | Unknown | Unknown | 0 / 0 |")
    lines.extend(["", "## Next actions", "", "| Account | Priority | Recorded next action | Due |", "|---|---|---|---|"])
    for action in report["action_queue"]:
        lines.append("| " + " | ".join(markdown_text(x) for x in (action["account"], action["priority"].replace("_", " "), action["next_action"] or "Define next action", action["due_date"] or "Not recorded")) + " |")
    if not report["action_queue"]:
        lines.append("| No flagged open opportunities | — | — | — |")
    lines.extend(["", "## Data quality", ""])
    lines.extend(f"- {key.replace('_', ' ').capitalize()}: {value}" for key, value in report["data_quality"].items())
    lines.extend(["", "## Method", ""])
    lines.extend(f"- {line}" for line in report["methodology"])
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="UTF-8 CSV with the documented 13 columns")
    parser.add_argument("--as-of", required=True, help="Report date, YYYY-MM-DD")
    parser.add_argument("--output", type=Path, help="Output file; defaults to stdout")
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    args = parser.parse_args(argv)
    try:
        as_of = parse_date(args.as_of, "as-of")
        if as_of is None:
            raise ValidationError("as-of is required")
        records = read_opportunities(args.input.read_text(encoding="utf-8-sig"), as_of)
        report = analyze(records, as_of)
        output = json.dumps(report, indent=2, ensure_ascii=False) + "\n" if args.format == "json" else render_markdown(report)
        if args.output:
            if args.output.resolve() == args.input.resolve() or (args.output.exists() and args.output.samefile(args.input)):
                raise ValidationError("output must not overwrite the input CSV")
            args.output.write_text(output, encoding="utf-8")
        else:
            sys.stdout.write(output)
    except (ValidationError, OSError, UnicodeError, csv.Error, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
