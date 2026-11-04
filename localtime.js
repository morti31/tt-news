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
  window.ElevenLocalTime = run;
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", () => run()); else run();
})();
