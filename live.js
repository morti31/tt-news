// Live scores from WTT (through Eleven's /api/live), used on event pages and in the scores strip.
// Each [data-wtt-live] element gets the matches on now plus the latest results, refreshed every 15 seconds.
(function () {
  const FLAGS = {"CHN": "cn", "TPE": "tw", "RUS": "ru", "JPN": "jp", "KOR": "kr", "PRK": "kp", "HKG": "hk", "MAC": "mo", "SGP": "sg", "IND": "in", "IRI": "ir", "KAZ": "kz", "UZB": "uz", "THA": "th", "MAS": "my", "INA": "id", "VIE": "vn", "PHI": "ph", "QAT": "qa", "KSA": "sa", "UAE": "ae", "BRN": "bh", "EGY": "eg", "NGR": "ng", "ALG": "dz", "TUN": "tn", "MAR": "ma", "RSA": "za", "FRA": "fr", "GER": "de", "SWE": "se", "DEN": "dk", "NOR": "no", "FIN": "fi", "ENG": "gb-eng", "SCO": "gb-sct", "WAL": "gb-wls", "GBR": "gb", "IRL": "ie", "POR": "pt", "ESP": "es", "ITA": "it", "AUT": "at", "SUI": "ch", "BEL": "be", "NED": "nl", "LUX": "lu", "POL": "pl", "CZE": "cz", "SVK": "sk", "SLO": "si", "CRO": "hr", "SRB": "rs", "BIH": "ba", "MNE": "me", "MKD": "mk", "GRE": "gr", "TUR": "tr", "ROU": "ro", "HUN": "hu", "BUL": "bg", "UKR": "ua", "MDA": "md", "LTU": "lt", "LAT": "lv", "EST": "ee", "ISR": "il", "BRA": "br", "ARG": "ar", "CHI": "cl", "PER": "pe", "COL": "co", "VEN": "ve", "ECU": "ec", "URU": "uy", "PAR": "py", "MEX": "mx", "CUB": "cu", "DOM": "do", "PUR": "pr", "GUA": "gt", "CAN": "ca", "USA": "us", "AUS": "au", "NZL": "nz", "FIJ": "fj", "ANG": "ao", "ANT": "ag", "BEN": "bj", "BLR": "by", "CIV": "ci", "CMR": "cm", "COD": "cd", "CGO": "cg", "CRC": "cr", "GHA": "gh", "GUI": "gn", "MAD": "mg", "MLT": "mt", "MON": "mc", "MRI": "mu", "NCL": "nc", "NRU": "nr", "PNG": "pg", "PYF": "pf", "TAH": "pf", "SEN": "sn", "SLE": "sl", "SYR": "sy", "TOG": "tg", "TTO": "tt", "ARM": "am", "AZE": "az", "GEO": "ge", "BAN": "bd", "PAK": "pk", "SRI": "lk", "NEP": "np", "KUW": "kw", "IRQ": "iq", "JOR": "jo", "LBN": "lb", "OMA": "om", "YEM": "ye", "KGZ": "kg", "TJK": "tj", "TKM": "tm", "MGL": "mn", "CAM": "kh", "LAO": "la", "MYA": "mm", "BRU": "bn", "MDV": "mv", "ISL": "is", "CYP": "cy", "ALB": "al", "KOS": "xk", "AND": "ad", "SMR": "sm", "LIE": "li", "GIB": "gi", "FRO": "fo", "KEN": "ke", "UGA": "ug", "TAN": "tz", "ZAM": "zm", "ZIM": "zw", "ETH": "et", "SUD": "sd", "LBA": "ly", "BOT": "bw", "NAM": "na", "MOZ": "mz", "GAB": "ga", "CAF": "cf", "CHA": "td", "NIG": "ne", "MLI": "ml", "BUR": "bf", "GAM": "gm", "LBR": "lr", "SEY": "sc", "RWA": "rw", "BDI": "bi", "DJI": "dj", "SOM": "so", "ERI": "er", "MTN": "mr", "CPV": "cv", "STP": "st", "GEQ": "gq", "COM": "km", "LES": "ls", "SWZ": "sz", "MAW": "mw", "BOL": "bo", "PAN": "pa", "HON": "hn", "ESA": "sv", "NCA": "ni", "JAM": "jm", "BAR": "bb", "HAI": "ht", "GUY": "gy", "SUR": "sr", "BAH": "bs", "CAY": "ky", "BER": "bm", "ARU": "aw", "GRN": "gd", "LCA": "lc", "VIN": "vc", "SKN": "kn", "DMA": "dm", "ISV": "vi", "IVB": "vg", "SAM": "ws", "TGA": "to", "VAN": "vu", "SOL": "sb", "GUM": "gu", "COK": "ck", "ASA": "as", "KIR": "ki", "TUV": "tv", "PLW": "pw", "FSM": "fm", "MHL": "mh", "TLS": "tl", "BHU": "bt", "AFG": "af", "PLE": "ps"};
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const flag = (c) => (FLAGS[c] ? `<span class="fi fi-${FLAGS[c]}" aria-hidden="true"></span>` : "");
  const time = (iso) => iso ? new Date(iso).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" }) : "";

  // World ranking (top 100 only), added by /api/live from data/rankings.json
  const wr = (s) => (s && s.rank ? `<span class="wr" title="World No ${s.rank}">${s.rank}</span>` : "");

  function card(m, event) {
    const live = m.status === "live";
    const won = live ? null : m.score[0] > m.score[1] ? 0 : 1;
    const row = (i) => {
      const s = m.sides[i] || {};
      const cells = m.games.map((g, k) => {
        const cur = live && k === m.games.length - 1;
        const w = !cur && g[i] > g[1 - i];
        return `<td class="${cur ? "lv-cur" : ""}${w ? " lv-gw" : ""}">${g[i]}</td>`;
      }).join("");
      return `<tr class="${won === i ? "lv-won" : ""}"><th scope="row">${flag(s.nat)}<span class="lv-name">${esc(s.name)}</span>${wr(s)}<span class="lv-nat">${esc(s.nat)}</span>${live && m.server === i ? '<span class="lv-serve" title="Serving"></span>' : ""}</th>
        <td class="lv-sets">${m.score[i]}</td>${cells}</tr>`;
    };
    const meta = live ? `<span class="lv-dot"></span>Live${m.game ? `, game ${m.game}` : ""}` : "Final";
    return `<article class="lv-card${live ? " is-live" : ""}"${event && m.code ? ` data-match="${esc(event)}|${esc(m.code)}" tabindex="0" role="button" aria-label="${esc(m.sides.map((x) => x.name).join(" v "))}: point by point"` : ""}><p class="lv-meta"><span>${meta}</span><span>${esc(m.label)}${m.table ? ` · ${esc(m.table)}` : ""}</span></p>
      <table class="lv-table"><caption class="sr-only">${esc(m.sides.map((s) => s.name).join(" v "))}</caption><tbody>${row(0)}${row(1)}</tbody></table>${!live && m.end ? `<p class="done-at">${esc(new Date(m.end).toLocaleDateString("en-GB", { weekday: "short", day: "numeric", month: "short" }))}, ${esc(new Date(m.end).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" }))}</p>` : ""}</article>`;
  }

  // The match centre's rows (data-key = the two players' names): live scores and fresh results go straight in
  const rowKey = (m) => m.sides.map((x) => String(x.name).trim().toLowerCase()).sort().join("|");
  function overlay(d, id) {
    const rows = {};
    document.querySelectorAll(".mc-row[data-key]").forEach((r) => (rows[r.dataset.key] = r));
    for (const m of (d.results || []).concat(d.live || [])) {
      const r = rows[rowKey(m)];
      if (!r) continue;
      const live = m.status === "live";
      // the row lists players in its own order; line the score up with it
      const names = [...r.querySelectorAll(".mc-p .nm")].map((x) => x.textContent.trim().toLowerCase());
      const flip = names.length === 2 && names[0] === String(m.sides[1].name).trim().toLowerCase();
      const sc = flip ? [m.score[1], m.score[0]] : m.score;
      const gs = m.games.map((g) => (flip ? [g[1], g[0]] : g));
      const won = live ? -1 : (sc[0] > sc[1] ? 0 : 1);
      r.classList.toggle("is-live", live);
      r.classList.toggle("done", !live);
      r.querySelector(".mc-time time").textContent = live ? "Live" : "Result";
      r.querySelectorAll(".mc-p").forEach((p, i) => p.classList.toggle("won", won === i));
      r.querySelector(".mc-sets").innerHTML = sc.map((v, i) => `<b class="${won === i ? "won" : ""}">${v}</b>`).join("");
      r.querySelector(".mc-games").innerHTML = gs.map((g, k) => {
        const cur = live && k === gs.length - 1;
        return `<span class="${cur ? "cur" : ""}"><i class="${!cur && g[0] > g[1] ? "w" : ""}">${g[0]}</i><i class="${!cur && g[1] > g[0] ? "w" : ""}">${g[1]}</i></span>`;
      }).join("");
      if (m.code && !r.dataset.match) { r.dataset.match = `${id}|${m.code}`; r.tabIndex = 0; r.setAttribute("role", "button"); }
      else if (m.code) r.dataset.match = `${id}|${m.code}`;
    }
  }

  async function get(id, all) {
    const r = await fetch(`/api/live?event=${encodeURIComponent(id)}${all ? "&all=1" : ""}`, { cache: "no-store" });
    if (!r.ok) throw new Error(r.status);
    return r.json();
  }

  // Event pages
  document.querySelectorAll("[data-wtt-live]").forEach((el) => {
    const id = el.dataset.wttLive;
    const now = el.querySelector(".lv-now"), done = el.querySelector(".lv-done"), note = el.querySelector(".lv-note");
    async function tick() {
      if (document.hidden) return;
      try {
        const d = await get(id, !!document.querySelector(".mc"));
        now.innerHTML = d.live.length ? d.live.map((m) => card(m, id)).join("") : '<p class="lv-empty">No match in play right now. Scores appear here as soon as the next one starts.</p>';
        if (done) done.innerHTML = d.results.slice(0, 12).map((m) => card(m, id)).join("");
        overlay(d, id);
        note.textContent = `Updated ${time(d.updated)}. Live data from World Table Tennis.`;
        el.hidden = done ? !(d.live.length || d.results.length) : !d.live.length;   // "Live now" only while a match is on
      } catch (e) {
        note.textContent = "Live scores are unavailable at the moment. They will return automatically.";
      }
    }
    tick();
    setInterval(tick, 15000);
    document.addEventListener("visibilitychange", tick);
  });

  // Event pages without live scores (finished events): fill in the match centre once, so every played match
  // has its result and opens point by point
  if (!document.querySelector("[data-wtt-live]")) document.querySelectorAll(".mc[data-wtt]").forEach((el) => get(el.dataset.wtt, true).then((d) => overlay(d, el.dataset.wtt)).catch(() => {}));

  document.querySelectorAll("[data-stream-q]").forEach((el) => { if (window.ElevenStream && !el.closest(".onnow")) window.ElevenStream(el); });

  // Scores strip: matches in play lead the strip, linking to the event page
  window.ElevenLive = { get, card };
})();
