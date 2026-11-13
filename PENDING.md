# Pending checks

Leads that a news run could not confirm. Every run rechecks these first (see UPDATE.md, step 2): publish and delete when confirmed, delete when shown wrong, otherwise update "last checked". Drop after 7 days unless the fact will confirm itself later.

Format: `- [first seen] Claim. Source of the claim. Checked: ... Would confirm it: ... Last checked: ...`

## Open

- [2026-11-13] World Para Championships, Pattaya (13 to 19 November): day one results for the 12-strong British team (Will Bayley, Bly Twomey, Rob Davies and others) and ITTF's "Shocks from the First Serve" day one report. Checked: ittf.com blocked (403, also through the probe workflow); British Para Table Tennis news page had nothing after the draw. Would confirm it: britishparatabletennis.com or tabletennisengland.co.uk reports, ITTF results through another route, Paralympics GB. This will confirm itself: cover the British results in a story once a report is out. Last checked: 2026-11-13 12:30 UTC.
- [2026-11-13] Wang Chuqin has a physical problem and needs time to recover before the Mixed Team World Cup (Chengdu, 29 November). Sina mobile headline "楚钦身体出状况需养伤", no named source. Checked: Chinese search found nothing official. Would confirm it: CTTA, Xinhua, CCTV Sports, or Wang or his coach speaking. If confirmed, update his profile `notes` and the Mixed Team World Cup squad story. Last checked: 2026-11-13 12:30 UTC.
- [2026-11-13] Fan Zhendong spoke at a UNHCR "Sport lights up the future" event, launching a three-year partnership between Anta and UNHCR. Sina repost of a Weibo video only. Checked: search found only the December 2025 Anta and UNHCR deal. Would confirm it: UNHCR, Anta or a named outlet's report. A quick update at most. Last checked: 2026-11-13 12:30 UTC.

## Waiting on events (will confirm themselves)

- [2026-11-13] ETTU Champions League Men last-16 first legs on 13 November (Saarbrücken v Lille, Hennebont v Ostrov, Hoboken v Priego, Roskilde v Nîmes/Montpellier, Białystok v Suchedniów, Działdowo v El Niño Praha) and Grodzisk Mazowiecki v Nulvi on 14 November: add results to `data/clubs/cl-men.json` and the news once ETTU publishes them.
