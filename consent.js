/* Cookie consent: Google Tag Manager loads only after the visitor accepts. */
(function () {
  var KEY = "eleven_consent", GTM = "GTM-KHC9R75V";
  var host = location.hostname, shared = /(^|\.)eleventabletennis\.com$/.test(host) ? "; domain=.eleventabletennis.com" : "";
  function get() {
    var m = document.cookie.match(new RegExp("(?:^|; )" + KEY + "=([^;]*)"));
    if (m) return m[1];
    try { return localStorage.getItem(KEY); } catch (e) { return null; }
  }
  function set(v) {
    document.cookie = KEY + "=" + v + "; max-age=15552000; path=/; SameSite=Lax; Secure" + shared;
    try { localStorage.setItem(KEY, v); } catch (e) {}
  }
  function clearGoogle() {
    var gone = /^(_ga|_gid|_gat|_gcl|__gads|__gpi|_gac)/;
    document.cookie.split("; ").forEach(function (c) {
      var n = c.split("=")[0];
      if (gone.test(n)) ["", "; domain=" + host, "; domain=." + host.replace(/^defensive\./, "")].forEach(function (d) {
        document.cookie = n + "=; max-age=0; path=/" + d;
      });
    });
  }
  var loaded = false;
  function load() {
    if (loaded) return; loaded = true;
    (function (w, d, s, l, i) {
      w[l] = w[l] || []; w[l].push({ "gtm.start": new Date().getTime(), event: "gtm.js" });
      var f = d.getElementsByTagName(s)[0], j = d.createElement(s);
      j.async = true; j.src = "https://www.googletagmanager.com/gtm.js?id=" + i; f.parentNode.insertBefore(j, f);
    })(window, document, "script", "dataLayer", GTM);
  }
  var css = document.createElement("style");
  css.textContent = "#cc{position:fixed;left:12px;right:12px;bottom:12px;z-index:99999;max-width:560px;margin:0 auto;background:#17202b;color:#fff;border-radius:12px;padding:16px 18px;box-shadow:0 8px 32px rgba(0,0,0,.35);font:15px/1.45 system-ui,sans-serif}#cc p{margin:0 0 12px}#cc a{color:#fff;text-decoration:underline}#cc .b{display:flex;gap:10px}#cc button{flex:1;font:600 15px system-ui,sans-serif;padding:10px 14px;border-radius:8px;border:2px solid #fff;background:#fff;color:#17202b;cursor:pointer}";
  document.head.appendChild(css);
  function banner() {
    var old = document.getElementById("cc"); if (old) old.remove();
    var b = document.createElement("div"); b.id = "cc"; b.setAttribute("role", "dialog"); b.setAttribute("aria-label", "Cookie choices");
    b.innerHTML = '<p>We never sell your data. If you accept, Google Analytics shows us which pages are read, so we can improve the site. It sets cookies only if you accept. <a href="https://eleventabletennis.com/privacy.html">Privacy and cookies</a></p><div class="b"><button type="button" data-v="no">Reject</button><button type="button" data-v="yes">Accept</button></div>';
    b.addEventListener("click", function (ev) {
      var v = ev.target.getAttribute && ev.target.getAttribute("data-v"); if (!v) return;
      set(v); b.remove();
      if (v === "yes") load(); else clearGoogle();
    });
    document.body.appendChild(b);
  }
  function init() {
    var c = get();
    if (c === "yes") load(); else if (c !== "no") banner();
    document.addEventListener("click", function (ev) {
      var t = ev.target.closest && ev.target.closest("[data-consent-open]");
      if (t) { ev.preventDefault(); banner(); }
    });
  }
  if (document.body) init(); else document.addEventListener("DOMContentLoaded", init);
})();
