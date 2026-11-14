# Pending checks

Leads that a news run could not confirm. Every run rechecks these first (see UPDATE.md, step 2): publish and delete when confirmed, delete when shown wrong, otherwise update "last checked". Drop after 7 days unless the fact will confirm itself later.

Format: `- [first seen] Claim. Source of the claim. Checked: ... Would confirm it: ... Last checked: ...`

## Open

- [2026-11-13] Wang Chuqin has a physical problem and needs time to recover before the Mixed Team World Cup (Chengdu, 29 November). Sina mobile headline "楚钦身体出状况需养伤", no named source. Checked: Chinese search found nothing official. Would confirm it: CTTA, Xinhua, CCTV Sports, or Wang or his coach speaking. If confirmed, update his profile `notes` and the Mixed Team World Cup squad story. Rechecks 16:30, 00:40 and 04:30: only self-media pieces (Sohu, Sina k.sina) speculating about his shoulder and knee; still nothing from CTTA, Xinhua or CCTV. Last checked: 2026-11-14 04:30 UTC.
- [2026-11-13] Fan Zhendong spoke at a UNHCR "Sport lights up the future" event, launching a three-year partnership between Anta and UNHCR. Sina repost of a Weibo video only. Checked: search found only the December 2025 Anta and UNHCR deal. Would confirm it: UNHCR, Anta or a named outlet's report. A quick update at most. Recheck 16:30: Chinese search again found only the December 2025 announcement. Last checked: 2026-11-14 04:30 UTC.
- [2026-11-13] Félix and Alexis Lebrun will both play at the WTT Finals Hong Kong. Orange Sports (exclusive, 12 November): https://sports.orange.fr/plus-de-sport/article/tennis-de-table-les-deux-freres-lebrun-iront-au-masters-exclu-CNT000002tEzEh.html (text not readable from the sandbox). Checked: no WTT or FFTT confirmation found. Would confirm it: WTT's list of qualified players for the Finals, or FFTT. Last checked: 2026-11-14 04:30 UTC.
- [2026-11-14] Malaysia won the mixed doubles and women's doubles titles at the Southeast Asian Championships in Kuala Lumpur: Javen Choong and Karen Lyne beat Singapore's Koen Pang and Ser Lin Qian 11-9, 8-11, 11-4, 15-13 in the mixed final; Karen Lyne and Tee Ai Xin won the women's doubles (opponents and score not seen). The Star, 14 November: https://www.thestar.com.my/sport/others/2026/11/14/paddlers-on-the-double (only a truncated excerpt read via the scan; the page could not be fetched from the sandbox). Checked: English search found only 2024 and 2025 reports. Would confirm it: the full Star page, NST, Bernama or the Malaysian or Southeast Asian federation's results. If confirmed, a quick update alongside the team-title stories of 12 November. Last checked: 2026-11-14 04:30 UTC.

## Waiting on events (will confirm themselves)

- [2026-11-13] ETTU Champions League Men last-16 first leg KS Bogoria Grodzisk Mazowiecki v ASD TT Santa Tecla Nulvi on Saturday 14 November (5pm local): add the result to `data/clubs/cl-men.json` and the news once ETTU publishes it. The other first legs were published on 14 November.
- [2026-11-14] ETTU Champions League Men last-16 return-leg dates (December): only Düsseldorf v Pontoise-Cergy (18 December) is in `data/clubs/cl-men.json`. Add the other seven when ETTU or the clubs publish them.
