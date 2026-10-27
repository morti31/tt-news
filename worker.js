// Eleven's Worker: serves the static site, plus /api/live, a cached, tidied view of WTT's live
// match data (used with WTT's permission). Everything else is static assets.
//
//   GET /api/live?event=3250   ->  { updated, live: [match], results: [match] }
//
// A match is { code, label, table, status, game, sides: [{name, nat}], score: [a, b],
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
  // "Women's Singles - Round of 32 - Match 14" -> "Women's singles, round of 32"
  const [ev, round] = String(desc || "").split(" - ");
  return [ev && ev[0] + ev.slice(1).toLowerCase(), round && round.toLowerCase()].filter(Boolean).join(", ");
}

const pairs = (s) => String(s || "").split(",").filter(Boolean).map((g) => g.split("-").map(Number));

function utc(s) {
  // "10/27/2026 14:30:00" -> "2026-10-27T14:30:00Z"
  const m = /^(\d+)\/(\d+)\/(\d+) (\d+):(\d+)/.exec(s || "");
  return m ? `${m[3]}-${m[1].padStart(2, "0")}-${m[2].padStart(2, "0")}T${m[4].padStart(2, "0")}:${m[5]}:00Z` : null;
}

function match(card) {
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
    table: card.tableName || null,
    status: live ? "live" : "final",
    game: Number(card.currentGameNumber) || null,
    sides: comps.map((c) => ({ name: (c.players || []).map((p) => playerName(p.playerName, p.playerOrgCode || c.competitiorOrg)).join(" / ") || playerName(c.competitiorName, c.competitiorOrg), nat: c.competitiorOrg })),
    score: pairs((card.overallScores || card.resultOverallScores || "0-0").replace(/,/g, ""))[0] || [0, 0],
    games,
    server: server >= 0 ? server : null,
    start: utc(card.matchDateTime && card.matchDateTime.startDateUTC),
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

async function live(eventId, ctx) {
  const [now, done] = await Promise.all([
    cached(`${WTT}/GetLiveResult?EventId=${eventId}&include_match_card=true`, ctx, 8),
    cached(`${WTT}/GetOfficialResult?EventId=${eventId}&include_match_card=true&take=40`, ctx, 45),
  ]);
  return {
    event: eventId,
    updated: new Date().toISOString(),
    live: (now || []).map((x) => match(x.match_card)).filter(Boolean),
    results: (done || []).map((x) => match(x.match_card)).filter(Boolean),
  };
}

// ---- WTT's YouTube streams: what's live now, or the latest finished stream to watch back
const CHANNEL = "https://www.youtube.com/@WTTGlobal";
const YT_HEADERS = { "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36", "Accept-Language": "en-GB,en;q=0.9" };

async function page(url, ctx, ttl) {
  const cache = caches.default, key = new Request(url);
  const hit = await cache.match(key);
  if (hit) return hit.text();
  const r = await fetch(url, { headers: YT_HEADERS, redirect: "follow" });
  const text = r.ok ? await r.text() : "";
  ctx.waitUntil(cache.put(key, new Response(text, { headers: { "Cache-Control": `max-age=${ttl}` } })));
  return text;
}

const unescapeJson = (s) => { try { return JSON.parse(`"${s}"`); } catch (e) { return s; } };

async function stream(ctx) {
  // The channel's /live address shows the current broadcast when there is one
  const live = await page(`${CHANNEL}/live`, ctx, 60);
  const id = (/<link rel="canonical" href="https:\/\/www\.youtube\.com\/watch\?v=([\w-]{11})"/.exec(live) || [])[1];
  if (id && /"isLiveNow":true/.test(live)) {
    const title = unescapeJson((/"title":"((?:[^"\\]|\\.)*)","lengthSeconds"/.exec(live) || /<meta name="title" content="([^"]*)"/.exec(live) || [])[1] || "");
    return { status: "live", id, title, channel: "World Table Tennis" };
  }
  // Otherwise the most recent stream on the channel's Live tab, to watch back
  const streams = await page(`${CHANNEL}/streams`, ctx, 300);
  const m = /"videoRenderer":\{"videoId":"([\w-]{11})".*?"title":\{"runs":\[\{"text":"((?:[^"\\]|\\.)*)"\}\]/.exec(streams);
  if (m) {
    const upcoming = streams.slice(m.index, m.index + 4000).includes('"upcomingEventData"');
    return { status: upcoming ? "upcoming" : "replay", id: m[1], title: unescapeJson(m[2]), channel: "World Table Tennis" };
  }
  return { status: "none" };
}

const json = (data, status = 200, maxAge = 8) =>
  new Response(JSON.stringify(data), { status, headers: { "Content-Type": "application/json; charset=utf-8", "Cache-Control": `public, max-age=${maxAge}` } });

export default {
  async fetch(req, env, ctx) {
    const url = new URL(req.url);
    if (url.pathname === "/api/live") {
      const id = url.searchParams.get("event") || "";
      if (!/^\d{1,6}$/.test(id)) return json({ error: "event must be a WTT event id" }, 400);
      try {
        return json(await live(id, ctx));
      } catch (err) {
        return json({ error: "Live data is unavailable right now", detail: String(err.message || err) }, 502, 5);
      }
    }
    if (url.pathname === "/api/stream") {
      try {
        return json(await stream(ctx), 200, 60);
      } catch (err) {
        return json({ status: "none", detail: String(err.message || err) }, 200, 30);
      }
    }
    return env.ASSETS.fetch(req);
  },
};
