#!/usr/bin/env python3
"""Собирает ссылку на поиск вакансий hh.ru.

Примеры:
    python scripts/hh_url.py --text "сварщик" --area "Тюмень"
    python scripts/hh_url.py --text "Python-разработчик" --area 113 \
        --schedule remote --experience 1-3 --salary 200000
    python scripts/hh_url.py --text "бухгалтер" --area "Казань" --json

Скрипт не ходит по вакансиям и ничего не парсит: он только строит корректный
URL с параметрами, чтобы агент не угадывал их вручную.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

AREAS_URL = "https://api.hh.ru/areas/113"
USER_AGENT = (
    "ai-job-finder-skill/1.0 "
    "(+https://github.com/kan1z0rofficial/ai-job-finder-skill)"
)

# id проверены через api.hh.ru/areas (ноябрь 2026).
AREA_IDS = {
    "россия": "113",
    "рф": "113",
    "москва": "1",
    "мск": "1",
    "санкт-петербург": "2",
    "спб": "2",
    "питер": "2",
    "екатеринбург": "3",
    "екб": "3",
    "новосибирск": "4",
    "нск": "4",
    "нижний новгород": "66",
    "казань": "88",
    "челябинск": "104",
    "омск": "68",
    "самара": "78",
    "ростов-на-дону": "76",
    "уфа": "99",
    "красноярск": "54",
    "пермь": "72",
    "воронеж": "26",
    "волгоград": "24",
    "краснодар": "53",
    "саратов": "79",
    "тюмень": "95",
    "киров": "49",
    "иваново": "32",
    "тольятти": "212",
    "ижевск": "96",
    "барнаул": "11",
    "ульяновск": "98",
    "иркутск": "35",
    "хабаровск": "102",
    "ярославль": "112",
    "владивосток": "22",
    "махачкала": "29",
    "томск": "90",
    "оренбург": "70",
    "кемерово": "47",
    "новокузнецк": "1240",
    "рязань": "77",
    "астрахань": "15",
    "набережные челны": "1641",
    "пенза": "71",
    "липецк": "58",
    "тула": "92",
    "чебоксары": "107",
    "калининград": "41",
    "брянск": "19",
    "курск": "56",
    "магнитогорск": "1399",
    "тверь": "89",
    "ставрополь": "84",
    "белгород": "17",
    "сочи": "237",
    "сургут": "1381",
    "владимир": "23",
    "нижний тагил": "1291",
    "архангельск": "14",
    "чита": "106",
    "смоленск": "83",
    "калуга": "43",
    "череповец": "1753",
    "вологда": "25",
    "мурманск": "64",
    "якутск": "80",
    "саранск": "63",
    "тамбов": "87",
    "стерлитамак": "1364",
    "грозный": "105",
    "кострома": "52",
    "петрозаводск": "73",
    "нижневартовск": "1375",
    "новый уренгой": "1419",
    "ноябрьск": "1420",
    "норильск": "246",
    "южно-сахалинск": "81",
    "петропавловск-камчатский": "44",
}

EXPERIENCE = {
    "none": "noExperience",
    "1-3": "between1And3",
    "3-6": "between3And6",
    "6+": "moreThan6",
}

SCHEDULE = {
    "office": "fullDay",
    "remote": "remote",
    "hybrid": "flexible",
    "shift": "shift",
    "fly-in-fly-out": "flyInFlyOut",
}

EMPLOYMENT = {
    "full": "full",
    "part": "part",
    "project": "project",
    "probation": "probation",
}

ORDER = {
    "relevance": "relevance",
    "date": "publication_time",
    "salary-desc": "salary_desc",
    "salary-asc": "salary_asc",
}


def fetch_areas(url: str = AREAS_URL) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def walk_areas(node: dict, path: tuple[str, ...] = ()) -> list[tuple[str, str, bool, str]]:
    """Возвращает (имя, id, есть_дочерние, полный_путь)."""
    current = path + (node["name"],)
    result = [(node["name"], str(node["id"]), bool(node.get("areas")), " / ".join(current))]
    for child in node.get("areas") or []:
        result.extend(walk_areas(child, current))
    return result


def _normalize(value: str) -> str:
    return " ".join(value.strip().casefold().split())


def _base_name(name: str) -> str:
    """Убирает уточнение региона: «Киров (Кировская область)» -> «Киров»."""
    if name.endswith(")") and " (" in name:
        return name[: name.rfind(" (")].strip()
    return name.strip()


def resolve_area(value: str, *, allow_network: bool = True) -> str:
    """Превращает название города или id в area-id hh.ru."""
    value = value.strip()
    if value.isdigit():
        return value

    key = _normalize(value)
    if key.startswith("город "):
        key = key.removeprefix("город ").strip()

    if key in AREA_IDS:
        return AREA_IDS[key]

    if not allow_network:
        raise LookupError(
            f"город «{value}» нет в офлайн-списке. "
            "Передайте area-id (например, 113 для всей России) или уберите --offline."
        )

    try:
        tree = fetch_areas()
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise LookupError(f"не удалось получить список регионов hh.ru: {exc}") from exc

    nodes = walk_areas(tree)
    matches = [item for item in nodes if _normalize(_base_name(item[0])) == key]
    if not matches:
        prefix = sorted(
            {
                _base_name(item[0])
                for item in nodes
                if _normalize(_base_name(item[0])).startswith(key[:4])
            }
        )[:5]
        hint = f" Похожие: {', '.join(prefix)}." if prefix else ""
        raise LookupError(f"город «{value}» не найден в справочнике hh.ru.{hint}")

    exact_city = [item for item in matches if not item[2]]
    if exact_city:
        matches = exact_city

    # Несколько городов с одинаковым названием: выбираем самый короткий путь.
    matches.sort(key=lambda item: item[3].count(" / "))
    same_depth = [
        item for item in matches if item[3].count(" / ") == matches[0][3].count(" / ")
    ]
    if len({item[1] for item in same_depth}) > 1:
        variants = "; ".join(
            f"{_base_name(item[0])} — area {item[1]} ({item[3]})" for item in same_depth[:5]
        )
        raise LookupError(
            f"название «{value}» неоднозначно: {variants}. "
            "Уточните регион или передайте area-id."
        )

    return matches[0][1]


def build_params(
    *,
    text: str,
    area: str,
    experience: str | None = None,
    schedule: str | None = None,
    employment: str | None = None,
    salary: int | None = None,
    only_with_salary: bool = False,
    order: str = "relevance",
    page: int = 0,
    exclude: tuple[str, ...] = (),
) -> dict[str, str]:
    query = text.strip()
    if not query:
        raise ValueError("пустой текст запроса")
    if page < 0:
        raise ValueError("page не может быть отрицательным")
    if salary is not None and salary <= 0:
        raise ValueError("salary должен быть положительным")

    for word in exclude:
        word = word.strip()
        if not word:
            continue
        query += f' NOT "{word}"' if " " in word else f" NOT {word}"

    params = {
        "text": query,
        "area": area,
        "order_by": ORDER.get(order, order),
        "items_on_page": "50",
        "page": str(page),
    }

    if experience:
        params["experience"] = EXPERIENCE.get(experience, experience)
    if schedule:
        params["schedule"] = SCHEDULE.get(schedule, schedule)
    if employment:
        params["employment"] = EMPLOYMENT.get(employment, employment)

    if salary is not None:
        params["salary"] = str(salary)
        params["currency_code"] = "RUR"
        params["only_with_salary"] = "true"
    elif only_with_salary:
        params["only_with_salary"] = "true"

    return params


def build_url(params: dict[str, str]) -> str:
    return "https://hh.ru/search/vacancy?" + urllib.parse.urlencode(params)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Собирает ссылку на поиск вакансий hh.ru.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--text", help="поисковый запрос, например «сварщик»")
    parser.add_argument("--area", default="113", help="город или area-id (по умолчанию 113 — Россия)")
    parser.add_argument("--experience", choices=sorted(EXPERIENCE), help="опыт работы")
    parser.add_argument("--schedule", choices=sorted(SCHEDULE), help="формат работы")
    parser.add_argument("--employment", choices=sorted(EMPLOYMENT), help="тип занятости")
    parser.add_argument("--salary", type=int, help="зарплата от, в рублях")
    parser.add_argument("--only-with-salary", action="store_true", help="только вакансии с зарплатой")
    parser.add_argument("--order", choices=sorted(ORDER), default="relevance", help="сортировка")
    parser.add_argument("--page", type=int, default=0, help="номер страницы (с 0)")
    parser.add_argument("--exclude", nargs="+", default=[], help="слова, которые нужно исключить")
    parser.add_argument("--offline", action="store_true", help="не обращаться к api.hh.ru")
    parser.add_argument("--list-areas", action="store_true", help="показать офлайн-список городов")
    parser.add_argument("--json", action="store_true", help="вывести JSON вместо ссылки")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    args = parse_args(argv)

    if args.list_areas:
        for name, area_id in sorted(AREA_IDS.items()):
            print(f"{area_id:>5}  {name}")
        return 0

    if not args.text:
        print("ERROR: нужен --text", file=sys.stderr)
        return 2

    try:
        area_id = resolve_area(args.area, allow_network=not args.offline)
        params = build_params(
            text=args.text,
            area=area_id,
            experience=args.experience,
            schedule=args.schedule,
            employment=args.employment,
            salary=args.salary,
            only_with_salary=args.only_with_salary,
            order=args.order,
            page=args.page,
            exclude=args.exclude,
        )
    except (LookupError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    url = build_url(params)

    if args.json:
        print(
            json.dumps(
                {"url": url, "area_id": area_id, "params": params},
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(url)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
