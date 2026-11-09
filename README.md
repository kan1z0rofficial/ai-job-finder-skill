# 🎯 ai-job-finder-skill

[![Release](https://img.shields.io/github/v/release/kan1z0rofficial/ai-job-finder-skill?style=flat-square&label=release)](https://github.com/kan1z0rofficial/ai-job-finder-skill/releases)
[![License](https://img.shields.io/github/license/kan1z0rofficial/ai-job-finder-skill?style=flat-square)](LICENSE)
[![Stars](https://img.shields.io/github/stars/kan1z0rofficial/ai-job-finder-skill?style=flat-square)](https://github.com/kan1z0rofficial/ai-job-finder-skill/stargazers)
[![Validate](https://github.com/kan1z0rofficial/ai-job-finder-skill/actions/workflows/validate.yml/badge.svg)](https://github.com/kan1z0rofficial/ai-job-finder-skill/actions/workflows/validate.yml)

Универсальный AI-скилл для поиска работы. Один файл `SKILL.md` — без зависимостей, API-ключей и установки пакетов. Работает в Claude Code, Claude Projects, ChatGPT, Codex, OpenClaw, Kimi и любых агентах, которые читают инструкции.

Вы пишете агенту «ищу работу сварщиком в Тюмени, вахта» — получаете таблицу вакансий с зарплатами, опытом и источниками, а также медиану по выборке и дату поиска.

## ✨ Что умеет

- 🔍 **Поиск вакансий** по профессии, городу, опыту, формату работы и зарплате
- 🏢 **Все форматы**: офис, удалёнка, гибрид, вахта, сменный график
- 📊 **Структурированный результат**: таблица + медианная зарплата + дата поиска
- 🧾 **JSON и CSV**: выгрузка для пайплайнов и таблиц по фиксированной схеме
- ⚙️ **Официальный API hh.ru**: поиск без парсинга страниц, с откатом на веб-поиск
- 🧠 **Уточняющие вопросы**: собирает недостающие параметры одним сообщением
- 🔒 **Безопасность**: не выдумывает вакансии, не откликается, не собирает персональные данные
- 🌐 **Кросс-платформенность**: один файл для всех популярных агентов

## 🎬 Демо

<!--
  TODO: запишите 20–30-секундный GIF (запрос → уточнение → таблица),
  положите его в docs/demo.gif и раскомментируйте строку ниже.
  ![Демо](docs/demo.gif)
-->

Пока демо нет — быстрый сценарий проверки:

1. Установите скилл (ниже).
2. Напишите агенту: «Найди работу сварщиком в Тюмени».
3. Агент задаст один уточняющий вопрос про формат и опыт.
4. Ответьте — получите таблицу до 10 вакансий с источниками и медианой зарплат.

## 📦 Установка

### Claude Code — плагин (рекомендуется)

```text
/plugin marketplace add kan1z0rofficial/ai-job-finder-skill
/plugin install ai-job-finder-skill@ai-job-finder
```

После установки перезапустите сессию или выполните `/reload-plugins`.

### Claude Code — вручную

macOS / Linux:

```bash
mkdir -p ~/.claude/skills/ai-job-finder-skill && \
curl -fsSL https://raw.githubusercontent.com/kan1z0rofficial/ai-job-finder-skill/main/SKILL.md \
  -o ~/.claude/skills/ai-job-finder-skill/SKILL.md
```

Windows (PowerShell):

```powershell
$dir = "$env:USERPROFILE\.claude\skills\ai-job-finder-skill"
New-Item -ItemType Directory -Force $dir | Out-Null
Invoke-WebRequest -UseBasicParsing `
  -Uri "https://raw.githubusercontent.com/kan1z0rofficial/ai-job-finder-skill/main/SKILL.md" `
  -OutFile "$dir\SKILL.md"
```

### Остальные агенты

Claude Projects, ChatGPT, Codex, OpenClaw, Kimi — пошагово в [INSTALL.md](INSTALL.md).

## 🚀 Использование

После установки пишите агенту обычными словами:

> «Найди работу сварщиком в Тюмени, вахта, опыт 3 года»

> «Python-разработчик, удалённо, от 200к»

> «Ищу бухгалтера в Казани, офис, без опыта»

Скилл сам уточнит недостающие параметры и выдаст таблицу вакансий с источниками: hh.ru, Rabota.ru, SuperJob, Авито Работа.

### Формат ответа

```text
| # | Должность | Компания | Зарплата | Опыт | Город / формат | Источник |
|---|---|---|---|---|---|---|
| 1 | …         | …        | …        | …    | …              | hh.ru    |

Итог: найдено N вакансий, медиана — X ₽, дата поиска 2026-11-10.
Совет: …
```

Это шаблон: скилл заполняет его только реальными данными из найденных источников.

### JSON и CSV

Для пайплайнов и таблиц:

> «Найди вакансии Python-разработчика в Москве и выведи JSON»

Схема описана в [references/output.md](references/output.md). Если у агента есть shell, он может отформатировать файл скриптом:

```bash
python scripts/format_results.py --input results.json --format csv
python scripts/format_results.py --input results.json --format markdown
```

Без доступа к shell агент отдаёт JSON или CSV прямо в ответе — схема та же.

### Официальный API hh.ru

Если у агента есть shell и токен приложения hh.ru:

```bash
export HH_ACCESS_TOKEN=...
python scripts/hh_api.py --text "сварщик" --area "Тюмень" --limit 20 --format json
```

Без токена API может вернуть `403`. В этом случае скилл не обходит защиту, а переключается на веб-поиск. Скрипт не парсит страницы и не обходит капчу.

## 🧩 Чем отличается от обычного вопроса к ChatGPT

| Обычный запрос | Этот скилл |
|---|---|
| Формат ответа меняется от запуска к запуску | Фиксированные колонки, медиана и дата поиска |
| Может придумать вакансию или ссылку | Явный запрет на выдуманные данные |
| Легко соглашается «откликнуться за вас» | Отказывается совершать действия от имени пользователя |
| Ничего не проверяется в CI | Контрактные тесты и evals в репозитории |

## ⚠️ Ограничения

- Нужен агент с доступом к веб-поиску или браузеру. Без него скилл выдаст только план поиска, а не вакансии.
- hh.ru, Авито и другие площадки могут показывать капчу или отдавать неполную выдачу — это ограничение источника, а не скилла.
- Официальный API hh.ru может требовать токен приложения; без него скилл работает через веб-поиск.
- Зарплаты в вакансиях часто указаны «до вычета» и заполнены не полностью, поэтому медиана приблизительная.
- Скилл **не** откликается на вакансии и **не** отправляет резюме — только ищет и показывает.
- Проект не связан с hh.ru, Rabota.ru, SuperJob и Авито.

## 🗂️ Структура

```text
ai-job-finder-skill/
├── .claude-plugin/          # плагин и маркетплейс для Claude Code
├── .github/                 # CI и шаблоны issue
├── evals/cases.json         # поведенческие кейсы
├── references/sources.md    # параметры URL и правила по источникам
├── references/output.md     # схема JSON и правила CSV
├── scripts/
│   ├── check_contract.py    # статическая проверка репозитория
│   ├── format_results.py    # JSON -> CSV / Markdown
│   ├── hh_api.py            # поиск через официальный API hh.ru
│   ├── hh_url.py            # генератор ссылок hh.ru
│   └── run_evals.py         # прогон кейсов через LLM (опционально)
├── tests/                   # юнит-тесты
├── SKILL.md                 # сам скилл
├── INSTALL.md               # подробная установка
├── README.md / README.en.md
├── CHANGELOG.md
├── CONTRIBUTING.md
└── LICENSE
```

## ✅ Проверки

```bash
python scripts/check_contract.py          # frontmatter, ссылки, согласованность файлов
python -m unittest discover -s tests -v   # юнит-тесты скриптов
```

Поведенческие кейсы лежат в `evals/cases.json`. Их можно прогнать через любой OpenAI-совместимый API:

```bash
export OPENAI_API_KEY=...
python scripts/run_evals.py --run --model gpt-4o-mini
```

Без ключа `--list` покажет кейсы для ручной проверки.

## 🗺️ Roadmap

- [x] Плагин Claude Code и маркетплейс
- [x] Контрактные тесты и CI
- [x] JSON/CSV-вывод для пайплайнов
- [x] Интеграция с API hh.ru
- [ ] Английская версия скилла и поддержка LinkedIn / Indeed
- [ ] Отчёт по рынку зарплат за период

## 🤝 Вклад

PR и issues приветствуются. Перед PR прочитайте [CONTRIBUTING.md](CONTRIBUTING.md) и прогоните `python scripts/check_contract.py`.

Особенно полезны:

- новые источники вакансий (с проверенными URL);
- улучшение промпта без роста `SKILL.md`;
- кейсы в `evals/`;
- переводы.

## 📄 Лицензия

MIT — используйте свободно, см. [LICENSE](LICENSE).

## 💵 Поддержать автора

Если скилл сэкономил время: [dalink.to/k33_official](https://dalink.to/k33_official) (RUB, без VPN).

---

Сделано с ❤️ для тех, кто ищет работу.
