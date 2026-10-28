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
    const [sch, arts, hubs, top, feats] = await Promise.all([opt("data/schedule.json"), opt("data/article-index.json"), opt("data/event-index.json"), opt("data/top-stories.json"), opt("data/features.json")]);
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

  $("updated").textContent = "Last updated " + new Date(data.updated).toLocaleString("en-GB", {
    weekday: "long", day: "numeric", month: "long", hour: "2-digit", minute: "2-digit"
  });

  // ---- Story pieces
  const stamp = (s) => ((arts[s.id] || {}).published) || s.published;
  const when = (s) => {
    const p = stamp(s);
    if (!p) return fmt(s.date);
    const t = new Date(p);
    return t.toISOString().slice(0, 10) === today ? t.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" })
      : t.toLocaleDateString("en-GB", { day: "numeric", month: "short" });
  };
  const who = (s) => (authors[s.author] || authors.tom || { name: "Eleven" }).name;
  const url = (s) => (arts[s.id] && arts[s.id].url) || `/news/${s.id}`;
  const kicker = (s) => {
    const hub = s.event && hubs[s.event];
    const daily = s.day && ["Preview", "Review"].includes(s.kind) ? `Day ${s.day} ${s.kind.toLowerCase()}` : s.kind === "Update" ? "Quick update" : "";
    const text = [hub ? hub.name : s.category, daily].filter(Boolean).join(" · ");
    return `<span class="kicker" style="color:var(--${s.category}, var(--ink))">${esc(text)}${s.lang ? `<span class="translated"> · translated from ${esc(s.lang)}</span>` : ""}</span>`;
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
  const liveEvent = data.events.filter((e) => e.start <= today && e.end >= today && hubs[e.id])
    .sort((a, b) => (b.prestige || 0) - (a.prestige || 0))[0];
  const onHub = liveEvent && hubs[liveEvent.id];
  function renderOnNow() {
    if (!onHub) return;
    const el = $("onnow");
    const s = day(onHub.start), n = Math.round((day(onHub.end) - s) / 864e5) + 1;
    const dnum = Math.round((day(today) - s) / 864e5) + 1;
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
        <span class="lab">Live and latest</span><div class="lv-strip" id="onnow-live"><p class="lv-wait">Scores appear here when play starts.</p></div></div>
    </div>`;
    if (onHub.wtt) liveScores();
    const st = el.querySelector(".onnow-stream");
    if (st && window.ElevenStream) window.ElevenStream(st);
  }
  async function liveScores() {
    const box = $("onnow-live");
    const tick = async () => {
      if (document.hidden) return;
      try {
        const d = await fetch(`/api/live?event=${encodeURIComponent(onHub.wtt)}`, { cache: "no-store" }).then((r) => r.json());
        const ms = (d.live || []).concat(d.results || []).slice(0, 4);
        if (!ms.length) return;
        box.innerHTML = ms.map((m) => {
          const live = m.status === "live", g = m.games[m.games.length - 1] || [0, 0];
          const won = live ? -1 : (m.score[0] > m.score[1] ? 0 : 1);
          const side = (i) => `<span class="row${won === i ? " won" : ""}"><span>${esc(m.sides[i].name)}</span><b>${m.score[i]}${live ? `<i class="pts">${g[i]}</i>` : ""}</b></span>`;
          return `<a class="score-card${live ? " is-live" : ""}" href="${esc(onHub.url)}#live"><span class="ev">${live ? '<span class="live-dot"></span>Live · ' : "Final · "}${esc(m.label)}</span>${side(0)}${side(1)}</a>`;
        }).join("");
      } catch (e) { /* keep the last scores showing */ }
    };
    tick();
    setInterval(tick, 15000);
    document.addEventListener("visibilitychange", tick);
  }

  // ---- Watch: official highlights, four at a time, rotating hourly and mixing men's and women's matches
  // Newest WTT match highlights for the event on now (or the latest one), straight from WTT's YouTube channel.
  // Falls back to the hand-picked list in news.json if the feed is empty or down.
  async function renderWatch() {
    const started = Object.values(hubs).filter((h) => h.start && h.start <= today && h.stream_q)
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

  // ---- Events row: posters for the event on now and the next ones
  function renderEvents() {
    const urls = new Set();
    const list = Object.values(hubs).filter((h) => h.end && h.end >= today && !urls.has(h.url) && urls.add(h.url))
      .sort((a, b) => (a.start || "").localeCompare(b.start || "")).slice(0, 4);
    if (!list.length) return;
    $("ev-row").innerHTML = `<div class="sec-head"><h2 id="evrow-h">Major events</h2><a href="/events/">All events</a></div>
      <div class="ev-tiles">${list.map((h) => `<a class="ev-tile" href="${esc(h.url)}"><img src="${esc(h.tile || h.poster)}" alt="" loading="lazy">
        <h3>${esc(h.name)}</h3><span>${h.start <= today ? "On now" : `${fmt(h.start)} to ${fmt(h.end)}`}</span></a>`).join("")}</div>`;
  }

  // ---- Stories
  const stories = [...data.stories].sort((a, b) => (stamp(b) || b.date).localeCompare(stamp(a) || a.date));
  function render(cat) {
    seen = new Set();
    const list = cat === "All" ? stories : stories.filter((s) => s.category === cat);
    const lead = (cat === "All" && list.find((s) => s.top)) || list[0];
    const rest = list.filter((s) => s !== lead);
    $("lead").innerHTML = lead ? `<article class="big">${art(lead, "big")}<div class="big-text">${kicker(lead)}
      <h1><a class="stretch" href="${esc(url(lead))}">${esc(lead.headline)}</a></h1><p>${esc(lead.summary)}</p>
      <span class="meta">${when(lead)} · By ${esc(who(lead))}</span></div></article>`
      : '<p class="empty">Nothing in this section yet. New stories arrive with each update.</p>';
    // Top stories: the weighted order worked out at build time (prestige, freshness, results, video, events on now)
    const rank = (s) => { const k = data.top.indexOf(s.id); return k < 0 ? 999 : k; };
    const tops = [...rest].sort((a, b) => rank(a) - rank(b)).slice(0, 5);
    // Latest: strictly newest first, whether or not a story is also in Top stories
    const more = rest;
    $("second").innerHTML = tops.map((s) => `<li><a href="${esc(url(s))}">${esc(s.headline)}</a><span class="meta">${when(s)}</span></li>`).join("");
    $("second").closest(".tops").hidden = !tops.length;
    $("stories").innerHTML = more.map((s) => `<article class="promo">${art(s, "small")}<div>${kicker(s)}
      <h3><a class="stretch" href="${esc(url(s))}">${esc(s.headline)}</a></h3><span class="meta">${when(s)} · By ${esc(who(s))}</span></div></article>`).join("");
    $("empty").hidden = more.length > 0;
    fillCartoons();
  }

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
    // the "on now" section carries the live scores, so the scores strip steps aside on the homepage
    document.body.classList.toggle("has-onnow", home && !!onHub);
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
  // Features: the newest three long reads
  function renderFeatures() {
    const fs = [...data.features].sort((a, b) => b.published.localeCompare(a.published)).slice(0, 3);
    if (!fs.length) return;
    $("feat-row").innerHTML = `<div class="sec-head"><h2 id="feat-h">Features</h2><a href="/features/">All features</a></div><div class="feat-grid">` +
      fs.map((f) => `<article class="feat"><a href="${esc(f.url)}">${f.cover ? `<img src="${esc(f.cover)}" alt="" loading="lazy">` : ""}
        <span class="kicker" style="color:var(--ball)">${esc(f.kind)}</span><h3>${esc(f.title)}</h3><p>${esc(f.standfirst)}</p><span class="meta">By ${esc(f.author)}</span></a></article>`).join("") + "</div>";
  }
  renderOnNow();
  renderFeatures();
  renderWatch();
  renderEvents();
  window.addEventListener("hashchange", () => { fromHash(); window.scrollTo(0, 0); });
  fromHash();
})();
