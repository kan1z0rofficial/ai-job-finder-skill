import contextlib
import csv
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import salary_report  # noqa: E402

VACANCIES = [
    {
        "title": "A",
        "company": "X",
        "city": "Москва",
        "work_format": "office",
        "experience": "1-3",
        "salary_from": 100000,
        "salary_to": 100000,
        "currency": "RUR",
        "source": "hh.ru",
        "published_at": "2026-10-01",
    },
    {
        "title": "B",
        "company": "X",
        "city": "Москва",
        "work_format": "office",
        "experience": "3-6",
        "salary_from": 180000,
        "salary_to": 220000,
        "currency": "RUR",
        "source": "hh.ru",
        "published_at": "2026-10-15",
    },
    {
        "title": "C",
        "company": "Y",
        "city": "Санкт-Петербург",
        "work_format": "remote",
        "experience": "1-3",
        "salary_from": 150000,
        "salary_to": 150000,
        "currency": "RUR",
        "source": "hh.ru",
        "published_at": "2026-11-01",
    },
    {
        "title": "D",
        "company": "X",
        "city": "Москва",
        "work_format": "remote",
        "experience": "none",
        "source": "hh.ru",
        "published_at": "2026-10-20",
    },
    {
        "title": "E",
        "company": "Z",
        "city": "Москва",
        "work_format": "office",
        "experience": "1-3",
        "salary_from": 1000,
        "salary_to": 1000,
        "currency": "USD",
        "source": "hh.ru",
        "published_at": "2026-10-10",
    },
]


class PercentileTest(unittest.TestCase):
    def test_edges(self):
        self.assertEqual(salary_report.percentile([10, 20, 30], 0), 10)
        self.assertEqual(salary_report.percentile([10, 20, 30], 1), 30)

    def test_interpolation(self):
        self.assertEqual(salary_report.percentile([10, 20, 30, 40], 0.25), 17.5)
        self.assertEqual(salary_report.percentile([10, 20, 30, 40], 0.5), 25)

    def test_empty(self):
        self.assertIsNone(salary_report.percentile([], 0.5))

    def test_invalid_ratio(self):
        with self.assertRaises(ValueError):
            salary_report.percentile([1], 1.5)


class DateFilterTest(unittest.TestCase):
    def test_period(self):
        selected, skipped = salary_report.filter_vacancies(
            VACANCIES,
            date_from=salary_report.parse_date("2026-10-01"),
            date_to=salary_report.parse_date("2026-10-31"),
        )
        self.assertEqual(len(selected), 4)
        self.assertEqual(skipped, 0)

    def test_missing_date_skipped_when_filtering(self):
        selected, skipped = salary_report.filter_vacancies(
            [{"title": "X", "company": "Y", "source": "hh.ru"}],
            date_from=salary_report.parse_date("2026-10-01"),
        )
        self.assertEqual(selected, [])
        self.assertEqual(skipped, 1)

    def test_invalid_date(self):
        with self.assertRaises(ValueError):
            salary_report.parse_date("10.10.2026")


class ReportTest(unittest.TestCase):
    def setUp(self):
        self.report = salary_report.build_report({"vacancies": VACANCIES}, currency="RUR")

    def test_overall(self):
        overall = self.report["overall"]
        self.assertEqual(overall["total"], 4)
        self.assertEqual(overall["with_salary"], 3)
        self.assertEqual(overall["median"], 150000)
        self.assertEqual(overall["p25"], 125000)
        self.assertEqual(overall["p75"], 175000)
        self.assertEqual(self.report["skipped_other_currency"], 1)

    def test_by_city(self):
        cities = {row["key"]: row for row in self.report["by_city"]}
        self.assertEqual(cities["Москва"]["total"], 3)
        self.assertEqual(cities["Москва"]["count"], 2)
        self.assertEqual(cities["Москва"]["median"], 150000)
        self.assertEqual(cities["Санкт-Петербург"]["count"], 1)

    def test_experience_order(self):
        keys = [row["key"] for row in self.report["by_experience"]]
        self.assertEqual(keys, ["none", "1-3", "3-6"])

    def test_markdown(self):
        text = salary_report.to_markdown(self.report)
        self.assertIn("# Отчёт по рынку зарплат", text)
        self.assertIn("## Общая статистика", text)
        self.assertIn("## По городам", text)
        self.assertIn("Медиана считается по серединам вилок", text)

    def test_csv(self):
        text = salary_report.to_csv(self.report)
        rows = list(csv.DictReader(io.StringIO(text)))
        self.assertEqual(rows[0]["segment"], "overall")
        self.assertEqual(rows[0]["median"], "150000")
        self.assertTrue(any(row["segment"] == "city" for row in rows))

    def test_json_serializable(self):
        text = json.dumps(self.report, ensure_ascii=False)
        self.assertIn("by_city", text)


class MainTest(unittest.TestCase):
    def run_main(self, argv):
        out = io.StringIO()
        err = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = salary_report.main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_markdown_from_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "results.json"
            path.write_text(json.dumps({"vacancies": VACANCIES}, ensure_ascii=False), encoding="utf-8")
            code, out, _ = self.run_main(["--input", str(path)])
        self.assertEqual(code, 0)
        self.assertIn("Отчёт по рынку зарплат", out)

    def test_bad_period(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "results.json"
            path.write_text(json.dumps({"vacancies": VACANCIES}), encoding="utf-8")
            code, _, err = self.run_main(
                ["--input", str(path), "--from", "2026-11-01", "--to", "2026-10-01"]
            )
        self.assertEqual(code, 2)
        self.assertIn("позже", err)

    def test_bad_date(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "results.json"
            path.write_text(json.dumps({"vacancies": VACANCIES}), encoding="utf-8")
            code, _, err = self.run_main(["--input", str(path), "--from", "01.10.2026"])
        self.assertEqual(code, 2)
        self.assertIn("ГГГГ-ММ-ДД", err)


if __name__ == "__main__":
    unittest.main()
