// Fixtures for the live score sections (homepage "On now" panel and the scores strip):
//   next   the next two matches on the order of play that haven't started
//   knock  from the quarter-finals on, the semi-finals and finals for women and men, filled in as
//          players go through ("Winner of Calderano v Moregard" until the quarter-final is played)
// Built from data/schedule.json (WTT order of play, synced every 30 minutes), data/draws/<id>.json
// (the draw) and the /api/live reply the page has already fetched, so results show at once.
(function () {
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const FLAGS = {"CHN": "cn", "TPE": "tw", "RUS": "ru", "JPN": "jp", "KOR": "kr", "PRK": "kp", "HKG": "hk", "MAC": "mo", "SGP": "sg", "IND": "in", "IRI": "ir", "KAZ": "kz", "THA": "th", "MAS": "my", "INA": "id", "QAT": "qa", "EGY": "eg", "NGR": "ng", "ALG": "dz", "TUN": "tn", "FRA": "fr", "GER": "de", "SWE": "se", "DEN": "dk", "NOR": "no", "FIN": "fi", "ENG": "gb-eng", "SCO": "gb-sct", "WAL": "gb-wls", "GBR": "gb", "IRL": "ie", "POR": "pt", "ESP": "es", "ITA": "it", "AUT": "at", "SUI": "ch", "BEL": "be", "NED": "nl", "LUX": "lu", "POL": "pl", "CZE": "cz", "SVK": "sk", "SLO": "si", "CRO": "hr", "SRB": "rs", "GRE": "gr", "TUR": "tr", "ROU": "ro", "HUN": "hu", "UKR": "ua", "BRA": "br", "ARG": "ar", "CHI": "cl", "PUR": "pr", "CAN": "ca", "USA": "us", "AUS": "au", "NZL": "nz", "MON": "mc"};
  const flag = (c) => (FLAGS[c] ? `<span class="fi fi-${FLAGS[c]}" aria-hidden="true"></span>` : "");
  const j = (u) => fetch(u, { cache: "no-store" }).then((r) => (r.ok ? r.json() : null)).catch(() => null);
  const key = (code) => String(code || "").replace(/-/g, "").toLowerCase();   // WTT document code, as in fixture ids
  const surname = (p) => {
    const w = String(p.name || "").trim().split(/\s+/);
    return ["CHN", "TPE", "KOR", "HKG", "MAC", "PRK"].includes(p.nat) ? w[0] : w[w.length - 1];
  };
  const same = (a, b) => a && b && a.toLowerCase() === b.toLowerCase();

  const store = {};
  async function base(hub) {
    const hit = store[hub.wtt];
    if (hit && Date.now() - hit.t < 5 * 6e4) return hit.v;
    const [sch, draw, rk] = await Promise.all([j("/data/schedule.json"), j(`/data/draws/${hub.wtt}.json`), j("/data/rankings.json")]);
    const people = {};
    for (const g of ["men", "women"]) for (const p of (rk && rk[g]) || []) people[p.name.toLowerCase()] = { nat: p.nat, rank: p.rank };
    for (const ev of Object.values((draw && draw.events) || {}))
      for (const r of ev.rounds || []) for (const m of r.matches || []) for (const p of m.players || [])
        if (p && p.name && !people[p.name.toLowerCase()]) people[p.name.toLowerCase()] = { nat: p.nat };
    const fx = ((sch && sch.fixtures) || []).filter((f) => f.id.startsWith(`wtt-${hub.wtt}-`));
    const v = { fx, draw, people };
    store[hub.wtt] = { t: Date.now(), v };
    return v;
  }

  function parseFixture(f, hub, people) {
    // "WTT Champions Frankfurt: Sofia Polcanova v Miwa Harimoto, women's singles, last 32"
    const rest = f.name.slice(f.name.indexOf(": ") + 2);
    const [pair, ...lab] = rest.split(", ");
    const sides = pair.split(" v ").map((n) => ({ name: n.trim(), ...(people[n.trim().toLowerCase()] || {}) }));
    const label = lab.join(", ").replace(/semifinal/i, "semi-final").replace(/quarterfinal/i, "quarter-final");
    return { kind: "fixture", id: f.id.slice(`wtt-${hub.wtt}-`.length), when: f.start, table: f.detail || "", label: label[0].toUpperCase() + label.slice(1), sides };
  }

  // Which side of a draw match won: from the draw, or from a WTT result with the same two players
  function winnerOf(m, done) {
    if (!m || !m.players || !m.players[0] || !m.players[1]) return null;
    if (m.winner === 0 || m.winner === 1) return m.winner;
    const r = done.find((x) => x.sides.length === 2 && m.players.every((p) => x.sides.some((s) => same(s.name, p.name))));
    if (!r) return null;
    const w = r.score[0] > r.score[1] ? 0 : 1;
    return same(r.sides[w].name, m.players[0].name) ? 0 : 1;
  }

  function slot(prev, i, done, prevName) {
    // Side i of a match in the next round: the winner of match i in the previous round, or who that is between
    const m = prev && prev.matches && prev.matches[i];
    const w = winnerOf(m, done);
    if (w !== null) return { ...m.players[w] };
    if (m && m.players && m.players[0] && m.players[1]) return { tbd: `Winner of ${surname(m.players[0])} v ${surname(m.players[1])}` };
    return { tbd: `Winner of ${prevName} ${i + 1}` };
  }

  async function get(hub, liveData) {
    const { fx, draw, people } = await base(hub);
    const live = (liveData && liveData.live) || [], done = (liveData && liveData.results) || [];
    const started = new Set(live.concat(done).map((m) => key(m.code)));
    const soon = Date.now() - 3 * 36e5;   // a fixture three hours past its time without a result is dropped
    const next = fx.filter((f) => !started.has(f.id.slice(`wtt-${hub.wtt}-`.length)) && new Date(f.start).getTime() > soon)
      .sort((a, b) => a.start.localeCompare(b.start)).slice(0, 2).map((f) => parseFixture(f, hub, people));

    // Knockout block: from the quarter-finals (all eight quarter-finalists known in either draw) until both finals are played
    const knock = [];
    let show = false, allDone = true;
    for (const [g, ev] of Object.entries((draw && draw.events) || {})) {
      const rounds = ev.rounds || [], idx = (n) => rounds.findIndex((r) => r.round.toLowerCase().startsWith(n));
      const qf = rounds[idx("quarter")], sf = rounds[idx("semi")], fin = rounds[idx("final")];
      if (!qf || !sf || !fin) continue;
      if (qf.matches.every((m) => m.players && m.players[0] && m.players[1])) show = true;
      const prefix = g === "women" ? "ttewsingles" : g === "men" ? "ttemsingles" : null;
      if (!prefix) continue;
      const card = (round, label, i, sidesFrom) => {
        const sides = [0, 1].map((s) => (round.matches[i] && round.matches[i].players && round.matches[i].players[s]) ? { ...round.matches[i].players[s] } : slot(sidesFrom, 2 * i + s, done, sidesFrom === qf ? "quarter-final" : "semi-final"));
        sides.forEach((s) => s.name && Object.assign(s, people[s.name.toLowerCase()] || {}, s));
        const code = `${prefix}${label === "Final" ? "fnl" : "sfnl"}000${i + 1}00`;
        const f = fx.find((x) => x.id.endsWith(code));
        const m = live.concat(done).find((x) => key(x.code) === code)
          || (sides.every((s) => s.name) ? live.concat(done).find((x) => sides.every((s) => x.sides.some((y) => same(y.name, s.name)))) : null);
        if (!m || m.status !== "final") allDone = false;
        return { kind: "knock", label: `${ev.name}, ${label.toLowerCase()}`, short: label, when: f ? f.start : null, table: f ? f.detail || "" : "", sides, match: m || null };
      };
      knock.push({ name: ev.name, items: [card(sf, "Semi-final", 0, qf), card(sf, "Semi-final", 1, qf), card(fin, "Final", 0, sf)] });
    }
    return { next, knock: show && !allDone ? knock : [] };
  }

  const when = (iso) => {
    if (!iso) return "Time to be confirmed";
    const d = new Date(iso), uk = {};
    const today = new Date().toLocaleDateString("en-GB", uk) === d.toLocaleDateString("en-GB", uk);
    const t = d.toLocaleTimeString("en-GB", { ...uk, hour: "2-digit", minute: "2-digit" });
    return today ? t : `${d.toLocaleDateString("en-GB", { ...uk, weekday: "short" })} ${t}`;
  };
  const wr = (s) => (s && s.rank ? `<span class="wr" title="World No ${s.rank}">${s.rank}</span>` : "");

  // A fixture card in the same style as the score cards: names on the left, the start time on the right
  function card(it, hub, opts = {}) {
    const m = it.match;
    if (m) {   // already under way or played: a normal score card that opens point by point
      const live = m.status === "live", won = live ? -1 : (m.score[0] > m.score[1] ? 0 : 1);
      const side = (i) => `<span class="row${won === i ? " won" : ""}"><span>${flag(m.sides[i].nat)}${esc(m.sides[i].name)}${wr(m.sides[i])}</span><b>${m.score[i]}</b></span>`;
      return `<a class="score-card${live ? " is-live" : ""}" href="${esc(hub.url)}#live" data-match="${esc(hub.wtt)}|${esc(m.code)}"><span class="ev">${live ? '<span class="live-dot"></span>Live · ' : "Result · "}${esc(opts.short ? it.short : it.label)}</span>${opts.where ? `<span class="where">${esc(hub.name)}</span>` : ""}${side(0)}${side(1)}</a>`;
    }
    const row = (s) => s.tbd ? `<span class="row tbd"><span>${esc(s.tbd)}</span></span>`
      : `<span class="row"><span>${flag(s.nat)}${esc(s.name)}${wr(s)}</span></span>`;
    return `<a class="score-card fx-card" href="${esc(hub.url)}#schedule"><span class="ev">${esc((opts.prefix || "") + (opts.short && it.short ? it.short : it.label))}</span>${opts.where ? `<span class="where">${esc(hub.name)}</span>` : ""}
      <span class="fx-when${it.when ? "" : " tbc"}">${esc(when(it.when))}${it.table ? ` · ${esc(it.table)}` : ""}</span>${row(it.sides[0])}${row(it.sides[1])}</a>`;
  }

  window.ElevenFixtures = { get, card };
})();
