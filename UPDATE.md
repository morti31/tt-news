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
     3. A cartoon for stories tied to a place: reuse one in `img/cartoons/` if it fits, or draw a new 640×360 SVG there in the same style (thick wobbly outlines through the feTurbulence filter, flat colours, a speech bubble with a short joke in Patrick Hand using textLength so it fits). Show places, objects and animals only, never a real person's likeness. Format: `{"type":"cartoon","src":"img/cartoons/<name>.svg"}`.
     4. Otherwise leave `image` out and the site draws its own table illustration.
     Never use photos from news sites, WTT, ITTF or federations, and never use a photo whose licence you could not check.
   - Mark the single biggest story `"top": true` and remove the flag from the previous one.
4. Remove stories older than 14 days. Keep at most 30.
5. Update `results` with finished matches from events on now or just ended (finals and semi-finals for WTT events, title-deciders for club competitions). Keep the three most recent events.
6. Update `rankings` when a new ITTF ranking week has been published.
7. Remove finished `events` and add newly confirmed ones from the ITTF and club calendars.
8. Set `updated` to the current UTC time, check the JSON parses, then commit with a message like `Update 2026-10-27 09:00` and push.

## Schedule

Every 4 hours as standard. Hourly while an event with prestige 3.5 or above is on (Mixed Team World Cup, WTT Finals, China Super League Finals, Grand Smashes, World Championships, Olympics).
