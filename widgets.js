// Shared panels used on every page: the scores strip, world rankings and "Coming up".
// Each renders only if its container exists on the page.
// Live stream player: WTT's YouTube broadcast for an event, or the latest session to watch back
window.ElevenStream = function (el) {
  const q = el.dataset.streamQ, link = el.dataset.link || "";
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  // "LIVE! | Infinity Arena I WTT Champions Montpellier 2026 | Session 1" -> "Session 1"
  const part = (t) => (String(t).split("|").map((x) => x.trim()).filter((x) => /session|day|final/i.test(x)).join(", ")) || "Full session";
  async function tick() {
    if (document.hidden || el.querySelector("iframe")) return;
    let s;
    try { s = await fetch(`/api/stream?q=${encodeURIComponent(q)}`).then((r) => r.json()); } catch (e) { return; }
    if (!s || !s.id || s.status === "none") { el.hidden = true; return; }
    const live = s.status === "live", soon = s.status === "upcoming";
    const head = live ? '<span class="st-badge"><span class="live-dot"></span>Live</span>Watch live' : soon ? "Coming up on the stream" : "Catch up on the action";
    const thumb = `https://i.ytimg.com/vi/${esc(s.id)}/${live ? "hqdefault_live" : "hqdefault"}.jpg`;
    el.innerHTML = `<div class="stream${live ? " is-live" : ""}">
      <button type="button" class="st-play" data-yt="${esc(s.id)}" aria-label="Play: ${esc(s.title)}"><img src="${thumb}" alt="" loading="lazy"><span class="yt-play" aria-hidden="true"></span></button>
      <div class="st-cap"><b>${head}</b><span>${esc(part(s.title))}${soon && s.scheduled ? ` · ${esc(s.scheduled)}` : ""}</span>
      <a href="https://www.youtube.com/watch?v=${esc(s.id)}" target="_blank" rel="noopener">World Table Tennis on YouTube</a></div></div>`;
    el.hidden = false;
  }
  el.addEventListener("click", (ev) => {
    const b = ev.target.closest(".st-play");
    if (!b) return;
    const f = document.createElement("iframe");
    f.src = "https://www.youtube-nocookie.com/embed/" + b.dataset.yt + "?autoplay=1&rel=0";
    f.title = b.getAttribute("aria-label");
    f.allow = "accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture; web-share";
    f.allowFullscreen = true;
    b.replaceWith(f);
  });
  tick();
  setInterval(tick, 60000);
};

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
        <span class="ev" title="${esc(r.event)}">${esc(m.round)}</span><span class="where">${esc(r.event)}</span>
        <span class="row won"><span>${withFlag(m.winner)}</span><b>${sc[1]}</b></span>
        <span class="row"><span>${withFlag(m.loser)}</span><b>${sc[2]}</b></span></a>`);
    }));
    $("ticker").innerHTML = cards.join("");
    if (!cards.length) $("ticker").closest(".ticker").hidden = true;

    // Slim scrolling: hidden scrollbar, fade at the edges, arrow buttons on desktop
    const strip = $("ticker"), shell = strip.closest(".ticker");
    shell.classList.add("has-arrows");
    shell.insertAdjacentHTML("beforeend", '<button class="tk-arrow prev" aria-label="Earlier scores" hidden>&#8249;</button><button class="tk-arrow next" aria-label="More scores">&#8250;</button>');
    const prev = shell.querySelector(".prev"), next = shell.querySelector(".next");
    const edges = () => {
      prev.hidden = strip.scrollLeft < 8;
      next.hidden = strip.scrollLeft + strip.clientWidth >= strip.scrollWidth - 8;
      shell.classList.toggle("at-start", prev.hidden);
      shell.classList.toggle("at-end", next.hidden);
    };
    prev.addEventListener("click", () => strip.scrollBy({ left: -strip.clientWidth * 0.8, behavior: "smooth" }));
    next.addEventListener("click", () => strip.scrollBy({ left: strip.clientWidth * 0.8, behavior: "smooth" }));
    strip.addEventListener("scroll", edges, { passive: true });
    window.addEventListener("resize", edges);
    new MutationObserver(edges).observe(strip, { childList: true });
    edges();

    // Matches in play (and the latest finished ones) from WTT, for events with an Eleven event page
    const liveHubs = events.filter((e) => e.start <= today && e.end >= today && hubs[e.id] && hubs[e.id].wtt).map((e) => hubs[e.id]);
    if (liveHubs.length) {
      // "Women's singles, round of 32" -> "Women's singles R32", so the label fits the card
      const short = (l) => String(l).replace(/, (?:round of|last) (\d+)/i, " R$1").replace(/, quarter-?finals?/i, " QF").replace(/, semi-?finals?/i, " SF").replace(/, final$/i, " final");
      const mcard = (m, hub) => {
        const live = m.status === "live", g = m.games[m.games.length - 1] || [0, 0];
        const won = live ? -1 : (m.score[0] > m.score[1] ? 0 : 1);
        const side = (i) => `<span class="row${won === i ? " won" : ""}"><span>${flag(m.sides[i].nat)}${esc(m.sides[i].name)}</span><b>${m.score[i]}${live ? `<i class="pts">${g[i]}</i>` : ""}</b></span>`;
        return `<a class="score-card${live ? " is-live" : ""}" href="${esc(hub.url)}#live"><span class="ev">${live ? '<span class="live-dot"></span>' : ""}${esc(short(m.label))}</span><span class="where">${esc(hub.name)}</span>${side(0)}${side(1)}</a>`;
      };
      const refresh = async () => {
        if (document.hidden) return;
        let extra = [];
        for (const hub of liveHubs) {
          try {
            const d = await fetch(`/api/live?event=${encodeURIComponent(hub.wtt)}`, { cache: "no-store" }).then((r) => r.json());
            extra = extra.concat((d.live || []).map((m) => mcard(m, hub)), (d.results || []).slice(0, 10).map((m) => mcard(m, hub)));
          } catch (e) {}
        }
        // On the homepage the "on now" section shows the event and its four newest matches,
        // so the strip carries on from there instead of repeating them
        const onHome = !!$("onnow") && (document.body.classList.contains("has-onnow") || !location.hash);
        if (onHome) extra = extra.slice(4);
        if (!extra.length && !onHome) return;
        const on = onHome ? [] : cards.filter((c) => c.includes("live-card"));
        for (const hub of liveHubs) {
          try {
            const st = await fetch(`/api/stream?q=${encodeURIComponent(hub.stream_q || hub.city)}`).then((r) => r.json());
            if (st.status === "live" && !onHome) on.unshift(`<a class="score-card watch-card" href="${esc(hub.url)}#stream"><span class="ev"><span class="live-dot"></span>Watch live</span><span class="where">${esc(hub.name)}</span><span class="row won"><span>Stream from the arena</span><b>▶</b></span></a>`);
          } catch (e) {}
        }
        $("ticker").innerHTML = on.concat(extra, cards.filter((c) => !c.includes("live-card"))).join("");
        $("ticker").closest(".ticker").hidden = false;
      };
      refresh();
      setInterval(refresh, 20000);
    }
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
      if (lead) lead.innerHTML = `<div class="rl"><span class="rl-label">${g === "men" ? "Men's" : "Women's"} world No. 1</span><span class="rl-name">${flag(top.nat)}${esc(top.name)}</span></div>
        <div class="rl-score"><b class="rl-pts">${f(top.points)}</b><span>points</span></div>`;
      $("rankings").innerHTML = list.slice(lead ? 1 : 0).map((p, k) => {
        const i = k + (lead ? 1 : 0);
        return `<li><span class="rk">${i + 1}</span><span class="who"><span class="nm">${esc(p.name)}</span><span class="nt">${flag(p.nat)}${esc(p.nat)}${move(p, i)}</span></span>
          <span class="pts">${p.points ? f(p.points) : ""}</span>
          ${p.points ? `<span class="bar"><i style="width:${Math.round(p.points / max * 100)}%"></i></span>` : ""}</li>`;
      }).join("");
    };
    if ($("rank-week")) $("rank-week").innerHTML = `${esc(news.rankings.week)}. <a href="/rankings">Full top 100</a>`;
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
        el.innerHTML = '<span class="ad-label">Advertisement</span><a class="ad-empty" href="/contact">Advertise with Eleven</a>';
      }
    });
  }
})();
