# Формат результатов

Один набор данных используется для ответа в чате, JSON и CSV. Схема общая для всех скриптов репозитория.

## JSON

```json
{
  "query": {
    "profession": "сварщик",
    "city": "Тюмень",
    "work_format": "fly-in-fly-out",
    "experience": "1-3",
    "salary_from": 150000,
    "date": "2026-11-10"
  },
  "vacancies": [
    {
      "id": "hh-123456",
      "title": "Сварщик на вахту",
      "company": "ООО «Пример»",
      "city": "Тюмень",
      "work_format": "fly-in-fly-out",
      "experience": "1-3",
      "salary_from": 150000,
      "salary_to": 180000,
      "currency": "RUR",
      "gross": false,
      "source": "hh.ru",
      "url": "https://hh.ru/vacancy/123456",
      "published_at": "2026-11-08",
      "rotation": "60/30"
    }
  ],
  "summary": {
    "found": 1,
    "with_salary": 1,
    "median_salary": 165000
  }
}
```

### Поля запроса

| Поле | Тип | Обязательное | Комментарий |
|---|---|---|---|
| `profession` | string | да | как сформулировал пользователь |
| `city` | string | да | «удалённо по РФ» для удалёнки |
| `work_format` | string | да | одно из значений `work_format` ниже |
| `experience` | string | нет | одно из значений `experience` ниже |
| `salary_from` | integer | нет | нижняя граница пожелания пользователя |
| `date` | string | да | дата поиска, `ГГГГ-ММ-ДД` |

### Поля вакансии

| Поле | Тип | Обязательное | Комментарий |
|---|---|---|---|
| `id` | string | нет | id на источнике |
| `title` | string | да | должность |
| `company` | string | да | работодатель |
| `city` | string | нет | город из объявления |
| `work_format` | string | нет | `office`, `remote`, `hybrid`, `fly-in-fly-out`, `shift`, `flexible` |
| `experience` | string | нет | `none`, `1-3`, `3-6`, `6+` |
| `salary_from` | integer | нет | в единицах валюты, `null` если не указано |
| `salary_to` | integer | нет | в единицах валюты, `null` если не указано |
| `currency` | string | нет | `RUR`, `USD`, `EUR`, `KZT`, `BYN`, `UAH`, `GEL` |
| `gross` | boolean | нет | `true` — до вычета, `false` — на руки, `null` — не указано |
| `source` | string | да | `hh.ru`, `Rabota.ru`, `SuperJob`, `Авито Работа`, `LinkedIn`, `Indeed` |
| `url` | string | нет | ссылка на вакансию |
| `published_at` | string | нет | `ГГГГ-ММ-ДД` |
| `rotation` | string | нет | для вахты: `60/30`, `30/15` и т.п. |

### Сводка

`summary` можно не передавать — `scripts/format_results.py` пересчитает её сам.

- `found` — сколько вакансий в выборке;
- `with_salary` — у скольких указана зарплата;
- `median_salary` — медиана по серединам вилок (округлённая).

Медиана считается по значениям: `(salary_from + salary_to) / 2`, если указаны обе границы; иначе берётся единственная указанная. Вакансии без зарплаты в расчёт не входят.

## CSV

```text
title,company,city,work_format,experience,salary_from,salary_to,currency,gross,source,published_at,rotation,url
```

Правила:

- кодировка UTF-8, разделитель — запятая, первая строка — заголовок;
- отсутствующие значения — пустая строка (не `null` и не `0`);
- `gross` — `true` / `false` / пусто;
- порядок колонок фиксированный.

## Markdown

Таблица из `SKILL.md`:

```text
| # | Должность | Компания | Зарплата | Опыт | Город / формат | Источник |
```

После таблицы — итог: найдено, медиана (если есть), дата поиска. В чате показывается максимум 10 вакансий, в файле — сколько угодно.

## Деградация

- Нет доступа к shell — выведи JSON прямо в ответе, соблюдая имена полей.
- Нет возможности сохранить файл — не обещай CSV-файл, отдай содержимое блоком кода.
- Нет зарплаты — `null` и «не указана» в таблице, без оценок «по рынку».
