# Eleven (working name)

Table tennis news, results, rankings and fixtures on one page.

- `index.html`, `styles.css`, `app.js`: the site
- `data/news.json`: all content, rewritten by each update run
- `data/articles/`: full articles, one JSON file each, added through review pull requests
- `tools/build_site.py`: builds article pages, the archive, sitemap, RSS feed and robots.txt (Cloudflare build command)
- `tools/build_calendar.py`: rebuilds `calendar.ics` from `data/schedule.json`
- `UPDATE.md`: what each update run does

Hosted on Cloudflare Workers from this repository. `wrangler.jsonc` serves the files as static assets; `.assetsignore` keeps the tooling and notes off the live site.
