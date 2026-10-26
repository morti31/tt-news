(async function () {
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const day = (iso) => new Date(iso + "T12:00:00");
  const fmt = (iso, o = { day: "numeric", month: "short" }) => day(iso).toLocaleDateString("en-GB", o);

  // Subscription links
  const feed = `${location.origin}/calendar.ics`;
  const webcal = feed.replace(/^https?:/, "webcal:");
  $("sub-google").href = "https://calendar.google.com/calendar/r?cid=" + encodeURIComponent(webcal);
  $("sub-apple").href = webcal;
  $("sub-outlook").href = "https://outlook.live.com/calendar/0/addfromweb?url=" + encodeURIComponent(feed) + "&name=" + encodeURIComponent("Eleven: table tennis");
  $("feed-url").value = feed;
  $("copy").addEventListener("click", async () => {
    try { await navigator.clipboard.writeText(feed); } catch (e) { $("feed-url").select(); document.execCommand("copy"); }
    $("copy").textContent = "Copied";
    setTimeout(() => ($("copy").textContent = "Copy link"), 2000);
  });

  let data;
  try {
    data = await fetch("data/schedule.json", { cache: "no-store" }).then((r) => r.json());
  } catch (e) {
    $("months").innerHTML = '<p class="empty">The schedule didn\'t load. Refresh the page to try again.</p>';
    return;
  }
  $("sched-note").textContent = data.note || "";

  const today = new Date().toISOString().slice(0, 10);
  const events = data.events.filter((e) => e.end >= today).sort((a, b) => a.start.localeCompare(b.start) || a.end.localeCompare(b.end));
  const fixtures = data.fixtures || [];
  const timeFmt = new Intl.DateTimeFormat("en-GB", { weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
  const place = (e) => [e.venue, e.city !== e.country ? e.city : "", e.country].filter(Boolean).join(", ");
  const tier = (p) => [1, 2, 3, 4, 5].filter((n) => p >= n - 0.25).length || 1;
  const dots = (p) => [1, 2, 3, 4, 5].map((n) => `<i class="${n <= tier(p) ? "on" : ""}"></i>`).join("");

  function render(series) {
    const list = series === "All" ? events : events.filter((e) => e.series === series);
    const byMonth = {};
    list.forEach((e) => { const k = e.start.slice(0, 7); (byMonth[k] ||= []).push(e); });
    $("months").innerHTML = Object.entries(byMonth).map(([k, evs]) => `
      <section class="month">
        <h2 class="section-title">${day(k + "-01").toLocaleDateString("en-GB", { month: "long", year: "numeric" })}</h2>
        <ul class="sched-list">${evs.map((e) => {
          const now = e.start <= today;
          const when = e.start === e.end ? fmt(e.start, { weekday: "short", day: "numeric", month: "short" }) : `${fmt(e.start)} to ${fmt(e.end)}`;
          const fx = fixtures.filter((f) => f.event_id === e.id);
          return `<li class="sched-item${now ? " now" : ""} s-${esc(e.series)}">
            <div class="cal"><b>${day(e.start).getDate()}</b><span>${fmt(e.start, { month: "short" })}</span></div>
            <div class="sched-body">
              <div class="sched-top"><h3>${esc(e.name)}</h3>${now ? '<span class="on-now">On now</span>' : ""}</div>
              <p class="sched-meta">${when}${place(e) ? `, ${esc(place(e))}` : ""}</p>
              <p class="sched-meta"><span class="series">${esc(e.type)}</span><span class="level tier-${tier(e.prestige)}" title="Prestige ${e.prestige} out of 5">${dots(e.prestige)}</span></p>
              ${fx.length ? `<details class="sessions"><summary>${fx.length} session times</summary><ul>${fx.map((f) =>
                `<li><span>${timeFmt.format(new Date(f.start))}</span><span>${esc(f.name.split(": ").pop())}</span></li>`).join("")}</ul></details>` : ""}
            </div>
          </li>`;
        }).join("")}</ul>
      </section>`).join("") || '<p class="empty">Nothing scheduled in this group yet.</p>';
    const tbc = (data.tbc || []).filter((t) => series === "All" || t.series === series);
    $("tbc").innerHTML = tbc.map((t) => `<li>${esc(t.name)}<span>${t.year}</span></li>`).join("");
    $("tbc").closest("section").hidden = !tbc.length;
  }

  $("filter").addEventListener("click", (e) => {
    const b = e.target.closest("button");
    if (!b) return;
    document.querySelectorAll("#filter button").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
    render(b.dataset.s);
  });
  render("All");
})();
