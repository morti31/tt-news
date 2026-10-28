# Features: one a day

A daily scheduled run writes one feature (analysis, opinion or original data), at least 1,000 words, and publishes it straight to `main`. There is no approval step, so every fact, name, number and quote must be checked against its source before committing. Tom is told by push notification and asks for changes afterwards if he wants them.

## Each run

1. Pull `main`.
2. Pick the topic: the first item under **Up next** that isn't already under **Done**. If a news event makes another backlog idea timely (a result, an injury, a ranking change), take that one instead. When fewer than four ideas are left, add five new ones to the end of **Up next**.
3. Research, write, build the data and make the cover (below).
4. Move the topic to **Done** with the date and slug, commit everything to `main` and push. Then send Tom a push notification: "Today's feature is live: <headline> <link>", using the clean link `https://tt-news.tommorti.workers.dev/news/<slug>`.

## How to write it

Follow STYLE.md (Guardian style) throughout; its Features section is the model. In particular:


- **Open on a person and a moment** from the last few days: a result, a quote, a decision, told as a scene. Widen out to the bigger story by the third or fourth paragraph.
- **Explain the system behind it**: history, money, rules, who decides. Plain explanation in short paragraphs, built around people rather than lists of numbers, no jargon, no subheadings.
- **Carry it with quotes**: secondary sources are fine. Quote only words that appear exactly in the published source, and say where they come from in the sentence: "Lebrun told L'Équipe", "Sun Yingsha said in an interview with Xinhua". Don't attribute results or other established facts to an outlet; put those sources in `sources` only. Keep each quote under 30 words and use no more than five. Never invent or tidy a quote. Name translated quotes as translated: "told Sohu (translated from Chinese)".
- **Bring original data together**: every piece has at least one number Eleven worked out itself (a count, a share, an average, a comparison over time), shown in a chart, with the method in one sentence. Keep to two or three numbers per paragraph; lists of names and countries go in the chart.
- **End on an image, a quote or a sharp line** that answers or reframes the opening. Never a promise of future coverage.
- Separate fact, reported claims, allegations and opinion clearly. Opinion pieces say they are opinion (`"kind": "Opinion"`) and still get every fact right.
- British English. At least 1,000 words, and longer when the story needs it: a history or a big subject can run to 2,000 words or more. Length must come from reporting, quotes and data, never padding. No em dashes, no clichés ("game-changer", "testament to", "landscape", "delve"), no "not X but Y", no padding.
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

1. **Next, requested by Tom: write this one next, even if another topic looks more timely.** Choppers and defenders: their history and where they stand now (long feature, 1,500 to 2,500 words). Ideas to check and build on:
   - Hook: Japan's two modern defenders are in the women's top 15: Hitomi Sato (No 8) and Honoka Hashimoto (No 14). Hashimoto beat Chen Yi and Wang Yidi in Japan's 3-2 win over China in the Asian Championships team final this month, and Sato beat Wang Manyu 12-10, 11-4, 15-13 at the US Smash in June (Butterfly called her a "Japanese modern defender"). Germany's Han Ying (No 16, 43) lost in Montpellier this week. Check Sato's and Hashimoto's Montpellier results.
   - History to verify: Richard Bergmann (England, four world singles titles, a defender); Ding Song's chopping in China's 1995 world team final; Joo Se-hyuk (2003 world singles final); Kim Kyung-ah (Athens 2004 Olympic bronze); Chen Xinhua (China then England); Hou Yingchao (2019 All China champion). Confirm every detail from primary or reliable sources.
   - Why defenders declined: the 40mm ball (2000), 11-point games (2001), the plastic ball (from 2014), the expedite rule, faster sponges. Look for published interviews with defenders or coaches on this.
   - Original data: count the defensive players (choppers and long-pimple defenders) in today's men's and women's top 100 (data/rankings.json) and top 20, and compare with an older ranking list if one can be found. Only count players whose style is confirmed by a reliable source; state the method. On a first look, the men's top 50 appears to have no defenders while the women's top 20 has at least three. Also consider Sabine Winter (No 10), whose switch to anti-spin rubber Table Tennis Kingdom covered: say what she plays and don't call her a chopper unless sources do.

2. **Requested by Tom: write this straight after the choppers feature.** Tables: why they are not all the same (long feature, 1,500 to 2,500 words). Which tables are used at which tournaments and in which countries (official suppliers of the WTT, the World Championships, the Olympics and the big national leagues), how table speed and bounce work (top thickness and material, the ITTF bounce rule of 23cm to 25cm from a 30cm drop in the laws, surface coating and friction, temperature, humidity and the floor underneath), what players and coaches have said in published interviews about fast or slow tables, and the comparison with grass, clay and hard tennis courts and with cricket pitches, where conditions are part of the contest. Original data: compare the tables at this season's major events (manufacturer and model, with any published specifications), and check the laws for exactly what is allowed. Verify every manufacturer and event pairing from the event's or manufacturer's own announcement.

3. Is the WTT calendar breaking players? (opinion with data: events, rest days and travel for the top 20 in 2026; hook: Wang Chuqin's withdrawal from WTT Champions Montpellier)
4. Where does the prize money go? (analysis, original data: share of WTT prize money to the top 10, top 50 and the rest; men's and women's pay at the same events)
5. After the money: what Hungary's sport funding overhaul means for table tennis (feature: TAO's end, the Hungarian federation's state funding, using Tom's published Kálnoki-Kiss interview)
6. The state of the English club game (feature, data: Table Tennis England membership and league entries, venue losses)
7. The Lebrun effect: has one family changed French table tennis? (feature, data: French licence numbers before and after Paris 2024, crowds)
8. Why the world's best still play in Germany (feature: Bundesliga and Champions League economics, compared with China's Super League and India's UTT)
9. Equal billing? (opinion with data: share of coverage given to men's and women's events at the last three majors)
10. Boosting: table tennis's open secret (feature: banned rubber treatments, racket control, enforcement)

## Done

- 2026-10-27: Exported talent: how many of the world's top 100 learned the game in China? (`chinese-born-players-world-top-100`)
- 2026-10-28: Why the men's world top 10 has got four years younger while the women's has aged (`average-age-table-tennis-world-top-10`)
