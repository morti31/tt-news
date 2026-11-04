// Match centre: tap any WTT score card (homepage, scores strip, event pages) and the match opens
// in a pop-up over the page, point by point, instead of sending you to another page.
// Cards opt in with data-match="<WTT event id>|<document code>". Live matches refresh every 5 seconds.
// The pop-up has its own address (#match=...), so it can be shared and the back button closes it.
(function () {
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const FLAGS = {"CHN": "cn", "TPE": "tw", "RUS": "ru", "JPN": "jp", "KOR": "kr", "PRK": "kp", "HKG": "hk", "MAC": "mo", "SGP": "sg", "IND": "in", "IRI": "ir", "KAZ": "kz", "THA": "th", "MAS": "my", "INA": "id", "QAT": "qa", "EGY": "eg", "NGR": "ng", "ALG": "dz", "TUN": "tn", "FRA": "fr", "GER": "de", "SWE": "se", "DEN": "dk", "NOR": "no", "FIN": "fi", "ENG": "gb-eng", "SCO": "gb-sct", "WAL": "gb-wls", "GBR": "gb", "IRL": "ie", "POR": "pt", "ESP": "es", "ITA": "it", "AUT": "at", "SUI": "ch", "BEL": "be", "NED": "nl", "LUX": "lu", "POL": "pl", "CZE": "cz", "SVK": "sk", "SLO": "si", "CRO": "hr", "SRB": "rs", "GRE": "gr", "TUR": "tr", "ROU": "ro", "HUN": "hu", "UKR": "ua", "BRA": "br", "ARG": "ar", "CHI": "cl", "PUR": "pr", "CAN": "ca", "USA": "us", "AUS": "au", "NZL": "nz", "MON": "mc"};
  const flag = (c) => (FLAGS[c] ? `<span class="fi fi-${FLAGS[c]}" aria-hidden="true"></span>` : "");
  // Second references by surname: family name first for Chinese, Korean and similar names (as the worker writes them)
  const FAMILY_FIRST = new Set(["CHN", "TPE", "KOR", "HKG", "MAC", "PRK"]);
  const surname = (s) => {
    if (String(s.name).includes(" / ")) return s.name.split(" / ").map((n) => n.trim().split(/\s+/).pop()).join("/");
    const w = String(s.name || "").trim().split(/\s+/);
    return FAMILY_FIRST.has(s.nat) ? w[0] : w[w.length - 1];
  };

  let dlg, current = null, timer = null, chosen = null, data = null;

  function shell() {
    if (dlg) return dlg;
    dlg = document.createElement("dialog");
    dlg.className = "mp";
    dlg.setAttribute("aria-label", "Match centre");
    dlg.innerHTML = '<div class="mp-in"><button type="button" class="mp-x" aria-label="Close">×</button><div class="mp-body"><p class="mp-wait">Loading the match…</p></div></div>';
    document.body.appendChild(dlg);
    dlg.querySelector(".mp-x").addEventListener("click", () => close());
    dlg.addEventListener("click", (e) => {
      if (e.target === dlg) return close();           // the backdrop
      const t = e.target.closest("[data-game]");
      if (t) { chosen = Number(t.dataset.game); draw(); }
    });
    dlg.addEventListener("cancel", (e) => { e.preventDefault(); close(); });   // Esc
    return dlg;
  }

  function scoreboard(m) {
    const live = m.status === "live", won = live ? null : m.score[0] > m.score[1] ? 0 : 1;
    const row = (i) => {
      const s = m.sides[i] || {};
      const cells = m.games.map((g, k) => {
        const cur = live && k === m.games.length - 1;
        return `<td class="${cur ? "cur" : ""}${!cur && g[i] > g[1 - i] ? " gw" : ""}">${g[i]}</td>`;
      }).join("");
      return `<tr class="mp-side s${i}${won === i ? " won" : ""}"><th scope="row"><span class="mp-chip"></span>${flag(s.nat)}<span class="mp-name">${esc(s.name)}</span>${s.rank ? `<span class="wr" title="World No ${s.rank}">${s.rank}</span>` : ""}${live && m.server === i ? '<span class="mp-serve" title="Serving"></span>' : ""}</th><td class="sets">${m.score[i]}</td>${cells}</tr>`;
    };
    return `<table class="mp-board"><caption class="sr-only">${esc(m.sides.map((s) => s.name).join(" v "))}</caption><tbody>${row(0)}${row(1)}</tbody></table>`;
  }

  // The lead through a game as a step line: above the middle, the first player is ahead
  function momentum(pts) {
    const p = pts.filter((x) => x.k === "p");
    if (!p.length) return "";
    const W = 600, H = 70, mid = H / 2, step = W / Math.max(p.length, 11);
    const max = Math.max(3, ...p.map((x) => Math.abs(x.h - x.a)));
    const y = (d) => mid - (d / max) * (mid - 6);
    let d = `M0 ${mid}`, x = 0;
    for (const q of p) { const yy = y(q.h - q.a); d += ` H${(x += step).toFixed(1)} V${yy.toFixed(1)}`; }
    return `<svg class="mp-mom" viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" aria-hidden="true"><line x1="0" x2="${W}" y1="${mid}" y2="${mid}" class="axis"/><path d="${d}"/></svg>`;
  }

  function pointList(m, pts, isLastGame) {
    const names = m.sides.map(surname);
    const rows = [];
    let run = 0, last = null;
    pts.forEach((q, i) => {
      if (q.k === "to") { rows.push(`<li class="mp-to">Time-out${q.by !== null && q.by !== undefined ? `: ${esc(names[q.by])}` : ""} at ${q.h}-${q.a}</li>`); return; }
      run = q.w === last ? run + 1 : 1; last = q.w;
      const next = pts.slice(i + 1).find((x) => x.k === "p");
      const runEnds = !next || next.w !== q.w;
      const tag = q.tag === "MP" ? "Match point" : q.tag === "GP" ? "Game point" : "";
      const end = Math.max(q.h, q.a) >= 11 && Math.abs(q.h - q.a) >= 2;
      rows.push(`<li class="mp-pt w${q.w}${end ? " end" : ""}"><span class="mp-sc"><b class="${q.w === 0 ? "on" : ""}">${q.h}</b>-<b class="${q.w === 1 ? "on" : ""}">${q.a}</b></span>
        <span class="mp-who"><span class="mp-chip"></span>${esc(names[q.w])}${q.s !== null && q.s !== undefined ? `<small>${q.s === q.w ? "on serve" : "on return"}</small>` : ""}</span>
        <span class="mp-tags">${end ? `<em>${m.status !== "live" && last === q.w && isLastGame && !next ? "Match" : "Game"} ${esc(names[q.w])}</em>` : tag ? `<em>${tag}</em>` : ""}${runEnds && run >= 4 ? `<em class="run">${run} in a row</em>` : ""}</span></li>`);
    });
    return `<ol class="mp-pts">${rows.reverse().join("")}</ol>`;   // newest first
  }

  function draw() {
    const m = data, body = dlg.querySelector(".mp-body");
    if (!m) return;
    const live = m.status === "live";
    const games = m.points || [];
    const g = chosen !== null && games[chosen] ? chosen : games.length - 1;
    const tabs = games.map((_, i) => `<button type="button" data-game="${i}" aria-pressed="${i === g}">G${i + 1}<span>${(m.games[i] || []).join("-")}</span></button>`).join("");
    const pts = games[g] || [];
    const won = pts.filter((x) => x.k === "p").reduce((t, x) => (t[x.w]++, t), [0, 0]);
    const srv = pts.filter((x) => x.k === "p" && x.s === x.w).reduce((t, x) => (t[x.w]++, t), [0, 0]);
    const names = m.sides.map(surname);
    body.innerHTML = `<p class="mp-meta">${live ? `<span class="live-dot"></span>Live${m.game ? `, game ${m.game}` : ""}` : "Final"}<span>${esc(m.label)}${m.table ? ` · ${esc(m.table)}` : ""}</span></p>
      ${scoreboard(m)}
      ${games.length ? `<div class="mp-tabs" role="group" aria-label="Game">${tabs}</div>
      <div class="mp-game"><div class="mp-key"><span class="s0"><span class="mp-chip"></span>${esc(names[0])} won ${won[0]} points (${srv[0]} on serve)</span><span class="s1"><span class="mp-chip"></span>${esc(names[1])} won ${won[1]} points (${srv[1]} on serve)</span></div>
        ${pts.length ? pointList(m, pts, g === games.length - 1) : '<p class="mp-wait">Points for this game were played before the match was opened here. The full record appears when the match finishes.</p>'}</div>` : '<p class="mp-wait">Point-by-point appears here once the first rally is played.</p>'}
      <p class="mp-foot">${live ? "Updates every few seconds. Live point by point builds up from the first time a match is opened. " : ""}Data from World Table Tennis.${current.hub ? ` <a href="${esc(current.hub)}">Event page</a>` : ""}</p>`;
  }

  async function load() {
    if (!current) return;
    try {
      const r = await fetch(`/api/match?event=${encodeURIComponent(current.event)}&code=${encodeURIComponent(current.code)}`, { cache: "no-store" });
      if (!r.ok) throw new Error(r.status);
      data = await r.json();
      draw();
      clearTimeout(timer);
      if (data.status === "live") timer = setTimeout(() => { if (!document.hidden) load(); else timer = setTimeout(load, 5000); }, 5000);
    } catch (e) {
      if (!data) dlg.querySelector(".mp-body").innerHTML = '<p class="mp-wait">This match isn\'t available right now. Try again in a moment.</p>';
      timer = setTimeout(load, 10000);
    }
  }

  function open(event, code, hub, push = true) {
    shell();
    current = { event, code, hub }; chosen = null; data = null;
    dlg.querySelector(".mp-body").innerHTML = '<p class="mp-wait">Loading the match…</p>';
    if (!dlg.open) dlg.showModal();
    document.documentElement.classList.add("mp-open");
    if (push) history.pushState({ mp: true }, "", `#match=${event}:${code}`);
    load();
  }

  function close(fromHistory) {
    if (!dlg || !dlg.open) return;
    dlg.close();
    clearTimeout(timer); current = null;
    document.documentElement.classList.remove("mp-open");
    if (!fromHistory) {
      if (history.state && history.state.mp) history.back();
      else history.replaceState(null, "", location.pathname + location.search);
    }
  }

  // Any card with data-match opens here, wherever it was drawn and however late
  document.addEventListener("click", (e) => {
    const a = e.target.closest("[data-match]");
    if (!a || e.metaKey || e.ctrlKey || e.shiftKey) return;
    const [event, code] = a.dataset.match.split("|");
    if (!event || !code) return;
    e.preventDefault();
    open(event, code, a.dataset.hub || (a.getAttribute("href") || "").split("#")[0] || "");
  });
  document.addEventListener("keydown", (e) => {
    const a = e.target.closest && e.target.closest("[data-match]");
    if (a && (e.key === "Enter" || e.key === " ") && a.tagName !== "A") { e.preventDefault(); a.click(); }
  });
  const fromHash = () => {
    const m = /^#match=(\d+):([A-Z0-9-]+)$/.exec(location.hash);
    if (m) open(m[1], m[2], "", false); else close(true);
  };
  window.addEventListener("popstate", fromHash);
  if (location.hash.startsWith("#match=")) fromHash();
  window.ElevenMatch = { open, close };
})();
