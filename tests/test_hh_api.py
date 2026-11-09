import contextlib
import io
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import format_results  # noqa: E402
import hh_api  # noqa: E402

ITEM = {
    "id": "123456",
    "name": "Python-разработчик",
    "employer": {"name": "ООО «Пример»"},
    "area": {"name": "Москва"},
    "salary": {"from": 200000, "to": 250000, "currency": "RUR", "gross": False},
    "experience": {"id": "between1And3"},
    "schedule": {"id": "remote"},
    "published_at": "2026-11-08T10:00:00+0300",
    "alternate_url": "https://hh.ru/vacancy/123456",
}


class BuildParamsTest(unittest.TestCase):
    def test_maps_filters(self):
        params = hh_api.build_params(
            text="сварщик",
            area="95",
            experience="1-3",
            schedule="fly-in-fly-out",
            salary=150000,
            per_page=50,
        )
        self.assertEqual(params["experience"], "between1And3")
        self.assertEqual(params["schedule"], "flyInFlyOut")
        self.assertEqual(params["salary"], "150000")
        self.assertEqual(params["currency"], "RUR")
        self.assertEqual(params["only_with_salary"], "true")
        self.assertEqual(params["per_page"], "50")

    def test_exclude_words(self):
        params = hh_api.build_params(text="водитель", area="68", exclude=["продажи"])
        self.assertIn("NOT продажи", params["text"])

    def test_validation(self):
        with self.assertRaises(ValueError):
            hh_api.build_params(text=" ", area="1")
        with self.assertRaises(ValueError):
            hh_api.build_params(text="x", area="1", per_page=0)
        with self.assertRaises(ValueError):
            hh_api.build_params(text="x", area="1", salary=0)


class NormalizeTest(unittest.TestCase):
    def test_normalize_item(self):
        vacancy = hh_api.normalize_item(ITEM)
        self.assertEqual(vacancy["title"], "Python-разработчик")
        self.assertEqual(vacancy["company"], "ООО «Пример»")
        self.assertEqual(vacancy["work_format"], "remote")
        self.assertEqual(vacancy["experience"], "1-3")
        self.assertEqual(vacancy["salary_from"], 200000)
        self.assertEqual(vacancy["published_at"], "2026-11-08")
        self.assertEqual(vacancy["source"], "hh.ru")

    def test_normalized_item_passes_schema(self):
        vacancy = hh_api.normalize_item(ITEM)
        self.assertEqual(format_results.validate_vacancy(0, vacancy), [])

    def test_missing_salary_and_schedule(self):
        item = {"id": "1", "name": "Грузчик", "employer": {"name": "X"}}
        vacancy = hh_api.normalize_item(item)
        self.assertIsNone(vacancy["salary_from"])
        self.assertIsNone(vacancy["work_format"])
        self.assertIsNone(vacancy["experience"])


class SearchTest(unittest.TestCase):
    def test_paginates_and_limits(self):
        def make_item(index):
            return {**ITEM, "id": str(index), "name": f"Вакансия {index}"}

        pages = {
            0: {"found": 101, "pages": 2, "items": [make_item(i) for i in range(100)]},
            1: {"found": 101, "pages": 2, "items": [make_item(100)]},
        }
        calls = []

        def fake(params, token=None, timeout=30):
            calls.append(dict(params))
            return pages[int(params["page"])]

        result = hh_api.search(
            text="Python",
            area="Москва",
            limit=150,
            fetch=fake,
            delay=0,
        )
        self.assertEqual(len(result["vacancies"]), 101)
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0]["page"], "0")
        self.assertEqual(calls[1]["page"], "1")

    def test_stops_on_empty_page(self):
        calls = []

        def fake(params, token=None, timeout=30):
            calls.append(params)
            return {"found": 0, "pages": 0, "items": []}

        result = hh_api.search(text="x", area="Москва", limit=10, fetch=fake, delay=0)
        self.assertEqual(result["vacancies"], [])
        self.assertEqual(len(calls), 1)

    def test_query_work_format(self):
        def fake(params, token=None, timeout=30):
            return {"found": 1, "pages": 1, "items": [ITEM]}

        result = hh_api.search(
            text="Python",
            area="Москва",
            schedule="remote",
            limit=1,
            fetch=fake,
            delay=0,
        )
        self.assertEqual(result["query"]["work_format"], "remote")


class MainTest(unittest.TestCase):
    def test_dry_run(self):
        out = io.StringIO()
        err = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = hh_api.main(["--text", "сварщик", "--area", "95", "--dry-run"])
        self.assertEqual(code, 0)
        self.assertIn("api.hh.ru/vacancies", out.getvalue())
        self.assertIn("area=95", out.getvalue())

    def test_bad_limit(self):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(hh_api.main(["--text", "x", "--limit", "0"]), 2)


if __name__ == "__main__":
    unittest.main()
