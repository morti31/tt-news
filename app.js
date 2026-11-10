(async function () {
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const day = (iso) => new Date(iso + "T12:00:00");
  const fmt = (iso, o = { day: "numeric", month: "short" }) => day(iso).toLocaleDateString("en-GB", o);
  const today = new Date().toISOString().slice(0, 10);

  let data;
  try {
    data = await fetch("data/news.json", { cache: "no-store" }).then((r) => r.json());
    const opt = (u) => fetch(u, { cache: "no-store" }).then((r) => (r.ok ? r.json() : {})).catch(() => ({}));
    const [sch, arts, hubs, top, feats, tagmap] = await Promise.all([opt("data/schedule.json"), opt("data/article-index.json"), opt("data/event-index.json"), opt("data/top-stories.json"), opt("data/features.json"), opt("data/tags.json")]);
    data.tags = tagmap || {};
    data.features = Array.isArray(feats) ? feats : [];
    data.top = Array.isArray(top) ? top : [];
    data.events = sch.events || [];
    data.articles = arts;
    data.hubs = hubs;
  } catch (e) {
    $("lead").innerHTML = "<p>The news didn't load. Refresh the page to try again.</p>";
    return;
  }
  const hubs = data.hubs, arts = data.articles, authors = data.authors || {};

  // ---- Story pieces
  const stamp = (s) => ((arts[s.id] || {}).published) || s.published;
  const when = (s) => {
    const p = stamp(s);
    if (!p) return fmt(s.date);
    const t = new Date(p);
    return t.toISOString().slice(0, 10) === today ? t.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" })
      : t.toLocaleDateString("en-GB", { day: "numeric", month: "short" });
  };
  const who = () => "Eleven Team";
  const url = (s) => (arts[s.id] && arts[s.id].url) || `/news/${s.id}`;
  const kicker = (s) => {
    const hub = s.event && hubs[s.event];
    const daily = s.day && ["Preview", "Review"].includes(s.kind) ? `Day ${s.day} ${s.kind.toLowerCase()}` : s.kind === "Update" ? "Quick update" : "";
    const text = [hub ? hub.name : (s.category === "Features" ? "Analysis" : s.category), daily].filter(Boolean).join(" · ");
    return `<span class="kicker" style="color:var(--${s.category}, var(--ink))">${esc(text)}</span>`;
  };

  const tagRow = (s, n) => {
    const t = (data.tags[s.id] || []).slice(0, n);
    return t.length ? `<ul class="tags" aria-label="Tags">${t.map(([name, href, type]) => `<li><a class="tg tg-${esc(type)}" href="${esc(href)}">${esc(name)}</a></li>`).join("")}</ul>` : "";
  };

  // Picture order: official video, then the event poster (once per page), then a photo, then an illustration
  let seen = new Set();
  function art(s, size) {
    const full = arts[s.id];
    if (full && full.video) {
      return `<div class="pic video-art"><img src="https://i.ytimg.com/vi/${esc(full.video)}/${size === "big" ? "maxresdefault" : "hqdefault"}.jpg" alt="" loading="lazy"
        onerror="this.onerror=null;this.src='https://i.ytimg.com/vi/${esc(full.video)}/hqdefault.jpg'"><span class="yt-play" aria-hidden="true"></span></div>`;
    }
    const hub = s.event && hubs[s.event];
    if (hub && hub.poster && !seen.has(s.event)) {
      seen.add(s.event);
      return `<div class="pic poster"><img src="${esc(hub.poster)}" alt="${esc(hub.name)} ${esc(hub.year)} poster" loading="lazy"></div>`;
    }
    const im = s.image;
    if (im && im.type === "photo") return `<div class="pic photo"><img src="${esc(im.url)}" alt="${esc(im.alt || "")}" loading="lazy"></div>`;
    if (im && im.type === "cartoon") return `<div class="pic cartoon" data-cartoon="${esc(im.src)}"></div>`;
    return "";
  }

  // ---- On now: the big event of the moment, in its own soft colour, with live scores
  // An event whose finals have all been played is over, even on its last day: it leaves "On now"
  const done = (h) => !!(h && h.champions && h.champions.length);
  const liveEvent = data.events.filter((e) => e.start <= today && e.end >= today && hubs[e.id] && !done(hubs[e.id]))
    .sort((a, b) => (b.prestige || 0) - (a.prestige || 0))[0];
  const onHub = liveEvent && hubs[liveEvent.id];
  // Events without the top players (Feeder and Contender: schedule prestige under 2) sit just above Analysis instead of at
  // the top of the page, and rise to the top at the quarter-finals. Star Contender (most have a world top-10 player
  // entered) and everything above lead from day one.
  const MAJOR = 2;
  const topNext = $("onnow").nextElementSibling;   // where the panel sits when it leads the page
  let lowPanel = false;
  function placeOnNow() {
    const el = $("onnow"), anchor = $("feat-row") && $("feat-row").closest("main");
    if (lowPanel && anchor) anchor.parentNode.insertBefore(el, anchor);
    else if (topNext) topNext.parentNode.insertBefore(el, topNext);
    document.body.classList.toggle("onnow-low", lowPanel && !$("onnow").hidden);
    window.__panelHigh = !lowPanel;
    document.dispatchEvent(new Event("onnow-placed"));   // the top strip switches between "panel carries the scores" and the usual cards
  }
  function moveUp() { if (!lowPanel) return; lowPanel = false; placeOnNow(); }
  function renderOnNow() {
    if (!onHub) return;
    const el = $("onnow");
    const s = day(onHub.start), n = Math.round((day(onHub.end) - s) / 864e5) + 1;
    const dnum = Math.round((day(today) - s) / 864e5) + 1;
    // Quarter-finals fall on the third day from the end of a six-day event, the second from the end of a shorter one
    lowPanel = (liveEvent.prestige || 0) < MAJOR && dnum < (n <= 5 ? n - 1 : n - 2);
    placeOnNow();
    const days = Array.from({ length: n }, (_, i) => {
      const d = new Date(s.getTime() + i * 864e5), iso = d.toISOString().slice(0, 10);
      const cls = [iso === today ? "now" : "", i === n - 1 ? "fin" : ""].join(" ");
      return `<div class="${cls}"><span>${d.toLocaleDateString("en-GB", { weekday: "short" })}</span><b>${String(d.getDate()).padStart(2, "0")}</b></div>`;
    }).join("");
    el.style.cssText = `--tint:${onHub.tint};--tint-rule:${onHub.tint_rule};--tint-ink:${onHub.tint_ink};--tier:${onHub.colour}`;
    el.innerHTML = `<div class="wrap onnow-inner">
      <div class="onnow-title"><span class="lab"><span class="live-dot"></span>On now · ${esc(onHub.series)}</span>
        <h2><a href="${esc(onHub.url)}">${esc(onHub.city)}</a></h2>
        <span class="lab sub">Day ${dnum} of ${n}${onHub.venue ? ` · ${esc(onHub.venue)}` : ""}</span>
        <div class="days">${days}</div>
        <a class="onnow-link" href="${esc(onHub.url)}">Draw, results and schedule</a></div>
      <div class="onnow-live"><div class="onnow-stream" data-stream-q="${esc(onHub.stream_q || onHub.city)}" hidden></div>
        <div id="onnow-live"><span class="lab">Live and latest</span><div class="lv-strip"><p class="lv-wait">Scores appear here when play starts.</p></div></div></div>
    </div>`;
    if (onHub.wtt) liveScores();
    const st = el.querySelector(".onnow-stream");
    if (st && window.ElevenStream) window.ElevenStream(st);
  }
  // ---- Champions: once a big event is over, the news leads again and the winners get their own panel
  // under the top stories for three days (or until the next big event starts)
  const FLAGS = {"CHN": "cn", "TPE": "tw", "RUS": "ru", "JPN": "jp", "KOR": "kr", "PRK": "kp", "HKG": "hk", "MAC": "mo", "SGP": "sg", "IND": "in", "IRI": "ir", "KAZ": "kz", "THA": "th", "MAS": "my", "INA": "id", "QAT": "qa", "EGY": "eg", "NGR": "ng", "ALG": "dz", "TUN": "tn", "FRA": "fr", "GER": "de", "SWE": "se", "DEN": "dk", "NOR": "no", "ENG": "gb-eng", "SCO": "gb-sct", "WAL": "gb-wls", "GBR": "gb", "IRL": "ie", "POR": "pt", "ESP": "es", "ITA": "it", "AUT": "at", "SUI": "ch", "BEL": "be", "NED": "nl", "LUX": "lu", "POL": "pl", "CZE": "cz", "SVK": "sk", "SLO": "si", "CRO": "hr", "SRB": "rs", "GRE": "gr", "TUR": "tr", "ROU": "ro", "HUN": "hu", "UKR": "ua", "BRA": "br", "ARG": "ar", "CHI": "cl", "PUR": "pr", "CAN": "ca", "USA": "us", "AUS": "au", "NZL": "nz", "MON": "mc"};
  const flagOf = (c) => (FLAGS[(c || "").toUpperCase()] ? `<span class="fi fi-${FLAGS[c.toUpperCase()]}" aria-hidden="true"></span>` : "");
  const plusDays = (iso, n) => new Date(day(iso).getTime() + n * 864e5).toISOString().slice(0, 10);
  const finished = onHub ? null : Object.entries(hubs)
    .filter(([id, h]) => id === Object.keys(hubs).find((k) => hubs[k] === h))   // each hub once, by its own id
    .filter(([, h]) => done(h) && !h.minor && h.end && h.start <= today && plusDays(h.end, 3) >= today)   // not Feeders or Contenders
    .sort((a, b) => b[1].end.localeCompare(a[1].end))[0];
  function renderChampions() {
    const el = $("champs");
    if (!el || !finished) return;
    const [id, h] = finished;
    const report = data.stories.filter((s) => s.event === id && s.kind === "Review")
      .sort((a, b) => (stamp(b) || b.date).localeCompare(stamp(a) || a.date))[0];
    const next = Object.values(hubs).filter((x, i, all) => all.indexOf(x) === i && x.start && x.start > today)
      .sort((a, b) => a.start.localeCompare(b.start))[0];
    const dates = `${day(h.start).toLocaleDateString("en-GB", { day: "numeric", month: "long" })} to ${day(h.end).toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric" })}`;
    const cards = h.champions.map((c) => `<div class="champ"><span class="champ-ev">${esc(c.event)} champion</span>
      <p class="champ-name">${flagOf(c.champion.nat)}${esc(c.champion.name)}</p>
      <p class="champ-final">Beat ${esc(c.runner_up.name)} ${esc(c.score)} in the final<span>${esc(c.games)}</span></p></div>`).join("");
    const nextTxt = next ? `<a class="champs-next" href="${esc(next.url)}">Next: ${esc(next.name)}, from ${esc(day(next.start).toLocaleDateString("en-GB", { weekday: "long", day: "numeric", month: "long" }))}</a>` : "";
    el.style.cssText = `--tier:${h.colour}`;
    el.innerHTML = `<div class="champs-head"><span class="lab">${esc(dates)}</span>
        <h2><a href="${esc(h.url)}">${esc(h.name)} ${esc(h.year)}: the champions</a></h2></div>
      <div class="champs">${cards}</div>
      <p class="champs-links">${report ? `<a href="${esc(url(report))}">Finals report</a>` : ""}<a href="${esc(h.url)}#draw">Results and draw</a><a href="${esc(h.url)}#watch">Highlights</a>${nextTxt}</p>`;
  }
  async function liveScores() {
    const box = $("onnow-live");
    const tick = async () => {
      if (document.hidden) return;
      try {
        const d = await fetch(`/api/live?event=${encodeURIComponent(onHub.wtt)}`, { cache: "no-store" }).then((r) => r.json());
        const scoreCard = (m) => {
          const live = m.status === "live", g = m.games[m.games.length - 1] || [0, 0];
          const won = live ? -1 : (m.score[0] > m.score[1] ? 0 : 1);
          const wr = (s) => (s && s.rank ? `<span class="wr" title="World No ${s.rank}">${s.rank}</span>` : "");
          const side = (i) => `<span class="row${won === i ? " won" : ""}"><span>${esc(m.sides[i].name)}${wr(m.sides[i])}</span><b>${m.score[i]}${live ? `<i class="pts">${g[i]}</i>` : ""}</b></span>`;
          return `<a class="score-card${live ? " is-live" : ""}" href="${esc(onHub.url)}#live" data-match="${esc(onHub.wtt)}|${esc(m.code)}"><span class="ev">${live ? '<span class="live-dot"></span>Live · ' : "Final · "}${esc(m.label)}</span>${side(0)}${side(1)}</a>`;
        };
        // Live matches, then the next two fixtures beside the last two results, then (from the
        // quarter-finals) every semi-final and final, filled in as players go through
        const fx = window.ElevenFixtures ? await window.ElevenFixtures.get(onHub, d).catch(() => ({ next: [], knock: [] })) : { next: [], knock: [] };
        const live = d.live || [], done = (d.results || []).slice(0, 2);
        // The first quarter-final (played or on the way) lifts a lower-profile event to the top of the page
        if (lowPanel && (fx.knock.length || [...live, ...(d.results || [])].some((m) => /quarter|semi|final/i.test(m.label || "")))) moveUp();
        if (!live.length && !done.length && !fx.next.length) return;
        const grp = (lab, cards, cls = "") => cards.length ? `<div class="lv-grp ${cls}"><span class="lab">${lab}</span><div class="lv-strip${cls ? "" : " one"}">${cards.join("")}</div></div>` : "";
        const F = window.ElevenFixtures;
        const html = grp('<span class="live-dot"></span>Live now', live.map(scoreCard), "lv-wide")
          + `<div class="lv-cols">${grp("Next up", fx.next.map((x) => F.card(x, onHub)))}${grp("Latest results", done.map(scoreCard))}</div>`
          + (fx.knock.length ? `<div class="lv-grp lv-knock"><span class="lab">Semi-finals and finals</span><div class="lv-ko">${fx.knock.map((k) =>
              `<div><h3>${esc(k.name)}</h3><div class="lv-strip one">${k.items.map((x) => F.card(x, onHub, { short: true })).join("")}</div></div>`).join("")}</div></div>` : "");
        if (box.dataset.h !== html) { box.dataset.h = html; box.innerHTML = html; }   // redraw only when something changed, so nothing flickers or loses a tap
      } catch (e) { console.error("live panel", e); /* keep the last scores showing */ }
    };
    tick();
    setInterval(tick, 15000);
    document.addEventListener("visibilitychange", tick);
  }

  // ---- Watch: official highlights, four at a time, rotating hourly and mixing men's and women's matches
  // Newest WTT match highlights for the event on now (or the latest one), straight from WTT's YouTube channel.
  // Falls back to the hand-picked list in news.json if the feed is empty or down.
  async function renderWatch() {
    const started = Object.values(hubs).filter((h) => h.start && h.start <= today && h.stream_q && !h.minor)
      .sort((a, b) => b.start.localeCompare(a.start));
    const target = onHub || started[0];
    if (target) {
      try {
        const q = target.stream_q || `${target.city} ${target.year}`;
        const d = await fetch(`/api/highlights?q=${encodeURIComponent(q)}`).then((r) => r.json());
        const vids = (d.videos || []).filter((v) => v.id);
        if (vids.length >= 2) {
          const w = vids.filter((v) => v.gender === "W"), m = vids.filter((v) => v.gender !== "W");
          const pick = [];
          for (let i = 0; pick.length < Math.min(4, vids.length); i++) {   // newest first, women and men in turn
            const v = (i % 2 ? m : w)[Math.floor(i / 2)] || (i % 2 ? w : m)[Math.floor(i / 2)];
            if (v && !pick.includes(v)) pick.push(v);
            if (i > 16) break;
          }
          return drawWatch(pick, target);
        }
      } catch (e) { /* fall back below */ }
    }
    const all = (data.highlights || []).filter((v) => v.id);
    if (all.length < 2) return;
    const byDate = [...all].sort((a, b) => b.date.localeCompare(a.date));
    const ev = ((onHub && byDate.find((v) => hubs[v.event] === onHub)) || byDate[0]).event;
    let pool = byDate.filter((v) => v.event === ev).slice(0, 8);
    if (pool.length < 4) pool = pool.concat(byDate.filter((v) => !pool.includes(v))).slice(0, 8);
    const turn = Math.floor(Date.now() / 36e5);
    const groups = [pool.filter((v) => v.gender === "W"), pool.filter((v) => v.gender === "M"), pool.filter((v) => !["M", "W"].includes(v.gender))];
    const pick = [];
    for (let i = 0; pick.length < Math.min(4, pool.length) && i < 24; i++) {
      const src = groups[i % 3];
      if (!src.length) continue;
      const v = src[(turn + Math.floor(i / 3)) % src.length];
      if (!pick.includes(v)) pick.push(v);
    }
    drawWatch(pick, hubs[ev]);
  }
  let curCat = "All";
  function drawWatch(pick, hub) {
    $("watch").innerHTML = `<div class="wrap"><div class="sec-head"><h2 id="watch-h">Watch</h2>${hub ? `<a href="${esc(hub.url)}">${esc(hub.name)} ${esc(hub.year)} highlights</a>` : ""}</div>
      <div class="rail">${pick.map((v) => `<figure class="video">
        <button type="button" class="yt" data-yt="${esc(v.id)}" aria-label="Play video: ${esc(v.title)}">
          <img src="https://i.ytimg.com/vi/${esc(v.id)}/hqdefault.jpg" alt="" loading="lazy" width="480" height="360"><span class="yt-play" aria-hidden="true"></span>
        </button><figcaption>${esc(v.title)}<span>Video: ${esc(v.channel || "YouTube")}</span></figcaption></figure>`).join("")}</div></div>`;
    $("watch").hidden = curCat !== "All";
  }
  document.addEventListener("click", (ev) => {
    const b = ev.target.closest("#watch .yt");
    if (!b) return;
    const f = document.createElement("iframe");
    f.src = "https://www.youtube-nocookie.com/embed/" + b.dataset.yt + "?autoplay=1&rel=0";
    f.title = b.getAttribute("aria-label").replace("Play video: ", "");
    f.allow = "accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture; web-share";
    f.allowFullscreen = true;
    b.replaceWith(f);
  });

  // ---- Events row: upcoming (on now and next) and recent (just finished), as two tabs
  function renderEvents() {
    const uniq = (arr) => { const u = new Set(); return arr.filter((h) => !u.has(h.url) && u.add(h.url)); };
    const all = uniq(Object.values(hubs).filter((h) => h.end && h.start && h.series !== "WTT Feeder"));   // Feeders have pages but are not major events
    const up = all.filter((h) => h.end >= today).sort((a, b) => a.start.localeCompare(b.start)).slice(0, 4);
    const past = all.filter((h) => h.end < today).sort((a, b) => b.end.localeCompare(a.end)).slice(0, 4);
    if (!up.length && !past.length) return;
    const tile = (h, recent) => `<a class="ev-tile" href="${esc(h.url)}"><img src="${esc(h.tile || h.poster)}" alt="" loading="lazy">
        <h3>${esc(h.name)}</h3><span>${recent ? `Finished ${fmt(h.end)} · Results` : h.start <= today ? "On now" : `${fmt(h.start)} to ${fmt(h.end)}`}</span></a>`;
    const first = up.length ? "up" : "past";
    $("ev-row").innerHTML = `<div class="sec-head"><h2 id="evrow-h">Major events</h2><a href="/events/">All events</a></div>
      <div class="ev-tabs" role="tablist" aria-label="Major events">
        <button type="button" role="tab" data-ev="up" aria-selected="${first === "up"}"${up.length ? "" : " disabled"}>Upcoming</button>
        <button type="button" role="tab" data-ev="past" aria-selected="${first === "past"}"${past.length ? "" : " disabled"}>Recent</button></div>
      <div class="ev-tiles" data-panel="up"${first === "up" ? "" : " hidden"}>${up.map((h) => tile(h, false)).join("")}</div>
      <div class="ev-tiles" data-panel="past"${first === "past" ? "" : " hidden"}>${past.map((h) => tile(h, true)).join("")}</div>`;
    $("ev-row").querySelectorAll(".ev-tabs button").forEach((b) => b.addEventListener("click", () => {
      $("ev-row").querySelectorAll(".ev-tabs button").forEach((x) => x.setAttribute("aria-selected", String(x === b)));
      $("ev-row").querySelectorAll("[data-panel]").forEach((p) => { p.hidden = p.dataset.panel !== b.dataset.ev; });
    }));
  }

  // ---- Stories
  const stories = [...data.stories].sort((a, b) => (stamp(b) || b.date).localeCompare(stamp(a) || a.date));
  function render(cat) {
    seen = new Set();
    const list = cat === "All" ? stories : stories.filter((s) => s.category === cat);
    const lead = (cat === "All" && list.find((s) => s.top)) || list[0];
    const rest = list.filter((s) => s !== lead);
    $("lead").innerHTML = lead ? `<article class="big">${art(lead, "big") || fallbackPic(lead, true)}<div class="big-text">${kicker(lead)}
      <h1><a class="stretch" href="${esc(url(lead))}">${esc(lead.headline)}</a></h1><p>${esc(lead.summary)}</p>
      <span class="meta">${when(lead)} · By ${esc(who(lead))}</span>${tagRow(lead, 3)}</div></article>`
      : '<p class="empty">Nothing in this section yet. New stories arrive with each update.</p>';
    // Top stories: the weighted order worked out at build time (prestige, freshness, results, video, events on now)
    const rank = (s) => { const k = data.top.indexOf(s.id); return k < 0 ? 999 : k; };
    // Features (not guides) can be Top stories too, on the All view
    const featTops = cat === "All" ? data.features.map((f) => ({ id: f.slug, headline: f.title, published: f.published, date: (f.published || "").slice(0, 10), category: "Features" })) : [];
    const tops = [...rest, ...featTops].filter((s) => cat !== "All" || rank(s) < 999).sort((a, b) => rank(a) - rank(b)).slice(0, 5);
    // Latest: strictly newest first, whether or not a story is also in Top stories
    const more = rest;
    $("second").innerHTML = tops.map((s) => `<li><a href="${esc(url(s))}">${esc(s.headline)}</a><span class="meta">${when(s)}</span></li>`).join("");
    $("second").closest(".tops").hidden = !tops.length;
    $("stories").innerHTML = latestColumns(more);
    $("empty").hidden = more.length > 0;
    fillCartoons();
    balance();
  }

  // Latest: three columns, Events, Clubs and Other news. Each has a picture card for its newest story and
  // three headlines under it. Every card has a picture: video, event poster, photo or illustration first, then
  // the league's poster for club stories and a topic poster for the rest (img/posters/league-*, topic-*).
  const LEAGUE_POSTER = [[/Champions League/i, "champions-league"], [/Bundesliga|TTBL/i, "bundesliga"], [/Super League|CTTSL/i, "super-league"],
    [/T\.? ?League/i, "t-league"], [/Pro A\b/i, "pro-a"], [/MLTT|Major League/i, "mltt"], [/\bUTT\b|Ultimate Table Tennis/i, "utt"]];
  // The lead story always has a picture: with no video, poster, photo or illustration it takes this poster too.
  function fallbackPic(s, eager) {
    const text = `${s.headline} ${s.summary || ""}`;
    let src;
    if (s.event && hubs[s.event] && hubs[s.event].poster) src = hubs[s.event].poster;
    else if (s.category === "Clubs") { const m = LEAGUE_POSTER.find(([rx]) => rx.test(text)); src = `/img/posters/league-${m ? m[1] : "champions-league"}.jpg`; }
    else if (/world (No|ranking)|rankings?\b/i.test(s.headline)) src = "/img/posters/topic-rankings.jpg";
    else if (s.category === "England") src = "/img/posters/topic-england.jpg";
    else if (s.category === "Equipment") src = "/img/posters/topic-equipment.jpg";
    else src = "/img/posters/topic-news.jpg";
    return `<div class="pic poster"><img src="${esc(src)}" alt=""${eager ? "" : ' loading="lazy"'}></div>`;
  }
  function latestColumns(list) {
    const group = (s) => (s.category === "Clubs" ? "clubs" : s.event ? "events" : "other");
    const cols = [["events", "Events", "/events/"], ["clubs", "Clubs", "/clubs/"], ["other", "Other news", "/news/"]];
    return `<div class="l3">${cols.map(([k, title, href]) => {
      const items = list.filter((s) => group(s) === k).slice(0, 4);
      if (!items.length) return "";
      const [first, ...rest] = items;
      seen = new Set();
      const pic = art(first, "small") || fallbackPic(first);
      return `<section class="l3-col" aria-label="${esc(title)}"><h3 class="l3-h"><a href="${href}">${esc(title)}</a></h3>
        <article class="l3-card">${pic}<span class="l3-meta">${when(first)}${first.kind === "Update" ? " · Quick update" : ""}</span>
        <h4><a class="stretch" href="${esc(url(first))}">${esc(first.headline)}</a></h4></article>
        <ul class="l3-list">${rest.map((s) => `<li><a href="${esc(url(s))}"><span class="l3-meta">${when(s)}</span><span class="l3-t">${esc(s.headline)}</span></a></li>`).join("")}</ul></section>`;
    }).join("")}</div>`;
  }

  // Latest stops where the sidebar stops, so the right-hand column never leaves white space beside it.
  // At least four stories always show; on phones (one column) the list is capped at eight.
  // The rest are a click away on the News page.
  function balance() {
    const list = $("stories"), aside = document.querySelector(".layout > aside");
    if (!list || !aside) return;
    if (list.querySelector(".l3")) {   // the three-column Latest is a fixed size: no trimming, one link to all news
      let more = $("latest-more");
      if (!more) { more = document.createElement("a"); more.id = "latest-more"; more.className = "panel-link latest-more"; more.href = "/news/"; list.after(more); }
      more.textContent = "More news"; more.hidden = false;
      return;
    }
    const items = [...list.children];
    items.forEach((el) => (el.hidden = false));
    const oneCol = getComputedStyle(list.closest(".layout")).gridTemplateColumns.split(" ").length < 2;
    let shown = items.length;
    if (oneCol) shown = Math.min(items.length, 8);
    else {
      // the aside may be stretched to the row's height, so measure its last panel rather than the aside itself
      const last = [...aside.children].filter((c) => !c.hidden && c.offsetHeight).pop();
      const limit = (last || aside).getBoundingClientRect().bottom;
      shown = items.filter((el) => el.getBoundingClientRect().bottom <= limit + 24).length;
      shown = Math.max(Math.min(4, items.length), shown);
    }
    items.forEach((el, i) => (el.hidden = i >= shown));
    let more = $("latest-more");
    if (!more) {
      more = document.createElement("a");
      more.id = "latest-more"; more.className = "panel-link latest-more"; more.href = "/news/";
      list.after(more);
    }
    more.textContent = "More news";
    more.hidden = shown >= items.length;
  }
  if (window.ResizeObserver) {
    let t;
    new ResizeObserver(() => { clearTimeout(t); t = setTimeout(balance, 120); }).observe(document.querySelector(".layout > aside") || document.body);
  }
  window.addEventListener("resize", () => balance());

  // Illustrations are inlined so they inherit the page's colours
  const cartoonCache = {};
  async function fillCartoons() {
    for (const el of document.querySelectorAll("[data-cartoon]:not(.filled)")) {
      const src = el.dataset.cartoon;
      try {
        cartoonCache[src] ??= fetch(src).then((r) => r.text());
        el.innerHTML = await cartoonCache[src];
        el.querySelector("svg")?.setAttribute("preserveAspectRatio", "xMidYMid slice");
        el.classList.add("filled");
      } catch (e) { /* leave the tinted panel showing */ }
    }
  }

  // Home shows everything; Clubs and Equipment filter the stories
  function show(cat) {
    curCat = cat;
    const home = cat === "All";
    $("onnow").hidden = !home || !onHub;
    if ($("champs")) $("champs").hidden = !home || !finished;
    // the "on now" section carries the live scores, so the scores strip steps aside on the homepage
    document.body.classList.toggle("has-onnow", home && !!onHub);
    document.body.classList.toggle("onnow-low", home && !!onHub && lowPanel);
    $("watch").hidden = !home || !$("watch").innerHTML;
    $("feat-row").hidden = !home || !$("feat-row").innerHTML;
    $("ev-row").hidden = !home || !$("ev-row").innerHTML;
    render(cat);
  }
  $("tabs").addEventListener("click", (e) => {
    const b = e.target.closest("button");
    if (!b) return;
    document.querySelectorAll("#tabs button").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
    show(b.dataset.cat);
  });
  const fromHash = () => {
    const h = decodeURIComponent(location.hash.slice(1));
    const cat = ["International", "England", "Clubs", "Equipment"].includes(h) ? h : "All";
    document.querySelectorAll("#tabs button").forEach((x) => x.setAttribute("aria-pressed", String(x.dataset.cat === cat)));
    show(cat);
  };
  // Analysis (the Features category): the newest three long reads
  function renderFeatures() {
    const fs = [...data.features].sort((a, b) => b.published.localeCompare(a.published)).slice(0, 3);
    if (!fs.length) return;
    $("feat-row").innerHTML = `<div class="sec-head"><h2 id="feat-h">Analysis</h2><a href="/features/">All analysis</a></div><div class="feat-grid" style="--n:${fs.length}">` +
      fs.map((f) => `<article class="feat"><a href="${esc(f.url)}">${f.cover ? `<img src="${esc(f.cover)}" alt="" loading="lazy">` : ""}
        <span class="kicker" style="color:var(--ball)">${esc(f.kind)}</span><h3>${esc(f.title)}</h3><p>${esc(f.standfirst)}</p><span class="meta">By ${esc(f.author)}</span></a></article>`).join("") + "</div>";
  }
  renderOnNow();
  renderChampions();
  renderFeatures();
  renderWatch();
  renderEvents();
  window.addEventListener("hashchange", () => { fromHash(); window.scrollTo(0, 0); });
  fromHash();
})();
