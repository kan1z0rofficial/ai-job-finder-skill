import contextlib
import io
import json
import sys
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import hh_url  # noqa: E402


class ResolveAreaTest(unittest.TestCase):
    def test_numeric_id_passthrough(self):
        self.assertEqual(hh_url.resolve_area("95", allow_network=False), "95")

    def test_known_city_offline(self):
        self.assertEqual(hh_url.resolve_area("Тюмень", allow_network=False), "95")
        self.assertEqual(hh_url.resolve_area("санкт-петербург", allow_network=False), "2")

    def test_alias_and_country(self):
        self.assertEqual(hh_url.resolve_area("РФ", allow_network=False), "113")
        self.assertEqual(hh_url.resolve_area("СПб", allow_network=False), "2")

    def test_city_prefix(self):
        self.assertEqual(hh_url.resolve_area("город Казань", allow_network=False), "88")

    def test_disambiguated_cities(self):
        self.assertEqual(hh_url.resolve_area("Киров", allow_network=False), "49")
        self.assertEqual(hh_url.resolve_area("Иваново", allow_network=False), "32")

    def test_base_name_strips_region(self):
        self.assertEqual(hh_url._base_name("Киров (Кировская область)"), "Киров")
        self.assertEqual(hh_url._base_name("Кемерово"), "Кемерово")

    def test_unknown_city_offline_raises(self):
        with self.assertRaises(LookupError):
            hh_url.resolve_area("Гадюкино", allow_network=False)


class BuildParamsTest(unittest.TestCase):
    def test_basic_params(self):
        params = hh_url.build_params(text="сварщик", area="95")
        self.assertEqual(params["text"], "сварщик")
        self.assertEqual(params["area"], "95")
        self.assertEqual(params["page"], "0")
        self.assertEqual(params["items_on_page"], "50")

    def test_experience_and_schedule_mapped(self):
        params = hh_url.build_params(
            text="сварщик",
            area="95",
            experience="1-3",
            schedule="fly-in-fly-out",
        )
        self.assertEqual(params["experience"], "between1And3")
        self.assertEqual(params["schedule"], "flyInFlyOut")

    def test_salary_enables_only_with_salary(self):
        params = hh_url.build_params(text="Python", area="1", salary=200000)
        self.assertEqual(params["salary"], "200000")
        self.assertEqual(params["currency_code"], "RUR")
        self.assertEqual(params["only_with_salary"], "true")

    def test_exclude_words(self):
        params = hh_url.build_params(text="водитель", area="68", exclude=["продажи", "сетевой маркетинг"])
        self.assertIn('NOT продажи', params["text"])
        self.assertIn('NOT "сетевой маркетинг"', params["text"])

    def test_invalid_input(self):
        with self.assertRaises(ValueError):
            hh_url.build_params(text="  ", area="1")
        with self.assertRaises(ValueError):
            hh_url.build_params(text="x", area="1", salary=0)
        with self.assertRaises(ValueError):
            hh_url.build_params(text="x", area="1", page=-1)

    def test_url_is_parseable(self):
        params = hh_url.build_params(text="Python-разработчик", area="1", schedule="remote")
        parsed = urlparse(hh_url.build_url(params))
        self.assertEqual(parsed.scheme, "https")
        self.assertEqual(parsed.netloc, "hh.ru")
        self.assertEqual(parsed.path, "/search/vacancy")
        query = parse_qs(parsed.query)
        self.assertEqual(query["text"], ["Python-разработчик"])
        self.assertEqual(query["schedule"], ["remote"])


class MainTest(unittest.TestCase):
    def test_json_output(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = hh_url.main(
                ["--text", "сварщик", "--area", "95", "--schedule", "office", "--json", "--offline"]
            )
        self.assertEqual(code, 0)
        payload = json.loads(out.getvalue())
        self.assertEqual(payload["area_id"], "95")
        self.assertIn("hh.ru/search/vacancy", payload["url"])

    def test_missing_text(self):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(hh_url.main(["--offline"]), 2)


if __name__ == "__main__":
    unittest.main()
