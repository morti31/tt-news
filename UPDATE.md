# How each update run works

The site is static. All content lives in `data/news.json`; `index.html`, `styles.css` and `app.js` only change when the design changes. Each scheduled run follows these steps.

1. Pull the latest `main`.
2. Search for table tennis news published since `updated` in `data/news.json`, in English and in the original languages. Search in each language with native terms (for example 乒乓球, 国乒, 乒超 in Chinese; 卓球, Tリーグ in Japanese; 탁구 in Korean; Tischtennis in German; tennis de table in French). Check, as a minimum:
   - International: worldtabletennis.com, ittf.com, ettu.org, butterflyonline.com
   - China: Xinhua and China Daily sports, CCTV Sports, NetEase (163.com) and Sina sports, the Chinese Table Tennis Association, China Super League coverage
   - Japan: jtta.or.jp, tleague.jp, TV Tokyo table tennis, Spread Sports
   - Korea: KTTA, Star News Korea, Yonhap
   - Germany: tischtennis.de, ttbl.de, mytischtennis.de
   - France: fftt.com
   - India: Ultimate Table Tennis, TTFI
   - England and UK: tabletennisengland.co.uk, Table Tennis Scotland and Wales
   - news for any event in `events` that is on now

   Write all stories in English. For a story based mainly on a non-English source, add `"lang"` with the language name (for example `"lang": "Chinese"`) and add the language in brackets to the source name, such as `"NetEase (Chinese)"`. Translate names using standard English spellings (Wang Chuqin, not 王楚钦). When English and non-English sources disagree, prefer the most recent report from the source closest to the player or federation, and say who reported it.
3. Add new stories. For each one:
   - `category` is one of International, England, Clubs, Equipment.
   - Write the headline and a summary of one to three sentences in your own words. No copied sentences, and any quote under 15 words.
   - Link every source used. Leave out anything sources contradict rather than guessing.
   - For a story about a single match result, add `"score"` (for example `"3-2"`), which appears on the story's artwork.
   - Give the story an `image` where a suitable one exists, in this order of preference:
     1. A photo of the main player from Wikimedia Commons, only where the file page names that player and the licence is CC0, public domain, CC BY or CC BY-SA. Use crowd or group shots only if the player is clearly the subject. Format: `{"type":"photo","url":"<1280px upload.wikimedia.org thumbnail>","alt":"...","caption":"<who, where, year>","credit":"<author as on the file page>","licence":"CC BY 4.0","licence_url":"...","page":"<Commons file page>"}`.
     2. A generic table tennis photo from Unsplash or Pexels for stories without a single named player (equipment, clubs, rule changes), in the same format with the photographer as credit and "Unsplash Licence" or "Pexels Licence".
     3. An illustration for stories tied to a place or an object: reuse one in `img/cartoons/` if it fits, or add a new one to `tools/draw_illustrations.py` and run it. Match the existing style exactly: black fine-line drawing with hatching, `currentColor` strokes, no colour, no text except plain labels, no jokes or speech bubbles, and never a real person's likeness. Format: `{"type":"cartoon","src":"img/cartoons/<name>.svg"}`.
     4. Otherwise leave `image` out and the site draws its own table illustration.
     Never use photos from news sites, WTT, ITTF or federations, and never use a photo whose licence you could not check.
   - Mark the single biggest story `"top": true` and remove the flag from the previous one.
   Full articles (review first):
   - When a story has enough verified material for roughly 250 to 350 words without padding (usually two or more sources, or one detailed primary source), also write a full article as `data/articles/<slug>.json` with: `slug` (kebab-case, unique), `story_id` (the matching story's `id` in `data/news.json`), `category`, `date`, `published` (UTC ISO), `title` (under 90 characters), `standfirst` (one or two sentences), optional `lang` and `image` (same rules as stories), `body` (a list of paragraphs), and `sources`. Don't pad thin stories: short items stay short.
   - Style: British English, plain and factual, past tense for results, specific numbers and scores, attribution for anything reported rather than confirmed ("according to NetEase"). Keep allegations, reported claims and confirmed fact clearly separate. Quote only words that appear exactly in a source, under 15 words. No AI disclosure line, no clichés, no em dashes, no padding about "the broader landscape".
   - Check every name, score, date and ranking against the sources before writing. If sources conflict, say so in the article or leave the detail out.
   - Never commit full articles to `main`. Put them on a review branch: if an open pull request titled "For review: ..." already exists (`gh pr list --repo morti31/tt-news --state open`), add the new files to its branch; otherwise create a branch `review/YYYY-MM-DD-HHMM` from `main`, commit the article files, push it and open a pull request with `gh pr create --repo morti31/tt-news --base main --title "For review: <number> articles" --body "<one line per article: headline and word count>"`. Tom publishes by merging it. The short version of the story still goes on `main` as normal, and the homepage links it to the full article once merged.
   - Don't commit anything in `news/`, `sitemap.xml`, `robots.txt`, `feed.xml` or `data/article-index.json`: Cloudflare builds those from the article files with `python3 tools/build_site.py` on every deploy.
4. Remove stories older than 14 days. Keep at most 30.
5. Update `results` with finished matches from events on now or just ended (finals and semi-finals for WTT events, title-deciders for club competitions). Keep the three most recent events.
6. Update `rankings` when a new ITTF ranking week has been published.
7. Keep the schedule in `data/schedule.json` current (`data/news.json` no longer holds events):
   - Add newly confirmed tournaments and club competitions from the ITTF/WTT, ETTU, TTBL, T.League, CTTSL and UTT calendars, and move anything in `tbc` into `events` once dates are published. Leave past events in place; the site hides them.
   - Add `fixtures` with real times (UTC, ISO format, with `event_id`, `name`, `start`, `end`, `source`) for any event within the next 14 days: session times as soon as the organiser publishes them, then notable matches once the draw is out, for example `"WTT Champions Frankfurt: Lebrun v Moregard, quarter-final"`. Use times from the organiser, live-score sites (WTT, Flashscore, SofaScore) or the federation, and convert local times to UTC. Keep each fixture's `id` stable when updating its time, so subscribers' calendars update rather than duplicate.
   - Remove fixtures more than 7 days old.
   - Run `python3 tools/build_calendar.py` to rebuild `calendar.ics`, and commit both files.
8. Set `updated` in both JSON files to the current UTC time, check the JSON parses, then commit with a message like `Update 2026-10-27 09:00` and push.

## Schedule

Every 4 hours as standard. Hourly while an event with prestige 3.5 or above is on (Mixed Team World Cup, WTT Finals, China Super League Finals, Grand Smashes, World Championships, Olympics).
