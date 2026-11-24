// Site search for Eleven and The Chop (tools/build_search.py).
// 1. The header search button opens a box with instant suggestions from /search-index.json
//    (players, tournaments, leagues, guides, defenders, recent stories). Enter goes to the results page.
// 2. /search.html shows full-text results from Pagefind (/pagefind/), filtered by section.
// Nothing is logged or stored: queries stay in the browser.
(() => {
  const CHOP = "defensive.eleventabletennis.com", CHOP_URL = "https://" + CHOP, ELEVEN = "https://eleventabletennis.com";
  const onChop = location.hostname === CHOP;
  const KIND = { p: "Player", e: "Tournament", l: "Club game", g: "Guide", c: "The Chop", s: "Story" };
  const ORDER = onChop ? { c: 0, p: 1, e: 2, l: 3, g: 4, s: 5 } : { p: 0, e: 1, c: 2, l: 3, g: 4, s: 5 };
  const SECTIONS = ["News", "Players", "Tournaments", "Club game", "Analysis", "Guide", "The Chop"];
  const PER_PAGE = 15;
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
  const fold = (s) => String(s).normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();

  // Addresses: Eleven's are stored as paths, The Chop's in full. On The Chop's host, Eleven's need the full address.
  function link(u) {
    u = u.replace(/\/index\.html$/, "/").replace(/\.html(?=$|[?#])/, "");   // clean addresses, as the sites publish them
    if (u.startsWith(CHOP_URL)) return onChop ? u.slice(CHOP_URL.length) || "/" : u;
    if (u.startsWith("/defensive/")) return onChop ? u.slice(10) : CHOP_URL + u.slice(10);   // Pagefind's paths for Chop pages
    return onChop && u.startsWith("/") ? ELEVEN + u : u;
  }

  // ---- Suggestions
  let index = null, loading = null;
  function load() {
    if (!loading) loading = fetch("/search-index.json").then((r) => r.json())
      .then((d) => { index = d.map((x) => { const f = fold(x[0]); return { t: x[0], u: x[1], k: x[2], d: x[3], r: x[4] || 0, f, w: f.split(" ") }; }); })
      .catch(() => { index = []; });
    return loading;
  }
  function suggest(q, max) {
    const qf = fold(q);
    if (!index || !qf) return [];
    const qw = qf.split(" ");
    const hits = [];
    for (const x of index) {
      let s = 0;
      if (x.f.startsWith(qf)) s = 3;
      else if (qw.every((w) => x.w.some((t) => t.startsWith(w)))) s = 2;
      else if (qf.length >= 4 && x.f.includes(qf)) s = 1;
      if (s) hits.push([s, x]);
    }
    hits.sort((a, b) => b[0] - a[0] || ORDER[a[1].k] - ORDER[b[1].k] || b[1].r - a[1].r || a[1].t.localeCompare(b[1].t));
    const out = [];
    let stories = 0;
    for (const [, x] of hits) {
      if (x.k === "s" && ++stories > 3) continue;   // a few stories; the results page has the rest
      out.push(x);
      if (out.length >= max) break;
    }
    return out;
  }

  // A search box with a suggestion list underneath (the header box and the results page box)
  function attach(input, list) {
    let items = [], active = -1;
    const form = input.form;
    input.setAttribute("role", "combobox");
    input.setAttribute("aria-autocomplete", "list");
    input.setAttribute("aria-controls", list.id);
    input.setAttribute("aria-expanded", "false");
    list.setAttribute("role", "listbox");
    function render() {
      const q = input.value.trim();
      items = q ? suggest(q, 8) : [];
      active = -1;
      list.innerHTML = items.map((x, i) => `<li role="option" id="${list.id}-${i}" aria-selected="false"><a href="${esc(link(x.u))}"><b>${esc(x.t)}</b>` +
        `<span>${esc(KIND[x.k])}${x.d ? " · " + esc(x.d) : ""}</span></a></li>`).join("") +
        (q ? `<li class="sx-all" role="option" id="${list.id}-all" aria-selected="false"><a href="${esc(form.action)}?q=${encodeURIComponent(q)}">See all results for “${esc(q)}”</a></li>` : "");
      list.hidden = !q;
      input.setAttribute("aria-expanded", q ? "true" : "false");
    }
    function move(d) {
      const opts = list.querySelectorAll('[role="option"]');
      if (!opts.length) return;
      if (active >= 0) opts[active].setAttribute("aria-selected", "false");
      active += d;   // -1 is back in the box
      if (active >= opts.length) active = -1;
      else if (active < -1) active = opts.length - 1;
      if (active >= 0) { opts[active].setAttribute("aria-selected", "true"); input.setAttribute("aria-activedescendant", opts[active].id); opts[active].scrollIntoView({ block: "nearest" }); }
      else input.removeAttribute("aria-activedescendant");
    }
    input.addEventListener("focus", () => load().then(render), { once: true });
    input.addEventListener("input", () => (index ? render() : load().then(render)));
    input.addEventListener("keydown", (ev) => {
      if (ev.key === "ArrowDown") { ev.preventDefault(); move(1); }
      else if (ev.key === "ArrowUp") { ev.preventDefault(); move(-1); }
      else if (ev.key === "Enter" && active >= 0) {
        const a = list.querySelectorAll('[role="option"]')[active].querySelector("a");
        if (a) { ev.preventDefault(); location.href = a.href; }
      }
    });
    form.addEventListener("submit", (ev) => { if (!input.value.trim()) ev.preventDefault(); });
    return render;
  }

  // ---- Header: the search button opens a box under the masthead
  function openBox(btn) {
    let box = document.getElementById("sx-pop");
    if (!box) {
      const header = btn.closest("header");
      box = document.createElement("div");
      box.id = "sx-pop";
      box.className = "sx-pop";
      box.innerHTML = `<div class="sx-pop-in"><form action="/search" method="get" role="search">
<label class="sx-visually-hidden" for="sx-pop-q">Search</label>
<input id="sx-pop-q" name="q" type="search" placeholder="${onChop ? "Search defenders, players, stories..." : "Search players, events, stories..."}" autocomplete="off" enterkeyhint="search">
<button type="button" class="sx-close" aria-label="Close search">Close</button></form>
<ul class="sx-sugg" id="sx-pop-list" hidden></ul></div>`;
      header.after(box);
      attach(box.querySelector("input"), box.querySelector("ul"));
      box.querySelector(".sx-close").addEventListener("click", () => closeBox(btn));
      box.addEventListener("keydown", (ev) => { if (ev.key === "Escape") closeBox(btn); });
    }
    box.hidden = false;
    btn.setAttribute("aria-expanded", "true");
    load();
    box.querySelector("input").focus();
  }
  function closeBox(btn) {
    const box = document.getElementById("sx-pop");
    if (box) box.hidden = true;
    btn.setAttribute("aria-expanded", "false");
    btn.focus();
  }
  const btn = document.querySelector("[data-search-open]");
  if (btn && !document.getElementById("search-page")) {
    btn.setAttribute("aria-expanded", "false");
    btn.addEventListener("click", (ev) => {
      ev.preventDefault();
      const box = document.getElementById("sx-pop");
      if (box && !box.hidden) closeBox(btn); else openBox(btn);
    });
    document.addEventListener("keydown", (ev) => {   // "/" opens search, as on most sites
      if (ev.key === "/" && !ev.ctrlKey && !ev.metaKey && !/^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement.tagName) && !document.activeElement.isContentEditable) {
        ev.preventDefault();
        openBox(btn);
      }
    });
  }

  // ---- Results page
  const page = document.getElementById("search-page");
  if (!page) return;
  const input = document.getElementById("sx-q");
  const quick = document.getElementById("sx-quick"), filters = document.getElementById("sx-filters");
  const count = document.getElementById("sx-count"), list = document.getElementById("sx-results"), more = document.getElementById("sx-more");
  const sugg = document.createElement("ul");
  sugg.className = "sx-sugg";
  sugg.id = "sx-page-list";
  sugg.hidden = true;
  input.form.after(sugg);
  attach(input, sugg);
  if (btn) btn.addEventListener("click", (ev) => { ev.preventDefault(); input.focus(); });

  const params = new URLSearchParams(location.search);
  const q = (params.get("q") || "").trim();
  let section = params.get("section") || "";
  input.value = q;
  if (!q) { input.focus(); return; }
  document.title = `${q} | Search | ${onChop ? "The Chop" : "Eleven"}`;

  // Quick links: the players, tournaments, leagues and defenders that match by name
  load().then(() => {
    const top = suggest(q, 12).filter((x) => x.k !== "s").slice(0, 6);
    quick.innerHTML = top.length ? `<ul class="sx-quick">${top.map((x) => `<li><a href="${esc(link(x.u))}"><b>${esc(x.t)}</b><span>${esc(KIND[x.k])}${x.d ? " · " + esc(x.d) : ""}</span></a></li>`).join("")}</ul>` : "";
  });

  let pf, all, current, shown = 0;
  async function show(n) {
    const slice = current.results.slice(shown, shown + n);
    const data = await Promise.all(slice.map((r) => r.data()));
    list.insertAdjacentHTML("beforeend", data.map((d) => {
      const sec = (d.filters && d.filters.section && d.filters.section[0]) || "";
      const title = (d.meta && d.meta.title || "").replace(/\s*\|\s*(Eleven|The Chop).*$/, "");
      return `<li><a href="${esc(link(d.url))}"><span class="sx-sec">${esc(sec)}${d.meta && d.meta.date ? " · " + esc(d.meta.date) : ""}</span>` +
        `<h2>${esc(title)}</h2><p>${d.excerpt}</p></a></li>`;
    }).join(""));
    shown += slice.length;
    more.hidden = shown >= current.results.length;
  }
  function chips() {
    const counts = (all.filters && all.filters.section) || {};
    const opts = [["", "All", all.results.length]].concat(SECTIONS.filter((s) => counts[s]).map((s) => [s, s, counts[s]]));
    filters.innerHTML = opts.length > 2 ? opts.map(([v, lab, n]) =>
      `<button type="button" data-v="${esc(v)}" aria-pressed="${v === section}">${esc(lab)} <span>${n}</span></button>`).join("") : "";
  }
  async function run() {
    current = section ? await pf.search(q, { filters: { section } }) : all;
    list.innerHTML = "";
    shown = 0;
    const n = current.results.length;
    count.textContent = n ? `${n} result${n === 1 ? "" : "s"} for “${q}”${section ? " in " + section : ""}` : `Nothing found for “${q}”${section ? " in " + section : ""}. Try a shorter search, or check the spelling.`;
    chips();
    await show(PER_PAGE);
  }
  filters.addEventListener("click", (ev) => {
    const b = ev.target.closest("button");
    if (!b) return;
    section = b.dataset.v;
    const u = new URL(location.href);
    if (section) u.searchParams.set("section", section); else u.searchParams.delete("section");
    history.replaceState(null, "", u);
    run();
  });
  more.addEventListener("click", () => show(PER_PAGE));
  (async () => {
    count.textContent = "Searching…";
    try {
      pf = await import("/pagefind/pagefind.js");
      await pf.options({ excerptLength: 26 });
      await pf.filters();   // loads the filter data, so results carry per-section counts
      all = await pf.search(q);
    } catch (err) {
      count.textContent = "Search isn't available right now. Please try again in a moment.";
      return;
    }
    if (section && !((all.filters && all.filters.section) || {})[section]) section = "";
    run();
  })();
})();
