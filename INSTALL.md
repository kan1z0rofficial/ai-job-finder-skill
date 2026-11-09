# 📖 Установка и использование ai-job-finder-skill

Подробная инструкция по всем платформам. Если нужен только быстрый старт — см. [README.md](README.md).

## Что делает этот скилл

Скилл превращает любого AI-агента в помощника по поиску работы. Вы пишете, кем и где хотите работать, — агент ищет актуальные вакансии и выдаёт таблицу с зарплатами, опытом и ссылками на источники.

**Форматы работы:** офис, удалёнка, гибрид, вахта, сменный график.

**Источники:** hh.ru, Rabota.ru, SuperJob, Авито Работа.

## Установка по платформам

### 1. Claude Code — плагин (рекомендуется)

В сессии Claude Code выполните:

```text
/plugin marketplace add kan1z0rofficial/ai-job-finder-skill
/plugin install ai-job-finder-skill@ai-job-finder
```

Затем перезапустите сессию или выполните `/reload-plugins`.
Скилл будет доступен как `/ai-job-finder-skill:ai-job-finder-skill` и активируется автоматически на запросы про работу.

Обновление: `claude plugin update ai-job-finder-skill@ai-job-finder` (или через панель `/plugin`).

### 2. Claude Code — вручную

macOS / Linux:

```bash
mkdir -p ~/.claude/skills/ai-job-finder-skill
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

Важно: имя папки должно быть ровно `ai-job-finder-skill`. Если папка названа иначе, агент может не найти скилл.

Для одного проекта используйте `.claude/skills/ai-job-finder-skill/SKILL.md` в корне проекта вместо `~/.claude`.

После установки перезапустите Claude Code.

### 3. Claude Projects (claude.ai)

1. Откройте проект на claude.ai.
2. Перейдите в **Project knowledge**.
3. Загрузите `SKILL.md`.
4. Готово — Claude будет следовать инструкциям в рамках проекта.

В этом режиме доступен только `SKILL.md`. Файлы `references/` и `scripts/` не загружаются, поэтому агент работает по встроенным инструкциям.

### 4. OpenClaw

```bash
mkdir -p ~/.openclaw/skills/ai-job-finder-skill
cp SKILL.md ~/.openclaw/skills/ai-job-finder-skill/
```

Путь к скиллам можно изменить в конфиге агента (`skills.dir`). Перезапустите агента — скилл подхватится автоматически.

### 5. Codex (OpenAI)

Скопируйте содержимое `SKILL.md` в `AGENTS.md` в корне проекта:

```bash
cat SKILL.md >> AGENTS.md
```

Codex прочитает инструкции при старте сессии в этом проекте.

### 6. ChatGPT (Custom GPT)

1. На chat.openai.com: **Explore GPTs → Create**.
2. В поле **Instructions** вставьте содержимое `SKILL.md`.
3. Включите **Web Search** — без него скилл не сможет искать вакансии.
4. Сохраните GPT.

### 7. Kimi и другие агенты

- Если агент поддерживает скиллы — поместите `SKILL.md` в папку скиллов.
- Если нет — вставьте содержимое `SKILL.md` в начало диалога или в системный промпт.

### 8. Английская версия

Для международного рынка (LinkedIn, Indeed, Glassdoor) используйте `SKILL.en.md`:

```bash
mkdir -p ~/.claude/skills/ai-job-finder-en
curl -fsSL https://raw.githubusercontent.com/kan1z0rofficial/ai-job-finder-skill/main/SKILL.en.md \
  -o ~/.claude/skills/ai-job-finder-en/SKILL.md
```

Имя папки — `ai-job-finder-en`, файл внутри должен называться `SKILL.md`.

## Быстрая проверка

Напишите агенту:

> «Найди работу менеджером по продажам в Москве, офис, от 100 тысяч»

Ожидаемое поведение: агент либо задаёт один уточняющий вопрос, либо сразу возвращает таблицу вакансий с колонкой «Источник» и датой поиска.

## Параметры поиска

| Параметр | Обязателен | Пример |
|---|---|---|
| Профессия | ✅ | «токарь», «аналитик», «грузчик» |
| Город | ✅ | «Сургут» (для удалёнки — «по РФ») |
| Формат работы | ✅ | офис / удалённо / гибрид / вахта / смены |
| Опыт | нет | «без опыта», «3 года» |
| Зарплата | нет | «от 120к» |
| График | нет | «2/2», «5/2» |
| Исключить слова | нет | «без продаж», «не аутсорс» |

## Возможные проблемы

| Проблема | Решение |
|---|---|
| Агент не активировал скилл | Проверьте имя папки (`ai-job-finder-skill`) и перезапустите агента |
| Плагин установлен, но скилла нет | Выполните `/reload-plugins` или начните новую сессию |
| Вакансии не находятся | Убедитесь, что у агента включён веб-поиск; ослабьте фильтры — уберите зарплату и опыт, расширьте город |
| Старые вакансии в выдаче | Скилл всегда пишет дату поиска — проверяйте её и уточняйте запрос |
| Агент «галлюцинирует» вакансии | Напишите: «показывай только вакансии из найденных источников, без выдуманных» |
| Пустая выдача на hh.ru | Площадка может показывать капчу; попросите агента открыть сайт в браузере или повторить позже |
