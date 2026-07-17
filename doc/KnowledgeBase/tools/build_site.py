#!/usr/bin/env python3
"""Static site generator for the Automotive Tech Lead Knowledge Base.

Converts every markdown file under md/*.md into a small HTML site under site/:
  - site/<slug>/index.html       full document (all H2 sections, anchored)
  - site/<slug>/<section>.html   one page per H2 section
  - site/index.html              home page (mirrors the 0.0 document)
  - site/diagrams/*.svg          copied PlantUML renders
  - site/images/*                copied screenshots/raster images (md/images/)
  - site/assets/style.css        shared stylesheet

Every page gets a header/footer with Home / back-to-top / back-to-topic links
plus a sidebar listing every topic, so any page is reachable from any other.
"""
import re
import shutil
from pathlib import Path

import markdown
from pygments.formatters import HtmlFormatter

ROOT = Path(__file__).resolve().parent.parent
MD_DIR = ROOT / "md"
DIAGRAMS_DIR = MD_DIR / "diagrams"
IMAGES_DIR = MD_DIR / "images"
SITE_DIR = ROOT / "site"

SITE_TITLE = "Automotive Tech Lead Knowledge Base"
HOME_SLUG = "0.0"

MD_EXTENSIONS = ["tables", "sane_lists", "toc", "pymdownx.tasklist", "pymdownx.superfences", "pymdownx.highlight"]
MD_EXTENSION_CONFIGS = {
    "pymdownx.tasklist": {"custom_checkbox": False, "clickable_checkbox": True},
    # Unknown languages (e.g. bitbake) fall back to plain text rather than erroring.
    "pymdownx.highlight": {"guess_lang": False},
}

# Pygments theme for fenced code blocks; one-dark's background matches --code-bg.
PYGMENTS_STYLE = "one-dark"

MD_LINK_RE = re.compile(r"\]\((\d+\.\d+)-[^)]+\.md\)")
IMG_LINK_RE = re.compile(r"\]\((diagrams|images)/([^)]+)\)")
H1_RE = re.compile(r"(?m)^# (.+)$")
H2_SPLIT_RE = re.compile(r"(?m)^## (.+)$")


def slugify(text: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower())
    return s.strip("-")


def rewrite_links(text: str) -> str:
    text = MD_LINK_RE.sub(r"](/\1/index.html)", text)
    text = IMG_LINK_RE.sub(r"](/\1/\2)", text)
    return text


def render_md(text: str) -> str:
    return markdown.markdown(text, extensions=MD_EXTENSIONS, extension_configs=MD_EXTENSION_CONFIGS)


class Doc:
    def __init__(self, path: Path):
        raw = rewrite_links(path.read_text(encoding="utf-8"))
        title_match = H1_RE.search(raw)
        self.title = title_match.group(1).strip() if title_match else path.stem
        body = raw[title_match.end():] if title_match else raw

        parts = H2_SPLIT_RE.split(body)
        self.preamble_html = render_md(parts[0].strip()) if parts[0].strip() else ""

        self.sections = []  # list of (heading, slug, html)
        for i in range(1, len(parts), 2):
            heading = parts[i].strip()
            section_body = parts[i + 1] if i + 1 < len(parts) else ""
            self.sections.append((heading, slugify(heading), render_md(section_body.strip())))

        self.slug = path.stem.split("-", 1)[0]
        self.filename = path.name


def nav_sidebar(docs, current_slug: str) -> str:
    items = []
    for d in docs:
        href = "/index.html" if d.slug == HOME_SLUG else f"/{d.slug}/index.html"
        cls = ' class="current"' if d.slug == current_slug else ""
        label = d.title if d.title.startswith(d.slug) else f"{d.slug} · {d.title}"
        items.append(f'<li{cls}><a href="{href}">{label}</a></li>')
    return "<nav class=\"kb-sidebar\"><h2>Topics</h2><ul>" + "".join(items) + "</ul></nav>"


def page_header(doc_title: str, section_title: str, doc_index_href: str, show_back_to_topic: bool) -> str:
    crumbs = f'<a href="/index.html">Home</a> &raquo; <a href="{doc_index_href}">{doc_title}</a>'
    if section_title:
        crumbs += f" &raquo; {section_title}"
    back = f'<a href="{doc_index_href}">&laquo; Back to topic overview</a> &middot; ' if show_back_to_topic else ""
    return f"""
<header class="kb-header" id="top">
  <div class="kb-header-title"><a href="/index.html">{SITE_TITLE}</a></div>
  <div class="kb-breadcrumb">{crumbs}</div>
</header>
<div class="kb-toolbar">{back}<a href="/index.html">Home</a> &middot; <a href="#top">Back to top</a></div>
"""


def page_footer(doc_index_href: str, show_back_to_topic: bool) -> str:
    back = f'<a href="{doc_index_href}">&laquo; Back to topic overview</a> &middot; ' if show_back_to_topic else ""
    return f"""
<footer class="kb-footer">
  {back}<a href="/index.html">Home</a> &middot; <a href="#top">Back to top</a>
</footer>
"""


def html_page(title: str, body: str, sidebar: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} &middot; {SITE_TITLE}</title>
<link rel="stylesheet" href="/assets/style.css">
</head>
<body>
<div class="kb-layout">
  {sidebar}
  <main class="kb-main">
    {body}
  </main>
</div>
</body>
</html>
"""


def build_doc_index_page(doc: Doc, docs, doc_index_href: str) -> str:
    sidebar = nav_sidebar(docs, doc.slug)
    toc_items = "".join(
        f'<li><a href="#{slug}">{heading}</a> &middot; <a href="/{doc.slug}/{slug}.html">(own page)</a></li>'
        for heading, slug, _ in doc.sections
    )
    sections_html = "".join(
        f'<section id="{slug}"><h2>{heading}</h2>{html}</section>'
        for heading, slug, html in doc.sections
    )
    body = (
        page_header(doc.title, "", doc_index_href, False)
        + f"<h1>{doc.title}</h1>"
        + doc.preamble_html
        + (f'<nav class="kb-page-toc"><strong>Sections on this page:</strong><ul>{toc_items}</ul></nav>' if toc_items else "")
        + sections_html
        + page_footer(doc_index_href, False)
    )
    return html_page(doc.title, body, sidebar)


def build_section_page(doc: Doc, docs, heading: str, slug: str, html: str, doc_index_href: str) -> str:
    sidebar = nav_sidebar(docs, doc.slug)
    siblings = "".join(
        f'<li{" class=\"current\"" if s == slug else ""}><a href="/{doc.slug}/{s}.html">{h}</a></li>'
        for h, s, _ in doc.sections
    )
    body = (
        page_header(doc.title, heading, doc_index_href, True)
        + f"<h1>{doc.title}</h1>"
        + f"<h2>{heading}</h2>"
        + html
        + f'<nav class="kb-page-toc"><strong>Other sections in {doc.title}:</strong><ul>{siblings}</ul></nav>'
        + page_footer(doc_index_href, True)
    )
    return html_page(f"{heading} — {doc.title}", body, sidebar)


STYLE_CSS = """
:root {
  --fg: #1d2027;
  --muted: #5b6270;
  --accent: #1a5fb4;
  --bg: #ffffff;
  --bg-alt: #f4f6f9;
  --border: #dde2e8;
  --code-bg: #282c34;
  --code-fg: #e6e6e6;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
  color: var(--fg);
  background: var(--bg);
  line-height: 1.6;
}
.kb-layout { display: flex; max-width: 1400px; margin: 0 auto; }
.kb-sidebar {
  flex: 0 0 260px;
  padding: 1.2rem 1rem;
  background: var(--bg-alt);
  border-right: 1px solid var(--border);
  min-height: 100vh;
  position: sticky;
  top: 0;
  align-self: flex-start;
  max-height: 100vh;
  overflow-y: auto;
}
.kb-sidebar h2 { font-size: 0.85rem; text-transform: uppercase; color: var(--muted); margin-top: 0; }
.kb-sidebar ul { list-style: none; padding: 0; margin: 0; }
.kb-sidebar li { margin-bottom: 0.35rem; }
.kb-sidebar a { color: var(--fg); text-decoration: none; font-size: 0.92rem; }
.kb-sidebar a:hover { color: var(--accent); text-decoration: underline; }
.kb-sidebar li.current a { color: var(--accent); font-weight: 600; }
.kb-main { flex: 1; padding: 1.5rem 2.5rem 4rem; min-width: 0; }
.kb-header { border-bottom: 2px solid var(--accent); padding-bottom: 0.5rem; margin-bottom: 0.3rem; }
.kb-header-title a { color: var(--accent); text-decoration: none; font-weight: 700; font-size: 1.3rem; }
.kb-breadcrumb { font-size: 0.88rem; color: var(--muted); margin-top: 0.3rem; }
.kb-breadcrumb a { color: var(--muted); }
.kb-toolbar { font-size: 0.85rem; margin: 0.4rem 0 1.2rem; }
.kb-toolbar a, .kb-footer a { color: var(--accent); text-decoration: none; }
.kb-toolbar a:hover, .kb-footer a:hover { text-decoration: underline; }
.kb-footer { margin-top: 3rem; padding-top: 1rem; border-top: 1px solid var(--border); font-size: 0.85rem; }
h1 { font-size: 1.9rem; margin-bottom: 0.3rem; }
h2 { font-size: 1.35rem; margin-top: 2.2rem; border-bottom: 1px solid var(--border); padding-bottom: 0.25rem; }
h3 { font-size: 1.1rem; }
section { margin-bottom: 1rem; }
a { color: var(--accent); }
table { border-collapse: collapse; width: 100%; margin: 1rem 0; font-size: 0.92rem; }
th, td { border: 1px solid var(--border); padding: 0.5rem 0.7rem; text-align: left; }
th { background: var(--bg-alt); }
code { background: var(--bg-alt); padding: 0.15rem 0.35rem; border-radius: 3px; font-size: 0.9em; }
pre { background: var(--code-bg); color: var(--code-fg); padding: 1rem; border-radius: 6px; overflow-x: auto; }
pre code { background: none; padding: 0; color: inherit; }
img { max-width: 100%; height: auto; border: 1px solid var(--border); border-radius: 4px; background: #fff; padding: 0.5rem; }
.kb-page-toc { background: var(--bg-alt); border: 1px solid var(--border); border-radius: 6px; padding: 0.8rem 1.2rem; margin: 1.5rem 0; font-size: 0.92rem; }
.kb-page-toc ul { margin: 0.4rem 0 0; }
.kb-page-toc li.current a { font-weight: 700; }
blockquote { border-left: 3px solid var(--accent); margin: 1rem 0; padding: 0.2rem 1rem; color: var(--muted); }
.task-list-item { list-style-type: none; margin-left: -1.4rem; }
.task-list-item input[type="checkbox"] { margin-right: 0.5rem; transform: scale(1.1); }
"""


def main() -> int:
    md_files = sorted(p for p in MD_DIR.glob("*.md"))
    if not md_files:
        print("No markdown files found under md/")
        return 1

    docs = [Doc(p) for p in md_files]

    if SITE_DIR.exists():
        shutil.rmtree(SITE_DIR)
    SITE_DIR.mkdir(parents=True)
    (SITE_DIR / "assets").mkdir()
    (SITE_DIR / "diagrams").mkdir()
    (SITE_DIR / "images").mkdir()

    pygments_css = HtmlFormatter(style=PYGMENTS_STYLE).get_style_defs(".highlight")
    (SITE_DIR / "assets" / "style.css").write_text(
        STYLE_CSS + "\n/* Pygments syntax highlighting */\n" + pygments_css + "\n",
        encoding="utf-8",
    )

    for svg in DIAGRAMS_DIR.glob("*.svg"):
        shutil.copy(svg, SITE_DIR / "diagrams" / svg.name)

    if IMAGES_DIR.exists():
        for img in IMAGES_DIR.iterdir():
            if img.is_file():
                shutil.copy(img, SITE_DIR / "images" / img.name)

    for doc in docs:
        doc_dir = SITE_DIR / doc.slug
        doc_dir.mkdir(exist_ok=True)
        doc_index_href = f"/{doc.slug}/index.html"

        index_html = build_doc_index_page(doc, docs, doc_index_href)
        (doc_dir / "index.html").write_text(index_html, encoding="utf-8")

        if doc.slug == HOME_SLUG:
            (SITE_DIR / "index.html").write_text(index_html, encoding="utf-8")

        for heading, slug, html in doc.sections:
            page = build_section_page(doc, docs, heading, slug, html, doc_index_href)
            (doc_dir / f"{slug}.html").write_text(page, encoding="utf-8")

    print(f"Built {len(docs)} document(s), "
          f"{sum(len(d.sections) for d in docs)} section page(s), "
          f"into {SITE_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
