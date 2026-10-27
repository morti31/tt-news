# The Guide: writing brief

The Guide (`/guide/`) explains table tennis to people getting into it, from the rules to how the professional game and its equipment work. Guides are evergreen: they are updated, not replaced, and they stay out of the news sitemap, Top stories and Latest.

The shelves and planned titles are in `data/guides/plan.json`. A written guide is `data/guides/<slug>.json` (format at the top of `tools/build_guides.py`). Unwritten titles show as "Coming soon", and links to them stay as plain words until they exist.

## Each run

1. Pull `main`. Pick the next three unwritten titles in `plan.json`, in shelf order, skipping any already in an open "Guides for review" pull request (`gh api "repos/morti31/tt-news/pulls?state=open"`).
2. Research each from primary sources first: the ITTF Statutes and Handbook, the WTT website, Table Tennis England, manufacturers' own specification pages for equipment. Use secondary sources only to add context, and name them.
3. Write, build (`python3 tools/build_site.py`), check each page renders, then commit on a branch `guides/YYYY-MM-DD`, push and open a pull request titled "Guides for review: <title>, <title>, <title>". Tom publishes by merging.

## How to write them

Follow STYLE.md (Guardian style) for spelling, numbers, names and tone.


- **Reader**: someone who has just started watching or playing. Assume nothing; explain every term the first time it appears, or link to the glossary.
- **Answer first**: the first paragraph answers the question in the title. Detail follows under `## ` subheadings (four to eight per guide).
- **Length**: 600 to 1,200 words. Long enough to be the best answer on the web for the search, no longer.
- **Accuracy**: every number (dimensions, points, prize money, event counts) checked against a source listed in `sources`. Rules change; say which season's rules apply when it matters ("from the 2026 season"). Set `updated` whenever anything changes.
- **Equipment**: explain how things work and what to buy at each stage. Name real products only as examples, never as paid-sounding recommendations, and give price bands rather than prices.
- **Key points**: three to five one-line takeaways in `key_points`.
- **Links**: three to six internal links per guide, mostly to other guides (`/guide/<slug>.html`), plus `/rankings.html`, `/events/` or event pages where useful. Every guide's last section should send the reader on to the next step.
- **Style**: British English. No em dashes, no clichés ("game-changer", "testament to", "landscape", "delve"), no "not X but Y". Short paragraphs. Second person ("you") is fine.
- **Byline**: `"author": "tom"` for equipment and the club game; `"author": "michael"` for the pro game; `"author": "michelle"` for England-specific guides (keys under `authors` in `data/news.json`).

## SEO

- `slug` is the search phrase, lowercase with hyphens (already set in `plan.json`; don't change it).
- `seo_title` under 60 characters, main phrase first.
- `description` 140 to 155 characters, says what the reader learns.
- `summary` one or two sentences for the shelf card and standfirst, different from the description.
