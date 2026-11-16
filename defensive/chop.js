// The Chop: tabs on the defenders page, filters on the reading page. Nothing else needs script.
(function () {
  document.querySelectorAll(".ch-tabs[role=tablist]").forEach((bar) => {
    const tabs = [...bar.querySelectorAll("[role=tab]")];
    tabs.forEach((t) => t.addEventListener("click", () => {
      tabs.forEach((x) => x.setAttribute("aria-selected", String(x === t)));
      document.querySelectorAll(".ch-panel").forEach((p) => { p.hidden = p.dataset.p !== t.dataset.t; });
    }));
  });
  const f = document.querySelector(".ch-filter");
  if (f) f.addEventListener("click", (ev) => {
    const b = ev.target.closest("button");
    if (!b) return;
    f.querySelectorAll("button").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
    document.querySelectorAll(".ch-links > li").forEach((li) => { li.hidden = b.dataset.k !== "all" && li.dataset.k !== b.dataset.k; });
  });
})();
// Style tags open a short definition with its sources
(function () {
  const dlg = document.getElementById("ch-def");
  if (!dlg) return;
  let data = {};
  try { data = JSON.parse(document.getElementById("ch-def-data").textContent); } catch (e) {}
  document.addEventListener("click", (ev) => {
    const b = ev.target.closest("button.ch-style");
    if (!b) return;
    const d = data[b.dataset.style];
    if (!d) return;
    dlg.className = "ch-dialog ch-dialog-" + b.dataset.style;
    dlg.querySelector("#ch-def-h").textContent = d.label;
    dlg.querySelector(".ch-def-about").textContent = d.about;
    if (dlg.showModal) dlg.showModal(); else dlg.setAttribute("open", "");
  });
  dlg.addEventListener("click", (ev) => { if (ev.target === dlg) dlg.close(); });   // click outside closes
})();
