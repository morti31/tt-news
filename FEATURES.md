# Features: one a day

A daily scheduled run writes one feature (analysis, opinion or original data), about 1,000 words, and sends it to Tom for approval as a pull request. Tom approves by merging (that publishes it) or declines by closing. Nothing in Features goes to `main` without his merge.

## Each run

1. Pull `main`. Check open pull requests titled "Feature for review: ..." (`gh api "repos/morti31/tt-news/pulls?state=open"`). If one from an earlier day is still open, still write today's, on its own branch.
2. Pick the topic: the first item under **Up next** that isn't marked done. If a news event makes another backlog idea timely (a result, an injury, a ranking change), take that one instead and say why in the pull request. When fewer than four ideas are left, add five new ones to the end of **Up next** in the same pull request, so Tom can approve or cut them.
3. Research, write, build the data, make the cover (below), then open the pull request and send Tom a push notification: "Today's feature is ready to approve: <headline>".
4. Move the topic to **Done** with the date and slug, in the same pull request.

## How to write it (Tom's style)

- **Open on a news hook**: something that happened in the last few days, a result, a quote, a decision. Two or three sentences, then widen out to the bigger story.
- **Explain the system behind it**: history, money, rules, who decides. Plain explanation in short paragraphs, no jargon, no subheadings.
- **Carry it with quotes**: secondary sources are fine. Quote only words that appear exactly in the published source, and say where they come from in the sentence: "Lebrun told L'Équipe", "Sun Yingsha said in an interview with Xinhua". Keep each quote under 30 words and use no more than five. Never invent or tidy a quote. Name translated quotes as translated: "told Sohu (translated from Chinese)".
- **Bring original data together**: every piece has at least one number Eleven worked out itself (a count, a share, an average, a comparison over time), shown in a chart and explained in the text, with the method in one sentence ("Eleven counted...").
- **End on the open question**: what happens next, what would change it, often a final quote.
- Separate fact, reported claims, allegations and opinion clearly. Opinion pieces say they are opinion (`"kind": "Opinion"`) and still get every fact right.
- British English. About 1,000 words (900 to 1,200). No em dashes, no clichés ("game-changer", "testament to", "landscape", "delve"), no "not X but Y", no padding.
- Byline: Tom Mortimer (`"author": "tom"`).

## SEO

- `slug`: 3 to 7 keyword words, lowercase, hyphens, no dates unless needed (e.g. `chinese-born-players-world-top-100`).
- `title`: the headline (under 90 characters), written for readers.
- `seo_title`: under 60 characters, the phrase people search, main keyword first (e.g. "Chinese-born players in table tennis's world top 100").
- `description`: 140 to 155 characters, says what the reader learns, includes the main keyword.
- `standfirst`: one or two sentences, different from the description.
- Main keyword in the first paragraph; related terms (player names, event names in full) used naturally.
- Two to four internal links in the body with `[words](/path)`: event pages (`/events/<id>.html`), `/rankings.html`, earlier stories (`/news/<slug>.html`). One or two outbound links to the primary sources.
- Every source in `sources`.

## File format

`data/articles/<slug>.json`:

```json
{
  "slug": "...", "category": "Features", "kind": "Analysis | Feature | Opinion",
  "date": "YYYY-MM-DD", "published": "YYYY-MM-DDTHH:MM:00Z", "author": "tom",
  "title": "...", "seo_title": "...", "description": "...", "standfirst": "...",
  "body": ["paragraph", "paragraph with an [internal link](/rankings.html)", "..."],
  "charts": [{"after": 3, "title": "...", "rows": [["label", 12], ["label", 9]], "unit": "%", "note": "How Eleven counted", "source": "[Source](https://...)"}],
  "cover": {"stat": "1 in 4", "label": "short line under the number", "colour": "#3a66e0"},
  "sources": [{"name": "...", "url": "https://..."}]
}
```

Then `python3 tools/feature_cover.py <slug>` (writes `img/features/<slug>.jpg`) and `python3 tools/build_site.py` to check it builds. Commit the article, the cover and this file on a branch `feature/YYYY-MM-DD`, push, and open the pull request with `gh api repos/morti31/tt-news/pulls -X POST -f title="Feature for review: <headline>" -f head=feature/YYYY-MM-DD -f base=main -F body=@body.md`. Make body.md with `python3 tools/review_body.py data/articles/<slug>.json` and add one line on why this topic today.

## Getting WTT data

The scheduled runs can't reach WTT directly. Use the probe workflow, which runs on GitHub's servers and saves the replies to the `probe` branch:

```
gh api repos/morti31/tt-news/actions/workflows/wtt-probe.yml/dispatches -X POST -f ref=main -f "inputs[paths]=<path or full URL> <path or full URL>"
# wait for the run to finish, then:
git fetch origin probe && git show origin/probe:1.body
```

Paths are under `https://wtt-website-api-vm-frontdoor-hhaec5epbhdyfugz.a01.azurefd.net/liveeventsapi/api/cms/` (for example `GetEventSchedule/<id>` has players' birth dates; `GetOfficialResult?EventId=<id>&include_match_card=true&take=100` has every result). The ranking is in `data/rankings.json`.

## Up next

1. The game is getting younger (analysis, original data: average age of the world top 10 and top 50 now against 2010 and 2016)
2. Is the WTT calendar breaking players? (opinion with data: events, rest days and travel for the top 20 in 2026; hook: Wang Chuqin's withdrawal from WTT Champions Montpellier)
3. Where does the prize money go? (analysis, original data: share of WTT prize money to the top 10, top 50 and the rest; men's and women's pay at the same events)
4. After the money: what Hungary's sport funding overhaul means for table tennis (feature: TAO's end, the Hungarian federation's state funding, using Tom's published Kálnoki-Kiss interview)
5. The state of the English club game (feature, data: Table Tennis England membership and league entries, venue losses)
6. The Lebrun effect: has one family changed French table tennis? (feature, data: French licence numbers before and after Paris 2024, crowds)
7. Why the world's best still play in Germany (feature: Bundesliga and Champions League economics, compared with China's Super League and India's UTT)
8. Equal billing? (opinion with data: share of coverage given to men's and women's events at the last three majors)
9. Boosting: table tennis's open secret (feature: banned rubber treatments, racket control, enforcement)

## Done

- 2026-10-27: Exported talent: China-born players in the world top 100 (`chinese-born-players-world-top-100`)
