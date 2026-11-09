#!/usr/bin/env python3
"""Отчёт по рынку зарплат на основе выгрузки вакансий.

Вход — JSON по схеме `references/output.md` (подходит вывод `hh_api.py`).

Примеры:
    python scripts/salary_report.py --input results.json
    python scripts/salary_report.py --input results.json --from 2026-10-01 --to 2026-10-31
    python scripts/salary_report.py --input results.json --format csv --output report.csv
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import math
import sys
from datetime import date
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import format_results  # noqa: E402

EXPERIENCE_ORDER = ["none", "1-3", "3-6", "6+"]
FORMAT_ORDER = ["office", "remote", "hybrid", "fly-in-fly-out", "shift", "flexible"]

EXPERIENCE_LABELS = {
    "none": "без опыта",
    "1-3": "1–3 года",
    "3-6": "3–6 лет",
    "6+": "более 6 лет",
    "unknown": "не указано",
}

FORMAT_LABELS = {
    "office": "офис",
    "remote": "удалённо",
    "hybrid": "гибрид",
    "fly-in-fly-out": "вахта",
    "shift": "смены",
    "flexible": "гибкий график",
    "unknown": "не указано",
}


def percentile(values: list[float], ratio: float) -> float | None:
    if not values:
        return None
    if not 0 <= ratio <= 1:
        raise ValueError("ratio должен быть от 0 до 1")
    ordered = sorted(values)
    position = (len(ordered) - 1) * ratio
    low = math.floor(position)
    high = math.ceil(position)
    if low == high:
        return ordered[low]
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


def stats(points: list[float]) -> dict:
    if not points:
        return {
            "count": 0,
            "median": None,
            "p25": None,
            "p75": None,
            "min": None,
            "max": None,
        }
    return {
        "count": len(points),
        "median": round(format_results.median(points)),
        "p25": round(percentile(points, 0.25)),
        "p75": round(percentile(points, 0.75)),
        "min": round(min(points)),
        "max": round(max(points)),
    }


def parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"дата «{value}» должна быть в формате ГГГГ-ММ-ДД") from exc


def filter_vacancies(
    vacancies: list[dict],
    *,
    date_from: date | None = None,
    date_to: date | None = None,
) -> tuple[list[dict], int]:
    if date_from is None and date_to is None:
        return vacancies, 0

    selected: list[dict] = []
    skipped = 0
    for vacancy in vacancies:
        published = vacancy.get("published_at")
        if not published:
            skipped += 1
            continue
        try:
            published_date = parse_date(str(published)[:10])
        except ValueError:
            skipped += 1
            continue
        if date_from and published_date < date_from:
            continue
        if date_to and published_date > date_to:
            continue
        selected.append(vacancy)
    return selected, skipped


def currency_points(vacancies: list[dict], currency: str) -> list[float]:
    points: list[float] = []
    for vacancy in vacancies:
        if (vacancy.get("currency") or "RUR") != currency:
            continue
        point = format_results.salary_midpoint(vacancy)
        if point is not None:
            points.append(point)
    return points


def detect_currency(vacancies: list[dict], requested: str | None) -> tuple[str, int]:
    counts: dict[str, int] = {}
    for vacancy in vacancies:
        if format_results.salary_midpoint(vacancy) is None:
            continue
        code = vacancy.get("currency") or "RUR"
        counts[code] = counts.get(code, 0) + 1
    if not counts:
        return requested or "RUR", 0
    primary = requested or max(counts, key=counts.get)
    other = sum(count for code, count in counts.items() if code != primary)
    return primary, other


def group_by(vacancies: list[dict], key: str) -> list[dict]:
    buckets: dict[str, list[dict]] = {}
    for vacancy in vacancies:
        value = vacancy.get(key) or "unknown"
        buckets.setdefault(str(value), []).append(vacancy)

    rows = []
    for value, items in buckets.items():
        points = [p for v in items if (p := format_results.salary_midpoint(v)) is not None]
        row = {"key": value, "total": len(items)}
        row.update(stats(points))
        rows.append(row)
    return rows


def sort_groups(rows: list[dict], order: list[str] | None = None, top: int | None = None) -> list[dict]:
    if order:
        rank = {value: index for index, value in enumerate(order)}
        rows.sort(key=lambda row: (rank.get(row["key"], len(order)), -row["total"]))
    else:
        rows.sort(key=lambda row: (-row["total"], -(row["median"] or 0)))
    return rows[:top] if top else rows


def period_label(
    vacancies: list[dict],
    date_from: date | None,
    date_to: date | None,
) -> str:
    if date_from or date_to:
        start = date_from.isoformat() if date_from else "начало"
        end = date_to.isoformat() if date_to else date.today().isoformat()
        return f"{start} — {end}"
    dates = sorted(
        str(v.get("published_at"))[:10]
        for v in vacancies
        if v.get("published_at")
    )
    if dates:
        return f"{dates[0]} — {dates[-1]}"
    return "не указан"


def build_report(
    payload: dict,
    *,
    currency: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    top: int = 10,
) -> dict:
    vacancies = payload.get("vacancies") or []
    filtered, skipped_no_date = filter_vacancies(vacancies, date_from=date_from, date_to=date_to)
    code, other_currency = detect_currency(filtered, currency)
    selected = [v for v in filtered if (v.get("currency") or "RUR") == code]
    points = currency_points(selected, code)

    overall = {"total": len(selected), "with_salary": len(points)}
    overall.update(stats(points))

    return {
        "period": {
            "from": date_from.isoformat() if date_from else None,
            "to": date_to.isoformat() if date_to else None,
            "label": period_label(filtered, date_from, date_to),
        },
        "currency": code,
        "skipped_no_date": skipped_no_date,
        "skipped_other_currency": other_currency,
        "overall": overall,
        "by_city": sort_groups(group_by(selected, "city"), top=top),
        "by_experience": sort_groups(group_by(selected, "experience"), order=EXPERIENCE_ORDER),
        "by_work_format": sort_groups(group_by(selected, "work_format"), order=FORMAT_ORDER),
        "top_employers": sort_groups(group_by(selected, "company"), top=top),
    }


def money(value: int | None) -> str:
    if value is None:
        return "—"
    return format_results.format_money(value)


def plural(count: int, one: str, few: str, many: str) -> str:
    remainder100 = count % 100
    remainder10 = count % 10
    if 11 <= remainder100 <= 14:
        return many
    if remainder10 == 1:
        return one
    if 2 <= remainder10 <= 4:
        return few
    return many


def to_markdown(report: dict) -> str:
    lines = [
        "# Отчёт по рынку зарплат",
        "",
        f"Период: {report['period']['label']}",
        (
            f"Выборка: {report['overall']['total']} "
            f"{plural(report['overall']['total'], 'вакансия', 'вакансии', 'вакансий')}, "
            f"из них {report['overall']['with_salary']} с зарплатой в {report['currency']}."
        ),
    ]
    if report["skipped_no_date"]:
        lines.append(f"Без даты публикации и не попали в период: {report['skipped_no_date']}.")
    if report["skipped_other_currency"]:
        lines.append(f"Пропущено из-за другой валюты: {report['skipped_other_currency']}.")

    lines += [
        "",
        "## Общая статистика",
        "",
        "| Показатель | Значение |",
        "|---|---|",
        f"| Медиана | {money(report['overall']['median'])} |",
        f"| 25-й процентиль | {money(report['overall']['p25'])} |",
        f"| 75-й процентиль | {money(report['overall']['p75'])} |",
        f"| Минимум | {money(report['overall']['min'])} |",
        f"| Максимум | {money(report['overall']['max'])} |",
    ]

    def section(title: str, rows: list[dict], labels: dict[str, str] | None = None) -> None:
        if not rows:
            return
        lines.extend(["", f"## {title}", "", "| Сегмент | Вакансий | С зарплатой | Медиана |", "|---|---|---|---|"])
        for row in rows:
            key = labels.get(row["key"], row["key"]) if labels else row["key"]
            lines.append(
                f"| {key} | {row['total']} | {row['count']} | {money(row['median'])} |"
            )

    section("По городам", report["by_city"])
    section("По опыту", report["by_experience"], EXPERIENCE_LABELS)
    section("По формату работы", report["by_work_format"], FORMAT_LABELS)
    section("Топ работодателей", report["top_employers"])

    lines += [
        "",
        "> Медиана считается по серединам вилок. Вакансии без зарплаты в расчёт не входят.",
    ]
    return "\n".join(lines)


def to_csv(report: dict) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(["segment", "key", "total", "with_salary", "median", "p25", "p75", "min", "max"])
    overall = report["overall"]
    writer.writerow(
        ["overall", "", overall["total"], overall["with_salary"], overall["median"],
         overall["p25"], overall["p75"], overall["min"], overall["max"]]
    )
    for segment, key in (
        ("city", "by_city"),
        ("experience", "by_experience"),
        ("work_format", "by_work_format"),
        ("employer", "top_employers"),
    ):
        for row in report[key]:
            writer.writerow(
                [segment, row["key"], row["total"], row["count"], row["median"],
                 row["p25"], row["p75"], row["min"], row["max"]]
            )
    return buffer.getvalue().rstrip("\n")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Отчёт по зарплатам из выгрузки вакансий.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--input", "-i", default="-", help="файл с JSON или - для stdin")
    parser.add_argument("--format", "-f", choices=["markdown", "json", "csv"], default="markdown")
    parser.add_argument("--output", "-o", default="-", help="файл для записи или - для stdout")
    parser.add_argument("--currency", default=None, help="валюта отчёта, по умолчанию самая частая")
    parser.add_argument("--from", dest="date_from", default=None, help="начало периода, ГГГГ-ММ-ДД")
    parser.add_argument("--to", dest="date_to", default=None, help="конец периода, ГГГГ-ММ-ДД")
    parser.add_argument("--top", type=int, default=10, help="сколько строк в разрезах")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    args = parse_args(argv)

    try:
        raw = sys.stdin.read() if args.input == "-" else Path(args.input).read_text(encoding="utf-8")
        payload = format_results.load_payload(raw)
        date_from = parse_date(args.date_from) if args.date_from else None
        date_to = parse_date(args.date_to) if args.date_to else None
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if date_from and date_to and date_from > date_to:
        print("ERROR: --from позже --to", file=sys.stderr)
        return 2

    report = build_report(
        payload,
        currency=args.currency,
        date_from=date_from,
        date_to=date_to,
        top=max(1, args.top),
    )

    if args.format == "json":
        text = json.dumps(report, ensure_ascii=False, indent=2)
    elif args.format == "csv":
        text = to_csv(report)
    else:
        text = to_markdown(report)

    if args.output == "-":
        print(text)
    else:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
        print(f"Записано: {args.output}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
