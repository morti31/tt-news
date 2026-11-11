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
  const FLAGS = {"CHN": "cn", "TPE": "tw", "RUS": "ru", "JPN": "jp", "KOR": "kr", "PRK": "kp", "HKG": "hk", "MAC": "mo", "SGP": "sg", "IND": "in", "IRI": "ir", "KAZ": "kz", "UZB": "uz", "THA": "th", "MAS": "my", "INA": "id", "VIE": "vn", "PHI": "ph", "QAT": "qa", "KSA": "sa", "UAE": "ae", "BRN": "bh", "EGY": "eg", "NGR": "ng", "ALG": "dz", "TUN": "tn", "MAR": "ma", "RSA": "za", "FRA": "fr", "GER": "de", "SWE": "se", "DEN": "dk", "NOR": "no", "FIN": "fi", "ENG": "gb-eng", "SCO": "gb-sct", "WAL": "gb-wls", "GBR": "gb", "IRL": "ie", "POR": "pt", "ESP": "es", "ITA": "it", "AUT": "at", "SUI": "ch", "BEL": "be", "NED": "nl", "LUX": "lu", "POL": "pl", "CZE": "cz", "SVK": "sk", "SLO": "si", "CRO": "hr", "SRB": "rs", "BIH": "ba", "MNE": "me", "MKD": "mk", "GRE": "gr", "TUR": "tr", "ROU": "ro", "HUN": "hu", "BUL": "bg", "UKR": "ua", "MDA": "md", "LTU": "lt", "LAT": "lv", "EST": "ee", "ISR": "il", "BRA": "br", "ARG": "ar", "CHI": "cl", "PER": "pe", "COL": "co", "VEN": "ve", "ECU": "ec", "URU": "uy", "PAR": "py", "MEX": "mx", "CUB": "cu", "DOM": "do", "PUR": "pr", "GUA": "gt", "CAN": "ca", "USA": "us", "AUS": "au", "NZL": "nz", "FIJ": "fj", "ANG": "ao", "ANT": "ag", "BEN": "bj", "BLR": "by", "CIV": "ci", "CMR": "cm", "COD": "cd", "CGO": "cg", "CRC": "cr", "GHA": "gh", "GUI": "gn", "MAD": "mg", "MLT": "mt", "MON": "mc", "MRI": "mu", "NCL": "nc", "NRU": "nr", "PNG": "pg", "PYF": "pf", "TAH": "pf", "SEN": "sn", "SLE": "sl", "SYR": "sy", "TOG": "tg", "TTO": "tt", "ARM": "am", "AZE": "az", "GEO": "ge", "BAN": "bd", "PAK": "pk", "SRI": "lk", "NEP": "np", "KUW": "kw", "IRQ": "iq", "JOR": "jo", "LBN": "lb", "OMA": "om", "YEM": "ye", "KGZ": "kg", "TJK": "tj", "TKM": "tm", "MGL": "mn", "CAM": "kh", "LAO": "la", "MYA": "mm", "BRU": "bn", "MDV": "mv", "ISL": "is", "CYP": "cy", "ALB": "al", "KOS": "xk", "AND": "ad", "SMR": "sm", "LIE": "li", "GIB": "gi", "FRO": "fo", "KEN": "ke", "UGA": "ug", "TAN": "tz", "ZAM": "zm", "ZIM": "zw", "ETH": "et", "SUD": "sd", "LBA": "ly", "BOT": "bw", "NAM": "na", "MOZ": "mz", "GAB": "ga", "CAF": "cf", "CHA": "td", "NIG": "ne", "MLI": "ml", "BUR": "bf", "GAM": "gm", "LBR": "lr", "SEY": "sc", "RWA": "rw", "BDI": "bi", "DJI": "dj", "SOM": "so", "ERI": "er", "MTN": "mr", "CPV": "cv", "STP": "st", "GEQ": "gq", "COM": "km", "LES": "ls", "SWZ": "sz", "MAW": "mw", "BOL": "bo", "PAN": "pa", "HON": "hn", "ESA": "sv", "NCA": "ni", "JAM": "jm", "BAR": "bb", "HAI": "ht", "GUY": "gy", "SUR": "sr", "BAH": "bs", "CAY": "ky", "BER": "bm", "ARU": "aw", "GRN": "gd", "LCA": "lc", "VIN": "vc", "SKN": "kn", "DMA": "dm", "ISV": "vi", "IVB": "vg", "SAM": "ws", "TGA": "to", "VAN": "vu", "SOL": "sb", "GUM": "gu", "COK": "ck", "ASA": "as", "KIR": "ki", "TUV": "tv", "PLW": "pw", "FSM": "fm", "MHL": "mh", "TLS": "tl", "BHU": "bt", "AFG": "af", "PLE": "ps"};
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
    const over = (id) => !!(hubs[id] && hubs[id].champions && hubs[id].champions.length);   // every final played
    // Club competitions on now link to their league page on Eleven; WTT events without a page link to WTT
    const LEAGUE_PAGE = [[/Champions League/i, "champions-league"], [/Super League/i, "super-league"], [/T\.? ?League/i, "t-league"], [/TTBL|Bundesliga/i, "bundesliga"],
      [/Pro A\b/i, "pro-a"], [/MLTT|Major League/i, "mltt"], [/\bUTT\b|Ultimate Table Tennis/i, "utt"]];
    const leaguePage = (e) => { if (hubs[e.id] || !/club|league/i.test(`${e.series} ${e.type}`)) return null; const m = LEAGUE_PAGE.find(([rx]) => rx.test(e.name)); return m ? `/clubs/${m[1]}.html` : null; };
    const cards = events.filter((e) => e.start <= today && e.end >= today && !over(e.id)).map((e) => {
      const lp = leaguePage(e);
      // A long name is split so the card keeps the strip's width: "ETTU Champions League Women, Stage 2 Round 1"
      // shows as "Champions League Women" with the stage on the line below
      const [head, ...rest] = e.name.split(", ");
      const title = head.replace(/^ETTU /, ""), stage = rest.join(", ");
      return `<a class="score-card live-card" href="${esc(lp || (hubs[e.id] ? hubs[e.id].url : news.live_results_url || "https://www.worldtabletennis.com/"))}"${hubs[e.id] || lp ? "" : ' target="_blank" rel="noopener"'}>
        <span class="ev"><span class="live-dot"></span>On now</span>
        <span class="row won"><span>${esc(title)}</span></span>
        <span class="row"><span>${esc(stage || (lp ? "Fixtures and results" : hubs[e.id] ? "Draw, results and schedule" : "Live scores on WTT"))}</span></span></a>`;
    });
    (news.results || []).forEach((r) => r.matches.forEach((m) => {
      const sc = /^(\d+)-(\d+)$/.exec(m.score || "");
      if (!sc || !m.loser) return;
      cards.push(`<a class="score-card" href="${esc(r.url)}" target="_blank" rel="noopener">
        <span class="ev" title="${esc(r.event)}">${esc(m.round)}</span><span class="where">${esc(r.event)}</span>
        <span class="row won"><span>${withFlag(m.winner)}</span><b>${sc[1]}</b></span>
        <span class="row"><span>${withFlag(m.loser)}</span><b>${sc[2]}</b></span></a>`);
    }));
    // Club leagues: results of the last two days and the next fixtures (data/club-strip.json, built from data/clubs).
    // Cards sit after the WTT cards; each links to the league's page.
    const clubCards = [];
    try {
      const rows = await fetch("/data/club-strip.json", { cache: "no-store" }).then((r) => (r.ok ? r.json() : []));
      const nowMs = Date.now();
      const stamp = (r) => new Date(r.when).getTime();
      const when = (r) => r.day ? fmt(r.when.slice(0, 10), { weekday: "short", day: "numeric", month: "short" })
        : new Date(r.when).toLocaleString("en-GB", { weekday: "short", hour: "2-digit", minute: "2-digit" });
      const label = (r) => `${r.league}${r.comp && r.comp !== "Mixed" ? " " + r.comp.toLowerCase() : ""}`;
      const done = rows.filter((r) => r.score && stamp(r) <= nowMs + 36e5 && stamp(r) >= nowMs - 2 * 864e5).sort((a, b) => stamp(b) - stamp(a)).slice(0, 8);
      const next = rows.filter((r) => !r.score && (r.day ? r.when.slice(0, 10) >= today : stamp(r) >= nowMs - 3 * 36e5) && stamp(r) <= nowMs + 2 * 864e5).sort((a, b) => stamp(a) - stamp(b)).slice(0, 6);
      // League "On now" cards (Fixtures and results) appear only on days that league has a match; no separate "Next" fixture cards
      const playing = new Set(rows.filter((r) => r.when.slice(0, 10) === today).map((r) => r.lg));
      for (let k = cards.length - 1; k >= 0; k--) {
        const m = /class="score-card live-card" href="\/clubs\/([^".]+)\.html"/.exec(cards[k]);
        if (m && !playing.has(m[1])) cards.splice(k, 1);
      }
      done.forEach((r) => {
        const hw = r.score[0] > r.score[1];
        clubCards.push(`<a class="score-card" href="/clubs/${esc(r.lg)}.html"><span class="ev" title="${esc(r.round)}">${esc(label(r))}</span><span class="where">${esc(r.round)}</span>
        <span class="row${hw ? " won" : ""}"><span>${esc(r.home)}</span><b>${r.score[0]}</b></span><span class="row${hw ? "" : " won"}"><span>${esc(r.away)}</span><b>${r.score[1]}</b></span></a>`);
      });
    } catch (e) {}
    // Club cards come straight after the "On now" cards, ahead of older stored results
    const firstOld = cards.findIndex((c) => !c.includes("live-card"));
    cards.splice(firstOld < 0 ? cards.length : firstOld, 0, ...clubCards);
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
    // An event stays here for three days after it ends, so its finals open point by point too
    const since = new Date(Date.now() - 3 * 864e5).toISOString().slice(0, 10);
    const liveHubs = events.filter((e) => e.start <= today && e.end >= since && hubs[e.id] && hubs[e.id].wtt).map((e) => hubs[e.id])
      .sort((a, b) => ((a.champions || []).length ? 1 : 0) - ((b.champions || []).length ? 1 : 0) || b.start.localeCompare(a.start));   // events in progress first
    // Those events' stored results (which link out to WTT) give way to WTT's own cards
    if (liveHubs.length) {
      const names = new Set(liveHubs.map((h) => h.name));
      cards.splice(0, cards.length, ...cards.filter((c) => ![...names].some((n) => c.includes(`title="${esc(n)}"`))));
      $("ticker").innerHTML = cards.join("");
    }
    // Home page with an event on: the "On now" panel carries the live scores, so the strip waits for them
    // rather than showing "On now" link cards that are swapped out a moment later
    if (liveHubs.length && ["/", "/index.html"].includes(location.pathname) && liveHubs.some((h) => !(h.champions || []).length && h.start <= today && h.end >= today) && window.__panelHigh !== false) {
      $("ticker").innerHTML = clubCards.join("");   // the "On now" panel carries the WTT scores; club results stay in the strip
      $("ticker").closest(".ticker").hidden = !clubCards.length;
    }
    if (liveHubs.length) {
      // "Women's singles, round of 32" -> "Women's singles R32", so the label fits the card
      const short = (l) => String(l).replace(/, (?:round of|last) (\d+)/i, " R$1").replace(/, quarter-?finals?/i, " QF").replace(/, semi-?finals?/i, " SF").replace(/, final$/i, " final");
      const wr = (s) => (s && s.rank ? `<span class="wr" title="World No ${s.rank}">${s.rank}</span>` : "");
      const mcard = (m, hub) => {
        const live = m.status === "live", g = m.games[m.games.length - 1] || [0, 0];
        const won = live ? -1 : (m.score[0] > m.score[1] ? 0 : 1);
        const side = (i) => `<span class="row${won === i ? " won" : ""}"><span>${flag(m.sides[i].nat)}${esc(m.sides[i].name)}${wr(m.sides[i])}</span><b>${m.score[i]}${live ? `<i class="pts">${g[i]}</i>` : ""}</b></span>`;
        return `<a class="score-card${live ? " is-live" : ""}" href="${esc(hub.url)}#live" data-match="${esc(hub.wtt)}|${esc(m.code)}"><span class="ev">${live ? '<span class="live-dot"></span>' : ""}${esc(short(m.label))}</span><span class="where">${esc(hub.name)}</span>${side(0)}${side(1)}</a>`;
      };
      const refresh = async () => {
        if (document.hidden) return;
        // Per event: live matches, the next two fixtures, the last two results, then (from the
        // quarter-finals) every semi-final and final, then older results
        const onHome = !!$("onnow") && document.body.classList.contains("has-onnow") && !document.body.classList.contains("onnow-low");   // panel low down: the strip at the top works as on every other page
        let extra = [];
        for (const hub of liveHubs) {
          try {
            const d = await fetch(`/api/live?event=${encodeURIComponent(hub.wtt)}`, { cache: "no-store" }).then((r) => r.json());
            const F = window.ElevenFixtures;
            const fx = F ? await F.get(hub, d).catch(() => ({ next: [], knock: [] })) : { next: [], knock: [] };
            const res = (d.results || []).slice(0, 10).map((m) => mcard(m, hub));
            // On the homepage the "on now" panel already shows all but the older results
            if (onHome) { extra = extra.concat(res.slice(2)); continue; }
            extra = extra.concat((d.live || []).map((m) => mcard(m, hub)), fx.next.map((x) => F.card(x, hub, { prefix: "Next · ", where: true })), res.slice(0, 2),
              ...fx.knock.map((k) => k.items.map((x) => F.card(x, hub, { where: true }))), res.slice(2));
          } catch (e) {}
        }
        if (!extra.length && !onHome) return;
        const on = onHome ? [] : cards.filter((c) => c.includes("live-card"));
        for (const hub of liveHubs) {
          try {
            const st = await fetch(`/api/stream?q=${encodeURIComponent(hub.stream_q || hub.city)}`).then((r) => r.json());
            if (st.status === "live" && !onHome && !(hub.champions && hub.champions.length)) on.unshift(`<a class="score-card watch-card" href="${esc(hub.url)}#stream"><span class="ev"><span class="live-dot"></span>Watch live</span><span class="where">${esc(hub.name)}</span><span class="row won"><span>Stream from the arena</span><b>▶</b></span></a>`);
          } catch (e) {}
        }
        const html = on.concat(extra, cards.filter((c) => !c.includes("live-card"))).join("");
        if ($("ticker").dataset.h !== html) { $("ticker").dataset.h = html; $("ticker").innerHTML = html; }   // no redraw when unchanged
        $("ticker").closest(".ticker").hidden = !html;
      };
      refresh();
      setInterval(refresh, 20000);
      document.addEventListener("onnow-placed", refresh);
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
    let prof = {};
    const nm = (p) => prof[p.name] ? `<a href="${prof[p.name].replace(/\.html$/, "")}">${esc(p.name)}</a>` : esc(p.name);
    const ranks = (g) => {
      const list = news.rankings[g] || [];
      if (!list.length) return;
      const top = list[0], max = top.points || 1;
      const lead = $("rank-lead");
      if (lead) lead.innerHTML = `<div class="rl"><span class="rl-label">${g === "men" ? "Men's" : "Women's"} world No. 1</span><span class="rl-name">${flag(top.nat)}${nm(top)}</span></div>
        <div class="rl-score"><b class="rl-pts">${f(top.points)}</b><span>points</span></div>`;
      $("rankings").innerHTML = list.slice(lead ? 1 : 0).map((p, k) => {
        const i = k + (lead ? 1 : 0);
        return `<li><span class="rk">${i + 1}</span><span class="who"><span class="nm">${nm(p)}</span><span class="nt">${flag(p.nat)}${esc(p.nat)}${move(p, i)}</span></span>
          <span class="pts">${p.points ? f(p.points) : ""}</span>
          ${p.points ? `<span class="bar"><i style="width:${Math.round(p.points / max * 100)}%"></i></span>` : ""}</li>`;
      }).join("");
    };
    if ($("rank-week")) $("rank-week").innerHTML = `${esc(news.rankings.week)}. <a href="/rankings">Full top 400</a>`;
    $("rank-toggle")?.addEventListener("click", (e) => {
      const b = e.target.closest("button");
      if (!b) return;
      document.querySelectorAll("#rank-toggle button").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
      ranks(b.dataset.g);
    });
    ranks("men");
    fetch("/data/profiles.json").then((r) => r.json()).then((d) => {
      prof = d || {};
      const on = document.querySelector('#rank-toggle button[aria-pressed="true"]');
      ranks(on ? on.dataset.g : "men");
    }).catch(() => {});
  }

  // Coming up
  if ($("events")) {
    const n = Number($("events").dataset.count || 7);
    const upcoming = events.filter((e) => e.end >= today).sort((a, b) => a.start.localeCompare(b.start)).slice(0, n);
    // Every event with a page of its own links to it: an event page, else its club league's page
    const LEAGUES = [[/Champions League/i, "champions-league"], [/Super League/i, "super-league"], [/T\.? ?League/i, "t-league"], [/TTBL|Bundesliga/i, "bundesliga"],
      [/Pro A\b/i, "pro-a"], [/MLTT|Major League/i, "mltt"], [/\bUTT\b|Ultimate Table Tennis/i, "utt"]];
    const pageOf = (e) => {
      if (hubs[e.id]) return hubs[e.id].url;
      const m = /club|league/i.test(`${e.series} ${e.type} ${e.name}`) && LEAGUES.find(([rx]) => rx.test(e.name));
      return m ? `/clubs/${m[1]}.html` : null;
    };
    $("events").innerHTML = upcoming.map((e) => {
      const now = e.start <= today;
      // "ETTU Champions League Women, Stage 2 Round 1": the competition as the name, the stage on the line below
      const [head, ...rest] = e.name.split(", ");
      const title = head.replace(/^ETTU /, ""), stage = rest.join(", ").replace(/^./, (c) => c.toUpperCase());
      const dates = now ? `<b class="on-now"><span class="live-dot"></span>On now</b> until ${fmt(e.end)}` : e.start === e.end ? fmt(e.start) : `${fmt(e.start)} to ${fmt(e.end)}`;
      const href = pageOf(e);
      return `<li class="${now ? "now" : ""}${href ? " linked" : ""}"><div class="cal"><b>${day(e.start).getDate()}</b><span>${fmt(e.start, { month: "short" })}</span></div>
        <div><span class="name">${href ? `<a class="stretch" href="${esc(href)}">${esc(title)}</a>` : esc(title)}</span>${stage ? `<span class="when stage">${esc(stage)}</span>` : ""}<span class="when">${dates}</span></div></li>`;
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
