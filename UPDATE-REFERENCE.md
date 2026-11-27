# UPDATE reference

Sections moved out of UPDATE.md so that every news run reads less. UPDATE.md has a one-line pointer where each used to be: read the section here only when the run touches that subject (the monthly schedule, profile and health-check tasks, a new event page, the Chop calendar, a Search Console question).

## Search Console (content decisions)

- Tom connected Google Search Console (property `sc-domain:eleventabletennis.com`, read-only) through a local MCP server on his computer. Its tools appear as `mcp__remote-devices__gscServer__*` (load with ToolSearch; start with `list_properties`, then `get_performance_overview`, `get_search_analytics`, `get_search_by_page_query`).
- When those tools are available in a run, check them before choosing what to write: top queries and pages, queries with impressions but few clicks (a page or story that could answer them better), and topics readers search for that Eleven hasn't covered. Let that shape which stories, guides and features get priority and how headlines and summaries are worded. Search Console data lags one to two days, so ignore the last two days.
- Google Analytics (GA4 property `properties/565018754`, read-only) is connected the same way: tools `mcp__remote-devices__gaServer__*` (`run_report`, `run_realtime_report`, `get_account_summaries`). Use it with Search Console: which pages readers actually read, where they come from (country, source), and what holds attention. GA only counts readers who accepted cookies, so treat its numbers as a sample; Search Console is the fuller count of search traffic.
- The tools only work while Tom's computer is on with the Claude desktop app open and the session linked to it. When they aren't there, carry on as normal and say in the closing message that Search Console wasn't available. Never block a run on it.

## Automatic event pages for WTT events

`tools/wtt_sync.py` (every 30 minutes, GitHub) gives every senior WTT event (Contender, Star Contender, Feeder, Champions, Smash, Finals) its own event page as it comes within 3 days, so the live scores, order of play, results and draw flow in with no hand-made page. The event ids come from the match database (`data/matches/events.json`); pages made this way carry `"auto": true` in `data/events.json` and take their dates from WTT's order of play. The sync renders Eleven's poster for each one (the workflow installs a browser only when a poster is missing); they have no write-up. To give one a poster, a venue or a "How it was won" story, edit the entry and delete `"auto": true`, and the sync leaves it alone. Under-15 events never get one (see "Age level" in step 2): the youth, junior, cadet and hopes names are excluded.

## Past events and full draws

- The WTT sync saves every draw WTT has for an event on now (singles, doubles, mixed and team), and the event page shows them as tabs in the draw and as filters in Matches. By hand: `python3 tools/fetch_draw.py <wtt id> "<name>" <utc offset> --all`.
- When an event finishes, its page shows the Champions from the draw. For events not on WTT (continental championships, the Asian Games), add `champions` to the hub in `data/events.json`: `[{"event": "Men's singles", "champion": {"name", "nat"}, "runner_up": {"name", "nat"}, "score": "4-1", "games": "11-5, ..."}]`, leaving out what isn't known.
- Every finished event Eleven did not cover day by day gets a `story` on its hub: three or four paragraphs, "How it was won", in STYLE.md style, covering both draws, the finals, upsets of top seeds and the storylines. Facts come from the draw file or checked sources.

## Event pages for past years

Past years are complete back to 2021 (finished 10 November 2026): every WTT Series event (Feeder, Contender, Star Contender, Champions, Grand Smash, Finals), the World Championships, World Team Championships, Mixed Team World Cup, the Tokyo 2020 and Paris 2024 Olympic Games, the continental championships, the Asian Games and the European Games.

- Events in WTT's results system were made by `tools/backfill_events.py` (read its docstring). Its `draws` step runs in the "Backfill draws" workflow, because WTT only answers GitHub's runners; that pushes the draw files to the `backfill` branch for checking. Its `hubs` step then adds a page for every draw file without one, and repairs known faults in WTT's older records. Run it again only to add an event that was missed.
- Events not in WTT's system (European and Asian championships, the Asian Games, the European Games, the Mixed Team World Cup 2023) are kept by hand with `champions`, as "Past events and full draws" describes. Scores were left out where they could not be confirmed.
- Tokyo 2020 (WTT id 2345) is held in an older Olympic format; its draw file was converted by hand and starts at the last 32.
- Every page from Star Contender level up has a "How it was won" (two short paragraphs for 2021 to 2023). Feeder and Contender pages have none.
- The Oceania Championships 2023 page is kept by hand from Table Tennis Australia's report (winners and runners-up, no scores).
- New events get their pages from `tools/wtt_sync.py` as they start (see "Automatic event pages for WTT events"). New hubs are appended to the end of `events` in data/events.json so existing posters keep their look.
- The events index shows one year at a time (tabs); `/events/#y2024` opens a year.

## Switching off WTT data

`data/switches.json` holds `"wtt": true`. If World Table Tennis ever asks Eleven to stop using its data, set it to `false` and push: the WTT, match and ranking-breakdown syncs stop, live scores and point by point stop within a minute, and player profiles drop the ranking breakdown at the next build. Results, draws and rankings already saved stay on the site until removed by hand. Never change this switch without Tom asking.

## Doubles rankings

`data/doubles-rankings.json` holds the ITTF doubles world rankings (top 400 pairs in men's, women's and mixed doubles), refreshed every Tuesday by the Doubles rankings workflow (`tools/doubles_rankings.py`). The rankings page shows them under Women, Men (Singles/Doubles switch) and Mixed doubles. Everyone in them gets a profile like the singles top 400 (`tools/doubles.py`, `tools/people.py`); `tools/stubs.py` writes stub profiles for new names, and the monthly profile check fills them in like any other stub. Profiles show each player's doubles rankings and partners.

## The Chop: "Likely" versus "In the draw"
A player counts as in the draw if their name appears anywhere in a published draw (data/draws/) for a current or upcoming event, whether or not their match has a time. Once an event's draw is out, no one is shown as "Likely" for it: they're either in the draw, or the guess moves on to their next likely event. Players who have already played an event (for example lost in qualifying) are skipped for it too. Logic in tools/build_chop.py, likely().

## The Chop: results and the Pulse workflow
- The Chop is rebuilt from data on every deploy (`tools/build_site.py` calls `tools/build_chop.py`), and every sync commit triggers a deploy, so its rankings, results, fixtures, draws and calendar update themselves. Nothing on The Chop needs a news run, except the club leagues kept by hand (Champions League, Pro A, China Super League), which have no feed a script can read.
- Recent results: the calendar has a "Recent results" section (`/calendar.html#results`): every defender's result in the last 14 days (WTT and ITTF events from `data/matches`, club matches from `data/clubs` and `data/leagues`), grouped by day. The home page shows the newest six under "Recent results", linking to it.
- `.github/workflows/pulse.yml` keeps the syncs on time. GitHub's scheduler was running the 30-minute WTT sync about every six hours. Pulse stays awake for five and a half hours, starts the WTT sync every 30 minutes, the club sync every hour, the news scan every hour, the match sync and Chop videos every three hours and the league sync once, then starts the next Pulse. Its own cron (every six hours) only restarts the chain if it breaks.
