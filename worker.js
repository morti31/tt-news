// Eleven's Worker: serves the static site and a small live-data API built on WTT's live results.
// WTT has given Eleven permission to use this data. Everything else is static assets.
const WTT = "https://wtt-website-api-vm-frontdoor-hhaec5epbhdyfugz.a01.azurefd.net";
const HEADERS = { "Origin": "https://www.worldtabletennis.com", "Referer": "https://www.worldtabletennis.com/", "Accept": "application/json", "User-Agent": "Eleven (tt-news.tommorti.workers.dev)" };

async function wtt(path, ctx, ttl = 20) {
  const url = WTT + path;
  const cache = caches.default, key = new Request(url);
  let res = await cache.match(key);
  if (!res) {
    const r = await fetch(url, { headers: HEADERS, cf: { cacheTtl: ttl } });
    res = new Response(await r.text(), { status: r.status, headers: { "Content-Type": r.headers.get("Content-Type") || "application/json", "Cache-Control": `max-age=${ttl}` } });
    ctx.waitUntil(cache.put(key, res.clone()));
  }
  return res;
}

export default {
  async fetch(req, env, ctx) {
    const url = new URL(req.url);
    if (url.pathname === "/api/wtt-probe") {
      // Temporary: lets the site's maintainer see the shape of WTT's live endpoints
      const path = url.searchParams.get("path") || "";
      if (!path.startsWith("/liveeventsapi/")) return new Response("bad path", { status: 400 });
      const r = await fetch(WTT + path, { headers: HEADERS });
      const text = await r.text();
      return new Response(`STATUS ${r.status}\nLENGTH ${text.length}\n${text.slice(0, Number(url.searchParams.get("n") || 3000))}`, { headers: { "Content-Type": "text/plain; charset=utf-8" } });
    }
    return env.ASSETS.fetch(req);
  },
};
