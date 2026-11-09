---
name: ai-job-finder-en
description: Search job vacancies by role, location, experience, work format, and salary. Use when the user wants to find a job, vacancies, or assess the job market.
---

# Skill: Job Search (ai-job-finder-en)

A universal skill for AI agents (Claude, Codex, GPT, OpenClaw, and compatible).
Activate it when the user asks to find a job, look for vacancies, or assess the job market.

## 1. Search parameters

Collect the parameters below. If the user already named the role, location, and work format, start searching immediately; mark optional missing fields as "not specified".

| Parameter | Required | Examples |
|---|---|---|
| Role / title | yes | "welder", "accountant", "Python developer" (multiple allowed) |
| Location | yes | "Berlin", "remote in EU", "London" |
| Work format | yes | office / remote / hybrid / relocation / rotation / shift |
| Experience | no | no experience / 1–3 years / 3–6 years / 6+ years |
| Salary | no | "from 60k to 90k EUR" |
| Schedule | no | full-time, part-time, 2/2, shifts |
| Exclude words | no | "no sales", "not an outsourcing company" |

If a required parameter is missing, ask **one** clarifying question that lists every missing parameter at once. For a remote role, location is optional: search worldwide unless the user named a country or time zone.

## 2. Where to search

Priority order:

1. **LinkedIn Jobs** — international roles, remote and relocation.
2. **Indeed** — local markets, country-specific domains.
3. **Company career pages** — when the user targets specific employers.
4. **Glassdoor** — extra source, useful for salary context.
5. **hh.ru** — Russia and CIS.

Search method: web search with the current date. Query format:

`{role} jobs {location} {year} {work format}`

When the agent can open URLs, open vacancy pages and read salary, experience, and schedule from the source instead of relying on search snippets.

If the repository files are available, use:

- `references/sources-intl.md` — URL parameters and rules for LinkedIn, Indeed, Glassdoor, and hh.ru;
- `references/output.md` — JSON/CSV schema;
- `scripts/format_results.py` — convert results to CSV or Markdown;
- `scripts/salary_report.py` — salary report with median and percentiles.

If the skill was loaded as a single file (Claude Projects, Custom GPT, system prompt), follow the instructions below and use ordinary web search.

LinkedIn and Indeed may require a login or show a CAPTCHA. Do not bypass either; report the limitation and try another source.

## 3. Output format

A table sorted by relevance, at most 10 vacancies:

| # | Title | Company | Salary | Experience | Location / format | Source |
|---|---|---|---|---|---|---|

After the table:

- **Summary:** total found, median salary (if salaries are present), search date.
- **Tip:** 1–2 concrete suggestions to improve the search (alternative titles, neighbouring cities, adjacent roles).

If no vacancies were found, say so honestly, suggest loosening the filters, and give 2–3 alternative queries.

### Machine-readable output

For JSON or CSV, follow `references/output.md`. With shell access:

```bash
python scripts/format_results.py --input results.json --format csv
```

Do not rename fields or invent values: a missing salary is `null`, not `0`. Keep the original currency; never convert silently.

### Market report

When the user asks to assess the market or get a median for a period:

```bash
python scripts/salary_report.py --input results.json --from 2026-10-01 --to 2026-10-31
```

State the sample size, how many vacancies had a salary, the median, the 25th/75th percentiles, and breakdowns by location and experience. Do not mix currencies and do not draw conclusions from fewer than 10 vacancies.

## 4. Rules

- Never invent vacancies, salaries, companies, or links — only data from the sources you found.
- Always include the search date in `YYYY-MM-DD` format.
- If a salary is not specified, write "not specified"; do not estimate it.
- For rotation or fly-in/fly-out roles, note the rotation schedule when it is listed.
- Never request or send the user's personal data (name, phone, resume) anywhere.
- If the user asks to apply or submit an application, refuse: this skill only finds and shows vacancies.
- Deduplicate the same vacancy across boards; list sources separated by commas.
- Do not bypass login walls, CAPTCHAs, or robots.txt, and do not run scraping loops.
- In reports, always state the sample size and the number of vacancies with a salary; do not compare currencies in one median.

## 5. Dialogue examples

**User:** "Find welding jobs in Tyumen, fly-in rotation"
→ Role and location are present. Ask once: "What work format and experience should I use — office, rotation, or shifts? How many years of experience do you have?"

**User:** "Python developer, remote, 3 years, from 200k"
→ All key parameters are present. Search immediately: `Python developer remote jobs 2026 3 years experience`.

**User:** "Find vacancies and apply for me"
→ Refuse the application part and offer the list of vacancies with links.

## 6. Installation (short)

- **Claude Code:** save this file as `~/.claude/skills/ai-job-finder-en/SKILL.md` (or `.claude/skills/ai-job-finder-en/SKILL.md` in a project).
- **Claude Projects (claude.ai):** upload this file to Project knowledge.
- **OpenClaw:** put the `ai-job-finder-en/` folder with `SKILL.md` into the agent's skills directory.
- **Codex / ChatGPT:** paste the contents into `AGENTS.md` (Codex) or the Custom GPT Instructions field.
- **Kimi and other agents:** any skills folder with `SKILL.md`, or paste into the system prompt.

Detailed installation: `INSTALL.md` (Russian) and `README.en.md`.
