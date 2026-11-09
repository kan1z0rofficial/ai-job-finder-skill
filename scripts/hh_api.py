#!/usr/bin/env python3
"""Поиск вакансий через официальный API hh.ru.

Примеры:
    python scripts/hh_api.py --text "сварщик" --area "Тюмень" --limit 10
    python scripts/hh_api.py --text "Python" --area 1 --schedule remote --format csv
    python scripts/hh_api.py --text "бухгалтер" --dry-run

Публичный поиск может требовать токен приложения: получите его на dev.hh.ru
и передайте через --token или переменную окружения HH_ACCESS_TOKEN.
Без токена скрипт честно сообщает об ошибке, а скилл откатывается к веб-поиску.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import format_results  # noqa: E402
import hh_url  # noqa: E402

API_URL = "https://api.hh.ru/vacancies"
USER_AGENT = (
    "ai-job-finder-skill/1.2 "
    "(+https://github.com/kan1z0rofficial/ai-job-finder-skill)"
)

EXPERIENCE_TO_SCHEMA = {
    "noExperience": "none",
    "between1And3": "1-3",
    "between3And6": "3-6",
    "moreThan6": "6+",
}

SCHEDULE_TO_FORMAT = {
    "fullDay": "office",
    "remote": "remote",
    "flexible": "hybrid",
    "shift": "shift",
    "flyInFlyOut": "fly-in-fly-out",
}


class ApiError(RuntimeError):
    """Ошибка официального API hh.ru."""


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
    search_field: str | None = None,
    page: int = 0,
    per_page: int = 20,
    exclude: tuple[str, ...] = (),
) -> dict[str, str]:
    query = text.strip()
    if not query:
        raise ValueError("пустой текст запроса")
    if page < 0:
        raise ValueError("page не может быть отрицательным")
    if not 1 <= per_page <= 100:
        raise ValueError("per_page должен быть от 1 до 100")
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
        "page": str(page),
        "per_page": str(per_page),
        "order_by": hh_url.ORDER.get(order, order),
    }

    if experience:
        params["experience"] = hh_url.EXPERIENCE.get(experience, experience)
    if schedule:
        params["schedule"] = hh_url.SCHEDULE.get(schedule, schedule)
    if employment:
        params["employment"] = hh_url.EMPLOYMENT.get(employment, employment)
    if search_field:
        params["search_field"] = search_field

    if salary is not None:
        params["salary"] = str(salary)
        params["currency"] = "RUR"
        params["only_with_salary"] = "true"
    elif only_with_salary:
        params["only_with_salary"] = "true"

    return params


def request_page(
    params: dict[str, str],
    *,
    token: str | None = None,
    timeout: int = 30,
    retries: int = 1,
) -> dict:
    url = API_URL + "?" + urllib.parse.urlencode(params)
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    attempt = 0
    while True:
        request = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", "replace")[:300]
            if exc.code == 429 and attempt < retries:
                attempt += 1
                delay = int(exc.headers.get("Retry-After", "1") or 1)
                time.sleep(min(delay, 5))
                continue
            if exc.code == 403:
                raise ApiError(
                    "hh.ru API вернул 403. Публичный поиск вакансий может требовать "
                    "токен приложения. Получите его на dev.hh.ru и передайте "
                    "--token или HH_ACCESS_TOKEN. Без токена используйте веб-поиск. "
                    f"Ответ API: {body}"
                ) from exc
            if exc.code == 429:
                raise ApiError("hh.ru API ограничил частоту запросов (429). Повторите позже.") from exc
            raise ApiError(f"hh.ru API вернул {exc.code}: {body}") from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            raise ApiError(f"не удалось подключиться к api.hh.ru: {exc}") from exc


def normalize_item(item: dict) -> dict:
    salary = item.get("salary") or {}
    area = item.get("area") or {}
    employer = item.get("employer") or {}
    schedule = (item.get("schedule") or {}).get("id")
    experience = (item.get("experience") or {}).get("id")

    return {
        "id": f"hh-{item['id']}" if item.get("id") else None,
        "title": item.get("name") or "",
        "company": employer.get("name") or "",
        "city": area.get("name"),
        "work_format": SCHEDULE_TO_FORMAT.get(schedule),
        "experience": EXPERIENCE_TO_SCHEMA.get(experience),
        "salary_from": salary.get("from"),
        "salary_to": salary.get("to"),
        "currency": salary.get("currency"),
        "gross": salary.get("gross"),
        "source": "hh.ru",
        "url": item.get("alternate_url"),
        "published_at": (item.get("published_at") or "")[:10] or None,
    }


def search(
    *,
    text: str,
    area: str,
    limit: int = 20,
    page: int = 0,
    experience: str | None = None,
    schedule: str | None = None,
    employment: str | None = None,
    salary: int | None = None,
    only_with_salary: bool = False,
    order: str = "relevance",
    search_field: str | None = None,
    exclude: tuple[str, ...] = (),
    token: str | None = None,
    timeout: int = 30,
    delay: float = 0.2,
    area_id: str | None = None,
    fetch=None,
) -> dict:
    if limit < 1:
        raise ValueError("limit должен быть положительным")

    fetch = fetch or request_page
    area_value = area_id or hh_url.resolve_area(area)
    per_page = min(100, limit)
    start_page = page
    collected: list[dict] = []
    found: int | None = None
    pages: int | None = None
    while len(collected) < limit:
        params = build_params(
            text=text,
            area=area_value,
            experience=experience,
            schedule=schedule,
            employment=employment,
            salary=salary,
            only_with_salary=only_with_salary,
            order=order,
            search_field=search_field,
            page=start_page,
            per_page=per_page,
            exclude=exclude,
        )
        data = fetch(params, token=token, timeout=timeout)
        found = data.get("found", found)
        pages = data.get("pages", pages)
        items = data.get("items") or []
        if not items:
            break

        collected.extend(items)
        if len(items) < per_page:
            break

        start_page += 1
        if pages is not None and start_page >= pages:
            break
        if delay:
            time.sleep(delay)

    vacancies = [normalize_item(item) for item in collected[:limit]]
    query = {        "profession": text,
        "city": area,
        "work_format": {
            "office": "office",
            "remote": "remote",
            "hybrid": "hybrid",
            "shift": "shift",
            "fly-in-fly-out": "fly-in-fly-out",
        }.get(schedule or "", "any"),
        "experience": experience,
        "salary_from": salary,
        "date": date.today().isoformat(),
    }

    return {
        "query": query,
        "vacancies": vacancies,
        "summary": format_results.summarize(vacancies),
        "found": found,
        "items": collected[:limit],
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Поиск вакансий через официальный API hh.ru.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--text", required=True, help="поисковый запрос")
    parser.add_argument("--area", default="113", help="город или area-id (по умолчанию 113 — Россия)")
    parser.add_argument("--limit", type=int, default=20, help="сколько вакансий получить (1–200)")
    parser.add_argument("--page", type=int, default=0, help="стартовая страница API (с 0)")
    parser.add_argument("--experience", choices=sorted(hh_url.EXPERIENCE))
    parser.add_argument("--schedule", choices=sorted(hh_url.SCHEDULE))
    parser.add_argument("--employment", choices=sorted(hh_url.EMPLOYMENT))
    parser.add_argument("--salary", type=int, help="зарплата от, в рублях")
    parser.add_argument("--only-with-salary", action="store_true")
    parser.add_argument("--order", choices=sorted(hh_url.ORDER), default="relevance")
    parser.add_argument("--search-field", choices=["name", "description", "company_name"])
    parser.add_argument("--exclude", nargs="+", default=[])
    parser.add_argument("--token", default=os.environ.get("HH_ACCESS_TOKEN", ""))
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--delay", type=float, default=0.2, help="пауза между страницами, сек")
    parser.add_argument("--format", choices=["json", "csv", "markdown", "raw"], default="json")
    parser.add_argument("--output", default="-", help="файл для записи или - для stdout")
    parser.add_argument("--dry-run", action="store_true", help="показать URL без запроса")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    args = parse_args(argv)

    if args.limit < 1 or args.limit > 200:
        print("ERROR: --limit должен быть от 1 до 200", file=sys.stderr)
        return 2

    try:
        area_id = hh_url.resolve_area(args.area)
        per_page = min(100, args.limit)
        params = build_params(
            text=args.text,
            area=area_id,
            experience=args.experience,
            schedule=args.schedule,
            employment=args.employment,
            salary=args.salary,
            only_with_salary=args.only_with_salary,
            order=args.order,
            search_field=args.search_field,
            page=args.page,
            per_page=per_page,
            exclude=args.exclude,
        )
    except (LookupError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.dry_run:
        print(API_URL + "?" + urllib.parse.urlencode(params))
        return 0

    try:
        result = search(
            text=args.text,
            area=args.area,
            area_id=area_id,
            limit=args.limit,
            page=args.page,
            experience=args.experience,
            schedule=args.schedule,
            employment=args.employment,
            salary=args.salary,
            only_with_salary=args.only_with_salary,
            order=args.order,
            search_field=args.search_field,
            exclude=args.exclude,
            token=args.token or None,
            timeout=args.timeout,
            delay=args.delay,
        )
    except (ApiError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.format == "raw":
        text = json.dumps(
            {"found": result["found"], "items": result["items"]},
            ensure_ascii=False,
            indent=2,
            default=str,
        )
    elif args.format == "csv":
        text = format_results.to_csv(result["vacancies"])
    elif args.format == "markdown":
        text = format_results.to_markdown(
            result["vacancies"], result["summary"], result["query"]
        )
    else:
        text = json.dumps(
            {
                "query": result["query"],
                "vacancies": result["vacancies"],
                "summary": result["summary"],
            },
            ensure_ascii=False,
            indent=2,
        )

    if args.output == "-":
        print(text)
    else:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
        print(f"Записано: {args.output}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
