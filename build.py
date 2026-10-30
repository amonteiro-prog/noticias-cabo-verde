#!/usr/bin/env python3
"""Gera o site estático "Notícias de Cabo Verde" a partir de data/edicoes/*.json.

Uso:  python3 build.py            (escreve em ./docs, servido pelo GitHub Pages)

Cada ficheiro data/edicoes/AAAA-MM-DD.json tem a forma:
  {"data": "AAAA-MM-DD", "atualizadoEm": "ISO UTC",
   "itens": [{"categoria","titulo","resumo","fonte","url"}, ...]}
"""
import html, json, re, shutil, unicodedata
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "edicoes"
OUT = ROOT / "docs"

BASE = "https://noticias.explorecaboverde.com"
DOMAIN = "noticias.explorecaboverde.com"
SITE_NAME = "Notícias de Cabo Verde"
PUBLISHER = "Explore Cabo Verde"
PUBLISHER_URL = "https://www.explorecaboverde.com"

MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro"]
DIAS = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira",
        "sexta-feira", "sábado", "domingo"]

e = lambda s: html.escape(str(s or ""), quote=True)


def safe_url(u):
    return u if isinstance(u, str) and re.match(r"^https?://", u) else ""


def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "outros"


def d_of(iso):
    return date.fromisoformat(iso)


def data_longa(iso):
    d = d_of(iso)
    return f"{DIAS[d.weekday()]}, {d.day} de {MESES[d.month - 1]} de {d.year}"


def data_curta(iso):
    d = d_of(iso)
    return f"{d.day} de {MESES[d.month - 1]} de {d.year}"


def day_path(iso):
    y, m, dd = iso.split("-")
    return f"/{y}/{m}/{dd}/"


def load():
    eds = []
    for f in sorted(DATA.glob("*.json")):
        try:
            ed = json.loads(f.read_text(encoding="utf-8"))
            d_of(ed["data"])
            ed["itens"] = [i for i in ed.get("itens", []) if i.get("titulo")]
            if ed["itens"]:
                eds.append(ed)
        except Exception as ex:  # um ficheiro estragado não deve parar o site
            print(f"aviso: ignorei {f.name}: {ex}")
    eds.sort(key=lambda x: x["data"], reverse=True)
    return eds


CSS = """
:root{--bg:#ffffff;--surface:#f6f7fa;--fg:#111111;--muted:#5d6475;--line:#e3e6ee;
--blue:#1d3f9a;--red:#c8202f;--star:#e6b400;
--f-head:"Manrope",system-ui,-apple-system,"Segoe UI",sans-serif;
--f-body:"Literata",Georgia,"Times New Roman",serif;color-scheme:light}
@media (prefers-color-scheme:dark){:root{--bg:#0c1222;--surface:#131b30;--fg:#eceff6;--muted:#a0a9bf;
--line:#263150;--blue:#86a3f2;--red:#ff7179;--star:#f2c94c;color-scheme:dark}}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--fg);font:17px/1.6 var(--f-body)}
a{color:var(--blue)}
a:focus-visible,button:focus-visible{outline:2px solid var(--star);outline-offset:2px}
.flag{height:8px;background:linear-gradient(to bottom,var(--blue) 0 40%,var(--bg) 40% 50%,var(--red) 50% 60%,var(--bg) 60% 70%,var(--blue) 70%)}
.wrap{max-width:1080px;margin:0 auto;padding:0 max(16px,env(safe-area-inset-right)) 0 max(16px,env(safe-area-inset-left))}
.top{display:flex;flex-wrap:wrap;gap:8px 20px;align-items:center;justify-content:space-between;padding-block:14px;
font:600 .9rem/1.2 var(--f-head);border-bottom:1px solid var(--line)}
.top a{text-decoration:none;color:var(--fg)}
.top nav{display:flex;flex-wrap:wrap;gap:16px}
.top nav a{color:var(--muted)}.top nav a:hover{color:var(--fg)}
.brand{font-weight:800;letter-spacing:-.01em}
.brand span{color:var(--star)}
header.hd{padding-block:28px 18px;border-bottom:2px solid var(--fg)}
.eyebrow{font:700 .75rem/1 var(--f-head);text-transform:uppercase;letter-spacing:.12em;color:var(--red)}
h1{font:800 clamp(1.9rem,5vw,3rem)/1.05 var(--f-head);letter-spacing:-.02em;margin:.35em 0 .25em;text-wrap:balance}
.sub{color:var(--muted);font-size:.95rem;margin:0}
.lead{padding-block:28px;border-bottom:1px solid var(--line);display:grid;gap:10px}
.lead h2{font:800 clamp(1.5rem,3.6vw,2.2rem)/1.12 var(--f-head);letter-spacing:-.015em;margin:0;text-wrap:balance}
.lead p{font-size:1.1rem;max-width:65ch;margin:0}
.cat{font:700 .72rem/1 var(--f-head);text-transform:uppercase;letter-spacing:.1em;color:var(--red)}
.src{font:600 .8rem/1.3 var(--f-head);color:var(--muted)}
.src a{text-decoration:none}.src a:hover{text-decoration:underline}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:0 32px}
.item{display:grid;gap:6px;align-content:start;padding-block:20px;border-bottom:1px solid var(--line);min-width:0}
.item h3{font:700 1.12rem/1.25 var(--f-head);margin:0;text-wrap:balance}
.item p{margin:0;font-size:.98rem}
section.more{padding-block:32px}
section.more h2{font:800 1.2rem/1.2 var(--f-head);margin:0 0 12px}
.days{list-style:none;margin:0;padding:0;display:flex;flex-wrap:wrap;gap:8px}
.days a{display:inline-block;font:600 .85rem/1 var(--f-head);text-decoration:none;color:var(--fg);
border:1px solid var(--line);border-radius:999px;padding:8px 14px;background:var(--surface)}
.days a:hover{border-color:var(--blue)}
.arch{display:grid;gap:28px;padding-block:24px}
.arch h2{font:800 1.15rem/1.2 var(--f-head);margin:0 0 8px;text-transform:capitalize}
.arch ul{margin:0;padding-left:1.1em;display:grid;gap:6px}
.pager{display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap;padding-block:24px;font:600 .9rem/1.3 var(--f-head)}
footer{border-top:1px solid var(--line);margin-top:24px;padding-block:24px 40px;color:var(--muted);font:500 .82rem/1.6 var(--f-head)}
footer p{margin:0 0 6px;max-width:75ch}
"""

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Manrope:wght@500;600;700;800'
         '&family=Literata:opsz,wght@7..72,400;7..72,600&display=swap">')


def page(*, title, desc, path, body, jsonld=None, og_type="website", modified=None):
    url = BASE + path
    ld = ""
    if jsonld:
        ld = '<script type="application/ld+json">' + json.dumps(jsonld, ensure_ascii=False).replace("</", "<\\/") + "</script>"
    mod = f'<meta property="article:modified_time" content="{e(modified)}">' if modified else ""
    return f"""<!doctype html>
<html lang="pt">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{e(url)}">
<meta name="robots" content="index,follow,max-snippet:-1">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{e(SITE_NAME)}">
<meta property="og:locale" content="pt_PT">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{e(url)}">
<meta name="twitter:card" content="summary">
{mod}
<link rel="alternate" type="application/rss+xml" title="{e(SITE_NAME)}" href="{BASE}/feed.xml">
{FONTS}
<style>{CSS}</style>
{ld}
</head>
<body>
<div class="flag" aria-hidden="true"></div>
<div class="wrap">
<div class="top"><a class="brand" href="/">Notícias de Cabo Verde <span aria-hidden="true">★</span></a>
<nav aria-label="Principal"><a href="/">Hoje</a><a href="/arquivo/">Arquivo</a></nav></div>
{body}
<footer>
<p>As principais notícias sobre Cabo Verde, resumidas todas as manhãs a partir da imprensa cabo-verdiana e internacional. Cada resumo liga ao artigo original, onde pode ler a notícia completa.</p>
<p>Um projeto <a href="{PUBLISHER_URL}">{e(PUBLISHER)}</a>. <a href="/feed.xml">Feed RSS</a></p>
</footer>
</div>
</body>
</html>
"""


def src_html(it):
    u = safe_url(it.get("url"))
    f = e(it.get("fonte") or "Fonte")
    return f'<div class="src">{"<a href=" + chr(34) + e(u) + chr(34) + " rel=" + chr(34) + "noopener" + chr(34) + ">" + f + " ↗</a>" if u else f}</div>'


def edition_body(ed, *, is_home, newer=None, older=None, recent=()):
    itens = ed["itens"]
    lead, rest = itens[0], itens[1:]
    upd = ""
    try:
        t = datetime.fromisoformat(ed["atualizadoEm"].replace("Z", "+00:00"))
        cv = t.astimezone(timezone.utc).timestamp() - 3600
        upd = " · Atualizado às " + datetime.fromtimestamp(cv, timezone.utc).strftime("%H:%M") + " (hora de Cabo Verde)"
    except Exception:
        pass
    eyebrow = "Edição de hoje" if is_home else "Edição diária"
    h1 = f"Notícias de Cabo Verde de {data_curta(ed['data'])}"
    out = [f'<header class="hd"><div class="eyebrow">{eyebrow}</div><h1>{e(h1)}</h1>'
           f'<p class="sub">{e(data_longa(ed["data"]).capitalize())} · {len(itens)} notícias{e(upd)}</p></header>']
    out.append(f'<main><article class="lead"><span class="cat">{e(lead.get("categoria"))}</span>'
               f'<h2>{e(lead["titulo"])}</h2><p>{e(lead.get("resumo"))}</p>{src_html(lead)}</article>')
    out.append('<section class="grid" aria-label="Mais notícias">')
    for it in rest:
        out.append(f'<article class="item"><span class="cat">{e(it.get("categoria"))}</span>'
                   f'<h3>{e(it["titulo"])}</h3><p>{e(it.get("resumo"))}</p>{src_html(it)}</article>')
    out.append("</section></main>")
    if is_home and recent:
        out.append('<section class="more"><h2>Edições anteriores</h2><ul class="days">')
        for r in recent:
            out.append(f'<li><a href="{day_path(r["data"])}">{e(data_curta(r["data"]))}</a></li>')
        out.append('<li><a href="/arquivo/">Ver arquivo completo</a></li></ul></section>')
    if not is_home:
        a = f'<a href="{day_path(older["data"])}">← {e(data_curta(older["data"]))}</a>' if older else "<span></span>"
        b = f'<a href="{day_path(newer["data"])}">{e(data_curta(newer["data"]))} →</a>' if newer else '<a href="/">Edição de hoje →</a>'
        out.append(f'<nav class="pager" aria-label="Outras edições">{a}{b}</nav>')
    return "\n".join(out)


def description(ed):
    heads = [i["titulo"] for i in ed["itens"][:3]]
    d = f"Notícias de Cabo Verde de {data_curta(ed['data'])}: " + "; ".join(heads) + "."
    return d if len(d) <= 300 else d[:297].rsplit(" ", 1)[0] + "…"


def jsonld_edition(ed, path):
    return {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": f"Notícias de Cabo Verde de {data_curta(ed['data'])}",
        "url": BASE + path,
        "inLanguage": "pt",
        "datePublished": ed["data"],
        "dateModified": ed.get("atualizadoEm", ed["data"]),
        "about": {"@type": "Country", "name": "Cabo Verde"},
        "publisher": {"@type": "Organization", "name": PUBLISHER, "url": PUBLISHER_URL},
        "mainEntity": {
            "@type": "ItemList",
            "itemListElement": [
                {"@type": "ListItem", "position": n + 1, "name": it["titulo"],
                 **({"url": safe_url(it.get("url"))} if safe_url(it.get("url")) else {})}
                for n, it in enumerate(ed["itens"])
            ],
        },
    }


def write(path, text):
    p = OUT / path.strip("/")
    if path.endswith("/"):
        p = p / "index.html"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def build():
    eds = load()
    if not eds:
        raise SystemExit("Sem edições em data/edicoes")
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()

    latest = eds[0]
    write("/", page(
        title=f"Notícias de Cabo Verde hoje, {data_curta(latest['data'])} | {SITE_NAME}",
        desc=description(latest), path="/", modified=latest.get("atualizadoEm"),
        jsonld=jsonld_edition(latest, "/"),
        body=edition_body(latest, is_home=True, recent=eds[1:8])))

    for n, ed in enumerate(eds):
        p = day_path(ed["data"])
        write(p, page(
            title=f"Notícias de Cabo Verde, {data_curta(ed['data'])} | {SITE_NAME}",
            desc=description(ed), path=p, og_type="article", modified=ed.get("atualizadoEm"),
            jsonld=jsonld_edition(ed, p),
            body=edition_body(ed, is_home=False,
                              newer=eds[n - 1] if n > 0 else None,
                              older=eds[n + 1] if n + 1 < len(eds) else None)))

    # Arquivo por mês
    meses = {}
    for ed in eds:
        meses.setdefault(ed["data"][:7], []).append(ed)
    arch = ['<header class="hd"><div class="eyebrow">Arquivo</div><h1>Todas as edições</h1>'
            f'<p class="sub">{len(eds)} edições diárias de notícias de Cabo Verde.</p></header><main class="arch">']
    for ym, lst in meses.items():
        y, m = ym.split("-")
        arch.append(f'<section><h2>{MESES[int(m) - 1]} de {y}</h2><ul>')
        for ed in lst:
            arch.append(f'<li><a href="{day_path(ed["data"])}">{e(data_longa(ed["data"]).capitalize())}</a>'
                        f' · {e(ed["itens"][0]["titulo"])}</li>')
        arch.append("</ul></section>")
    arch.append("</main>")
    write("/arquivo/", page(title=f"Arquivo de notícias | {SITE_NAME}",
                            desc="Arquivo das edições diárias com as principais notícias de Cabo Verde.",
                            path="/arquivo/", body="\n".join(arch)))

    write("/404.html", page(title=f"Página não encontrada | {SITE_NAME}", desc="Página não encontrada.",
                            path="/404.html",
                            body='<header class="hd"><h1>Página não encontrada</h1>'
                                 '<p class="sub"><a href="/">Ver as notícias de hoje</a></p></header>'))

    # sitemap, RSS, robots, CNAME
    urls = [(BASE + "/", latest.get("atualizadoEm", latest["data"]))] + \
           [(BASE + day_path(ed["data"]), ed.get("atualizadoEm", ed["data"])) for ed in eds] + \
           [(BASE + "/arquivo/", latest.get("atualizadoEm", latest["data"]))]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u, lm in urls:
        sm.append(f"<url><loc>{e(u)}</loc><lastmod>{e(lm)}</lastmod></url>")
    sm.append("</urlset>")
    (OUT / "sitemap.xml").write_text("\n".join(sm), encoding="utf-8")

    def rfc822(iso):
        try:
            t = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        except Exception:
            t = datetime.fromisoformat(iso[:10] + "T08:00:00+00:00")
        return t.strftime("%a, %d %b %Y %H:%M:%S +0000")

    rss = ['<?xml version="1.0" encoding="UTF-8"?>', '<rss version="2.0"><channel>',
           f"<title>{e(SITE_NAME)}</title><link>{BASE}/</link>",
           "<description>As principais notícias de Cabo Verde, todas as manhãs.</description><language>pt</language>"]
    for ed in eds[:20]:
        link = BASE + day_path(ed["data"])
        summary = " · ".join(i["titulo"] for i in ed["itens"][:5])
        rss.append(f"<item><title>{e('Notícias de Cabo Verde, ' + data_curta(ed['data']))}</title>"
                   f"<link>{link}</link><guid>{link}</guid>"
                   f"<pubDate>{rfc822(ed.get('atualizadoEm', ed['data']))}</pubDate>"
                   f"<description>{e(summary)}</description></item>")
    rss.append("</channel></rss>")
    (OUT / "feed.xml").write_text("\n".join(rss), encoding="utf-8")

    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n", encoding="utf-8")
    (OUT / "CNAME").write_text(DOMAIN + "\n", encoding="utf-8")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    print(f"OK: {len(eds)} edições → {OUT}")


if __name__ == "__main__":
    build()
