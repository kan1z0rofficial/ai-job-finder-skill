import contextlib
import csv
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import format_results  # noqa: E402

SAMPLE = {
    "query": {"profession": "сварщик", "city": "Тюмень", "date": "2026-11-10"},
    "vacancies": [
        {
            "title": "Сварщик",
            "company": "ООО «Пример»",
            "city": "Тюмень",
            "work_format": "fly-in-fly-out",
            "experience": "1-3",
            "salary_from": 150000,
            "salary_to": 180000,
            "currency": "RUR",
            "gross": False,
            "source": "hh.ru",
            "published_at": "2026-11-08",
            "rotation": "60/30",
            "url": "https://hh.ru/vacancy/1",
        },
        {
            "title": "Сварщик | ночная смена",
            "company": "Завод",
            "city": "Тюмень",
            "work_format": "shift",
            "salary_from": 90000,
            "salary_to": None,
            "currency": "RUR",
            "source": "Rabota.ru",
            "url": "https://example.com/2",
        },
        {
            "title": "Сварщик",
            "company": "Без зарплаты",
            "source": "SuperJob",
        },
    ],
}


class MathTest(unittest.TestCase):
    def test_median_odd(self):
        self.assertEqual(format_results.median([10, 30, 20]), 20)

    def test_median_even(self):
        self.assertEqual(format_results.median([10, 20, 30, 40]), 25)

    def test_median_empty(self):
        self.assertIsNone(format_results.median([]))

    def test_salary_midpoint(self):
        self.assertEqual(format_results.salary_midpoint({"salary_from": 100, "salary_to": 200}), 150)
        self.assertEqual(format_results.salary_midpoint({"salary_from": 100}), 100)
        self.assertEqual(format_results.salary_midpoint({"salary_to": 200}), 200)
        self.assertIsNone(format_results.salary_midpoint({}))

    def test_summary(self):
        summary = format_results.summarize(SAMPLE["vacancies"])
        self.assertEqual(summary["found"], 3)
        self.assertEqual(summary["with_salary"], 2)
        self.assertEqual(summary["median_salary"], 127500)


class FormatTest(unittest.TestCase):
    def test_salary_cell(self):
        self.assertEqual(format_results.salary_cell(SAMPLE["vacancies"][0]), "150 000 – 180 000 ₽ на руки")
        self.assertEqual(format_results.salary_cell(SAMPLE["vacancies"][1]), "от 90 000 ₽")
        self.assertEqual(format_results.salary_cell(SAMPLE["vacancies"][2]), "не указана")

    def test_markdown_has_header_and_escapes_pipes(self):
        summary = format_results.summarize(SAMPLE["vacancies"])
        text = format_results.to_markdown(SAMPLE["vacancies"], summary, SAMPLE["query"])
        self.assertIn("| # | Должность |", text)
        self.assertIn("Сварщик \\| ночная смена", text)
        self.assertIn("Итог: найдено 3", text)
        self.assertIn("дата поиска 2026-11-10", text)

    def test_csv_columns_and_values(self):
        text = format_results.to_csv(SAMPLE["vacancies"])
        rows = list(csv.DictReader(io.StringIO(text)))
        self.assertEqual(list(rows[0].keys()), format_results.CSV_COLUMNS)
        self.assertEqual(rows[0]["title"], "Сварщик")
        self.assertEqual(rows[0]["gross"], "false")
        self.assertEqual(rows[2]["salary_from"], "")

    def test_json_recomputes_summary(self):
        payload = format_results.normalize({"vacancies": SAMPLE["vacancies"], "summary": {"found": 99}})
        self.assertEqual(payload["summary"]["found"], 3)
        self.assertEqual(payload["summary"]["median_salary"], 127500)


class MainTest(unittest.TestCase):
    def run_main(self, argv):
        out = io.StringIO()
        err = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = format_results.main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_markdown_from_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "results.json"
            path.write_text(json.dumps(SAMPLE, ensure_ascii=False), encoding="utf-8")
            code, out, _ = self.run_main(["--input", str(path), "--format", "markdown"])
        self.assertEqual(code, 0)
        self.assertIn("Итог: найдено 3", out)

    def test_csv_to_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "results.json"
            target = Path(tmp) / "out.csv"
            source.write_text(json.dumps(SAMPLE, ensure_ascii=False), encoding="utf-8")
            code, _, err = self.run_main(
                ["--input", str(source), "--format", "csv", "--output", str(target)]
            )
            content = target.read_text(encoding="utf-8")
        self.assertEqual(code, 0)
        self.assertIn("Записано", err)
        self.assertTrue(content.startswith("title,company"))

    def test_strict_validation_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            path.write_text(json.dumps({"vacancies": [{"company": "X"}]}), encoding="utf-8")
            code, _, err = self.run_main(["--input", str(path), "--strict"])
        self.assertEqual(code, 1)
        self.assertIn("обязательно", err)

    def test_invalid_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            path.write_text("{", encoding="utf-8")
            code, _, _ = self.run_main(["--input", str(path)])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
