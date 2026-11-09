# Changelog

Формат: [Keep a Changelog](https://keepachangelog.com/ru/1.1.0/), версии по [SemVer](https://semver.org/lang/ru/).

## [1.1.0] — 2026-11-10

### Добавлено

- `references/output.md` — единая схема результата: поля запроса, вакансии, сводка, правила CSV.
- `scripts/format_results.py` — конвертация JSON в CSV, Markdown или нормализованный JSON, пересчёт медианы.
- `tests/test_format_results.py` — 13 тестов на медиану, форматирование, валидацию и CLI.
- В `SKILL.md` добавлен режим машинного вывода: JSON/CSV по схеме, без выдуманных значений.

### Изменено

- README и README.en: раздел про JSON/CSV, обновлённая структура и roadmap.

## [1.0.0] — 2026-11-10

Первая версия с репозиторной обвязкой.

### Добавлено

- Скилл `SKILL.md` для поиска вакансий: параметры, источники, формат ответа, правила безопасности.
- Плагин и маркетплейс Claude Code (`.claude-plugin/`) — установка командой `/plugin install`.
- `INSTALL.md` с инструкциями для Claude Code, Claude Projects, OpenClaw, Codex, ChatGPT и Kimi.
- `references/sources.md` — параметры URL и правила фильтрации по источникам.
- `scripts/hh_url.py` — генератор ссылок hh.ru с area-id, опытом, графиком и зарплатой.
- `scripts/check_contract.py` — статическая проверка frontmatter, ссылок и согласованности файлов.
- `evals/cases.json` и `scripts/run_evals.py` — поведенческие кейсы и опциональный прогон через LLM.
- CI: контрактные проверки и юнит-тесты на каждый push и pull request.
- `README.en.md`, `CONTRIBUTING.md`, `SECURITY.md`, шаблоны issue.

### Исправлено

- Опечатка в пути установки Claude Code (`ai-job-finder-skillh`).
- `SKILL.md` ссылался на README.md вместо INSTALL.md.
- Устаревшее описание структуры репозитория в README.

## [0.1.0] — 2026-10-29

- Первый публичный релиз: `SKILL.md`, `README.md`, `INSTALL.md`, `LICENSE`.
