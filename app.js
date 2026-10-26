(async function () {
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const day = (iso) => new Date(iso + "T12:00:00");
  const fmt = (iso, o = { day: "numeric", month: "short" }) => day(iso).toLocaleDateString("en-GB", o);

  let data;
  try {
    const res = await fetch("data/news.json", { cache: "no-store" });
    data = await res.json();
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
    const h = hash(s.id);
    const rot = ((h % 25) - 12);
    const side = h & 1 ? 1 : -1;
    const bx = 160 + side * (40 + (h >> 3) % 50), by = 52 + (h >> 7) % 70;
    const c = `var(--${s.category}, var(--International))`, t = `var(--${s.category}-tint, var(--International-tint))`;
    const score = s.score && showScore ? `<g transform="translate(18 18)"><rect width="${22 + s.score.length * 15}" height="40" rx="12" fill="#fff"/><text x="${11 + s.score.length * 7.5}" y="28" text-anchor="middle" font-family="Bricolage Grotesque, system-ui, sans-serif" font-weight="800" font-size="24" fill="#17202b">${esc(s.score.replace("-", "–"))}</text></g>` : "";
    return `<svg class="art" viewBox="0 0 320 180" preserveAspectRatio="xMidYMid slice" role="img" aria-label="Illustration of a table tennis table">
      <rect width="320" height="180" fill="${t}"/>
      <g transform="translate(160 96) scale(.86) rotate(${rot}) translate(-160 -96)">
        <rect x="58" y="44" width="204" height="112" rx="4" fill="${c}"/>
        <rect x="61" y="47" width="198" height="106" rx="2" fill="none" stroke="#fff" stroke-width="3"/>
        <line x1="61" y1="100" x2="259" y2="100" stroke="#fff" stroke-width="1.5"/>
        <line x1="160" y1="36" x2="160" y2="164" stroke="#17202b" stroke-opacity=".55" stroke-width="5" stroke-linecap="round"/>
        <line x1="160" y1="36" x2="160" y2="164" stroke="#fff" stroke-width="1.2" stroke-dasharray="2 3"/>
      </g>
      <path d="M${160 - side * 120} ${150 - (h >> 5) % 40} Q 160 ${by - 50} ${bx} ${by}" fill="none" stroke="#17202b" stroke-opacity=".28" stroke-width="2" stroke-dasharray="1 6" stroke-linecap="round"/>
      <circle cx="${bx}" cy="${by + 10}" r="7" fill="#17202b" fill-opacity=".07"/>
      <circle cx="${bx}" cy="${by}" r="8" fill="#f37021"/>
      <circle cx="${bx - 2.5}" cy="${by - 2.5}" r="2.5" fill="#fff" fill-opacity=".55"/>
      ${score}
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
  $("author-avatar").innerHTML = avatar(56);
  $("about-h").textContent = au.name;
  $("author-bio").textContent = au.bio || "";
  const byline = `<a class="byline" href="#about">${avatar(26)}<span>By ${esc(au.name)}</span></a>`;
  const meta = (s) => `${byline}<div class="meta">${fmt(s.date)}, via ${s.sources.map((x) => `<a href="${esc(x.url)}" target="_blank" rel="noopener">${esc(x.name)}</a>`).join(" and ")}</div>`;
  const card = (s, heading = "h3", sc = true) => `<article class="card">${art(s, sc)}<div class="card-body">${tag(s)}<${heading}>${esc(s.headline)}</${heading}><p>${esc(s.summary)}</p>${meta(s)}</div></article>`;

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
  $("tabs").addEventListener("click", (e) => {
    const b = e.target.closest("button");
    if (!b) return;
    document.querySelectorAll("#tabs button").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
    render(b.dataset.cat);
  });
  render("All");

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
