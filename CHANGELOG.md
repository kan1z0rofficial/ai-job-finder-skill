# Changelog

Формат: [Keep a Changelog](https://keepachangelog.com/ru/1.1.0/), версии по [SemVer](https://semver.org/lang/ru/).

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
