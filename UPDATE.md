# How each update run works

The site is static. All content lives in `data/news.json`; `index.html`, `styles.css` and `app.js` only change when the design changes. Each scheduled run follows these steps.

1. Pull the latest `main`.
2. Search for table tennis news published since `updated` in `data/news.json`. Check, as a minimum: worldtabletennis.com, ittf.com, tabletennisengland.co.uk, butterflyonline.com, ettu.org, the T.League site, and news for any event in `events` that is on now.
3. Add new stories. For each one:
   - `category` is one of International, England, Clubs, Equipment.
   - Write the headline and a summary of one to three sentences in your own words. No copied sentences, and any quote under 15 words.
   - Link every source used. Leave out anything sources contradict rather than guessing.
   - Mark the single biggest story `"top": true` and remove the flag from the previous one.
4. Remove stories older than 14 days. Keep at most 30.
5. Update `results` with finished matches from events on now or just ended (finals and semi-finals for WTT events, title-deciders for club competitions). Keep the three most recent events.
6. Update `rankings` when a new ITTF ranking week has been published.
7. Remove finished `events` and add newly confirmed ones from the ITTF and club calendars.
8. Set `updated` to the current UTC time, check the JSON parses, then commit with a message like `Update 2026-10-27 09:00` and push.

## Schedule

Every 4 hours as standard. Hourly while an event with prestige 3.5 or above is on (Mixed Team World Cup, WTT Finals, China Super League Finals, Grand Smashes, World Championships, Olympics).
