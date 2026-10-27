// Live scores from WTT (through Eleven's /api/live), used on event pages and in the scores strip.
// Each [data-wtt-live] element gets the matches on now plus the latest results, refreshed every 15 seconds.
(function () {
  const FLAGS = {"CHN": "cn", "JPN": "jp", "KOR": "kr", "PRK": "kp", "HKG": "hk", "MAC": "mo", "SGP": "sg", "IND": "in", "IRI": "ir", "KAZ": "kz", "UZB": "uz", "THA": "th", "MAS": "my", "INA": "id", "VIE": "vn", "PHI": "ph", "QAT": "qa", "KSA": "sa", "UAE": "ae", "BRN": "bh", "EGY": "eg", "NGR": "ng", "ALG": "dz", "TUN": "tn", "MAR": "ma", "RSA": "za", "FRA": "fr", "GER": "de", "SWE": "se", "DEN": "dk", "NOR": "no", "FIN": "fi", "ENG": "gb-eng", "SCO": "gb-sct", "WAL": "gb-wls", "GBR": "gb", "IRL": "ie", "POR": "pt", "ESP": "es", "ITA": "it", "AUT": "at", "SUI": "ch", "BEL": "be", "NED": "nl", "LUX": "lu", "POL": "pl", "CZE": "cz", "SVK": "sk", "SLO": "si", "CRO": "hr", "SRB": "rs", "BIH": "ba", "MNE": "me", "MKD": "mk", "GRE": "gr", "TUR": "tr", "ROU": "ro", "HUN": "hu", "BUL": "bg", "UKR": "ua", "MDA": "md", "LTU": "lt", "LAT": "lv", "EST": "ee", "ISR": "il", "BRA": "br", "ARG": "ar", "CHI": "cl", "PER": "pe", "COL": "co", "VEN": "ve", "ECU": "ec", "URU": "uy", "PAR": "py", "MEX": "mx", "CUB": "cu", "DOM": "do", "PUR": "pr", "GUA": "gt", "CAN": "ca", "USA": "us", "AUS": "au", "NZL": "nz", "FIJ": "fj", "MON": "mc"};
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const flag = (c) => (FLAGS[c] ? `<span class="fi fi-${FLAGS[c]}" aria-hidden="true"></span>` : "");
  const time = (iso) => iso ? new Date(iso).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit", timeZone: "Europe/London" }) : "";

  function card(m) {
    const live = m.status === "live";
    const won = live ? null : m.score[0] > m.score[1] ? 0 : 1;
    const row = (i) => {
      const s = m.sides[i] || {};
      const cells = m.games.map((g, k) => {
        const cur = live && k === m.games.length - 1;
        const w = !cur && g[i] > g[1 - i];
        return `<td class="${cur ? "lv-cur" : ""}${w ? " lv-gw" : ""}">${g[i]}</td>`;
      }).join("");
      return `<tr class="${won === i ? "lv-won" : ""}"><th scope="row">${flag(s.nat)}<span class="lv-name">${esc(s.name)}</span><span class="lv-nat">${esc(s.nat)}</span>${live && m.server === i ? '<span class="lv-serve" title="Serving"></span>' : ""}</th>
        <td class="lv-sets">${m.score[i]}</td>${cells}</tr>`;
    };
    const meta = live ? `<span class="lv-dot"></span>Live${m.game ? `, game ${m.game}` : ""}` : "Final";
    return `<article class="lv-card${live ? " is-live" : ""}"><p class="lv-meta"><span>${meta}</span><span>${esc(m.label)}${m.table ? ` · ${esc(m.table)}` : ""}</span></p>
      <table class="lv-table"><caption class="sr-only">${esc(m.sides.map((s) => s.name).join(" v "))}</caption><tbody>${row(0)}${row(1)}</tbody></table></article>`;
  }

  async function get(id) {
    const r = await fetch(`/api/live?event=${encodeURIComponent(id)}`, { cache: "no-store" });
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
        const d = await get(id);
        now.innerHTML = d.live.length ? d.live.map(card).join("") : '<p class="lv-empty">No match in play right now. Scores appear here as soon as the next one starts.</p>';
        done.innerHTML = d.results.slice(0, 12).map(card).join("");
        note.textContent = `Updated ${time(d.updated)}. Live data from World Table Tennis.`;
        el.hidden = !(d.live.length || d.results.length);
      } catch (e) {
        note.textContent = "Live scores are unavailable at the moment. They will return automatically.";
      }
    }
    tick();
    setInterval(tick, 15000);
    document.addEventListener("visibilitychange", tick);
  });

  // Scores strip: matches in play lead the strip, linking to the event page
  window.ElevenLive = { get, card };
})();
