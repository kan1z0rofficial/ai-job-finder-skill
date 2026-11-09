#!/usr/bin/env python3
"""Форматирует результаты поиска вакансий в CSV, Markdown или JSON.

Вход — JSON по схеме `references/output.md` или простой массив вакансий.

Примеры:
    python scripts/format_results.py --input results.json --format csv
    python scripts/format_results.py --input results.json --format markdown
    cat results.json | python scripts/format_results.py --format csv
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from datetime import date
from pathlib import Path

CSV_COLUMNS = [
    "title",
    "company",
    "city",
    "work_format",
    "experience",
    "salary_from",
    "salary_to",
    "currency",
    "gross",
    "source",
    "published_at",
    "rotation",
    "url",
]

EXPERIENCE_LABELS = {
    "none": "без опыта",
    "1-3": "1–3 года",
    "3-6": "3–6 лет",
    "6+": "более 6 лет",
}

FORMAT_LABELS = {
    "office": "офис",
    "remote": "удалённо",
    "hybrid": "гибрид",
    "fly-in-fly-out": "вахта",
    "shift": "смены",
    "flexible": "гибкий график",
}

CURRENCY_SYMBOLS = {
    "RUR": "₽",
    "RUB": "₽",
    "USD": "$",
    "EUR": "€",
    "KZT": "₸",
    "BYN": "Br",
    "BYR": "Br",
    "UAH": "₴",
    "GEL": "₾",
}


def load_payload(raw: str) -> dict:
    data = json.loads(raw)
    if isinstance(data, list):
        return {"vacancies": data}
    if isinstance(data, dict):
        return data
    raise ValueError("ожидался объект или массив вакансий")


def validate_vacancy(index: int, vacancy: dict) -> list[str]:
    prefix = f"вакансия #{index + 1}"
    errors: list[str] = []

    if not isinstance(vacancy, dict):
        return [f"{prefix}: ожидался объект"]

    for field in ("title", "company", "source"):
        value = vacancy.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{prefix}: поле «{field}» обязательно")

    for field in ("salary_from", "salary_to"):
        value = vacancy.get(field)
        if value is None:
            continue
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            errors.append(f"{prefix}: «{field}» должно быть положительным целым или null")

    for field in ("city", "work_format", "experience", "currency", "url", "published_at", "rotation"):
        value = vacancy.get(field)
        if value is not None and not isinstance(value, str):
            errors.append(f"{prefix}: «{field}» должно быть строкой или null")

    return errors


def salary_midpoint(vacancy: dict) -> float | None:
    low = vacancy.get("salary_from")
    high = vacancy.get("salary_to")
    if low is not None and high is not None:
        return (low + high) / 2
    if low is not None:
        return float(low)
    if high is not None:
        return float(high)
    return None


def median(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2


def summarize(vacancies: list[dict]) -> dict:
    points = [point for vacancy in vacancies if (point := salary_midpoint(vacancy)) is not None]
    return {
        "found": len(vacancies),
        "with_salary": len(points),
        "median_salary": round(median(points)) if points else None,
    }


def format_money(value: int) -> str:
    return f"{value:,}".replace(",", " ")


def salary_cell(vacancy: dict) -> str:
    low = vacancy.get("salary_from")
    high = vacancy.get("salary_to")
    symbol = CURRENCY_SYMBOLS.get(vacancy.get("currency") or "RUR", "")

    if low is not None and high is not None:
        text = f"{format_money(low)} – {format_money(high)} {symbol}".strip()
    elif low is not None:
        text = f"от {format_money(low)} {symbol}".strip()
    elif high is not None:
        text = f"до {format_money(high)} {symbol}".strip()
    else:
        return "не указана"

    gross = vacancy.get("gross")
    if gross is True:
        text += " до вычета"
    elif gross is False:
        text += " на руки"
    return text


def city_and_format(vacancy: dict) -> str:
    city = (vacancy.get("city") or "").strip()
    work_format = FORMAT_LABELS.get(vacancy.get("work_format") or "", vacancy.get("work_format") or "")
    parts = [part for part in (city, work_format) if part]
    return " / ".join(parts) if parts else "не указано"


def escape_cell(value: object) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", " ").strip()


def to_markdown(vacancies: list[dict], summary: dict, query: dict | None = None) -> str:
    lines = [
        "| # | Должность | Компания | Зарплата | Опыт | Город / формат | Источник |",
        "|---|---|---|---|---|---|---|",
    ]
    for index, vacancy in enumerate(vacancies, start=1):
        experience = EXPERIENCE_LABELS.get(
            vacancy.get("experience") or "", vacancy.get("experience") or "не указано"
        )
        lines.append(
            "| {n} | {title} | {company} | {salary} | {experience} | {place} | {source} |".format(
                n=index,
                title=escape_cell(vacancy.get("title")),
                company=escape_cell(vacancy.get("company")),
                salary=escape_cell(salary_cell(vacancy)),
                experience=escape_cell(experience),
                place=escape_cell(city_and_format(vacancy)),
                source=escape_cell(vacancy.get("source")),
            )
        )

    lines.append("")
    total = f"Итог: найдено {summary['found']}"
    if summary.get("median_salary"):
        total += f", медиана — {format_money(summary['median_salary'])} ₽"
    search_date = (query or {}).get("date") or date.today().isoformat()
    total += f", дата поиска {search_date}."
    lines.append(total)
    return "\n".join(lines)


def to_csv(vacancies: list[dict]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CSV_COLUMNS, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    for vacancy in vacancies:
        row = {column: vacancy.get(column) for column in CSV_COLUMNS}
        if row["gross"] is None:
            row["gross"] = ""
        elif isinstance(row["gross"], bool):
            row["gross"] = "true" if row["gross"] else "false"
        writer.writerow(row)
    return buffer.getvalue().rstrip("\n")


def normalize(payload: dict) -> dict:
    vacancies = payload.get("vacancies") or []
    query = payload.get("query") or {}
    query.setdefault("date", date.today().isoformat())
    return {
        "query": query,
        "vacancies": vacancies,
        "summary": summarize(vacancies),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Форматирует вакансии в CSV, Markdown или JSON.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--input", "-i", default="-", help="файл с JSON или - для stdin")
    parser.add_argument("--format", "-f", choices=["markdown", "csv", "json"], default="markdown")
    parser.add_argument("--output", "-o", default="-", help="файл для записи или - для stdout")
    parser.add_argument("--strict", action="store_true", help="падать при ошибках валидации")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    args = parse_args(argv)

    try:
        raw = sys.stdin.read() if args.input == "-" else Path(args.input).read_text(encoding="utf-8")
        payload = load_payload(raw)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: не удалось прочитать JSON: {exc}", file=sys.stderr)
        return 2

    vacancies = payload.get("vacancies") or []
    if not isinstance(vacancies, list):
        print("ERROR: «vacancies» должен быть массивом", file=sys.stderr)
        return 2

    errors: list[str] = []
    for index, vacancy in enumerate(vacancies):
        errors.extend(validate_vacancy(index, vacancy))

    if errors:
        for error in errors:
            print(f"WARN: {error}", file=sys.stderr)
        if args.strict:
            the_end = "строгий режим: исправьте данные"
            print(f"ERROR: {the_end}", file=sys.stderr)
            return 1
        vacancies = [vacancy for vacancy in vacancies if isinstance(vacancy, dict)]

    normalized = normalize(payload)

    if args.format == "csv":
        result = to_csv(normalized["vacancies"])
    elif args.format == "json":
        result = json.dumps(normalized, ensure_ascii=False, indent=2)
    else:
        result = to_markdown(normalized["vacancies"], normalized["summary"], normalized["query"])

    if args.output == "-":
        print(result)
    else:
        Path(args.output).write_text(result + "\n", encoding="utf-8")
        print(f"Записано: {args.output}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
