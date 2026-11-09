#!/usr/bin/env python3
"""Прогон поведенческих кейсов из evals/cases.json.

Без ключа доступен только список кейсов:
    python scripts/run_evals.py --list

С ключом и OpenAI-совместимым API:
    export OPENAI_API_KEY=...
    python scripts/run_evals.py --run --model gpt-4o-mini

Важно: в этом режиме у модели нет инструментов, поэтому запускаются только
кейсы mode=no-tools. Они проверяют следование правилам (уточняющий вопрос,
отказ от отклика, отсутствие выдуманных вакансий), а не качество поиска.
Кейсы mode=live требуют агента с браузером и запускаются вручную.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES_PATH = ROOT / "evals" / "cases.json"
SKILL_PATH = ROOT / "SKILL.md"

GUARD = """

## Режим автоматической проверки

Сейчас у тебя нет инструментов: ты не можешь искать в интернете и открывать сайты.
Не выдумывай вакансии, компании, зарплаты и ссылки.
Следуй правилам скилла: задай один уточняющий вопрос, откажись от отклика
или честно скажи, что без веб-поиска вакансии не найти.
"""


def load_cases() -> list[dict]:
    data = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    return data.get("cases", [])


def evaluate(answer: str, checks: dict) -> list[str]:
    text = answer.casefold()
    problems: list[str] = []

    for needle in checks.get("must_include_all", []):
        if needle.casefold() not in text:
            problems.append(f"нет обязательного «{needle}»")

    alternatives = checks.get("must_include_any", [])
    if alternatives and not any(item.casefold() in text for item in alternatives):
        problems.append("нет ни одного из: " + ", ".join(alternatives))

    for needle in checks.get("must_not_include", []):
        if needle.casefold() in text:
            problems.append(f"не должно быть «{needle}»")

    return problems


def call_model(
    *,
    base_url: str,
    api_key: str,
    model: str,
    system: str,
    prompt: str,
    timeout: int,
) -> str:
    payload = {
        "model": model,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
    }
    request = urllib.request.Request(
        base_url.rstrip("/") + "/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        data = json.load(response)
    return data["choices"][0]["message"]["content"]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--list", action="store_true", help="показать кейсы")
    parser.add_argument("--run", action="store_true", help="запустить no-tools кейсы через API")
    parser.add_argument("--include-live", action="store_true", help="включить live-кейсы (нужен браузер)")
    parser.add_argument("--case", action="append", default=[], help="id кейса, можно повторять")
    parser.add_argument("--model", default=os.environ.get("OPENAI_MODEL", ""))
    parser.add_argument("--base-url", default=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"))
    parser.add_argument("--api-key", default=os.environ.get("OPENAI_API_KEY", ""))
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--out", default="", help="сохранить результаты в JSON")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    args = parse_args(argv)
    cases = load_cases()

    if args.case:
        selected = set(args.case)
        cases = [case for case in cases if case["id"] in selected]
        if not cases:
            print("ERROR: кейсы не найдены", file=sys.stderr)
            return 2

    if args.list or not args.run:
        print(f"Кейсов: {len(cases)}\n")
        for case in cases:
            print(f"[{case.get('mode', 'no-tools')}] {case['id']}: {case['prompt']}")
        if not args.run:
            print("\nЗапуск: --run --model <model> и переменная OPENAI_API_KEY.")
        return 0

    if not args.api_key:
        print("ERROR: нужен OPENAI_API_KEY или --api-key", file=sys.stderr)
        return 2
    if not args.model:
        print("ERROR: нужен --model или OPENAI_MODEL", file=sys.stderr)
        return 2

    system = SKILL_PATH.read_text(encoding="utf-8") + GUARD
    results = []
    failed = 0

    for case in cases:
        mode = case.get("mode", "no-tools")
        if mode == "live" and not args.include_live:
            print(f"SKIP {case['id']} (live)")
            continue

        try:
            answer = call_model(
                base_url=args.base_url,
                api_key=args.api_key,
                model=args.model,
                system=system,
                prompt=case["prompt"],
                timeout=args.timeout,
            )
            problems = evaluate(answer, case.get("checks", {}))
        except (urllib.error.URLError, TimeoutError, KeyError, json.JSONDecodeError) as exc:
            answer = ""
            problems = [f"ошибка запроса: {exc}"]

        status = "PASS" if not problems else "FAIL"
        if problems:
            failed += 1
        print(f"{status} {case['id']}")
        for problem in problems:
            print(f"     - {problem}")

        results.append(
            {
                "id": case["id"],
                "mode": mode,
                "status": status,
                "problems": problems,
                "answer": answer,
            }
        )

    if args.out:
        Path(args.out).write_text(
            json.dumps(results, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"\nРезультаты: {args.out}")

    print(f"\nПровалено: {failed} из {len(results)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
