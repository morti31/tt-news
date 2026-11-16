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
