// Times on the site are built in UK time; this shows them in the reader's own time zone.
// <time data-lt="hm" datetime="...Z"> becomes 13:00, data-lt="dhm" becomes Wed 4 Nov, 13:00.
// <span data-tz-note> becomes "Times are in your local time (Madrid, CET)."
(function () {
  const zone = (() => { try { return Intl.DateTimeFormat().resolvedOptions().timeZone || ""; } catch (e) { return ""; } })();
  const name = (d) => { try { return (new Intl.DateTimeFormat("en-GB", { timeZoneName: "short" }).formatToParts(d).find((p) => p.type === "timeZoneName") || {}).value || ""; } catch (e) { return ""; } };
  const hm = { hour: "2-digit", minute: "2-digit" }, dhm = { weekday: "short", day: "numeric", month: "short", ...hm };
  function run(root) {
    (root || document).querySelectorAll("time[data-lt]").forEach((t) => {
      const d = new Date(t.getAttribute("datetime"));
      if (isNaN(d) || !/^(\d{2}:\d{2}|\w{3} \d+ \w{3}, \d{2}:\d{2})$/.test(t.textContent.trim())) return;   // leave "Live" and "Result" alone
      const o = t.dataset.lt === "dhm" ? dhm : hm;
      t.textContent = d.toLocaleString("en-GB", o).replace(/^(\w{3}),? /, "$1 ");
      t.title = `${d.toLocaleString("en-GB", { ...dhm, timeZone: "Europe/London" })} UK time`;
    });
    document.querySelectorAll("[data-tz-note]").forEach((n) => {
      if (!zone) return;
      const city = zone.split("/").pop().replace(/_/g, " ");
      n.textContent = `Times are in your local time (${city}${name(new Date()) ? ", " + name(new Date()) : ""}).`;
    });
  }
  // Story times read "1 hr ago" like BBC Sport; the full date stays in the tooltip. The story page's own byline keeps the full date.
  const MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  function ago(d, now) {
    const s = Math.floor((now - d) / 1000);
    if (s < 0) return "";
    if (s < 60) return "Just now";
    const m = Math.floor(s / 60);
    if (m < 60) return m + (m === 1 ? " min ago" : " mins ago");
    const h = Math.floor(m / 60);
    if (h < 24) return h + (h === 1 ? " hr ago" : " hrs ago");
    const days = Math.floor(h / 24);
    if (days < 7) return days + (days === 1 ? " day ago" : " days ago");
    const u = new Date(d.toLocaleString("en-US", { timeZone: "Europe/London" }));
    return u.getDate() + " " + MON[u.getMonth()] + (u.getFullYear() === new Date().getFullYear() ? "" : " " + u.getFullYear());
  }
  window.ElevenAgo = ago;
  function relative() {
    const now = Date.now();
    document.querySelectorAll('time[datetime*="T"]:not([data-lt])').forEach((t) => {
      if (t.closest(".article-byline")) return;
      const d = new Date(t.getAttribute("datetime"));
      if (isNaN(d)) return;
      if (t.dataset.full === undefined) {
        const txt = t.textContent.trim();
        if (/^Updated /.test(txt)) return;
        t.dataset.full = txt;
        const m = txt.match(/^(By [^,]+), /);
        t.dataset.by = m ? m[1] : "";
      }
      const a = ago(d, now);
      if (!a) return;
      const text = (t.dataset.by ? t.dataset.by + ", " : "") + a;
      if (t.textContent !== text) t.textContent = text;
      t.title = d.toLocaleString("en-GB", { ...dhm, year: "numeric", timeZone: "Europe/London" }) + " UK time";
    });
  }
  window.ElevenRelative = relative;
  function start() {
    run(); relative();
    setInterval(relative, 60000);
    let q = 0;
    new MutationObserver(() => { clearTimeout(q); q = setTimeout(relative, 50); }).observe(document.body, { childList: true, subtree: true });
  }
  window.ElevenLocalTime = (r) => { run(r); relative(); };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start); else start();
})();
