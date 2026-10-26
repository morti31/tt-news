(async function () {
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const fmtDate = (iso, opts = { day: "numeric", month: "short" }) =>
    new Date(iso + (iso.length === 10 ? "T12:00:00" : "")).toLocaleDateString("en-GB", opts);

  let data;
  try {
    const res = await fetch("data/news.json", { cache: "no-store" });
    data = await res.json();
  } catch (e) {
    $("stories").innerHTML = '<p class="empty">News could not be loaded. Try refreshing.</p>';
    return;
  }

  const updated = new Date(data.updated);
  $("updated").textContent = "Updated " + updated.toLocaleString("en-GB", { weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });

  // Live banner: any event whose dates include today
  const today = new Date().toISOString().slice(0, 10);
  const liveNow = data.events.filter((e) => e.start <= today && e.end >= today);
  if (liveNow.length) {
    const el = $("live");
    el.innerHTML = '<div class="wrap"><strong>On now</strong>' +
      liveNow.map((e) => `<span>${esc(e.name)}</span>`).join("") +
      `<a href="${esc(data.live_results_url)}" target="_blank" rel="noopener">Live scores at WTT &rarr;</a></div>`;
    el.hidden = false;
  }

  // Stories
  const stories = [...data.stories].sort((a, b) => b.date.localeCompare(a.date) || (b.top ? 1 : 0) - (a.top ? 1 : 0));
  const catColour = (c) => `var(--cat-${c}, var(--accent))`;
  const sourceLinks = (s) => s.sources.map((x) => `<a href="${esc(x.url)}" target="_blank" rel="noopener">${esc(x.name)}</a>`).join(", ");

  function renderStories(cat) {
    const list = cat === "All" ? stories : stories.filter((s) => s.category === cat);
    const top = list.find((s) => s.top) || list[0];
    $("top").innerHTML = top ? `
      <article class="top-story">
        <span class="tag" style="color:${catColour(top.category)}">${esc(top.category)}</span>
        <h2>${esc(top.headline)}</h2>
        <p>${esc(top.summary)}</p>
        <div class="meta">${fmtDate(top.date)} &middot; Source: ${sourceLinks(top)}</div>
      </article>` : "";
    const rest = list.filter((s) => s !== top);
    $("stories").innerHTML = rest.map((s) => `
      <article class="story">
        <span class="tag" style="color:${catColour(s.category)}">${esc(s.category)}</span>
        <h3>${esc(s.headline)}</h3>
        <p>${esc(s.summary)}</p>
        <div class="meta">${fmtDate(s.date)} &middot; ${sourceLinks(s)}</div>
      </article>`).join("");
    $("empty").hidden = list.length > 0;
  }

  $("tabs").addEventListener("click", (e) => {
    const b = e.target.closest("button");
    if (!b) return;
    document.querySelectorAll("#tabs button").forEach((x) => x.classList.toggle("active", x === b));
    renderStories(b.dataset.cat);
  });
  renderStories("All");

  // Results
  $("results").innerHTML = data.results.map((r) => `
    <div class="result-event">
      <h3><a href="${esc(r.url)}" target="_blank" rel="noopener">${esc(r.event)}</a></h3>
      ${r.matches.map((m) => `
        <div class="match">
          <span class="round">${esc(m.round)}</span>
          <span><strong>${esc(m.winner)}</strong>${m.loser ? ` <span class="loser">bt ${esc(m.loser)}</span>` : ""}</span>
          <span class="score">${esc(m.score)}</span>
        </div>`).join("")}
    </div>`).join("");

  // Rankings
  function renderRankings(g) {
    $("rankings").innerHTML = data.rankings[g].map((p) => `<li>${esc(p.name)}<span class="nat">${esc(p.nat)}</span></li>`).join("");
  }
  $("rank-week").innerHTML = `${esc(data.rankings.week)} &middot; <a href="${esc(data.rankings.url)}" target="_blank" rel="noopener">Full list</a>`;
  $("rank-toggle").addEventListener("click", (e) => {
    const b = e.target.closest("button");
    if (!b) return;
    document.querySelectorAll("#rank-toggle button").forEach((x) => x.classList.toggle("active", x === b));
    renderRankings(b.dataset.g);
  });
  renderRankings("men");

  // Upcoming events (next 8 not yet finished)
  const upcoming = data.events.filter((e) => e.end >= today).sort((a, b) => a.start.localeCompare(b.start)).slice(0, 8);
  $("events").innerHTML = upcoming.map((e) => {
    const now = e.start <= today;
    const when = e.start === e.end ? fmtDate(e.start) : `${fmtDate(e.start)} to ${fmtDate(e.end)}`;
    const stars = "●".repeat(Math.round(e.prestige));
    return `<li>${esc(e.name)} <span class="stars" title="Prestige ${e.prestige}/5">${stars}</span>
      <span class="when">${now ? '<span class="now">On now</span> &middot; ' : ""}${when} &middot; ${esc(e.type)}</span></li>`;
  }).join("");
})();
