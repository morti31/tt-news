// Shared panels used on every page: the scores strip, world rankings and "Coming up".
// Each renders only if its container exists on the page.
(async function () {
  const $ = (id) => document.getElementById(id);
  if (!$("ticker") && !$("rankings") && !$("events") && !document.querySelector("[data-ad]")) return;
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const day = (iso) => new Date(iso + "T12:00:00");
  const fmt = (iso, o = { day: "numeric", month: "short" }) => day(iso).toLocaleDateString("en-GB", o);
  const today = new Date().toISOString().slice(0, 10);
  const FLAGS = {"CHN": "cn", "JPN": "jp", "KOR": "kr", "PRK": "kp", "HKG": "hk", "MAC": "mo", "SGP": "sg", "IND": "in", "IRI": "ir", "KAZ": "kz", "UZB": "uz", "THA": "th", "MAS": "my", "INA": "id", "VIE": "vn", "PHI": "ph", "QAT": "qa", "KSA": "sa", "UAE": "ae", "BRN": "bh", "EGY": "eg", "NGR": "ng", "ALG": "dz", "TUN": "tn", "MAR": "ma", "RSA": "za", "FRA": "fr", "GER": "de", "SWE": "se", "DEN": "dk", "NOR": "no", "FIN": "fi", "ENG": "gb-eng", "SCO": "gb-sct", "WAL": "gb-wls", "GBR": "gb", "IRL": "ie", "POR": "pt", "ESP": "es", "ITA": "it", "AUT": "at", "SUI": "ch", "BEL": "be", "NED": "nl", "LUX": "lu", "POL": "pl", "CZE": "cz", "SVK": "sk", "SLO": "si", "CRO": "hr", "SRB": "rs", "BIH": "ba", "MNE": "me", "MKD": "mk", "GRE": "gr", "TUR": "tr", "ROU": "ro", "HUN": "hu", "BUL": "bg", "UKR": "ua", "MDA": "md", "LTU": "lt", "LAT": "lv", "EST": "ee", "ISR": "il", "BRA": "br", "ARG": "ar", "CHI": "cl", "PER": "pe", "COL": "co", "VEN": "ve", "ECU": "ec", "URU": "uy", "PAR": "py", "MEX": "mx", "CUB": "cu", "DOM": "do", "PUR": "pr", "GUA": "gt", "CAN": "ca", "USA": "us", "AUS": "au", "NZL": "nz", "FIJ": "fj"};
  const flag = (c) => (FLAGS[(c || "").toUpperCase()] ? `<span class="fi fi-${FLAGS[c.toUpperCase()]}" aria-hidden="true"></span>` : "");
  // "Tomokazu Harimoto (JPN)" -> name with a flag before it
  const withFlag = (s) => { const m = /^(.*?)\s*\(([A-Z]{3})\)$/.exec(s || ""); return m ? `${flag(m[2])}${esc(m[1])}` : esc(s); };

  let news = {}, sched = {};
  try { news = await fetch("/data/news.json", { cache: "no-store" }).then((r) => r.json()); } catch (e) {}
  try { sched = await fetch("/data/schedule.json", { cache: "no-store" }).then((r) => r.json()); } catch (e) {}
  const events = sched.events || news.events || [];
  let hubs = {};
  { try { hubs = await fetch("/data/event-index.json", { cache: "no-store" }).then((r) => (r.ok ? r.json() : {})); } catch (e) {} }

  // Scores strip, led by anything on now with a link to live scores
  if ($("ticker")) {
    const cards = events.filter((e) => e.start <= today && e.end >= today).map((e) =>
      `<a class="score-card live-card" href="${esc(hubs[e.id] ? hubs[e.id].url : news.live_results_url || "https://www.worldtabletennis.com/")}"${hubs[e.id] ? "" : ' target="_blank" rel="noopener"'}>
        <span class="ev"><span class="live-dot"></span>On now</span>
        <span class="row won"><span>${esc(e.name)}</span></span>
        <span class="row"><span>${hubs[e.id] ? "Draw, results and schedule" : "Live scores on WTT"}</span></span></a>`);
    (news.results || []).forEach((r) => r.matches.forEach((m) => {
      const sc = /^(\d+)-(\d+)$/.exec(m.score || "");
      if (!sc || !m.loser) return;
      cards.push(`<a class="score-card" href="${esc(r.url)}" target="_blank" rel="noopener">
        <span class="ev" title="${esc(r.event)}">${esc(m.round)}, ${esc(r.event.split(", ")[1] || r.event)}</span>
        <span class="row won"><span>${withFlag(m.winner)}</span><b>${sc[1]}</b></span>
        <span class="row"><span>${withFlag(m.loser)}</span><b>${sc[2]}</b></span></a>`);
    }));
    $("ticker").innerHTML = cards.join("");
    if (!cards.length) $("ticker").closest(".ticker").hidden = true;
  }

  // World rankings: leader card, then points with a bar against the No. 1
  if ($("rankings") && news.rankings) {
    const f = (n) => Number(n || 0).toLocaleString("en-GB");
    const move = (p, i) => {
      if (!p.prev) return "";
      const d = p.prev - (i + 1);
      if (d > 0) return `<span class="mv up" title="Up ${d}">▲${d}</span>`;
      if (d < 0) return `<span class="mv down" title="Down ${-d}">▼${-d}</span>`;
      return "";
    };
    const ranks = (g) => {
      const list = news.rankings[g] || [];
      if (!list.length) return;
      const top = list[0], max = top.points || 1;
      const lead = $("rank-lead");
      if (lead) lead.innerHTML = `<div><span class="rl-label">World No. 1</span><span class="rl-name">${esc(top.name)}</span><span class="rl-nat">${flag(top.nat)}${esc(top.nat)}</span></div>
        <div class="rl-pts"><b>${f(top.points)}</b><span>points</span></div>`;
      $("rankings").innerHTML = list.slice(lead ? 1 : 0).map((p, k) => {
        const i = k + (lead ? 1 : 0);
        return `<li><span class="rk">${i + 1}</span><span class="who"><span class="nm">${esc(p.name)}</span><span class="nt">${flag(p.nat)}${esc(p.nat)}${move(p, i)}</span></span>
          <span class="pts">${p.points ? f(p.points) : ""}</span>
          ${p.points ? `<span class="bar"><i style="width:${Math.round(p.points / max * 100)}%"></i></span>` : ""}</li>`;
      }).join("");
    };
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
        <div><span class="name">${hubs[e.id] ? `<a href="${esc(hubs[e.id].url)}">${esc(e.name)}</a>` : esc(e.name)}</span><span class="when">${when}</span></div></li>`;
    }).join("");
  }

  // Advertising slots: fill from data/ads.json, otherwise show a quiet placeholder
  const slots = document.querySelectorAll("[data-ad]");
  if (slots.length) {
    let ads = {};
    try { ads = await fetch("/data/ads.json", { cache: "no-store" }).then((r) => r.json()); } catch (e) {}
    slots.forEach((el) => {
      const code = ads[el.dataset.ad];
      if (code) {
        const range = document.createRange();
        el.innerHTML = '<span class="ad-label">Advertisement</span>';
        el.appendChild(range.createContextualFragment(code)); // runs any ad scripts
        el.classList.add("filled");
      } else {
        el.innerHTML = '<span class="ad-label">Advertisement</span><a class="ad-empty" href="/contact.html">Advertise with Eleven</a>';
      }
    });
  }
})();
