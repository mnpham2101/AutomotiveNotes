#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build static HTML slide decks from a standard deck directory.

Usage:
    python tools/slides-generator/build_slides.py --path <deck-dir>
    python tools/slides-generator/build_slides.py --path doc/Standards/ISO14229-UDS

Markdowns are read from <deck-dir>/md/ (or <deck-dir>/ directly when no md/
sub-folder exists).  Output goes to <deck-dir>/slides/.

Markdown conventions:
    #   deck title            -> title slide
    ##  section               -> divider slide + nav group
    ###  slide                -> one slide
    > subtitle: / > footer:   -> title-slide subtitle / per-slide footer
    > note: ...               -> speaker note (screen-hidden, printed)
    `[Clause x]` trailing     -> rendered as a small source reference
"""
import argparse
import base64
import mimetypes
import re
import shutil
import xml.dom.minidom as minidom
from pathlib import Path

import markdown

from slides_theme import CSS, JS

# ---------------------------------------------------------------------------
# Markdown extensions used by the Python-Markdown renderer
# ---------------------------------------------------------------------------
MD_EXT = ["tables", "sane_lists", "attr_list"]

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------
NOTE_RE    = re.compile(r"(?m)^>\s*note:\s*(.+)$")
META_RE    = re.compile(r"(?m)^>\s*(subtitle|footer):\s*(.+)$")
REF_RE     = re.compile(r"(?m)^`\[(.+?)\]`\s*$")
IMG_RE     = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
MATH_D_RE  = re.compile(r"\$\$(.+?)\$\$", re.S)
MATH_I_RE  = re.compile(r"\$([^$\n]+?)\$")
MATH_SLOT_RE = re.compile(r"xmathslot(\d+)x")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ---------------------------------------------------------------------------
# LaTeX-subset math renderer
# ---------------------------------------------------------------------------
GREEK = {
    "Gamma": "Γ", "Delta": "Δ", "Theta": "Θ", "Lambda": "Λ",
    "Sigma": "Σ", "Phi": "Φ",   "Psi": "Ψ",   "Omega": "Ω",
    "alpha": "α", "beta": "β",  "gamma": "γ",  "delta": "δ",
    "epsilon": "ε", "varepsilon": "ε", "zeta": "ζ", "eta": "η",
    "theta": "θ",   "kappa": "κ", "lambda": "λ", "mu": "μ",
    "nu": "ν",      "pi": "π",    "rho": "ρ",    "sigma": "σ",
    "tau": "τ",     "phi": "φ",   "omega": "ω",
}
OPS = {
    "approx": "≈", "times": "×",  "cdot": "·",   "div": "÷",
    "le": "≤",     "leq": "≤",    "ge": "≥",      "geq": "≥",
    "ne": "≠",     "neq": "≠",    "pm": "±",      "mp": "∓",
    "ll": "≪",     "gg": "≫",     "equiv": "≡",   "propto": "∝",
    "to": "→",     "rightarrow": "→", "Rightarrow": "⇒",
    "infty": "∞",  "sim": "∼",
}
BIN = set("=+<>")


def _grp(s: str, i: int) -> tuple[str, int]:
    """Read a {…} group, a \\macro, or one character at s[i]."""
    while i < len(s) and s[i] == " ":
        i += 1
    if i >= len(s):
        return "", i
    if s[i] == "{":
        depth, j = 1, i + 1
        while j < len(s) and depth:
            depth += {"{": 1, "}": -1}.get(s[j], 0)
            j += 1
        return s[i + 1:j - 1], j
    if s[i] == "\\":
        j = i + 1
        while j < len(s) and s[j].isalpha():
            j += 1
        return s[i:max(j, i + 2)], max(j, i + 2)
    return s[i], i + 1


def render_math(s: str) -> str:
    """Render a LaTeX-subset expression to HTML+CSS spans."""
    out, i, n = [], 0, len(s)
    unary = True
    while i < n:
        c = s[i]
        if c == "\\":
            j = i + 1
            while j < n and s[j].isalpha():
                j += 1
            name = s[i + 1:j]
            if not name:
                nxt = s[i + 1:i + 2]
                out.append('<span class="msp"></span>' if nxt in ",;:! " else esc(nxt))
                i += 2
                continue
            if name == "frac":
                a, i = _grp(s, j)
                b, i = _grp(s, i)
                out.append('<span class="frac"><span class="fn">%s</span>'
                           '<span class="fd">%s</span></span>'
                           % (render_math(a), render_math(b)))
                continue
            if name == "sqrt":
                a, i = _grp(s, j)
                tall = " tall" if "\\frac" in a else ""
                out.append('<span class="sqrt%s"><span class="sr">√</span>'
                           '<span class="rad">%s</span></span>' % (tall, render_math(a)))
                continue
            if name == "text":
                a, i = _grp(s, j)
                out.append('<span class="mtxt">%s</span>' % esc(a))
                continue
            if name in GREEK:
                out.append(GREEK[name] if name[0].isupper() else "<i>%s</i>" % GREEK[name])
                i = j
                continue
            if name in OPS:
                out.append('<span class="mo">%s</span>' % OPS[name])
                unary = True
                i = j
                continue
            out.append(esc(name))
            unary = False
            i = j
            continue
        if c in "_^":
            a, i = _grp(s, i + 1)
            tag = "sub" if c == "_" else "sup"
            out.append("<%s>%s</%s>" % (tag, render_math(a), tag))
            unary = False
            continue
        if c.isalpha():
            out.append("<i>%s</i>" % c)
            unary = False
        elif c in "-+":
            sign = "−" if c == "-" else "+"
            out.append('<span class="mo%s">%s</span>' % (" un" if unary else "", sign))
            unary = True
        elif c in BIN:
            out.append('<span class="mo">%s</span>' % esc(c))
            unary = True
        elif c == " ":
            out.append(" ")
        else:
            out.append(esc(c))
            unary = False
        i += 1
    return "".join(out)


def extract_math(text: str) -> tuple[str, list[str]]:
    """Replace $…$ / $$…$$ with slot tokens before markdown runs.

    Returns the modified text and a list of pre-rendered HTML spans so that
    markdown cannot mangle backslashes or misread _subscripts_ as emphasis.
    """
    store: list[str] = []

    def take(expr: str, cls: str) -> str:
        store.append('<span class="math %s">%s</span>' % (cls, render_math(expr.strip())))
        return "xmathslot%dx" % (len(store) - 1)

    text = MATH_D_RE.sub(lambda m: take(m.group(1), "math-display"), text)
    text = MATH_I_RE.sub(lambda m: take(m.group(1), "math-inline"),  text)
    return text, store


def restore_math(html: str, store: list[str]) -> str:
    return MATH_SLOT_RE.sub(lambda m: store[int(m.group(1))], html)


# ---------------------------------------------------------------------------
# Asset handling
# ---------------------------------------------------------------------------

def data_uri(path: Path) -> str:
    """Return a base64 data: URI for a local asset.

    draw.io SVGs carry a full editable mxfile in the `content` attribute;
    strip it before embedding — it is useless for rendering.
    """
    raw  = path.read_bytes()
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    if path.suffix.lower() == ".svg":
        mime = "image/svg+xml"
        try:
            doc  = minidom.parseString(raw)
            root = doc.documentElement
            assert root is not None
            if root.hasAttribute("content"):
                root.removeAttribute("content")
            raw = root.toxml().encode("utf-8")
        except Exception as e:
            print("    (could not strip drawio source from %s: %s)" % (path.name, e))
    return "data:%s;base64,%s" % (mime, base64.b64encode(raw).decode("ascii"))


def embed_images(text: str, md_path: Path, outdir: Path, inline: bool) -> tuple[str, int]:
    """Rewrite local image references in *text* to either data: URIs or
    copied-file names.  Returns (modified text, number of images handled)."""
    assets: dict[str, str] = {}
    for src in IMG_RE.findall(COMMENT_RE.sub("", text)):
        if src.startswith(("http://", "https://", "data:")) or src in assets:
            continue
        p = (md_path.parent / src).resolve()
        if not p.is_file():
            print("  ! missing image, skipped: %s" % src)
            continue
        if inline:
            assets[src] = data_uri(p)
        else:
            outdir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, outdir / p.name)
            assets[src] = p.name

    if assets:
        text = IMG_RE.sub(
            lambda m: m.group(0).replace(m.group(1), assets.get(m.group(1), m.group(1))),
            text,
        )
    return text, len(assets)


# ---------------------------------------------------------------------------
# Markdown parser
# ---------------------------------------------------------------------------

def parse_deck(md_text: str) -> tuple[str, str, str, list[dict]]:
    """Parse a deck markdown file.

    Returns (title, subtitle, footer, slides) where each slide dict has:
        section   – current H2 name (None for top-level slides)
        title     – H3 title, or None for divider slides
        body      – raw markdown body
        divider   – True for H2-generated section dividers
    """
    md_text = COMMENT_RE.sub("", md_text)
    meta    = dict(META_RE.findall(md_text))
    md_text = META_RE.sub("", md_text)

    m     = re.search(r"(?m)^#\s+(.+)$", md_text)
    title = m.group(1).strip() if m else "Untitled deck"
    body  = md_text[m.end():] if m else md_text

    slides: list[dict] = []
    section = None
    # re.split keeps the delimiter groups so we iterate pairs (header, text)
    parts = re.split(r"(?m)^(##\s+.+|###\s+.+)$", body)
    i = 1
    while i < len(parts):
        head = parts[i].strip()
        text = parts[i + 1] if i + 1 < len(parts) else ""
        if head.startswith("### "):
            slides.append(dict(section=section, title=head[4:].strip(), body=text))
        else:
            section = head[3:].strip()
            slides.append(dict(section=section, title=None, body=text, divider=True))
        i += 2

    return title, meta.get("subtitle", ""), meta.get("footer", ""), slides


def add_slide(slides: list[dict], *, section: str | None = None,
              title: str, body: str = "") -> None:
    """Append a new content slide to an existing slides list.

    Example:
        add_slide(slides, title="Quick Reference", body="- item one\\n- item two")
    """
    slides.append(dict(section=section, title=title, body=body))


def add_section(slides: list[dict], section: str, body: str = "") -> None:
    """Append a new section-divider slide (H2 equivalent) to a slides list."""
    slides.append(dict(section=section, title=None, body=body, divider=True))


# ---------------------------------------------------------------------------
# Slide HTML builders
# ---------------------------------------------------------------------------

def build_slide_title(title: str, subtitle: str, footer: str) -> str:
    """Return HTML for the opening title slide (slide index 0)."""
    parts = [
        '<section class="slide title" id="s0"><div class="slide-inner">',
        "<h1>%s</h1>" % esc(title),
        '<div class="bar"></div>',
    ]
    if subtitle:
        parts.append('<div class="sub">%s</div>' % esc(subtitle))
    if footer:
        parts.append('<div class="meta">%s</div>' % esc(footer))
    parts.append("</div></section>")
    return "\n".join(parts)


def build_slide_content(slide: dict, idx: int, total: int,
                        footer: str, deck_title: str) -> str:
    """Return HTML for one content or divider slide."""
    body  = slide["body"]
    notes = NOTE_RE.findall(body)
    body  = NOTE_RE.sub("", body)
    refs  = REF_RE.findall(body)
    body  = REF_RE.sub("", body)

    body, math = extract_math(body)
    html = markdown.markdown(body.strip(), extensions=MD_EXT)
    html = restore_math(html, math)
    html = re.sub(r"<p>(<img [^>]+>)</p>", r"<figure>\1</figure>", html)

    cls: str   = "slide"
    inner: list[str] = []

    if slide.get("divider"):
        cls += " divider"
        inner.append('<div class="kicker">Section</div>')
        inner.append("<h2>%s</h2>" % esc(slide["section"]))
        if html.strip():
            inner.append(html)
    else:
        inner.append("<h2>%s</h2>" % esc(slide["title"]))
        inner.append(html)

    for r in refs:
        inner.append('<div class="ref">%s</div>' % esc(r))
    for n in notes:
        inner.append('<div class="note"><b>Note — </b>%s</div>' % esc(n))

    foot = ('<div class="foot">'
            '<span>%s</span>'
            '<span class="n">%d / %d</span>'
            '</div>' % (esc(footer or deck_title), idx, total))

    return ('<section class="%s" id="s%d">'
            '<div class="slide-inner">%s</div>'
            '%s'
            '</section>' % (cls, idx, "\n".join(inner), foot))


def build_nav(title: str, subtitle: str, slides: list[dict]) -> str:
    """Return HTML for the sidebar navigation."""
    items = ['<a href="#s0" data-i="0">Title</a>']
    for i, s in enumerate(slides, 1):
        if s.get("divider"):
            items.append('<div class="grp">%s</div>' % esc(s["section"]))
            items.append('<a href="#s%d" data-i="%d">Overview</a>' % (i, i))
        else:
            items.append('<a href="#s%d" data-i="%d">%s</a>' % (i, i, esc(s["title"])))

    brand = ('<div class="brand">'
             '<b>%s</b>'
             '<span>%s</span>'
             '</div>' % (esc(title), esc(subtitle)))
    return "<nav>%s%s</nav>" % (brand, "\n".join(items))


# ---------------------------------------------------------------------------
# Full-deck builder
# ---------------------------------------------------------------------------

def build(md_path: Path, outdir: Path, inline: bool = True) -> Path:
    """Build one HTML slide deck from *md_path* and write it to *outdir*."""
    md_path = md_path.resolve()
    text    = md_path.read_text(encoding="utf-8")

    text, embedded = embed_images(text, md_path, outdir, inline)
    title, subtitle, footer, slides = parse_deck(text)
    outdir.mkdir(parents=True, exist_ok=True)

    total = len(slides)  # excludes the title slide in the counter shown on screen

    slide_html = [build_slide_title(title, subtitle, footer)]
    for i, s in enumerate(slides, 1):
        slide_html.append(build_slide_content(s, i, total, footer, title))

    nav_html = build_nav(title, subtitle, slides)

    html = (
        "<!doctype html>\n"
        '<html lang="en"><head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        "<title>%s</title>\n"
        "<style>%s</style>\n"
        "</head><body>\n"
        '<div class="rail"><i></i></div>\n'
        '<div class="shell">\n'
        "%s\n"
        "<main>%s</main>\n"
        "</div>\n"
        "<script>%s</script>\n"
        "</body></html>"
    ) % (esc(title), CSS, nav_html, "\n".join(slide_html), JS)

    out = outdir / (md_path.stem + ".html")
    out.write_text(html, encoding="utf-8")
    print("  %s  (%d slides, %d image%s %s, %.1f MB)"
          % (out, total + 1, embedded, "" if embedded == 1 else "s",
             "embedded" if inline else "copied", len(html) / 1048576.0))
    return out


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

def find_markdowns(deck_dir: Path) -> tuple[list[Path], Path]:
    """Return (markdown files, output directory) for a deck directory.

    Source search order:
        1. <deck_dir>/markdowns/   – preferred location
        2. <deck_dir>/md/          – legacy alternate name
        3. <deck_dir>/slides/      – old layout where md lived with HTML
        4. <deck_dir>/             – bare fallback

    HTML output always goes to <deck_dir>/slides/.
    """
    outdir = deck_dir / "slides"
    for src in ("markdowns", "md"):
        d = deck_dir / src
        if d.is_dir() and any(d.glob("*.md")):
            return sorted(d.glob("*.md")), outdir
    slides_dir = deck_dir / "slides"
    if slides_dir.is_dir() and any(slides_dir.glob("*.md")):
        return sorted(slides_dir.glob("*.md")), outdir
    return sorted(deck_dir.glob("*.md")), outdir


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(
        description="Build HTML slide decks from a deck directory.",
    )
    ap.add_argument(
        "--path", required=True,
        help=(
            "Root directory of the deck (e.g. doc/Standards/ISO14229-UDS). "
            "Markdowns are read from <path>/md/ (or <path>/ if no md/ folder). "
            "Output goes to <path>/slides/."
        ),
    )
    ap.add_argument(
        "--no-inline", action="store_true",
        help="Copy images beside the HTML instead of embedding them "
             "(smaller HTML, but no longer a single portable file).",
    )
    a = ap.parse_args()

    deck_dir = Path(a.path).resolve()
    if not deck_dir.is_dir():
        ap.error("--path is not a directory: %s" % deck_dir)

    markdowns, outdir = find_markdowns(deck_dir)
    if not markdowns:
        ap.error("No *.md files found under %s" % deck_dir)

    print("building -> %s" % outdir)
    for md in markdowns:
        build(md, outdir, inline=not a.no_inline)


if __name__ == "__main__":
    main()
