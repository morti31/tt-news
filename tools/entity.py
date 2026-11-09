"""The shared layout for every "thing" page: players now, then tournaments, leagues, teams and countries.

  header, then a row of tabs (Overview, News, Results ...), then one panel per tab, with an optional sidebar.

Tabs are plain links to #<id>, so the page works without JavaScript (every panel shows, stacked). With
JavaScript one panel shows at a time, the address bar keeps the tab (/players/felix-lebrun.html#news), and a
link to anything inside a panel (#h2h) opens that panel first.
"""
import html

e = html.escape

SCRIPT = """<script>(function(){var tabs=[].slice.call(document.querySelectorAll('.ent-tabs a'));if(!tabs.length)return;
var ids=tabs.map(function(t){return t.getAttribute('href').slice(1);});document.documentElement.classList.add('ent-js');
function panelFor(h){if(ids.indexOf(h)>-1)return h;var el=h&&document.getElementById(h);var p=el&&el.closest('.ent-panel');return p?p.id:null;}
function show(id,scroll){tabs.forEach(function(t){var on=t.getAttribute('href')==='#'+id;t.setAttribute('aria-selected',on);if(on)t.scrollIntoView({block:'nearest',inline:'nearest'});});
ids.forEach(function(i){document.getElementById(i).hidden=i!==id;});if(scroll)document.querySelector('.ent-tabs').scrollIntoView({block:'start'});}
function route(scroll){var h=decodeURIComponent(location.hash.slice(1));var p=panelFor(h)||ids[0];show(p,false);if(h&&ids.indexOf(h)<0){var el=document.getElementById(h);if(el)el.scrollIntoView();}else if(scroll){show(p,true);}}
tabs.forEach(function(t){t.addEventListener('click',function(ev){ev.preventDefault();var id=t.getAttribute('href').slice(1);history.replaceState(null,'','#'+id);show(id,true);});});
document.addEventListener('click',function(ev){var a=ev.target.closest('a[data-tab]');if(!a)return;ev.preventDefault();var id=a.dataset.tab;history.replaceState(null,'','#'+id);show(id,true);});
window.addEventListener('hashchange',function(){route(true);});route(false);})();</script>"""


def tab_link(id_, label):
    """A link inside a panel that switches tab: "All 24 stories"."""
    return f'<a class="ent-more" href="#{id_}" data-tab="{id_}">{e(label)} &rarr;</a>'


def page(crumbs, head, tabs, aside="", cls=""):
    """crumbs: [(url or None, label)]; head: header html; tabs: [(id, label, html)], empty panels left out."""
    tabs = [t for t in tabs if t[2]]
    cr = " / ".join(f'<a href="{u}">{e(x)}</a>' if u else e(x) for u, x in crumbs)
    bar = "".join(f'<a role="tab" href="#{i}" id="tab-{i}" aria-controls="{i}" aria-selected="{"true" if n == 0 else "false"}">{e(lab)}</a>'
                  for n, (i, lab, _) in enumerate(tabs))
    panels = "".join(f'<section class="ent-panel" id="{i}" role="tabpanel" aria-labelledby="tab-{i}"><h2 class="ent-ptitle">{e(lab)}</h2>{body}</section>'
                     for i, lab, body in tabs)
    main = f'<div class="hub-grid"><div class="hub-main">{panels}</div><aside class="article-side">{aside}</aside></div>' if aside else panels
    return f'''<main class="wrap ent-page {cls}">
<nav class="crumbs" aria-label="Breadcrumb">{cr}</nav>
{head}
<nav class="ent-tabs" role="tablist" aria-label="Sections">{bar}</nav>
{main}
</main>
{SCRIPT}'''
