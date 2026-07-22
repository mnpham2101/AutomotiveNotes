#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a static HTML slide deck from a slides markdown file.

Usage:
    python build_slides.py <deck.md> [<deck2.md> ...] [-o OUTDIR]

Markdown conventions (see SLIDE_TEMPLATE.md):
    #   deck title            -> title slide
    ##  section               -> divider slide + nav group
    ###  slide                -> one slide
    > subtitle: / > footer:   -> title-slide subtitle / per-slide footer
    > note: …                 -> speaker note (screen-hidden, printed)
    `[Clause x]` trailing     -> rendered as a small source reference

Colours and fonts follow BTC_phan_hoi_V2X_team.pdf.
Referenced .svg files are copied next to the generated HTML, so the output
directory is self-contained and needs no network access.
"""
import argparse
import base64
import mimetypes
import re
import shutil
import xml.dom.minidom as minidom
from pathlib import Path

import markdown

# --- BTC_phan_hoi_V2X_team.pdf palette --------------------------------------
CSS = """
:root{
  --ink:#263238; --ink-2:#37474f; --muted:#607d8b; --faint:#90a4ae;
  --rule:#b0bec5; --rule-soft:#cfd8dc; --wash:#eceff1; --page:#f7f9fb;
  --navy:#14337a; --blue:#1565c0; --blue-wash:#e3f2fd;
  --accent:#f26f21; --accent-dark:#e65100; --accent-wash:#fff3e0;
  --green:#2e7d32; --green-wash:#e8f5e9; --red:#c62828;
  --font:"DejaVu Sans",Verdana,Geneva,sans-serif;
  --mono:"DejaVu Sans Mono",Consolas,monospace;
}
*{box-sizing:border-box}
html,body{margin:0;padding:0}
body{background:var(--wash);color:var(--ink);font-family:var(--font);
     font-size:16px;line-height:1.5;-webkit-font-smoothing:antialiased}

/* ---------------------------------------------------------------- shell */
.shell{display:grid;grid-template-columns:264px 1fr;min-height:100vh}
nav{background:var(--ink);color:#fff;padding:26px 0 40px;position:sticky;top:0;
    height:100vh;overflow-y:auto}
nav .brand{padding:0 22px 18px;border-bottom:1px solid rgba(255,255,255,.14);margin-bottom:14px}
nav .brand b{display:block;font-size:15px;line-height:1.35}
nav .brand span{display:block;color:var(--faint);font-size:11.5px;margin-top:6px}
nav .grp{color:var(--accent);font-size:10.5px;letter-spacing:.10em;text-transform:uppercase;
         padding:16px 22px 6px;font-weight:700}
nav a{display:block;color:#cfd8dc;text-decoration:none;font-size:13px;
      padding:6px 22px 6px 26px;border-left:3px solid transparent}
nav a:hover{color:#fff;background:rgba(255,255,255,.06)}
nav a.on{color:#fff;border-left-color:var(--accent);background:rgba(242,111,33,.14)}

main{padding:0}
.rail{position:fixed;top:0;left:264px;right:0;height:3px;background:transparent;z-index:20}
.rail i{display:block;height:100%;width:0;background:var(--accent)}

/* ---------------------------------------------------------------- slides */
.slide{min-height:100vh;padding:64px 76px 92px;display:flex;flex-direction:column;
       justify-content:center;background:var(--page);border-bottom:1px solid var(--rule-soft);
       position:relative;scroll-margin-top:0}
.slide-inner{max-width:1080px;width:100%;margin:0 auto}
.slide h2{margin:0 0 30px;font-size:34px;line-height:1.2;color:var(--navy);font-weight:700;
          letter-spacing:-.01em}
.slide h2::after{content:"";display:block;width:64px;height:4px;background:var(--accent);
                 margin-top:16px;border-radius:2px}

.slide ul{margin:0;padding-left:0;list-style:none}
.slide li{position:relative;padding:0 0 0 30px;margin:0 0 14px;font-size:19px;line-height:1.5}
.slide li::before{content:"";position:absolute;left:6px;top:.62em;width:8px;height:8px;
                  background:var(--accent);border-radius:50%}
.slide li strong{color:var(--navy)}
.slide p{font-size:18px}
.slide code{font-family:var(--mono);font-size:.88em;background:var(--blue-wash);
            color:var(--blue);padding:2px 6px;border-radius:3px}

figure{margin:0 0 26px;text-align:center}
figure img{max-width:100%;height:auto;border:1px solid var(--rule-soft);border-radius:4px;
           background:#fff}

table{border-collapse:collapse;width:100%;margin:0 0 22px;font-size:16px;background:#fff}
th{background:var(--ink);color:#fff;text-align:left;padding:11px 14px;font-weight:700;font-size:14px}
td{padding:10px 14px;border-bottom:1px solid var(--rule-soft);vertical-align:top}
tr:nth-child(even) td{background:var(--page)}
td strong{color:var(--accent-dark)}

.ref{margin-top:26px;font-family:var(--mono);font-size:12.5px;color:var(--muted)}
.ref::before{content:"▸ ";color:var(--accent)}
.note{display:none}

.foot{position:absolute;left:76px;right:76px;bottom:26px;display:flex;
      justify-content:space-between;align-items:center;font-size:11.5px;color:var(--faint);
      border-top:1px solid var(--rule-soft);padding-top:10px}
.foot .n{font-family:var(--mono)}

/* ------------------------------------------------------- title & divider */
.slide.title{background:var(--ink);color:#fff;text-align:center}
.slide.title h1{margin:0;font-size:50px;line-height:1.15;color:#fff;font-weight:700;
                letter-spacing:-.02em}
.slide.title .bar{width:96px;height:5px;background:var(--accent);margin:26px auto;border-radius:3px}
.slide.title .sub{font-size:21px;color:var(--rule)}
.slide.title .meta{margin-top:44px;font-size:12.5px;color:var(--faint);font-family:var(--mono)}
.slide.title .foot{display:none}

.slide.divider{background:var(--navy);color:#fff}
.slide.divider .kicker{font-size:12px;letter-spacing:.16em;text-transform:uppercase;
                       color:var(--accent);font-weight:700;margin-bottom:14px}
.slide.divider h2{color:#fff;font-size:42px}
.slide.divider h2::after{background:var(--accent)}
.slide.divider ol{margin:26px 0 0;padding-left:20px;color:var(--rule);font-size:17px}
.slide.divider li{font-size:17px}
.slide.divider li::before{background:var(--rule)}

/* ---------------------------------------------------------------- print */
@media print{
  nav,.rail{display:none}
  .shell{display:block}
  body{background:#fff}
  .slide{min-height:auto;height:19.0cm;page-break-after:always;break-after:page;
         padding:36px 44px 60px;border:0}
  .slide h2{font-size:26px}.slide li{font-size:15px;margin-bottom:9px}
  .slide.title h1{font-size:38px}
  .note{display:block;margin-top:18px;padding:10px 14px;background:var(--wash);
        border-left:3px solid var(--faint);font-size:12px;color:var(--ink-2)}
  .foot{left:44px;right:44px;bottom:16px}
  @page{size:A4 landscape;margin:8mm}
}
@media (max-width:900px){
  .shell{grid-template-columns:1fr}
  nav{position:static;height:auto}
  .rail{left:0}
  .slide{padding:44px 26px 80px;min-height:auto}
  .slide h2{font-size:26px}.slide li{font-size:16px}
  .foot{left:26px;right:26px}
}
"""

JS = """
(function(){
  var slides=[].slice.call(document.querySelectorAll('.slide'));
  var links=[].slice.call(document.querySelectorAll('nav a'));
  var bar=document.querySelector('.rail i');
  function current(){
    var best=0,bd=1e9;
    slides.forEach(function(s,i){var d=Math.abs(s.getBoundingClientRect().top);
      if(d<bd){bd=d;best=i}});
    return best;
  }
  function sync(){
    var i=current();
    links.forEach(function(a){a.classList.toggle('on',a.dataset.i===String(i))});
    if(bar)bar.style.width=(slides.length<2?100:(i/(slides.length-1))*100)+'%';
  }
  addEventListener('scroll',sync,{passive:true});
  addEventListener('resize',sync);
  addEventListener('keydown',function(e){
    if(e.metaKey||e.ctrlKey||e.altKey)return;
    var i=current(),t=null;
    if(e.key==='ArrowDown'||e.key==='ArrowRight'||e.key===' '||e.key==='PageDown')t=i+1;
    if(e.key==='ArrowUp'||e.key==='ArrowLeft'||e.key==='PageUp')t=i-1;
    if(e.key==='Home')t=0;
    if(e.key==='End')t=slides.length-1;
    if(t===null)return;
    e.preventDefault();
    slides[Math.max(0,Math.min(slides.length-1,t))].scrollIntoView({behavior:'smooth'});
  });
  sync();
})();
"""

MD_EXT = ["tables", "sane_lists", "attr_list"]

NOTE_RE = re.compile(r"(?m)^>\s*note:\s*(.+)$")
META_RE = re.compile(r"(?m)^>\s*(subtitle|footer):\s*(.+)$")
REF_RE = re.compile(r"(?m)^`\[(.+?)\]`\s*$")
IMG_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
COMMENT_RE = re.compile(r"<!--.*?-->", re.S)


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def data_uri(path):
    """Read an asset and return a base64 data: URI.

    draw.io exports carry the whole editable mxfile in the svg's `content`
    attribute; it is useless for rendering, so drop it before embedding.
    """
    path = Path(path)
    raw = path.read_bytes()
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    if path.suffix.lower() == ".svg":
        mime = "image/svg+xml"
        try:
            doc = minidom.parseString(raw)
            if doc.documentElement.hasAttribute("content"):
                doc.documentElement.removeAttribute("content")
            raw = doc.documentElement.toxml().encode("utf-8")
        except Exception as e:                       # keep the original on any parse trouble
            print("    (could not strip drawio source from %s: %s)" % (path.name, e))
    return "data:%s;base64,%s" % (mime, base64.b64encode(raw).decode("ascii"))


def parse(md_text):
    """-> (title, subtitle, footer, [ {section, title, body_md, notes[]} ])"""
    md_text = COMMENT_RE.sub("", md_text)
    meta = dict(META_RE.findall(md_text))
    md_text = META_RE.sub("", md_text)

    m = re.search(r"(?m)^#\s+(.+)$", md_text)
    title = m.group(1).strip() if m else "Untitled deck"
    body = md_text[m.end():] if m else md_text

    slides, section = [], None
    # split on H2 / H3 while keeping the delimiter
    parts = re.split(r"(?m)^(##\s+.+|###\s+.+)$", body)
    i = 1
    while i < len(parts):
        head, text = parts[i].strip(), parts[i + 1] if i + 1 < len(parts) else ""
        if head.startswith("### "):
            slides.append(dict(section=section, title=head[4:].strip(), body=text))
        else:
            section = head[3:].strip()
            slides.append(dict(section=section, title=None, body=text, divider=True))
        i += 2
    return title, meta.get("subtitle", ""), meta.get("footer", ""), slides


def render_slide(s, idx, total, footer, deck_title):
    body = s["body"]
    notes = NOTE_RE.findall(body)
    body = NOTE_RE.sub("", body)
    refs = REF_RE.findall(body)
    body = REF_RE.sub("", body)

    html = markdown.markdown(body.strip(), extensions=MD_EXT)
    html = re.sub(r"<p>(<img [^>]+>)</p>", r"<figure>\1</figure>", html)

    cls, inner = "slide", []
    if s.get("divider"):
        cls += " divider"
        inner.append('<div class="kicker">Section</div>')
        inner.append("<h2>%s</h2>" % esc(s["section"]))
        if html.strip():
            inner.append(html)
    else:
        inner.append("<h2>%s</h2>" % esc(s["title"]))
        inner.append(html)
    for r in refs:
        inner.append('<div class="ref">%s</div>' % esc(r))
    for n in notes:
        inner.append('<div class="note"><b>Note — </b>%s</div>' % esc(n))

    foot = ('<div class="foot"><span>%s</span><span class="n">%d / %d</span></div>'
            % (esc(footer or deck_title), idx, total))
    return ('<section class="%s" id="s%d"><div class="slide-inner">%s</div>%s</section>'
            % (cls, idx, "\n".join(inner), foot))


def build(md_path, outdir, inline=True):
    md_path = Path(md_path).resolve()
    text = md_path.read_text(encoding="utf-8")

    # Resolve every referenced image (examples inside HTML comments don't count).
    # inline=True embeds them as data: URIs so the .html is one portable file
    # that opens straight off the filesystem with no sibling assets.
    assets, embedded = {}, 0
    for src in IMG_RE.findall(COMMENT_RE.sub("", text)):
        if src.startswith(("http://", "https://", "data:")) or src in assets:
            continue
        p = (md_path.parent / src).resolve()
        if not p.is_file():
            print("  ! missing image, skipped: %s" % src)
            continue
        if inline:
            assets[src] = data_uri(p)
            embedded += 1
        else:
            outdir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, outdir / p.name)
            assets[src] = p.name
    if assets:
        text = IMG_RE.sub(lambda m: m.group(0).replace(m.group(1), assets.get(m.group(1), m.group(1))),
                          text)

    title, subtitle, footer, slides = parse(text)
    outdir.mkdir(parents=True, exist_ok=True)

    total = len(slides) + 1
    parts = ['<section class="slide title" id="s0"><div class="slide-inner">',
             "<h1>%s</h1>" % esc(title), '<div class="bar"></div>']
    if subtitle:
        parts.append('<div class="sub">%s</div>' % esc(subtitle))
    if footer:
        parts.append('<div class="meta">%s</div>' % esc(footer))
    parts.append("</div></section>")

    nav, cur = [], None
    nav.append('<a href="#s0" data-i="0">Title</a>')
    for i, s in enumerate(slides, 1):
        if s.get("divider"):
            cur = s["section"]
            nav.append('<div class="grp">%s</div>' % esc(cur))
            nav.append('<a href="#s%d" data-i="%d">Overview</a>' % (i, i))
        else:
            nav.append('<a href="#s%d" data-i="%d">%s</a>' % (i, i, esc(s["title"])))
        parts.append(render_slide(s, i, total - 1, footer, title))

    html = """<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%s</title>
<style>%s</style>
</head><body>
<div class="rail"><i></i></div>
<div class="shell">
<nav><div class="brand"><b>%s</b><span>%s</span></div>%s</nav>
<main>%s</main>
</div>
<script>%s</script>
</body></html>""" % (esc(title), CSS, esc(title), esc(subtitle), "\n".join(nav),
                     "\n".join(parts), JS)

    out = outdir / (md_path.stem + ".html")
    out.write_text(html, encoding="utf-8")
    print("  %s  (%d slides, %d image%s %s, %.1f MB)"
          % (out, total, embedded, "" if embedded == 1 else "s",
             "embedded" if inline else "copied", len(html) / 1048576.0))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("markdown", nargs="+")
    ap.add_argument("-o", "--outdir", default=None)
    ap.add_argument("--no-inline", action="store_true",
                    help="copy images beside the html instead of embedding them "
                         "(smaller html, but no longer a single portable file)")
    a = ap.parse_args()
    outdir = Path(a.outdir) if a.outdir else Path(a.markdown[0]).resolve().parent.parent / "slides"
    print("building ->", outdir)
    for m in a.markdown:
        build(m, outdir, inline=not a.no_inline)


if __name__ == "__main__":
    main()
