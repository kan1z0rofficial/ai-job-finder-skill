# 🎯 ai-job-finder-skill

[![Release](https://img.shields.io/github/v/release/kan1z0rofficial/ai-job-finder-skill?style=flat-square&label=release)](https://github.com/kan1z0rofficial/ai-job-finder-skill/releases)
[![License](https://img.shields.io/github/license/kan1z0rofficial/ai-job-finder-skill?style=flat-square)](LICENSE)

An AI-agent skill for job search. One `SKILL.md` file, no dependencies, no API keys. Works with Claude Code, Claude Projects, ChatGPT, Codex, OpenClaw, Kimi, and any agent that reads instructions.

> 🇷🇺 Русская версия: [README.md](README.md)

Ask your agent *"find me welding jobs in Tyumen, fly-in rotation"* and get a table of vacancies with salaries, experience requirements, sources, the median salary, and the search date.

## ✨ Features

- 🔍 Search by job title, city, experience, work format, and salary
- 🏢 Office, remote, hybrid, fly-in rotation, shift schedules
- 📊 Fixed output: table + median salary + search date
- 🧾 JSON and CSV export with a fixed schema
- ⚙️ Optional hh.ru API search with a web-search fallback
- 🧠 Asks one clarifying question for missing parameters
- 🔒 Refuses to invent vacancies, auto-apply, or collect personal data
- 🌐 One file for all popular agents

## 📦 Install

### Claude Code — plugin

```text
/plugin marketplace add kan1z0rofficial/ai-job-finder-skill
/plugin install ai-job-finder-skill@ai-job-finder
```

### Claude Code — manual

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

Other platforms: [INSTALL.md](INSTALL.md) (Russian).

## 🚀 Usage

```text
Find welding jobs in Tyumen, fly-in rotation, 3 years of experience
Python developer, remote, from 200k
Accountant in Kazan, office, no experience
```

The skill asks for missing details and returns up to 10 vacancies from hh.ru, Rabota.ru, SuperJob, and Avito Rabota.

Need machine-readable output? Ask for JSON or CSV. The schema is in [references/output.md](references/output.md), and `scripts/format_results.py` converts a JSON file to CSV or Markdown.

With a shell and an hh.ru app token, `scripts/hh_api.py` searches through the official API. Without a token the API may return `403`; the skill falls back to web search instead of bypassing the restriction.

## ⚠️ Limitations

- Requires an agent with web search or browser access.
- Job boards may show CAPTCHAs or partial results.
- Salary figures are often incomplete or pre-tax; the median is approximate.
- The skill never applies to jobs or sends a resume.
- Not affiliated with any job board.

## 🧱 Repository layout

```text
.claude-plugin/   Claude Code plugin + marketplace
evals/            behavioural cases
references/       source URL rules
scripts/          contract checks, hh.ru URL builder, eval runner
tests/            unit tests
SKILL.md          the skill itself
INSTALL.md        detailed installation
```

## ✅ Checks

```bash
python scripts/check_contract.py
python -m unittest discover -s tests -v
```

## 📄 License

MIT — see [LICENSE](LICENSE).
