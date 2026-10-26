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
    $("lead").innerHTML = "<p>The news feed didn't load. Refresh the page to try again.</p>";
    return;
  }

  $("updated").textContent = "Last updated " + new Date(data.updated).toLocaleString("en-GB", {
    weekday: "long", day: "numeric", month: "long", hour: "2-digit", minute: "2-digit"
  });

  // Live strip
  const today = new Date().toISOString().slice(0, 10);
  const live = data.events.filter((e) => e.start <= today && e.end >= today);
  if (live.length) {
    $("live").innerHTML = '<div class="wrap"><span class="pulse">On now</span>' +
      live.map((e) => `<span>${esc(e.name)}</span>`).join("") +
      `<a href="${esc(data.live_results_url)}" target="_blank" rel="noopener">Live scores on WTT</a></div>`;
    $("live").hidden = false;
  }

  const stories = [...data.stories].sort((a, b) => b.date.localeCompare(a.date));
  const colour = (c) => `var(--cat-${c}, var(--ink))`;
  const tag = (s) => `<span class="tag" style="color:${colour(s.category)}">${esc(s.category)}${s.lang ? ` <span class="translated">translated from ${esc(s.lang)}</span>` : ""}</span>`;
  const meta = (s) => `<div class="meta">${fmt(s.date)}, via ${s.sources.map((x) => `<a href="${esc(x.url)}" target="_blank" rel="noopener">${esc(x.name)}</a>`).join(" and ")}</div>`;

  function render(cat) {
    const list = cat === "All" ? stories : stories.filter((s) => s.category === cat);
    const lead = list.find((s) => s.top) || list[0];
    const rest = list.filter((s) => s !== lead);
    const second = rest.slice(0, 2);
    const others = rest.slice(2);

    $("lead").innerHTML = lead ? `<article>${tag(lead)}<h2>${esc(lead.headline)}</h2><p>${esc(lead.summary)}</p>${meta(lead)}</article>`
      : "<p>Nothing new in this section. Check back after the next update.</p>";
    $("second").innerHTML = second.map((s) => `<article>${tag(s)}<h3>${esc(s.headline)}</h3><p>${esc(s.summary)}</p>${meta(s)}</article>`).join("");
    $("stories").innerHTML = others.map((s) => `<article class="story">${tag(s)}<h3>${esc(s.headline)}</h3><p>${esc(s.summary)}</p>${meta(s)}</article>`).join("");
    $("empty").hidden = others.length > 0;
  }

  $("tabs").addEventListener("click", (e) => {
    const b = e.target.closest("button");
    if (!b) return;
    document.querySelectorAll("#tabs button").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
    render(b.dataset.cat);
  });
  render("All");

  // Results, shown on scoreboard tiles when the score is numeric
  const board = (score) => {
    const m = /^(\d+)-(\d+)$/.exec(score || "");
    if (!m) return score ? `<span class="score-text">${esc(score)}</span>` : "";
    return `<span class="scoreboard" aria-label="${m[1]} to ${m[2]}"><span class="digit win">${m[1]}</span><span class="digit">${m[2]}</span></span>`;
  };
  $("results").innerHTML = data.results.map((r) => `
    <div class="result-event">
      <h3><a href="${esc(r.url)}" target="_blank" rel="noopener">${esc(r.event)}</a></h3>
      ${r.matches.map((m) => `
        <div class="match">
          <div class="who"><span class="round">${esc(m.round)}</span><strong>${esc(m.winner)}</strong>${m.loser ? `<br><span class="loser">beat ${esc(m.loser)}</span>` : ""}</div>
          ${board(m.score)}
        </div>`).join("")}
    </div>`).join("");

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
  const upcoming = data.events.filter((e) => e.end >= today).sort((a, b) => a.start.localeCompare(b.start)).slice(0, 8);
  $("events").innerHTML = upcoming.map((e) => {
    const now = e.start <= today;
    const when = e.start === e.end ? fmt(e.start) : `${fmt(e.start)} to ${fmt(e.end)}`;
    const dots = [1, 2, 3, 4, 5].map((n) => `<i class="${e.prestige >= n - 0.25 ? "on" : ""}"></i>`).join("");
    return `<li class="${now ? "now" : ""}">
      <div class="cal"><b>${day(e.start).getDate()}</b><span>${fmt(e.start, { month: "short" })}</span></div>
      <div><span class="name">${esc(e.name)}</span><span class="when">${now ? "On now, until " + fmt(e.end) : when}. ${esc(e.type)}</span>
      <span class="level" title="Prestige ${e.prestige} out of 5">${dots}</span></div></li>`;
  }).join("");
})();
