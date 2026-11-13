// Eleven's Worker: serves the static site, plus /api/live, a cached, tidied view of WTT's live
// match data (used with WTT's permission). Everything else is static assets.
//
//   GET /api/live?event=3250   ->  { updated, live: [match], results: [match] }
//   GET /api/match?event=3250&code=<documentCode>  ->  one match with every point (see matchDetail)
//
// A match is { code, label, table, status, game, sides: [{name, nat, rank}], score: [a, b],
//              games: [[a, b], ...], server: 0|1|null, start (UTC ISO) }.
const WTT = "https://wtt-website-api-vm-frontdoor-hhaec5epbhdyfugz.a01.azurefd.net/liveeventsapi/api/cms";
const HEADERS = { Origin: "https://www.worldtabletennis.com", Referer: "https://www.worldtabletennis.com/", Accept: "application/json" };

// Same spellings as the rest of the site (tools/fetch_draw.py)
const FIXES = { "Felix Lebrun": "Félix Lebrun", "Anton Kallberg": "Anton Källberg", "Joao Geraldo": "João Geraldo",
  "Bernadette Szocs": "Bernadette Szőcs", "Ying Han": "Han Ying", "Peng Yu-Han": "Peng Yu-han" };

const cap = (s) => s.toLowerCase().replace(/(^|[ -])(\p{L})/gu, (m, a, b) => a + b.toUpperCase());

// WTT match cards give "FAMILY Given"; the site writes given name first except for
// Chinese, Korean and similar names, which keep the family name first
const FAMILY_FIRST = new Set(["CHN", "TPE", "KOR", "HKG", "MAC", "PRK"]);
function playerName(raw, org) {
  const words = String(raw || "").trim().split(/\s+/);
  const isFamily = (w) => w === w.toUpperCase() && /\p{L}/u.test(w);
  const family = words.filter(isFamily).map(cap).join(" ");
  const given = words.filter((w) => !isFamily(w)).join(" ");
  const full = (FAMILY_FIRST.has(org) ? `${family} ${given}` : `${given} ${family}`).trim();
  return FIXES[full] || full;
}

function label(desc) {
  // "Women's Singles - Round of 32 - Match 14" -> "Women's singles, last 32" (Guardian style)
  const [ev, round] = String(desc || "").split(" - ");
  const r = round && round.toLowerCase().replace(/^round of (\d+)$/, "last $1").replace(/finals$/, "final");
  return [ev && ev[0] + ev.slice(1).toLowerCase(), r].filter(Boolean).join(", ");
}

const pairs = (s) => String(s || "").split(",").filter(Boolean).map((g) => g.split("-").map(Number));

function utc(s) {
  // "10/27/2026 14:30:00" -> "2026-10-27T14:30:00Z"
  const m = /^(\d+)\/(\d+)\/(\d+) (\d+):(\d+)/.exec(s || "");
  return m ? `${m[3]}-${m[1].padStart(2, "0")}-${m[2].padStart(2, "0")}T${m[4].padStart(2, "0")}:${m[5]}:00Z` : null;
}

// World ranking by ITTF id, from the site's own data/rankings.json (top 100 men and women).
// Players outside the top 100, and doubles pairs, get no rank.
async function rankMap(env, origin, ctx) {
  try {
    const r = await env.ASSETS.fetch(new Request(origin + "/data/rankings.json"));
    if (!r.ok) return {};
    const data = await r.json();
    const out = {};
    for (const g of ["men", "women"]) for (const p of data[g] || []) if (p.ittf_id) out[String(p.ittf_id)] = p.rank;
    return out;
  } catch (e) {
    return {};
  }
}

// Finish time of a played match: WTT gives the start and the length ("00:40:02")
function finish(t) {
  const d = /^(\d+):(\d\d):(\d\d)$/.exec((t && t.duration) || "");
  const st = utc(t && t.startDateUTC);
  if (!d || !st) return {};
  const secs = +d[1] * 3600 + +d[2] * 60 + +d[3];
  return secs > 0 ? { end: new Date(Date.parse(st) + secs * 1000).toISOString() } : {};
}

function match(card, ranks = {}, venue = false) {
  if (!card || !card.competitiors) return null;
  const comps = card.competitiors;
  const live = card.resultStatus !== "OFFICIAL";
  let games = pairs(live ? card.gameScores : card.resultsGameScores || card.gameScores);
  if (live) games = games.slice(0, Math.max(1, Number(card.currentGameNumber) || 1));
  else games = games.filter(([a, b]) => a || b);
  const server = card.action && card.action.serverNext ? comps.findIndex((c) => c.competitiorId === card.action.serverNext) : -1;
  return {
    code: card.documentCode,
    label: label(card.subEventDescription),
    table: (venue && card.venueName) || card.tableName || null,
    status: live ? "live" : "final",
    game: Number(card.currentGameNumber) || null,
    sides: comps.map((c) => {
      const players = c.players || [];
      const rank = players.length <= 1 ? ranks[String((players[0] && players[0].playerId) || c.competitiorId)] : undefined;
      return { name: players.map((p) => playerName(p.playerName, p.playerOrgCode || c.competitiorOrg)).join(" / ") || playerName(c.competitiorName, c.competitiorOrg),
               nat: c.competitiorOrg, ...(rank ? { rank } : {}) };
    }),
    score: pairs((card.overallScores || card.resultOverallScores || "0-0").replace(/,/g, ""))[0] || [0, 0],
    games,
    server: server >= 0 ? server : null,
    start: utc(card.matchDateTime && card.matchDateTime.startDateUTC),
    ...(live ? {} : finish(card.matchDateTime)),
  };
}

async function cached(url, ctx, ttl) {
  const cache = caches.default, key = new Request(url);
  const hit = await cache.match(key);
  if (hit) return hit.json();
  const r = await fetch(url, { headers: HEADERS });
  if (!r.ok) throw new Error(`WTT ${r.status}`);
  const text = await r.text();
  ctx.waitUntil(cache.put(key, new Response(text, { headers: { "Content-Type": "application/json", "Cache-Control": `max-age=${ttl}` } })));
  return JSON.parse(text);
}

// One table in use at the event: its cards name the venue instead of "Table 1"
async function oneTable(eventId, env, origin) {
  try {
    const sched = await (await env.ASSETS.fetch(new Request(origin + "/data/schedule.json"))).json();
    const t = new Set((sched.fixtures || []).filter((f) => f.id.startsWith(`wtt-${eventId}-`) && f.detail).map((f) => f.detail));
    return t.size === 1;
  } catch (e) { return false; }
}

async function live(eventId, ctx, env, origin, all = false) {
  const [now, done, ranks] = await Promise.all([
    cached(`${WTT}/GetLiveResult?EventId=${eventId}&include_match_card=true`, ctx, 8),
    cached(`${WTT}/GetOfficialResult?EventId=${eventId}&include_match_card=true&take=${all ? 150 : 40}`, ctx, 45),   // all: every result of the event (event pages)
    rankMap(env, origin, ctx),
  ]);
  let dbg = null;
  const one = await oneTable(eventId, env, origin);
  const liveNow = (now || []).map((x) => match(x.match_card, ranks, one)).filter(Boolean);
  const results = (done || []).map((x) => match(x.match_card, ranks, one)).filter(Boolean);
  // WTT's result list can lag behind: matches on the order of play that started a while ago and are in neither
  // list are read from their own match card, so every page shows the same score
  try {
    const seen = new Set(liveNow.concat(results).map((m) => String(m.code).replace(/-/g, "").toLowerCase()));
    const sched = await (await env.ASSETS.fetch(new Request(origin + "/data/schedule.json"))).json();
    const t = Date.now();
    const missing = (sched.fixtures || []).filter((f) => f.id.startsWith(`wtt-${eventId}-`) && f.start && Date.parse(f.start) < t - 12 * 6e4 && Date.parse(f.start) > t - 36 * 36e5
      && !seen.has(f.id.slice(`wtt-${eventId}-`.length))).sort((a, b) => b.start.localeCompare(a.start)).slice(0, 12);
    const found = await Promise.all(missing.map(async (f) => {
      const k = f.id.slice(`wtt-${eventId}-`.length).toUpperCase();
      const code = f.code || (k.length >= 12 && /^\d{6}$/.test(k.slice(-6)) ? `${k.slice(0, 11).padEnd(22, "-")}${k.slice(11, -6)}-${k.slice(-6)}`.padEnd(42, "-") : null);
      if (!code) return null;
      try {
        const card = await cached(`${WTT}/GetMatchCardDetails/${eventId}/${encodeURIComponent(code)}?no_cache=true&require_full_msg=true&require_play_by_play_full=true`, ctx, 20);
        const m = match(card, ranks, one);
        if (!m || !m.sides.length || (m.score[0] === 0 && m.score[1] === 0 && !m.games.some(([a, b]) => a || b))) return null;
        const need = Math.ceil((Number((card.matchConfig || {}).bestOfXGames) || 5) / 2);
        if (m.status === "live" && Math.max(...m.score) >= need) { m.status = "final"; m.games = m.games.filter(([a, b]) => a || b); }
        return m;
      } catch (e) { return null; }
    }));
    for (const m of found.filter(Boolean)) (m.status === "live" ? liveNow : results).push(m);
    results.sort((a, b) => String(b.start || "").localeCompare(String(a.start || "")));
  } catch (e) { dbg = String(e && e.stack || e); }
  return { event: eventId, updated: new Date().toISOString(), live: liveNow, results, ...(dbg ? { dbg } : {}) };
}

// ---- One match, point by point: GET /api/match?event=3250&code=TTEMSINGLES-...
// { ...match, best, points: [game, ...] } where each game is a list of
//   { k: "p", s: server 0|1, w: winner 0|1, h, a, tag?: "GP"|"MP" }   a point, score after it, and whether
//                                                                     the leader then has game or match point
//   { k: "to", by: 0|1, h, a }                                        a time-out
async function matchDetail(eventId, code, ctx, env, origin) {
  const url = `${WTT}/GetMatchCardDetails/${eventId}/${encodeURIComponent(code)}?no_cache=true&require_full_msg=true&require_play_by_play_full=true`;
  const [card, ranks] = await Promise.all([cached(url, ctx, 5), rankMap(env, origin, ctx)]);
  const m = match(card, ranks, await oneTable(eventId, env, origin));
  if (!m) throw new Error("No such match");
  const comps = card.competitiors || [];
  const side = (x) => (x === "H" || x === (comps[0] || {}).competitiorId ? 0 : x === "A" || x === (comps[1] || {}).competitiorId ? 1 : null);
  const best = Number((card.matchConfig || {}).bestOfXGames) || 5, need = Math.ceil(best / 2);
  const all = ((card.full_msg || {}).PlayByPlay || []).map((x) => x.MessagePayLoad || {}).filter((x) => x.Competition);
  const msgs = all.filter((x) => Array.isArray(x.Competition.ActionsProgressionByGame))
    .sort((a, b) => Number(b.SequenceNumber) - Number(a.SequenceNumber));
  let acts = msgs.length ? msgs[0].Competition.ActionsProgressionByGame : [];
  if (!acts.length && m.status === "live") {
    // While a match is on, WTT sends only the last few actions (one per message). Keep every action seen so far
    // in the cache, so the list builds up while the match is open; the full record arrives when it finishes.
    const key = new Request(`https://eleven.internal/pbp/${eventId}/${code}`), cache = caches.default;
    let kept = [];
    try { const hit = await cache.match(key); if (hit) kept = await hit.json(); } catch (e) {}
    const seen = new Map(kept.map((a) => [a._n, a]));
    for (const x of all) if (x.Competition.Actions && x.SequenceNumber !== undefined) seen.set(Number(x.SequenceNumber), { ...x.Competition.Actions, _n: Number(x.SequenceNumber) });
    acts = [...seen.values()].sort((a, b) => a._n - b._n);
    ctx.waitUntil(cache.put(key, new Response(JSON.stringify(acts), { headers: { "Cache-Control": "max-age=7200" } })));
  }
  const games = [], won = [0, 0];
  for (const a of acts) {
    const g = /^G(\d+)$/.exec(a.Period || "");
    if (!g) continue;
    const n = Number(g[1]) - 1;
    while (games.length <= n) games.push([]);
    const h = Number(a.ScoreH) || 0, aw = Number(a.ScoreA) || 0;
    if (a.ActionType === "PT" && side(a.IsWinner) !== null) {
      const p = { k: "p", s: side(a.ServerCompetitor), w: side(a.IsWinner), h, a: aw };
      const lead = h > aw ? 0 : aw > h ? 1 : null, top = Math.max(h, aw);
      const over = top >= 11 && Math.abs(h - aw) >= 2;
      const before = m.games.slice(0, n).filter((gm) => gm[lead === 1 ? 1 : 0] > gm[lead === 1 ? 0 : 1]).length;   // games already won by the leader
      if (!over && lead !== null && top >= 10) p.tag = before === need - 1 ? "MP" : "GP";
      games[n].push(p);
    } else if (a.ActionType === "TO" && a.TimeoutStatus === "START") {
      games[n].push({ k: "to", by: side(a.TimeoutRequestedBy), h, a: aw });
    }
  }
  return { ...m, best, points: m.status === "live" ? games : games.filter((g) => g.length), partial: m.status === "live" && !msgs.length };
}

// ---- WTT's YouTube streams: what's live now, or the latest finished stream to watch back
const CHANNEL = "https://www.youtube.com/@WTTGlobal";
const YT_HEADERS = { "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36", "Accept-Language": "en-GB,en;q=0.9" };

async function page(url, ctx, ttl) {
  // YouTube sometimes answers with a consent or error page that lists no videos. That answer is never cached:
  // caching it is what left the home page with no stream and old highlights for up to half an hour.
  const cache = caches.default, key = new Request(url);
  const hit = await cache.match(key);
  if (hit) return hit.text();
  let text = "";
  for (const u of [url, url + (url.includes("?") ? "&" : "?") + "hl=en&gl=GB"]) {
    const r = await fetch(u, { headers: { ...YT_HEADERS, Cookie: "CONSENT=YES+1; SOCS=CAI" }, redirect: "follow" }).catch(() => null);
    text = r && r.ok ? await r.text() : "";
    if (text.includes('"lockupViewModel":{')) break;
  }
  if (text.includes('"lockupViewModel":{')) ctx.waitUntil(cache.put(key, new Response(text, { headers: { "Cache-Control": `max-age=${ttl}` } })));
  return text;
}

const unescapeJson = (s) => { try { return JSON.parse(`"${s}"`); } catch (e) { return s; } };

function streamList(html) {
  // Each video on the channel's Live tab: on air now, scheduled, or finished (watch back)
  return html.split('"lockupViewModel":{').slice(1).map((chunk) => {
    const id = (/"contentId":"([\w-]{11})"/.exec(chunk) || [])[1];
    const title = (/"lockupMetadataViewModel":\{"title":\{"content":"((?:[^"\\]|\\.)*)"/.exec(chunk) || [])[1] || "";
    const head = chunk.slice(0, 8000);
    const when = (/"content":"(Scheduled for [^"]*)"/.exec(chunk) || [])[1] || null;
    return { id, title: unescapeJson(title), live: /"text":"LIVE"/.test(head), upcoming: /Scheduled for|"content":"\d[\d,]* waiting"/.test(chunk.slice(0, 20000)), scheduled: when };
  }).filter((v) => v.id);
}

async function stream(ctx, q) {
  // q: words that identify the event in WTT's stream titles, e.g. "Montpellier"
  const words = String(q || "").toLowerCase().split(/[\s,]+/).filter(Boolean);
  const match = (v) => !words.length || words.every((w) => v.title.toLowerCase().includes(w));
  const list = streamList(await page(`${CHANNEL}/streams`, ctx, 60)).filter(match);
  const live = list.filter((v) => v.live);
  if (live.length) return { status: "live", ...live[0], channel: "World Table Tennis", more: live.slice(1, 4) };
  const done = list.find((v) => !v.upcoming && !v.live);  // newest finished stream first, as the tab lists them
  const next = list.find((v) => v.upcoming);
  if (done) return { status: "replay", ...done, channel: "World Table Tennis", next: next || null };
  if (next) return { status: "upcoming", ...next, channel: "World Table Tennis" };
  return { status: "none" };
}

// ---- WTT's match highlights from the channel's Videos tab, e.g. "Chen Yi vs Peng Yu-Han | WS R32 | #WTTMontpellier 2026"
const EVENTS = { MS: ["M", "men's singles"], WS: ["W", "women's singles"], MD: ["M", "men's doubles"], WD: ["W", "women's doubles"], XD: ["X", "mixed doubles"] };
const ROUNDS = { F: "final", Final: "final", SF: "semi-final", QF: "quarter-final", R16: "last 16", R32: "last 32", R64: "last 64" };

async function highlights(ctx, q) {
  const words = String(q || "").toLowerCase().split(/[\s,]+/).filter(Boolean);
  const out = [];
  for (const v of streamList(await page(`${CHANNEL}/videos`, ctx, 1800))) {
    const parts = v.title.split("|").map((x) => x.trim());
    if (parts.length < 3 || !/ vs /i.test(parts[0]) || /^(LIVE|FULL MATCH)/i.test(v.title)) continue;
    if (words.length && !words.every((w) => v.title.toLowerCase().includes(w))) continue;
    const [code, ...rest] = parts[1].split(/\s+/);
    const ev = EVENTS[code];
    if (!ev) continue;
    const round = ROUNDS[rest.join(" ")] || rest.join(" ");
    out.push({ id: v.id, title: `${parts[0].replace(/ vs /i, " v ")}, ${ev[1]} ${round}`.trim(), gender: ev[0], channel: "World Table Tennis" });
  }
  return { videos: out.slice(0, 16) };
}

const json = (data, status = 200, maxAge = 8) =>
  new Response(JSON.stringify(data), { status, headers: { "Content-Type": "application/json; charset=utf-8", "Cache-Control": `public, max-age=${maxAge}` } });

// data/switches.json: "wtt": false turns off live scores and point by point from World Table Tennis at once
let SWITCHES = null, SWITCHES_AT = 0;
async function switches(env, origin) {
  if (SWITCHES && Date.now() - SWITCHES_AT < 60000) return SWITCHES;
  try { SWITCHES = await (await env.ASSETS.fetch(new Request(origin + "/data/switches.json"))).json(); } catch (e) { SWITCHES = SWITCHES || {}; }
  SWITCHES_AT = Date.now();
  return SWITCHES;
}

export default {
  async fetch(req, env, ctx) {
    const url = new URL(req.url);
    if ((url.pathname === "/api/live" || url.pathname === "/api/match") && (await switches(env, url.origin)).wtt === false) {
      return json({ error: "Live scores are unavailable", disabled: true }, 503, 60);
    }
    // The old workers.dev address and www both go to the main domain (the API stays reachable for tooling)
    if ((url.hostname.endsWith(".workers.dev") && !url.pathname.startsWith("/api/")) || url.hostname === "www.eleventabletennis.com") {
      return Response.redirect("https://eleventabletennis.com" + url.pathname + url.search, 301);
    }
    if (url.pathname === "/api/live") {
      const id = url.searchParams.get("event") || "";
      if (!/^\d{1,6}$/.test(id)) return json({ error: "event must be a WTT event id" }, 400);
      try {
        return json(await live(id, ctx, env, url.origin, url.searchParams.get("all") === "1"));
      } catch (err) {
        return json({ error: "Live data is unavailable right now", detail: String(err.message || err) }, 502, 5);
      }
    }
    if (url.pathname === "/api/match") {
      const id = url.searchParams.get("event") || "", code = url.searchParams.get("code") || "";
      if (!/^\d{1,6}$/.test(id) || !/^[A-Z0-9-]{10,60}$/.test(code)) return json({ error: "event and code are required" }, 400);
      try {
        const d = await matchDetail(id, code, ctx, env, url.origin);
        return json(d, 200, d.status === "live" ? 5 : 300);
      } catch (err) {
        return json({ error: "Match data is unavailable right now", detail: String(err.message || err) }, 502, 5);
      }
    }
    if (url.pathname === "/api/stream") {
      try {
        return json(await stream(ctx, url.searchParams.get("q")), 200, 60);
      } catch (err) {
        return json({ status: "none", detail: String(err.message || err) }, 200, 30);
      }
    }
    if (url.pathname === "/api/highlights") {
      try {
        return json(await highlights(ctx, url.searchParams.get("q")), 200, 600);
      } catch (err) {
        return json({ videos: [], detail: String(err.message || err) }, 200, 60);
      }
    }
    return env.ASSETS.fetch(req);
  },
};
