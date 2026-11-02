#!/usr/bin/env python3
"""Behavior checks for pipeline integrity and deterministic action prioritization."""
import csv
import io
import json
import os
import tempfile
import unittest
from datetime import date
from pathlib import Path

from analyze_pipeline import FIELDS, ValidationError, analyze, main, read_opportunities, render_markdown

AS_OF = date(2026, 11, 2)


def source(*rows):
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=FIELDS)
    writer.writeheader()
    for index, values in enumerate(rows):
        row = dict.fromkeys(FIELDS, "")
        row.update(opportunity_id=str(index + 1), account="Demo account", stage="qualified",
                   owner="Owner", next_action="Schedule discovery", due_date="2026-11-10",
                   last_contact_date="2026-11-01", source_url="https://example.com/evidence", verified_at="2026-11-02")
        row.update(values)
        writer.writerow(row)
    return buffer.getvalue()


def report(*rows):
    return analyze(read_opportunities(source(*rows), AS_OF), AS_OF)


class PipelineTests(unittest.TestCase):
    def test_empty_header_only(self):
        result = report()
        self.assertEqual(result["open_opportunities"], 0)
        self.assertEqual(result["currency_totals"], [])
        self.assertEqual(result["action_queue"], [])
        self.assertEqual(sum(result["stage_counts"].values()), 0)
        with self.assertRaises(ValidationError):
            read_opportunities("", AS_OF)

    def test_rejects_duplicate_ids_including_closed_rows(self):
        with self.assertRaisesRegex(ValidationError, "duplicate opportunity_id"):
            report({"opportunity_id": "a"}, {"opportunity_id": "a", "stage": "lost"})

    def test_unknowns_and_zero_are_distinct(self):
        result = report({"annual_revenue": "0", "currency": "USD", "probability": "0"},
                        {"annual_revenue": "", "currency": "USD", "probability": ""},
                        {"annual_revenue": "", "currency": "EUR"})
        eur, usd = result["currency_totals"]
        self.assertIsNone(eur["known_annual_revenue"])
        self.assertIsNone(eur["weighted_annual_revenue"])
        self.assertEqual(usd["known_annual_revenue"], "0")
        self.assertEqual(usd["weighted_annual_revenue"], "0")
        self.assertEqual(usd["known_revenue_opportunities"], 1)
        self.assertEqual(usd["weighted_opportunities"], 1)
        self.assertEqual(usd["weighted_opportunity_coverage_percent"], "50.00")
        self.assertIsNone(usd["weighted_revenue_coverage_percent"])
        self.assertIsNone(usd["top_account"]["known_revenue_share_percent"])
        self.assertEqual(result["data_quality"]["unknown_revenue"], 2)

    def test_mixed_currencies_exact_weighting_and_coverage(self):
        result = report({"account": "Alpha", "annual_revenue": "100.10", "currency": "USD", "probability": "0.5"},
                        {"account": "alpha", "annual_revenue": "50", "currency": "USD"},
                        {"account": "Beta", "annual_revenue": "49.90", "currency": "USD", "probability": "1"},
                        {"account": "Gamma", "annual_revenue": "300", "currency": "EUR", "probability": "0.1"})
        eur, usd = result["currency_totals"]
        self.assertEqual(eur["known_annual_revenue"], "300")
        self.assertEqual(eur["weighted_annual_revenue"], "30.0")
        self.assertEqual(usd["known_annual_revenue"], "200.00")
        self.assertEqual(usd["weighted_annual_revenue"], "99.950")
        self.assertEqual(usd["weighted_opportunities"], 2)
        self.assertEqual(usd["weighted_opportunity_coverage_percent"], "66.67")
        self.assertEqual(usd["weighted_revenue_coverage_percent"], "75.00")
        self.assertEqual(usd["top_account"]["account"], "Alpha")
        self.assertEqual(usd["top_account"]["known_annual_revenue"], "150.10")
        self.assertEqual(usd["top_account"]["known_revenue_share_percent"], "75.05")

    def test_closed_opportunities_do_not_inflate_open_metrics(self):
        result = report({"stage": "won", "annual_revenue": "999", "currency": "USD", "due_date": "2026-01-01", "renewal_date": "2026-11-03"},
                        {"stage": "lost", "annual_revenue": "999", "currency": "USD"},
                        {"annual_revenue": "1", "currency": "USD"})
        self.assertEqual(result["open_opportunities"], 1)
        self.assertEqual(result["closed_opportunities"], 2)
        self.assertEqual(result["currency_totals"][0]["known_annual_revenue"], "1")
        self.assertEqual(result["action_queue"], [])
        self.assertEqual(result["renewal_windows"]["0_30_days"], [])
        self.assertEqual(result["stage_counts"]["won"], 1)

    def test_dates_are_calendar_dates_and_future_history_rejected(self):
        for bad in ("2026-02-30", "2026-2-01", "2026-11-02T12:00:00Z", "11/02/2026"):
            with self.subTest(bad=bad), self.assertRaises(ValidationError):
                report({"due_date": bad})
        for field in ("last_contact_date", "verified_at"):
            with self.subTest(field=field), self.assertRaisesRegex(ValidationError, "after as-of"):
                report({field: "2026-11-03"})
        result = report({"due_date": "2028-02-29", "renewal_date": "2028-02-29"})
        self.assertEqual(len(result["renewal_windows"]["over_120_days"]), 1)

    def test_invalid_numbers_and_currency_fail_instead_of_coercing(self):
        for field, invalid in (("annual_revenue", "NaN"), ("annual_revenue", "Infinity"),
                               ("annual_revenue", "-1"), ("annual_revenue", "1,000"),
                               ("annual_revenue", "=SUM(1,2)"), ("annual_revenue", "0.001"),
                               ("annual_revenue", "1000000000000001"), ("probability", "50%"),
                               ("probability", "1.1"), ("probability", "-0.5"),
                               ("probability", "0.123456789")):
            with self.subTest(field=field, invalid=invalid), self.assertRaises(ValidationError):
                report({field: invalid, "currency": "USD"})
        with self.assertRaisesRegex(ValidationError, "requires currency"):
            report({"annual_revenue": "5"})
        with self.assertRaises(ValidationError):
            report({"currency": "usd"})

    def test_action_priority_and_multiple_flags(self):
        result = report({"opportunity_id": "stale", "last_contact_date": "2026-10-19"},
                        {"opportunity_id": "missing", "next_action": ""},
                        {"opportunity_id": "today", "due_date": "2026-11-02"},
                        {"opportunity_id": "overdue", "due_date": "2026-11-01", "next_action": ""},
                        {"opportunity_id": "fresh", "last_contact_date": "2026-10-20"})
        self.assertEqual([x["opportunity_id"] for x in result["action_queue"]], ["overdue", "today", "missing", "stale"])
        self.assertEqual(result["action_queue"][0]["flags"], ["overdue", "missing_next_action"])
        self.assertEqual(result["action_queue"][0]["days_overdue"], 1)
        self.assertEqual(result["action_queue"][-1]["days_since_contact"], 14)

    def test_renewal_boundaries_no_overlap(self):
        from datetime import timedelta
        distances = [-1, 0, 30, 31, 60, 61, 90, 91, 120, 121]
        result = report(*({"renewal_date": (AS_OF + timedelta(days=delta)).isoformat()} for delta in distances))
        self.assertEqual([len(x) for x in result["renewal_windows"].values()], [1, 2, 2, 2, 2, 1])

    def test_text_is_not_executed_and_unsafe_url_rejected(self):
        result = report({"account": "=SUM(A1:A2)|<script>", "next_action": "", "due_date": "2026-11-01"})
        self.assertEqual(result["action_queue"][0]["account"], "=SUM(A1:A2)|<script>")
        text = render_markdown(result)
        self.assertIn("\\|&lt;script&gt;", text)
        self.assertNotIn("<script>", text)
        for url in ("javascript:alert(1)", "file:///tmp/x", "https://user:pass@example.com", "http://"):
            with self.subTest(url=url), self.assertRaises(ValidationError):
                report({"source_url": url})

    def test_invalid_headers_and_rows_fail(self):
        with self.assertRaises(ValidationError):
            read_opportunities("opportunity_id,account\n1,A\n", AS_OF)
        with self.assertRaises(ValidationError):
            read_opportunities(source() + "1,A,qualified\n", AS_OF)
        with self.assertRaises(ValidationError):
            report({"stage": "maybe"})
        with self.assertRaises(ValidationError):
            report({"account": ""})
        header = source().strip()
        with self.assertRaises(ValidationError):
            read_opportunities(header + ",account\n", AS_OF)

    def test_markdown_preserves_unknown_currency_denominator(self):
        text = render_markdown(report({}, {}, {"annual_revenue": "50", "currency": "USD"}))
        self.assertIn("| Currency not recorded | Unknown | Unknown | 0 / 2 |", text)
        self.assertIn("| USD | 50 | Unknown | 0 / 1 |", text)
        self.assertIn("0 / 1", render_markdown(report({})))

    def test_output_hardlink_cannot_overwrite_source(self):
        with tempfile.TemporaryDirectory() as folder:
            input_path = Path(folder) / "source.csv"
            alias = Path(folder) / "alias.json"
            original = source({})
            input_path.write_text(original, encoding="utf-8")
            os.link(input_path, alias)
            self.assertEqual(main(["--input", str(input_path), "--as-of", AS_OF.isoformat(), "--output", str(alias)]), 2)
            self.assertEqual(input_path.read_bytes().decode("utf-8"), original)

    def test_cli_runs_json_and_markdown_and_protects_input(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            input_path = path / "input.csv"
            output_path = path / "report.json"
            original = source({"annual_revenue": "100", "currency": "USD", "probability": "0.25"})
            input_path.write_text(original, encoding="utf-8")
            self.assertEqual(main(["--input", str(input_path), "--as-of", AS_OF.isoformat(), "--output", str(output_path)]), 0)
            self.assertEqual(json.loads(output_path.read_text())["currency_totals"][0]["weighted_annual_revenue"], "25.00")
            self.assertEqual(main(["--input", str(input_path), "--as-of", AS_OF.isoformat(), "--output", str(output_path), "--format", "markdown"]), 0)
            self.assertTrue(output_path.read_text().startswith("# IMC Growth Desk"))
            self.assertEqual(main(["--input", str(input_path), "--as-of", AS_OF.isoformat(), "--output", str(input_path)]), 2)
            self.assertEqual(input_path.read_bytes().decode("utf-8"), original)
            input_path.write_text(source({"probability": "2"}), encoding="utf-8")
            output_path.write_text("retain previous good report", encoding="utf-8")
            self.assertEqual(main(["--input", str(input_path), "--as-of", AS_OF.isoformat(), "--output", str(output_path)]), 2)
            self.assertEqual(output_path.read_text(), "retain previous good report")


if __name__ == "__main__":
    unittest.main()
