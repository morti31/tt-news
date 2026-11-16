# Pending checks

Leads that a news run could not confirm. Every run rechecks these first (see UPDATE.md, step 2): publish and delete when confirmed, delete when shown wrong, otherwise update "last checked". Drop after 7 days unless the fact will confirm itself later.

Format: `- [first seen] Claim. Source of the claim. Checked: ... Would confirm it: ... Last checked: ...`

## Open

- [2026-11-13] Wang Chuqin has a physical problem and needs time to recover before the Mixed Team World Cup (Chengdu, 29 November). Sina mobile headline "楚钦身体出状况需养伤", no named source. Checked: Chinese search found nothing official. Would confirm it: CTTA, Xinhua, CCTV Sports, or Wang or his coach speaking. If confirmed, update his profile `notes` and the Mixed Team World Cup squad story. Rechecks 16:30, 00:40, 04:30, 08:15, 12:50, 17:40, 20:40, 00:40 and 18:20: only self-media pieces (Sohu, Sina k.sina) speculating about his shoulder and knee; still nothing from CTTA, Xinhua or CCTV. Last checked: 2026-11-16 00:40 UTC (digest and Chinese, French searches: nothing new).
- [2026-11-13] Fan Zhendong spoke at a UNHCR "Sport lights up the future" event, launching a three-year partnership between Anta and UNHCR. Sina repost of a Weibo video only. Checked: search found only the December 2025 Anta and UNHCR deal. Would confirm it: UNHCR, Anta or a named outlet's report. A quick update at most. Rechecks 16:30, 08:15, 00:40 and 18:20: Chinese search again found only the December 2025 announcement. Last checked: 2026-11-16 00:40 UTC (digest and Chinese, French searches: nothing new).
- [2026-11-13] Félix and Alexis Lebrun will both play at the WTT Finals Hong Kong. Orange Sports (exclusive, 12 November): https://sports.orange.fr/plus-de-sport/article/tennis-de-table-les-deux-freres-lebrun-iront-au-masters-exclu-CNT000002tEzEh.html (text not readable from the sandbox). Checked: no WTT or FFTT confirmation found; a lepetitjournal.com Hong Kong piece on the Lebruns going to Hong Kong turned out to be about the 2025 Finals; an 18:20 search again found only 2025 coverage. Would confirm it: WTT's list of qualified players for the Finals, or FFTT. Last checked: 2026-11-16 00:40 UTC (digest and Chinese, French searches: nothing new).
- [2026-11-15] Liang Jingkun has pulled out of a second WTT event in a row (presumably WTT Star Contender Muscat). Sohu self-media headline "梁靖崑连续放弃2站WTT赛", no named source. Checked: not in the Oman Observer's list of leading Muscat entries, but that list is not complete; nothing from CTTA or WTT. Would confirm it: WTT's Muscat main draw (Wednesday 18 November) or a CTTA or Xinhua report. Last checked: 2026-11-16 00:40 UTC (digest and Chinese, French searches: nothing new).

## Waiting on events (will confirm themselves)

- [2026-11-14] ETTU Champions League Men last-16 return-leg dates (December): only Düsseldorf v Pontoise-Cergy (18 December) is in `data/clubs/cl-men.json`. Add the other seven when ETTU or the clubs publish them. ETTU says Bogoria v Santa Tecla is in Poland in December, no date yet.
- [2026-11-15] ETTU Champions League Women Stage 2 rounds 3 and 4 (15-16 and 19-20 December): pairings and times not yet in `data/clubs/cl-women.json`. Add them when ETTU publishes the fixtures.
