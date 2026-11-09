# International job sources

URL patterns and filtering rules for LinkedIn, Indeed, Glassdoor, and hh.ru. Use them to build a precise search link instead of guessing parameters.

> Job boards change URL parameters without notice, and some restrict automated access. If a filter does not apply, open the search page and set it manually, then reuse the resulting URL. Never bypass a login wall or CAPTCHA.

## LinkedIn Jobs

```text
https://www.linkedin.com/jobs/search/?keywords=python%20developer&location=Berlin%2C%20Germany&f_TPR=r604800&f_E=2%2C3&f_WT=2
```

| Parameter | Meaning | Values |
|---|---|---|
| `keywords` | role or skills | URL-encoded text |
| `location` | city, region, or country | URL-encoded text |
| `geoId` | LinkedIn location id | numeric, optional |
| `f_TPR` | time since posting | `r86400` (24h), `r604800` (week), `r2592000` (month) |
| `f_E` | experience level | `1` internship, `2` entry, `3` associate, `4` mid-senior, `5` director, `6` executive |
| `f_WT` | workplace type | `1` on-site, `2` remote, `3` hybrid |
| `f_JT` | job type | `F` full-time, `P` part-time, `C` contract, `T` temporary, `I` internship |

Notes:

- Some results require a LinkedIn login; the public page still shows a preview list.
- Do not automate sign-in or scrape profiles.
- Use the public search page only for reading results, not for bulk crawling.

## Indeed

```text
https://www.indeed.com/jobs?q=python+developer&l=Berlin&fromage=7&jt=fulltime
```

| Parameter | Meaning | Values |
|---|---|---|
| `q` | query | `+`-separated words |
| `l` | location | city, region, or postal code |
| `fromage` | posted within days | `1`, `3`, `7`, `14` |
| `jt` | job type | `fulltime`, `parttime`, `contract`, `temporary`, `internship` |
| `radius` | search radius | miles, numeric |

Country domains: `de.indeed.com`, `uk.indeed.com`, `ca.indeed.com`, `au.indeed.com`, `ie.indeed.com`, `fr.indeed.com`, `nl.indeed.com`, `in.indeed.com`, `sg.indeed.com`. Use the local domain for local results.

Notes:

- Indeed aggressively blocks automated traffic. Prefer reading a few result pages over a loop.
- Job descriptions often hide salary in the text; record it as "not specified" if absent.

## Glassdoor

```text
https://www.glassdoor.com/Job/jobs.htm?sc.keyword=python+developer&locT=C&locId=3062478
```

- `sc.keyword` — role or skills;
- `locT=C` + `locId` — city; the numeric id must be looked up on Glassdoor, so a keyword-only search is often simpler;
- Glassdoor is useful for salary context, but its job list may be incomplete.

## hh.ru

For Russia and CIS, see `references/sources.md`: area ids, filters, and the official API. The same output schema applies.

## Cross-source rules

1. **Deduplicate** the same role and company across boards; list sources separated by commas.
2. **Keep the original currency.** Do not convert between currencies in one median. Note whether the salary is annual or monthly.
3. **Record the posting date** and the search date (`YYYY-MM-DD`). Mark vacancies older than a month as possibly stale.
4. **Do not guess** salary, experience, or work authorization. If the listing does not say "visa sponsorship" or "relocation", do not claim it.
5. **Respect access limits.** No login walls bypass, no CAPTCHA solving, no bulk scraping.
6. **Never apply** on the user's behalf or send a resume anywhere.
