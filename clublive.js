// Live club scores: Bundesliga ties in play, from Eleven's /api/club-live (the league's own match data).
// Updates the fixture rows on the Clubs pages (li.cl-m[data-when]) and the cards in the scores strip ([data-cl]).
// It only asks for data while a tie on the page is in its playing window, and stops once every one is finished.
(function () {
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const WINDOW_BEFORE = 10 * 6e4, WINDOW_AFTER = 5 * 36e5;
  const finished = new Set();
  const targets = () => [...document.querySelectorAll(".cl-m[data-when]:not(.done), [data-cl]")].filter((el) => {
    const t = Date.parse(el.dataset.when || el.dataset.cl), n = Date.now();
    return !finished.has(el) && t - WINDOW_BEFORE <= n && n <= t + WINDOW_AFTER;
  });
  // The league writes "TTC OE Clarity-Tel.Syst.Bad Homburg" where Eleven writes "TTC Bad Homburg": every word of ours must be in theirs
  const words = (s) => String(s || "").toLowerCase().normalize("NFKD").replace(/[^a-z0-9 ]+/g, " ").split(/\s+/).filter(Boolean);
  const same = (ours, theirs) => { const t = words(theirs).join(" "); return words(ours).every((w) => t.includes(w)); };
  const find = (ties, when, home) => {
    const at = ties.filter((t) => t.when && Date.parse(t.when) === Date.parse(when));
    return at.find((t) => same(home, t.home)) || null;   // never by time alone: another league may start at the same minute
  };
  const surname = (n) => n.split(" / ").map((x) => x.trim().split(" ").slice(-1)[0]).join(" / ");
  function rubberLine(t) {
    const r = (t.rubbers || []).filter((x) => x.st === "live").pop();
    if (!r) return "";
    const games = r.g ? ` (${r.g.split(",").join(", ")})` : "";
    return `${esc(surname(r.home))} ${r.s[0]}-${r.s[1]} ${esc(surname(r.away))}${esc(games)}`;
  }
  function paintRow(li, t) {
    if (t.st === "due") return;
    const sc = li.querySelector(".cl-sc");
    if (sc) { sc.className = "cl-sc" + (t.st === "live" ? " live" : ""); sc.innerHTML = `${t.score[0]}<i>-</i>${t.score[1]}`; }
    li.classList.toggle("is-live", t.st === "live");
    let note = li.querySelector(".cl-now");
    if (!note) { note = document.createElement("span"); note.className = "cl-meta cl-now"; li.appendChild(note); }
    if (t.st === "live") {
      const line = rubberLine(t);
      note.innerHTML = `<b class="cl-livetag"><span class="live-dot"></span>Live</b>${line ? " " + line : ""}`;
    } else {
      note.remove();
      li.classList.add("done");
      const ts = li.querySelectorAll(".cl-t");
      if (ts.length === 2 && t.score[0] !== t.score[1]) ts[t.score[0] > t.score[1] ? 0 : 1].classList.add("won");
      finished.add(li);
    }
  }
  function paintCard(a, t) {
    if (t.st === "due") return;
    a.hidden = false;
    a.classList.toggle("is-live", t.st === "live");
    const ev = a.querySelector(".ev"), bs = a.querySelectorAll(".row b"), rows = a.querySelectorAll(".row");
    if (ev) ev.innerHTML = t.st === "live" ? '<span class="live-dot"></span>Live' : "Bundesliga";
    if (bs.length === 2) { bs[0].textContent = t.score[0]; bs[1].textContent = t.score[1]; }
    const wh = a.querySelector(".where");
    if (wh) wh.textContent = t.st === "live" ? (rubberLine(t).replace(/&amp;/g, "&") || "Bundesliga") : "Bundesliga, full time";
    if (t.st === "done") {
      if (rows.length === 2 && t.score[0] !== t.score[1]) { rows[0].classList.toggle("won", t.score[0] > t.score[1]); rows[1].classList.toggle("won", t.score[1] > t.score[0]); }
      finished.add(a);
    }
  }
  let last = null;
  function paint(ties) {
    targets().forEach((el) => {
      const t = find(ties, el.dataset.when || el.dataset.cl, el.dataset.home || "");
      if (!t) return;
      if (el.matches("[data-cl]")) paintCard(el, t); else paintRow(el, t);
    });
  }
  async function tick() {
    if (!targets().length || document.hidden) return;
    let d;
    try { d = await fetch("/api/club-live", { cache: "no-store" }).then((r) => r.json()); } catch (e) { return; }
    last = (d && d.ties) || [];
    paint(last);
  }
  // The scores strip is redrawn as WTT scores come in: repaint its club cards from the last reply, or fetch if there is none yet
  const strip = document.getElementById("ticker");
  if (strip) new MutationObserver(() => { if (last) paint(last); else tick(); }).observe(strip, { childList: true });
  const start = () => { tick(); setInterval(tick, 20000); };
  if (document.readyState === "complete") start(); else window.addEventListener("load", () => setTimeout(start, 1200));
})();
