#!/usr/bin/env python3
"""Статические проверки репозитория ai-job-finder-skill.

Проверяет то, что легко сломать при правках: frontmatter скилла, обязательные
правила, пути установки, внутренние ссылки, JSON-файлы и согласованность версий.

Запуск: python scripts/check_contract.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FAILURES: list[str] = []
CHECKS = 0

REQUIRED_FILES = [
    "SKILL.md",
    "README.md",
    "README.en.md",
    "INSTALL.md",
    "LICENSE",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    ".claude-plugin/plugin.json",
    ".claude-plugin/marketplace.json",
    ".github/workflows/validate.yml",
    "evals/cases.json",
    "references/sources.md",
    "references/output.md",
    "scripts/hh_url.py",
    "scripts/format_results.py",
    "scripts/check_contract.py",
    "scripts/run_evals.py",
    "tests/test_hh_url.py",
    "tests/test_format_results.py",
]

SKILL_RULES = [
    "не выдумывай",
    "личные данные",
    "отклоняй",
    "дата поиска",
    "медиан",
]

MARKDOWN_FILES = [
    "README.md",
    "README.en.md",
    "INSTALL.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "CHANGELOG.md",
]


def check(name: str, condition: bool, detail: str = "") -> bool:
    global CHECKS
    CHECKS += 1
    if condition:
        print(f"  OK   {name}")
        return True
    message = f"{name}: {detail}" if detail else name
    print(f"  FAIL {message}")
    FAILURES.append(message)
    return False


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def parse_frontmatter(text: str) -> dict[str, str] | None:
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    block = text[3:end].strip("\n")
    data: dict[str, str] = {}
    for line in block.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"').strip("'")
    return data


def internal_links(text: str) -> list[str]:
    without_comments = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    links = re.findall(r"\[[^\]]*\]\(([^)]+)\)", without_comments)
    result = []
    for link in links:
        link = link.strip()
        if link.startswith(("http://", "https://", "mailto:", "tel:", "#")):
            continue
        if " " in link and not link.startswith("<"):
            link = link.split(" ", 1)[0]
        path = link.split("#", 1)[0]
        if path:
            result.append(path)
    return result


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("Файлы")
    for relative in REQUIRED_FILES:
        check(f"{relative} существует", (ROOT / relative).is_file())

    print("\nSKILL.md")
    skill = read("SKILL.md")
    meta = parse_frontmatter(skill)
    check("frontmatter есть", meta is not None)
    if meta:
        name = meta.get("name", "")
        description = meta.get("description", "")
        check("name = ai-job-finder-skill", name == "ai-job-finder-skill", name)
        check(
            "name в kebab-case и <= 64 символов",
            bool(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name)) and len(name) <= 64,
            name,
        )
        check("description заполнен", len(description) >= 40, f"{len(description)} символов")
        check("description <= 1024 символов", len(description) <= 1024, f"{len(description)} символов")

    lowered = skill.casefold()
    for rule in SKILL_RULES:
        check(f"правило «{rule}» на месте", rule in lowered)

    check("ссылка на INSTALL.md", "INSTALL.md" in skill)
    check("нет ссылки на README.md как на инструкцию", "README.md репозитория" not in skill)
    check("ссылка на схему вывода", "references/output.md" in skill)
    check("упомянут format_results.py", "format_results.py" in skill)

    print("\nINSTALL.md")
    install = read("INSTALL.md")
    install_lower = install.casefold()
    check("правильный путь Claude Code", "ai-job-finder-skill/SKILL.md" in install)
    check("нет опечатки skillh", "skillh" not in install_lower)
    check("описан плагин Claude Code", "plugin marketplace add" in install)
    check("описан Windows", "powershell" in install_lower)

    print("\nREADME")
    readme = read("README.md")
    readme_lower = readme.casefold()
    check("ссылка на INSTALL.md", "install.md" in readme_lower)
    check("команда установки плагина", "ai-job-finder-skill@ai-job-finder" in readme)
    check("раздел ограничений", "ограничения" in readme_lower)
    check("описание структуры актуально", "references/sources.md" in readme and "CHANGELOG.md" in readme)
    check("описан JSON/CSV", "references/output.md" in readme and "format_results.py" in readme)

    print("\nВнутренние ссылки")
    for relative in MARKDOWN_FILES:
        for link in internal_links(read(relative)):
            target = (ROOT / link).resolve()
            inside = ROOT.resolve() in target.parents or target == ROOT.resolve()
            check(f"{relative} -> {link}", target.exists() and inside)

    print("\nJSON и версии")
    plugin = json.loads(read(".claude-plugin/plugin.json"))
    marketplace = json.loads(read(".claude-plugin/marketplace.json"))
    cases = json.loads(read("evals/cases.json"))

    check("plugin.name", plugin.get("name") == "ai-job-finder-skill", str(plugin.get("name")))
    check("marketplace.plugins не пуст", bool(marketplace.get("plugins")))
    entry = (marketplace.get("plugins") or [{}])[0]
    check("имя плагина в маркетплейсе совпадает", entry.get("name") == plugin.get("name"))
    check("версия плагина совпадает с маркетплейсом", entry.get("version") == plugin.get("version"))
    changelog = read("CHANGELOG.md")
    check(
        f"версия {plugin.get('version')} есть в CHANGELOG",
        f"[{plugin.get('version')}]" in changelog,
    )
    check("source плагина указывает на корень", entry.get("source") == "./")

    print("\nEvals")
    case_list = cases.get("cases") or []
    check("кейсов >= 6", len(case_list) >= 6, str(len(case_list)))
    ids = [case.get("id") for case in case_list]
    check("id кейсов уникальны", len(ids) == len(set(ids)))
    check(
        "у каждого кейса есть prompt и checks",
        all(case.get("prompt") and case.get("checks") for case in case_list),
    )
    modes = {case.get("mode", "no-tools") for case in case_list}
    check("есть кейсы без инструментов", "no-tools" in modes)
    check("есть live-кейсы", "live" in modes)

    print(f"\nПроверок: {CHECKS}, ошибок: {len(FAILURES)}")
    if FAILURES:
        print("\nЧто исправить:")
        for failure in FAILURES:
            print(f"  - {failure}")
        return 1
    print("Все проверки пройдены.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
