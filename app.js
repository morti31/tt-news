(async function () {
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const day = (iso) => new Date(iso + "T12:00:00");
  const fmt = (iso, o = { day: "numeric", month: "short" }) => day(iso).toLocaleDateString("en-GB", o);

  let data;
  try {
    const res = await fetch("data/news.json", { cache: "no-store" });
    data = await res.json();
    try {
      const sch = await fetch("data/schedule.json", { cache: "no-store" }).then((r) => r.json());
      data.events = sch.events;
    } catch (e) { /* fall back to events in news.json */ }
    try {
      data.articles = await fetch("data/article-index.json", { cache: "no-store" }).then((r) => (r.ok ? r.json() : {}));
    } catch (e) { data.articles = {}; }
  } catch (e) {
    $("lead").innerHTML = '<div class="card"><div class="card-body"><p>The news didn\'t load. Refresh the page to try again.</p></div></div>';
    return;
  }

  $("updated").textContent = "Last updated " + new Date(data.updated).toLocaleString("en-GB", {
    weekday: "long", day: "numeric", month: "long", hour: "2-digit", minute: "2-digit"
  });

  // Artwork: a table seen from above, with a ball in flight. Each story gets its own angle and flight path.
  const hash = (str) => { let h = 2166136261; for (const c of str) h = Math.imul(h ^ c.charCodeAt(0), 16777619); return h >>> 0; };
  function art(s, showScore = true) {
    const im = s.image;
    if (im && im.type === "photo") {
      return `<figure class="art photo"><img src="${esc(im.url)}" alt="${esc(im.alt || "")}" loading="lazy">
        <figcaption>${im.caption ? esc(im.caption) + ". " : ""}Photo: <a href="${esc(im.page)}" target="_blank" rel="noopener">${esc(im.credit)}</a>, <a href="${esc(im.licence_url)}" target="_blank" rel="noopener">${esc(im.licence)}</a></figcaption></figure>`;
    }
    if (im && im.type === "cartoon") return `<div class="art cartoon" data-cartoon="${esc(im.src)}"></div>`;
    // Fallback: a line drawing of the table, with the ball's flight varied per story
    const h = hash(s.id);
    const flip = h & 1;
    const x0 = 120, y0 = 250, L = 400, dx = 20, dy = 14, mx = x0 + L / 2;
    const net = [1, 2, 3, 4, 5].map((i) => { const t = i / 6, px = mx + dx - dx * t, py = y0 + dy * t; return `<line x1="${px}" y1="${py}" x2="${px}" y2="${py - 13}" stroke-width=".4"/>`; }).join("");
    const legs = [x0 + 40, x0 + L - 40].map((lx) => `<path d="M${lx - 10} ${y0 + dy + 5} L${lx - 14} ${y0 + dy + 44} M${lx + 10} ${y0 + dy + 5} L${lx + 14} ${y0 + dy + 44}" stroke-width="1.4"/>`).join("");
    const fx = flip ? 180 + (h >> 4) % 60 : 400 + (h >> 4) % 60, fy = y0 - 4;
    const bx = flip ? 380 + (h >> 9) % 90 : 160 + (h >> 9) % 90, by = 150 + (h >> 13) % 70;
    const score = s.score && showScore
      ? `<text x="40" y="96" font-family="Bricolage Grotesque, system-ui, sans-serif" font-weight="600" font-size="64" fill="currentColor" stroke="none" letter-spacing="-.02em">${esc(s.score.replace("-", "–"))}</text>` : "";
    return `<svg class="art" viewBox="0 0 640 360" preserveAspectRatio="xMidYMid slice" role="img" aria-label="Line drawing of a table tennis table">
      <g stroke="currentColor" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <line x1="0" y1="${y0 + dy + 44}" x2="640" y2="${y0 + dy + 44}" stroke-width=".6"/>
        <path d="M${x0 + dx} ${y0} L${x0 + L + dx} ${y0} L${x0 + L} ${y0 + dy} L${x0} ${y0 + dy} Z" fill="#2f5fd0" stroke-width="1.6"/>
        <path d="M${x0 + dx + 4} ${y0 + 1.5} L${x0 + L + dx - 4} ${y0 + 1.5} L${x0 + L - 3} ${y0 + dy - 1.5} L${x0 + 3} ${y0 + dy - 1.5} Z" stroke="#fff" stroke-width=".9"/>
        <line x1="${x0 + 14}" y1="${y0 + dy / 2}" x2="${x0 + L + 6}" y2="${y0 + dy / 2}" stroke="#fff" stroke-width=".7"/>
        <path d="M${x0} ${y0 + dy} L${x0 + L} ${y0 + dy} L${x0 + L} ${y0 + dy + 5} L${x0} ${y0 + dy + 5} Z" fill="currentColor" stroke-width="1"/>
        <path d="M${mx + dx} ${y0} L${mx + dx} ${y0 - 13} L${mx} ${y0 + dy - 13} L${mx} ${y0 + dy}" stroke-width="1.2"/>${net}${legs}
        <path d="M${fx} ${fy} Q${(fx + bx) / 2} ${by - 60} ${bx} ${by}" stroke-width=".8" stroke-dasharray="1 5"/>
        <circle cx="${bx}" cy="${by}" r="5.5" fill="#f37021" stroke-width="1.1"/>
      </g>${score}
    </svg>`;
  }

  // Live notice
  const today = new Date().toISOString().slice(0, 10);
  const live = data.events.filter((e) => e.start <= today && e.end >= today);
  if (live.length) {
    $("live").innerHTML = '<span class="pulse">On now</span>' + live.map((e) => `<span>${esc(e.name)}</span>`).join("") +
      `<a href="${esc(data.live_results_url)}" target="_blank" rel="noopener">Live scores on WTT</a>`;
    $("live").hidden = false;
  }

  // Scores strip
  const cards = [];
  data.results.forEach((r) => r.matches.forEach((m) => {
    const sc = /^(\d+)-(\d+)$/.exec(m.score || "");
    if (!sc || !m.loser) return;
    cards.push(`<a class="score-card" href="${esc(r.url)}" target="_blank" rel="noopener">
      <span class="ev" title="${esc(r.event)}">${esc(m.round)}, ${esc((r.event.split(", ")[1] || r.event))}</span>
      <span class="row won"><span>${esc(m.winner)}</span><b>${sc[1]}</b></span>
      <span class="row"><span>${esc(m.loser)}</span><b>${sc[2]}</b></span></a>`);
  }));
  $("ticker").innerHTML = cards.join("");
  if (!cards.length) $("ticker").parentElement.hidden = true;

  // Stories
  const stories = [...data.stories].sort((a, b) => b.date.localeCompare(a.date));
  const tag = (s) => `<span class="tag" style="color:var(--${s.category}, var(--ink))">${esc(s.category)}${s.lang ? `<span class="translated">, translated from ${esc(s.lang)}</span>` : ""}</span>`;
  const au = data.author || { name: "Eleven" };
  const avatar = (size) => au.photo
    ? `<img class="avatar" src="${esc(au.photo)}" alt="" width="${size}" height="${size}">`
    : `<span class="avatar" style="width:${size}px;height:${size}px;font-size:${size * 0.4}px" aria-hidden="true">${esc(au.name.split(" ").map((w) => w[0]).join("").slice(0, 2))}</span>`;
  const byline = `<span class="byline">${avatar(26)}<span>By ${esc(au.name)}</span></span>`;
  const meta = (s) => `${byline}<div class="meta">${fmt(s.date)}</div>`;
  const card = (s, heading = "h3", sc = true) => {
    const full = (data.articles || {})[s.id];
    const link = full ? full.url : (s.sources[0] || {}).url;
    const ext = full ? "" : ' target="_blank" rel="noopener"';
    const title = link ? `<a class="stretch" href="${esc(link)}"${ext}>${esc(s.headline)}</a>` : esc(s.headline);
    return `<article class="card">${art(s, sc)}<div class="card-body">${tag(s)}<${heading}>${title}</${heading}><p>${esc(s.summary)}</p>${full ? '<p class="read-more">Read the full story</p>' : ""}${meta(s)}</div></article>`;
  };

  function render(cat) {
    const list = cat === "All" ? stories : stories.filter((s) => s.category === cat);
    const lead = list.find((s) => s.top) || list[0];
    const rest = list.filter((s) => s !== lead);
    $("lead").className = "lead";
    $("lead").innerHTML = lead ? card(lead, "h2") : '<div class="card"><div class="card-body"><p>Nothing in this section yet. New stories arrive with each update.</p></div></div>';
    $("second").innerHTML = rest.slice(0, 3).map((s) => card(s, "h3", false)).join("");
    $("stories").innerHTML = rest.slice(3).map((s) => card(s)).join("");
    $("empty").hidden = rest.length > 3;
  }
  // Cartoons are inlined so their speech bubbles use the page's hand-lettered font
  const cartoonCache = {};
  async function fillCartoons() {
    for (const el of document.querySelectorAll("[data-cartoon]:not(.filled)")) {
      const src = el.dataset.cartoon;
      try {
        cartoonCache[src] ??= fetch(src).then((r) => r.text());
        el.innerHTML = await cartoonCache[src];
        el.querySelector("svg")?.setAttribute("preserveAspectRatio", "xMidYMid slice");
        el.classList.add("filled");
      } catch (e) { /* leave the tinted panel showing */ }
    }
  }
  const _render = render;
  render = (cat) => { _render(cat); fillCartoons(); };

  $("tabs").addEventListener("click", (e) => {
    const b = e.target.closest("button");
    if (!b) return;
    document.querySelectorAll("#tabs button").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
    render(b.dataset.cat);
  });
  const fromHash = decodeURIComponent(location.hash.slice(1));
  const startCat = ["International", "England", "Clubs", "Equipment"].includes(fromHash) ? fromHash : "All";
  document.querySelectorAll("#tabs button").forEach((x) => x.setAttribute("aria-pressed", String(x.dataset.cat === startCat)));
  render(startCat);

  // Rankings
  const ranks = (g) => { $("rankings").innerHTML = data.rankings[g].map((p) => `<li><span>${esc(p.name)}</span><span class="nat">${esc(p.nat)}</span></li>`).join(""); };
  $("rank-week").innerHTML = `${esc(data.rankings.week)}. <a href="${esc(data.rankings.url)}" target="_blank" rel="noopener">See the full list</a>`;
  $("rank-toggle").addEventListener("click", (e) => {
    const b = e.target.closest("button");
    if (!b) return;
    document.querySelectorAll("#rank-toggle button").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
    ranks(b.dataset.g);
  });
  ranks("men");

  // Coming up
  const upcoming = data.events.filter((e) => e.end >= today).sort((a, b) => a.start.localeCompare(b.start)).slice(0, 7);
  $("events").innerHTML = upcoming.map((e) => {
    const now = e.start <= today;
    const when = now ? `On now, until ${fmt(e.end)}` : e.start === e.end ? fmt(e.start) : `${fmt(e.start)} to ${fmt(e.end)}`;
    return `<li class="${now ? "now" : ""}"><div class="cal"><b>${day(e.start).getDate()}</b><span>${fmt(e.start, { month: "short" })}</span></div>
      <div><span class="name">${esc(e.name)}</span><span class="when">${when}</span></div></li>`;
  }).join("");
})();
