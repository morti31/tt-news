# Features: one a day

The site calls this section **Analysis** (nav, section heading, labels). The URL stays /features/ and the data category stays "Features".

A daily scheduled run writes one feature (analysis, opinion or original data), at least 1,000 words, and publishes it straight to `main`. There is no approval step, so every fact, name, number and quote must be checked against its source before committing. Tom is told by push notification and asks for changes afterwards if he wants them.

## Each run

1. Pull `main`.
2. Pick the topic, keeping the audience mix (below) level: look at the audience tags on the last six items under **Done** and take the first item under **Up next** whose audience is the least represented there. If a news event makes another backlog idea timely (a result, an injury, a ranking change), take that one instead and write it for whichever audience suits it. When fewer than four ideas are left, add five new ones to the end of **Up next**, tagged so that the backlog stays about a third each.
3. Research, write, build the data and make the cover (below).
4. Move the topic to **Done** with the date and slug, commit everything to `main` and push. Then send Tom a push notification: "Today's feature is live: <headline> <link>", using the clean link `https://eleventabletennis.com/news/<slug>`.

## Audience: a third each

Features aim at three audiences in equal measure over any run of nine, so that every kind of reader is covered. Tag every backlog and Done item `[New]`, `[Both]` or `[Expert]`.

- **[New]: newer fans** (about a third). Assume the reader has watched a Lebrun or Sun Yingsha highlight and wants to know more. Explain every term, rule and name the first time, with no jargon left undefined, and make the reader feel the sport's depth rather than talked down to.
- **[Both]: new and established fans** (about a third). A subject with a way in for the newcomer and a sharper angle, a surprise or new data for the long-time follower: money, the calendar, a player or a family, a place.
- **[Expert]: established, expert fans** (about a third). Assume knowledge of the rankings, the circuit, equipment and the history of the game. Go further and into detail: tactics, rules and their enforcement, governance, finance, technique, with original data and named sources. Don't stop to explain what an expert already knows, but never be impenetrable.

## Voice and history

- **Write like the Guardian's long reads and the New Yorker**: intelligent, precise, sophisticated prose with a distinct point of view, wit used sparingly and never at the expense of accuracy. Build paragraphs that carry an argument; vary rhythm and sentence length; prefer the telling detail, the scene and the well-chosen quote to summary. Use a metaphor only when it clarifies. Respect the reader's intelligence at every level of expertise. Style rules in STYLE.md still apply (no clichés, no em dashes, no "not X but Y").
- **Always bring in historical context, and plenty of it.** Every feature places its subject in the sport's history: how it began, who changed it, which rule, match, player or decision made today possible, with dates and names. Aim for history to run through at least a quarter to a third of the piece, woven into the argument and not parked in a single "background" paragraph: the 1926 founding of the ITTF and the first World Championships in London in 1926, the Japanese sponge revolution of the 1950s, "ping-pong diplomacy" in 1971, the switch to the 40mm plastic ball in 2014 and the move to 11-point games in 2001 are examples of the kind of turning point to look for. Verify every date, name and figure against a reliable source (the ITTF's own history, the museum, books, newspaper archives, federation records), say where a disputed account differs, and never repeat a legend as fact.
- Newer-fan pieces explain the history as a story; expert pieces use it to test a claim or a trend against the record, with figures from earlier decades where they exist.

## How to write it

Follow STYLE.md (Guardian style) throughout; its Features section is the model. In particular:


- **Open on a person and a moment** (recent where the subject has one, or a defining moment from the sport's history): a result, a quote, a decision, told as a scene. Widen out to the bigger story by the third or fourth paragraph.
- **Explain the system behind it**: history first, then money, rules, who decides. Clear explanation built around people rather than lists of numbers, no subheadings. Define jargon for [New] and [Both] pieces; [Expert] pieces may use the sport's own terms.
- **Carry it with quotes**: secondary sources are fine. Quote only words that appear exactly in the published source, and say where they come from in the sentence: "Lebrun told L'Équipe", "Sun Yingsha said in an interview with Xinhua". Don't attribute results or other established facts to an outlet; put those sources in `sources` only. Player and coach quotes can run to two or three sentences (up to about 40 words); use as many voices as the story needs, and don't quote an outlet's own prose. Never invent or tidy a quote. Name translated quotes as translated: "told Sohu (translated from Chinese)".
- **Bring original data together**: every piece has at least one number Eleven worked out itself (a count, a share, an average, a comparison over time), shown in a chart, with the method in one sentence. Keep to two or three numbers per paragraph; lists of names and countries go in the chart.
- **End on an image, a quote or a sharp line** that answers or reframes the opening. Never a promise of future coverage.
- **WTT and the ITTF (for now)**: Eleven relies on WTT's data, so features about WTT or the ITTF stay informational. Same depth, data and history as any other feature, but no verdicts on their business or governance, no "breaking", "blame" or "has failed" framing, and no allegations or speculation about named individuals, ownership or investigations. Report what the published figures, rules and official statements say, give WTT's or the ITTF's own position where one exists, and let readers draw conclusions. Use `"kind": "Analysis"` or `"Feature"` for these, not `"Opinion"`. Player and federation views can be quoted, attributed and balanced.
- Separate fact, reported claims, allegations and opinion clearly. Opinion pieces say they are opinion (`"kind": "Opinion"`) and still get every fact right.
- British English. At least 1,000 words, and longer when the story needs it: a history or a big subject can run to 2,000 words or more. Length must come from reporting, quotes and data, never padding. No em dashes, no clichés ("game-changer", "testament to", "landscape", "delve"), no "not X but Y", no padding.
- Byline: no `"author"` field and no personal names anywhere on the site. Every story, article, feature and guide is credited to the Eleven Team by the build, and the About, Contact and article pages name no individual. Never write the names of Tom, Michael or Michelle in published copy.

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
  "slug": "...", "category": "Features", "kind": "Analysis | Opinion",
  "date": "YYYY-MM-DD", "published": "YYYY-MM-DDTHH:MM:00Z",
  "title": "...", "seo_title": "...", "description": "...", "standfirst": "...",
  "body": ["paragraph", "paragraph with an [internal link](/rankings.html)", "..."],
  "charts": [{"after": 3, "title": "...", "rows": [["label", 12], ["label", 9]], "unit": "%", "note": "How Eleven counted", "source": "[Source](https://...)"}],
  "cover": {"stat": "1 in 4", "label": "short line under the number", "colour": "#3a66e0"},
  "sources": [{"name": "...", "url": "https://..."}]
}
```

Then `python3 tools/feature_cover.py <slug>` (writes `img/features/<slug>.jpg`) and `python3 tools/build_site.py` to check it builds. Commit the article, the cover and this file to `main` with a message like "Feature: <headline>" and push. If the push is rejected because `main` has moved on, run `git pull --rebase origin main` and push again.

## Getting WTT data

The scheduled runs can't reach WTT directly. Use the probe workflow, which runs on GitHub's servers and saves the replies to the `probe` branch:

```
gh api repos/morti31/tt-news/actions/workflows/wtt-probe.yml/dispatches -X POST -f ref=main -f "inputs[paths]=<path or full URL> <path or full URL>"
# wait for the run to finish, then:
git fetch origin probe && git show origin/probe:1.body
```

Paths are under `https://wtt-website-api-vm-frontdoor-hhaec5epbhdyfugz.a01.azurefd.net/liveeventsapi/api/cms/` (for example `GetEventSchedule/<id>` has players' birth dates; `GetOfficialResult?EventId=<id>&include_match_card=true&take=100` has every result). The ranking is in `data/rankings.json`.

## Up next

1. [Both] Where does the prize money go? (analysis, original data: share of WTT prize money to the top 10, top 50 and the rest; men's and women's pay at the same events)
2. [Expert] After the money: what Hungary's sport funding overhaul means for table tennis (feature: TAO's end, the Hungarian federation's state funding, using Tom's published Kálnoki-Kiss interview)
3. [Both] The state of the English club game (feature, data: Table Tennis England membership and league entries, venue losses)
4. [Expert] Why the world's best still play in Germany (feature: Bundesliga and Champions League economics, compared with China's Super League and India's UTT)
5. [Both] Equal billing? (opinion with data: share of coverage given to men's and women's events at the last three majors)
6. [New] Boosting: table tennis's open secret (feature: banned rubber treatments, racket control, enforcement)
7. [Both] Why has table tennis been a niche sport forever? (feature: how the sport was built in the 1920s and 1930s, the Asian centre of gravity, Olympic inclusion in 1988 and why that did not make it mainstream in the West; history from the ITTF's own records and books on the sport's past)

## Done

- 2026-10-27: Exported talent: how many of the world's top 100 learned the game in China? (`chinese-born-players-world-top-100`) [Both]
- 2026-10-28: Why the men's world top 10 has got four years younger while the women's has aged (`average-age-table-tennis-world-top-10`) [Both]
- 2026-10-29: Japan's choppers keep an old art alive as defence disappears from the men's game (`table-tennis-choppers-defenders-history`) [Both]
- 2026-11-01: WTT's money, part one: China's money, and where it actually goes (`wtt-china-money-table-tennis-part-one`) [Both]
- 2026-11-02: WTT's money, part two: where it comes from, and what the 2025 accounts show (`wtt-finances-ittf-accounts-part-two`) [Expert]
- 2026-11-03: Why no two table tennis tables play alike (`table-tennis-tables-speed-bounce-suppliers`) [New]
- 2026-11-05: How much do the top players play? Eleven counted every WTT match since June (`wtt-calendar-player-workload-injuries`) [Expert]
- 2026-11-07: The Lebrun effect: has one family changed French table tennis? (`lebrun-effect-french-table-tennis-licences`) [New]


Series: when a feature runs in parts, name them "<Series>, part one: ..." and "<Series>, part two: ...", link each part to the other in the first paragraph, and publish the parts on consecutive days.
