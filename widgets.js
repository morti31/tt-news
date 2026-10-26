// Shared panels used on every page: the scores strip, world rankings and "Coming up".
// Each renders only if its container exists on the page.
(async function () {
  const $ = (id) => document.getElementById(id);
  if (!$("ticker") && !$("rankings") && !$("events")) return;
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const day = (iso) => new Date(iso + "T12:00:00");
  const fmt = (iso, o = { day: "numeric", month: "short" }) => day(iso).toLocaleDateString("en-GB", o);
  const today = new Date().toISOString().slice(0, 10);

  let news = {}, sched = {};
  try { news = await fetch("/data/news.json", { cache: "no-store" }).then((r) => r.json()); } catch (e) {}
  try { sched = await fetch("/data/schedule.json", { cache: "no-store" }).then((r) => r.json()); } catch (e) {}
  const events = sched.events || news.events || [];

  // Scores strip, led by anything on now with a link to live scores
  if ($("ticker")) {
    const cards = events.filter((e) => e.start <= today && e.end >= today).map((e) =>
      `<a class="score-card live-card" href="${esc(news.live_results_url || "https://www.worldtabletennis.com/")}" target="_blank" rel="noopener">
        <span class="ev"><span class="live-dot"></span>On now</span>
        <span class="row won"><span>${esc(e.name)}</span></span>
        <span class="row"><span>Live scores on WTT</span></span></a>`);
    (news.results || []).forEach((r) => r.matches.forEach((m) => {
      const sc = /^(\d+)-(\d+)$/.exec(m.score || "");
      if (!sc || !m.loser) return;
      cards.push(`<a class="score-card" href="${esc(r.url)}" target="_blank" rel="noopener">
        <span class="ev" title="${esc(r.event)}">${esc(m.round)}, ${esc(r.event.split(", ")[1] || r.event)}</span>
        <span class="row won"><span>${esc(m.winner)}</span><b>${sc[1]}</b></span>
        <span class="row"><span>${esc(m.loser)}</span><b>${sc[2]}</b></span></a>`);
    }));
    $("ticker").innerHTML = cards.join("");
    if (!cards.length) $("ticker").closest(".ticker").hidden = true;
  }

  // World rankings with men/women toggle
  if ($("rankings") && news.rankings) {
    const ranks = (g) => { $("rankings").innerHTML = news.rankings[g].map((p) => `<li><span>${esc(p.name)}</span><span class="nat">${esc(p.nat)}</span></li>`).join(""); };
    if ($("rank-week")) $("rank-week").innerHTML = `${esc(news.rankings.week)}. <a href="${esc(news.rankings.url)}" target="_blank" rel="noopener">See the full list</a>`;
    $("rank-toggle")?.addEventListener("click", (e) => {
      const b = e.target.closest("button");
      if (!b) return;
      document.querySelectorAll("#rank-toggle button").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
      ranks(b.dataset.g);
    });
    ranks("men");
  }

  // Coming up
  if ($("events")) {
    const n = Number($("events").dataset.count || 7);
    const upcoming = events.filter((e) => e.end >= today).sort((a, b) => a.start.localeCompare(b.start)).slice(0, n);
    $("events").innerHTML = upcoming.map((e) => {
      const now = e.start <= today;
      const when = now ? `On now, until ${fmt(e.end)}` : e.start === e.end ? fmt(e.start) : `${fmt(e.start)} to ${fmt(e.end)}`;
      return `<li class="${now ? "now" : ""}"><div class="cal"><b>${day(e.start).getDate()}</b><span>${fmt(e.start, { month: "short" })}</span></div>
        <div><span class="name">${esc(e.name)}</span><span class="when">${when}</span></div></li>`;
    }).join("");
  }
})();
