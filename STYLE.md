# Eleven style guide

Eleven writes like the Guardian's sport desk: clear, confident, plainly told, with the facts doing the work. This guide applies to every short story, full article, feature and guide. Where something isn't covered here, follow the [Guardian and Observer style guide](https://www.theguardian.com/guardian-observer-style-guide-a).

## Attribution

- **Don't attribute what happened.** Results, scores, who plays whom, times, line-ups, records and confirmed withdrawals are facts: state them. Write "Lebrun won 14 of the next 17 points", never "Lebrun won 14 of the next 17 points, according to tennis2table". Keep the source in `sources`, not in the sentence.
- **Do attribute** quotes, opinions, claims that only one outlet has, things not yet confirmed, reasons for an injury or withdrawal that the player or federation hasn't given, and conflicting reports. "Chinese media reported" belongs only where the fact itself is in doubt.
- When a fact is in doubt, say once that it is, then move on. Don't attribute every following sentence.
- Quotes: "said" for news, in the past tense. Name where translated quotes come from the first time ("she told Sina Sports"). Give foreign-language quotes in English only, marked "(translated from French)" or similar; never print the original words as well. Reported speech needs attribution once per paragraph, no more.
- Never write "Eleven understands", "Eleven has learned" or similar unless we have our own sourcing.

## News stories

- **The intro is the news.** One sentence, ideally under 30 words, saying who did what. Lead with the most important or surprising thing, usually a name and a result.
- **Second paragraph** adds the key detail: the score, the turning point, what it means.
- **Then** quotes, context and the other results, in order of importance. Keep every paragraph to one idea, one to three sentences.
- **End** with what happens next (the next opponent or session), stated simply. No summing-up line.
- Story cards (`summary` in news.json): one sentence, intro style, different from the article's standfirst.
- Quick updates (see UPDATE.md): one sentence of summary, then up to four short paragraphs. Same style rules.
- Length: a full article is at least 400 words (see UPDATE.md); short news is a quick update. Reach it with facts, results, context and quotes, never padding: a longer article must still have one idea per paragraph.
- Match reports describe the match: the moment it turned, the run of points, the comeback. One vivid detail beats three scorelines. Give the full scoreline once, for the main match.

### Storylines: find the news in the results

Every report and preview should look for the story behind the scoreline, using what Eleven has already reported (earlier articles, features, the rankings, the event pages) as well as the sources. Read the site first. When one of these applies, make it a main thread, near the top, not a passing clause:

- **A return from injury or a break.** Say what the injury was (if reported), how long the player was out, what they missed and where they were ranked before and now. In the match report, look for signs of rust: slow starts, lost leads, wasted game points, short rallies, anything the player says about rhythm, stiffness or confidence. Never invent a physical problem; describe what the match showed and what the player or reliable reports said. Follow it in the next round's preview and review.
- **A withdrawal or injury during an event,** and what it does to the draw.
- **A former world No 1 or champion** losing early, or a run of defeats.
- **A first:** first title, first win over a top-10 player, first final, first medal for a country.
- **Revenge or a repeat:** a rematch of a recent final, someone reversing last week's result.
- **Teenagers and veterans** beating established players; a big age gap.
- **Ranking consequences:** a result that will change the world No 1 or a top-10 place.
- **Home players** at a home event, and the home nations (England, Scotland, Wales).
- **Streaks:** unbeaten runs, a run of titles, a player who has not dropped a game.

Link to the earlier Eleven story that set the storyline up.

## Shocks and upsets

Every news run reads `data/upsets.json` first (rebuilt on every build by `tools/upsets.py` from the WTT results and the Bundesliga and T.League rubbers of the past four days). It ranks singles results by how unlikely they were, from the world ranking gap, and lists the extra angles (the winner's age, the round and the match labels below). It also labels every recent match and league tie by how it was won (see "Match labels"). The level decides how the result is written.

**Shock** (a top-10 player beaten by someone outside the top 100, a top-3 player beaten by someone outside the top 50, or a winner ranked 25 times lower). This is the story, whatever else happened that day:
- It gets its own story, never a line in a team or day report. If a quick update has already gone out without it, upgrade it.
- The headline names the winner, the gap and the victim, in that order of surprise, and says it was a shock: "16-year-old Yuta Ito, ranked 368th, stuns world No 1 Sora Matsushima". No competition prefix with a colon ("T.League:"); put the competition in the standfirst.
- Verbs with force: stuns, shocks, knocks out, topples, ends (a run). Use "shock" or "stunning" once, in the headline or intro, not both.
- The intro is the gap: age, ranking, who they beat, how. The second paragraph gives the score and the moment it turned. The third tells the reader how big it is: the last time the loser lost to someone ranked that low, their record this season, what the winner had done before (a youth title, a first senior event).
- The team result, the other rubbers and the table go lower down.
- Mark it `"top": true` in news.json so it leads the home page, and add the winner to `data/tag-registry.json` if they are new.

**Upset** (a top-50 player beaten by someone ranked five or more times lower, or a top-10 player beaten by someone outside the top 30): lead the story with it, put it in the headline ("Szudi stuns Togami as Dortmund..."), and say plainly that it was an upset.

**Notable** (a top-100 player beaten by someone ranked three or more times lower): mention it high up in the report, with both rankings, as a surprise. It does not need its own headline.

Never call a result a shock when the numbers mislead: check whether the loser was injured, returning, resting players or playing a dead rubber, and whether the winner's ranking is low only because they are new to senior events, returning from a break or out of the rankings by choice (Fan Zhendong). Say so in the story, and drop the shock framing if it no longer holds.

### Match labels: how the match was won

`data/upsets.json` also labels every recent singles match involving a top-300 player or played in the Bundesliga or T.League (`matches`), and every finished league tie (`ties`), from the score, the game-by-game points, the match length and the match database. Each label has a trigger and the words that go with it. Use the label in the headline or intro when it is the most striking thing about the match, with its number. These are BBC and Guardian register: forceful, never tabloid (no "batters", "annihilates", "hammers" as a verb).

| Label | Trigger | Words |
|---|---|---|
| sweep | No game dropped (3-0, 4-0) | sweeps, wins in straight games, without dropping a game |
| hammering | A sweep with every game won by six points or more | crushes, routs, demolishes, thrashes; give the points dropped ("dropped eight points") |
| routine | The favourite wins with no deuce game and no decider | eases past, cruises, breezes through; never in a headline unless nothing else happened, never for a final |
| ground out | 60 minutes or more (best of five) or 75 or more (best of seven), or three deuce games in a match that was not a sweep | grinds out, outlasts, battles past; give the time ("after 71 minutes") |
| comeback | The winner was two games down or more (0-2, 1-3, 0-3) | comes from two games down, fights back, recovers from 3-1 down. "Reverse sweep" only for exactly 0-2 to 3-2 |
| collapse | The same match from the loser's side | lets slip a 2-0 lead, throws away a 3-1 lead; use it when the loser is the bigger name |
| edged | The match went to a deciding game | edges, squeezes past, a five-game thriller, a seven-game epic; "in a deciding game won 12-10" |
| saved match points | Only when point-by-point data or a source says so; the scores alone cannot prove it | saves match points, wins from match point down, saves three match points |
| 11-0 game | A game won 11-0 | "won a game 11-0", rare at this level and worth a line |
| sudden death | A T.League game settled at 10-10 on its single deciding point (it has no deuce) | on the sudden-death point; never "deuce" in the T.League |

### Match labels: what the result means

| Label | Trigger | Words |
|---|---|---|
| scare | A favourite taken to a decider by someone ranked three or more times lower | survives a scare, is pushed to the limit, is taken the distance |
| streak | A winning run reaches 10, 15, 20..., or a run of 10 or more ends | a 20th straight win, extends unbeaten run, ends X's 21-match winning run |
| revenge | Beats someone who beat them in the past 12 months | gains revenge for last month's defeat in Chongqing |
| first | First win over a current top-10 player in Eleven's records (from 2021), or a first title or final (check) | maiden title, breakthrough win, first win over a top-10 player |
| perfect week | Wins the title without dropping a game in the event | wins the title without dropping a game all week |
| champion out | The defending champion or top seed loses (check the draw and last year's event page; not labelled automatically) | defending champion crashes out, top seed falls |

### Match labels: team ties

| Label | Trigger | Words |
|---|---|---|
| team whitewash | Tie won without losing a rubber | whitewash, wins 3-0 without dropping a rubber |
| final rubber | Tie decided in the last rubber | decided in the final rubber, came down to the last match |
| team turnaround | Team won from two rubbers down | fight back from 2-0 down |

**Guardrails.** One label per headline, carried by its strongest number ("from two games down", "in 71 minutes", "dropped eight points"). Never "hammering" or "crushes" when any game went to deuce. Never "routine" for a final. Vary the verbs within a day's coverage, so no two headlines on the same day share one. A label never outranks a shock or upset: lead with the gap, then the manner ("16-year-old ranked 368th stuns world No 1 on the sudden-death point").

### Writing the news: patterns

These apply to every news story, and most of all when something unexpected happened.
- **Lead with what nobody expected.** Ask what a fan would text a friend. A favourite winning is rarely the news; how they won, who nearly beat them or what it means is.
- **Numbers that do the work go in the headline:** the ranking ("ranked 368th"), the age ("16-year-old"), the score when it is dramatic ("from 3-0 down"), the streak ("ends 21-match run").
- **Strong, specific verbs.** Beats, stuns, edges, survives, saves match points, crushes, ends, sets up. Avoid "claims victory", "secures win", "is victorious".
- **One story, one angle.** If a match day has two big stories, write two stories rather than one headline that tries to hold both.
- **Context makes the scale clear:** a first ever, the last time it happened, a record, a ranking change. Check the match database and earlier Eleven stories for it.
- **Reaction.** For a shock or an upset, look hard for what the winner and the loser said (club and league sites, Japanese, German and Chinese outlets) and quote it high up.
- **Follow it.** A shock creates the next story: the winner's next match, the loser's response, the ranking change. Set it up in the closing paragraph and come back to it.
- **Titles by outsiders** (a WTT champion ranked outside the top 100, a first-time winner, a qualifier or wild card going all the way) follow the same rules as a shock: say how far down the rankings they started, and lead with it.

## Features

- **Register**: Guardian long read and New Yorker: intelligent, precise, sophisticated, with a point of view. Every feature carries substantial historical context, woven through it (see FEATURES.md), and is pitched at newer fans, at both new and established fans, or at expert fans, a third each (see FEATURES.md).
- **Open on a person and a moment**, told as a scene or a single striking fact, not a summary of the argument. Bring in the bigger story by the third or fourth paragraph (the paragraph that tells the reader why this matters now).
- Build the piece around people. Data supports the story; it isn't the story. Give no more than two or three numbers in a paragraph, and round where precision doesn't matter.
- Lists of names and countries go in a chart or a short list sentence, never a whole paragraph of them.
- **Quotes: more of them, and longer.** Let the players speak. A match report or day review should carry quotes from several players, winners and losers, men and women, home players and visitors, not one line from the winner. Each quote from a player or coach can run to two or three sentences (up to about 40 words) when that keeps their meaning and voice; give the full thought rather than a fragment. Use four or more quoted voices in a day review when they exist, and look beyond English sources (tischtennis.de, L'Équipe, Sina, Sohu, Nikkan Sports, Yonhap) for them. Don't quote an outlet's own reporting prose; paraphrase it.
- Let quotes carry voice. Introduce each speaker before the quote, keep quotes exact, and don't follow a quote with a sentence that repeats it.
- Vary sentence length. Short sentences land points; longer ones carry explanation.
- End on an image, a quote or a sharp line that answers or reframes the opening. Never "only time will tell" or a promise of future coverage.
- The method behind original data: one plain sentence ("Eleven checked the birthplace of every player in the top 100").

## Guides

- Answer the question in the first paragraph. Then explain, under subheadings, in the order a newcomer needs.
- Plain, friendly, exact. "You" is fine. Explain every term the first time it appears.

## Headlines and standfirsts

- Sentence case, present tense for news ("Harimoto comes from two down to win Asian title"), no full stop. Active verbs. Name the competition in full (WTT Champions Montpellier, not Montpellier), worked into the sentence rather than as a prefix with a colon where possible.
- Standfirst: one sentence that adds to the headline rather than repeating it.

## House style (Guardian conventions)

- **Numbers**: one to nine in words, 10 and above in figures; figures for all scores, ages, rankings and points. Start sentences with words, not figures.
- **Rankings**: world No 1 (no full stop), the world No 11. "Ranked seventh in the world" is fine too.
- **Rounds**: first round, last 32, last 16, quarter-final, semi-final, final. Lower case.
- **Scores**: 11-8, 3-1, with a hyphen. A match score in games ("won 3-1"), a game score in points ("took the decider 11-2"). Write "two games to love" only if the phrase helps.
- **Times and dates**: 6.30pm, 11am, midday; 27 October, Sunday 1 November. Say "UK time" or "local time" when it matters.
- **Nations**: South Korea (not Korea) and Taiwan (not Chinese Taipei), except in a team or competition name. "Hong Kong's Doo Hoi Kem". The US, the UK.
- **Words**: teammate, defender, chopper, world champion (lower case), the Olympics, Paris 2024, -ise spellings, organisers. "%" in copy.
- **Names**: full name first, surname after. Keep accents (Félix, Szőcs, Källberg). Chinese, Japanese and Korean names in the order the player uses on the WTT entry list.
- **Second references**: surname only, with no Mr or Ms. For siblings use first names (Félix, Alexis).
- No em dashes. No clichés or hype words: "stunning", "game-changer", "testament to", "sent shockwaves", "showdown", "clash" (as a noun for a match), "landscape", "delve". No "not X but Y" constructions. No exclamation marks.

**Player names.** Write every player's name exactly as their profile has it (the `name` in data/players/<slug>.json), in the same order and with the same accents, never the other way round from another source ("Fang Bo", never "Bo Fang"). The rules live in one place: `data/names.json` (associations that put the family name first, and fixed spellings) and `tools/names.py`, which every sync, the build and the live-score worker use; a profile name automatically wins over the same name reversed. The build prints a "name warning" for any story that reverses a profiled name: fix it before committing. If WTT spells someone differently from their profile, add a line to `fixes` in data/names.json rather than changing it in one place.


## Story times

Everywhere except the story's own byline, publication times read like BBC Sport: "Just now", "5 mins ago", "1 hr ago", "23 hrs ago", "1 day ago", up to "6 days ago", then a date ("8 Nov"). `localtime.js` does this in the reader's browser for every `<time datetime="...T...">` outside `.article-byline` (the full UK date and time is in the tooltip), so new list or card markup only needs a `<time datetime=ISO>` with the full date and time as its text. Fixture times (`data-lt`) and "Updated" lines are left alone.

## "On now" cards

The scores strip's "On now" cards link, best first, to Eleven's event page, Eleven's league page, Eleven's latest story about the event (any story since the event began whose headline or summary names it), WTT's live scores (WTT events only), and otherwise Eleven's schedule. So a story on an event without its own page is what readers reach from the strip: name the competition in the headline or summary ("Europe Cup", "World Para Championships").
