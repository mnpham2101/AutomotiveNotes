#!/usr/bin/env python3
"""
Convert the resume .docx into the web markdown format used by resume-generator.py.

Stdlib only (zipfile + xml.etree), no third-party packages required.

Usage from repository root:
    py tools/resume-generator/docx-to-markdown.py
    py tools/resume-generator/docx-to-markdown.py --docx <in.docx> --md <out.md>

Defaults:
    --docx doc/resume/Minh_Resume _CPlusPlus.docx
    --md   doc/resume/Minh_Resume_for_web.md

The .docx is the content source. The output follows the conventions that
resume-generator.py parses:
    # Name / location / "Phone: x | Email: <x>" / [Label](url) link line
    ## Section headings separated by ---
    **School** — date + *degree* lines for education
    ### Company — Location + **Role** · dates + intro + **Subheading** + bullets
    - **Label:** text for domain background
"""

import argparse
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

W_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
R_NS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
REL_NS = "{http://schemas.openxmlformats.org/package/2006/relationships}"

ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_DOCX = ROOT / "doc" / "resume" / "Minh_Resume _CPlusPlus.docx"
DEFAULT_MD = ROOT / "doc" / "resume" / "Minh_Resume_for_web.md"

# Docx heading text (upper case, colon optional) -> markdown heading
KNOWN_HEADINGS = {
    "OBJECTIVE": "Objective",
    "EDUCATION": "Education",
    "CERTIFICATIONS": "Certifications",
    "DOMAIN SPECIFIC BACKGROUND": "Domain-Specific Background",
    "SOFTWARE TOOLS": "Software Tools",
    "INDIVIDUAL PROJECTS & AWARD": "Individual Projects & Award",
    "PROFESSIONAL EXPERIENCE": "Professional Experience",
    "HOBBIES AND OTHER ACTIVITIES": "Hobbies and Other Activities",
}

MONTHS = (
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|"
    r"Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
)
DATE = rf"(?:{MONTHS}\.?\s+)?\d{{4}}"
ROLE_DATE_RE = re.compile(
    rf"({DATE})\s+(?:to|-|–)\s+({DATE}|current|present)", re.IGNORECASE
)
EDU_DATE_RE = re.compile(rf"((?:{DATE})(?:\s*[-–]\s*{DATE})?)\s*$", re.IGNORECASE)
CAPS_PREFIX_RE = re.compile(r"^([A-Z][A-Z &]*):\s*(.*)$")
CAPS_ONLY_RE = re.compile(r"^[A-Z][A-Z &]*:?$")
CONTACT_LABEL_RE = re.compile(r"(LinkedIn|Website|GitHub|Email|Phone)\s*:", re.IGNORECASE)


# ═══════════════════════════════════════════════════════════════
#  Docx reading
# ═══════════════════════════════════════════════════════════════

@dataclass
class Segment:
    text: str
    bold: bool = False
    italic: bool = False
    link: str = ""


@dataclass
class Para:
    segments: list = field(default_factory=list)
    bullet: bool = False  # has w:numPr -> rendered as a list item

    @property
    def plain(self) -> str:
        return normalize_space("".join(s.text for s in self.segments))

    @property
    def is_empty(self) -> bool:
        return not self.plain


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _flag(rpr, name: str) -> bool:
    el = rpr.find(W_NS + name) if rpr is not None else None
    if el is None:
        return False
    return el.get(W_NS + "val") not in ("0", "false", "off")


def _read_paragraphs(docx_path: Path):
    with zipfile.ZipFile(docx_path) as z:
        document = ET.fromstring(z.read("word/document.xml"))
        rels = ET.fromstring(z.read("word/_rels/document.xml.rels"))
    targets = {r.get("Id"): r.get("Target") for r in rels.iter(REL_NS + "Relationship")}

    body = document.find(W_NS + "body")
    paras = []
    for el in body:
        if _local(el.tag) != "p":
            continue
        para = Para()
        ppr = el.find(W_NS + "pPr")
        para.bullet = ppr is not None and ppr.find(W_NS + "numPr") is not None
        _walk_runs(el, "", targets, para.segments)
        paras.append(para)
    return paras


def _walk_runs(node, link, targets, out):
    for child in node:
        name = _local(child.tag)
        if name == "pPr":
            continue
        if name == "hyperlink":
            rid = child.get(R_NS + "id")
            target = targets.get(rid, "") or child.get(W_NS + "anchor", "")
            _walk_runs(child, target, targets, out)
        elif name == "r":
            rpr = child.find(W_NS + "rPr")
            text = ""
            for part in child:
                pname = _local(part.tag)
                if pname == "t" and part.text:
                    text += part.text
                elif pname in ("tab", "br", "cr"):
                    text += " "
            if text:
                out.append(Segment(
                    text=text,
                    bold=_flag(rpr, "b"),
                    italic=_flag(rpr, "i"),
                    link=link,
                ))
        elif name in ("ins", "smartTag", "sdt", "sdtContent", "fldSimple"):
            _walk_runs(child, link, targets, out)


# ═══════════════════════════════════════════════════════════════
#  Text helpers
# ═══════════════════════════════════════════════════════════════

def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def typeset(text: str) -> str:
    """Match the typographic dashes used in the web markdown."""
    text = re.sub(r"(?<=\s)-(?=\s)", "–", text)
    text = re.sub(r"\s*\bto\b\s*(?=(?:\w+\s+)?\d{4}|current|present)", " – ", text, flags=re.IGNORECASE)
    return text


def normalize_date(text: str) -> str:
    text = typeset(text)
    text = re.sub(r"\s*[-–]\s*", " – ", text)
    text = re.sub(r"\bcurrent\b", "Present", text, flags=re.IGNORECASE)
    text = re.sub(r"\bJanuary\b", "Jan", text)
    return normalize_space(text)


def render_inline(segments, bullet: bool = False, strip_bold: bool = False) -> str:
    """strip_bold=True renders the text plain: no bold and no italic emphasis."""
    """Render segments as markdown. Bold and italic runs are merged so that
    Word's fragmented runs (e.g. 'Autosar' 'AI') become one emphasis span."""
    merged = []
    for seg in segments:
        if not seg.text:
            continue
        bold = seg.bold and not strip_bold
        italic = seg.italic and not strip_bold
        if merged and (merged[-1].bold, merged[-1].italic, merged[-1].link) == (bold, italic, seg.link):
            merged[-1].text += seg.text
        else:
            merged.append(Segment(seg.text, bold, italic, seg.link))

    # A label colon belongs to the bold label: "**Label:** text", not "**Label**: text".
    for i in range(len(merged) - 1):
        a, b = merged[i], merged[i + 1]
        if a.bold and not b.bold and not a.link and not b.link and b.text.startswith(":"):
            a.text += ":"
            b.text = b.text[1:]

    out = []
    for seg in merged:
        text = seg.text
        if seg.link:
            label = normalize_space(text)
            if label in (seg.link, seg.link.rstrip("/")) or label.startswith("http"):
                out.append(seg.link)
            elif seg.link.startswith("mailto:"):
                out.append(f"<{seg.link[len('mailto:'):]}>")
            else:
                out.append(f"[{label}]({seg.link})")
            continue
        lead = " " if text[:1].isspace() else ""
        trail = " " if text[-1:].isspace() else ""
        core = normalize_space(text)
        if not core:
            out.append(" ")
            continue
        if seg.bold and seg.italic:
            core = f"***{core}***"
        elif seg.bold:
            core = f"**{core}**"
        elif seg.italic:
            core = f"*{core}*"
        out.append(f"{lead}{core}{trail}")

    result = "".join(out)
    result = re.sub(r"\*\*\s+\*\*", " ", result)  # join bold runs split by spaces
    result = re.sub(r"\*\s+\*", " ", result)
    result = re.sub(r"\s+", " ", result).strip()
    return typeset(result)


def heading_of(text: str):
    """Return (heading, rest) when a paragraph starts a section, else None."""
    t = normalize_space(text)
    m = CAPS_PREFIX_RE.match(t)
    if m:
        key = m.group(1).strip()
        if key in KNOWN_HEADINGS or key.isupper():
            return KNOWN_HEADINGS.get(key, key.title()), m.group(2).strip()
    return None


# ═══════════════════════════════════════════════════════════════
#  Document -> sections
# ═══════════════════════════════════════════════════════════════

def split_sections(paras):
    """Group paragraphs under their section headings. Word splits some headings
    across paragraphs ('DOMAIN SPECIFIC' / 'BACKGROUND:'), so caps fragments are
    accumulated until they form a known heading."""
    sections = []  # list of (heading, [Para])
    current = None
    pending = ""
    for para in paras:
        text = para.plain
        if not text:
            continue
        if not para.bullet and CAPS_ONLY_RE.match(text):
            pending = normalize_space(f"{pending} {text}")
            key = pending.rstrip(":").strip()
            if key in KNOWN_HEADINGS:
                current = [KNOWN_HEADINGS[key], []]
                sections.append(current)
                pending = ""
            continue
        pending = ""
        hr = None if para.bullet else heading_of(text)
        if hr:
            heading, rest = hr
            current = [heading, []]
            sections.append(current)
            if rest:
                # Heading shares its paragraph with body text ("OBJECTIVE:Looking ...").
                raw = "".join(s.text for s in para.segments)
                label_len = re.match(r"\s*[A-Z][A-Z &]*:\s*", raw).end()
                current[1].append(Para(segments=_segments_after(para.segments, label_len)))
            continue
        if current is not None:
            current[1].append(para)
    return sections


# ═══════════════════════════════════════════════════════════════
#  Section renderers -> list of blocks
#  A block is either a str (paragraph / heading line) or a list of bullet strings.
# ═══════════════════════════════════════════════════════════════

def render_plain(paras, strip_bold: bool = True):
    """Bullet lists and plain paragraphs. The web markdown does not bold these items."""
    blocks, bullets = [], []
    for p in paras:
        if p.is_empty:
            continue
        if p.bullet:
            bullets.append(render_inline(p.segments, strip_bold=strip_bold))
            continue
        if bullets:
            blocks.append(bullets)
            bullets = []
        blocks.append(render_inline(p.segments, strip_bold=strip_bold))
    if bullets:
        blocks.append(bullets)
    return blocks


def _bullet(para: Para) -> str:
    """Experience bullets are plain text in the web markdown."""
    return render_inline(para.segments, strip_bold=True)


def render_labelled_bullets(paras):
    """Bullets whose bold lead-in is a label, e.g. '- **Android Platform:** ...'."""
    return render_plain(paras, strip_bold=False)


def render_objective(paras):
    return [" ".join(render_inline(p.segments, strip_bold=True) for p in paras if not p.is_empty)]


def render_education(paras):
    blocks = []
    for p in paras:
        if p.is_empty:
            continue
        plain = p.plain
        italic_only = all((s.italic or not s.text.strip()) and not s.bold for s in p.segments)
        if italic_only and blocks and isinstance(blocks[-1], str):
            blocks[-1] += "\n" + render_inline(p.segments)
            continue
        m = EDU_DATE_RE.search(plain)
        if m:
            school = plain[: m.start()].rstrip(" ,")
            date = normalize_date(m.group(1))
            blocks.append(f"**{school}** — {date}")
        else:
            blocks.append(render_inline(p.segments))
    return blocks


def _role_line(header_lines):
    """Split 'Role   January 2025 to current' into '**Role** · Jan 2025 – Present'."""
    text = normalize_space(" ".join(header_lines))
    m = ROLE_DATE_RE.search(text)
    if not m:
        return f"**{text}**" if text else ""
    role = text[: m.start()].strip(" -–·,")
    dates = normalize_date(f"{m.group(1)} – {m.group(2)}")
    return f"**{role}** · {dates}" if role else dates


def render_experience(paras):
    """Group paragraphs into job entries (company, role/date header, body), then render each."""
    entries = []
    for p in paras:
        if p.is_empty:
            continue
        if _is_company(p):
            entries.append({"company": p, "header": [], "body": []})
        elif not entries:
            continue
        elif not entries[-1]["body"] and not p.bullet and not _has_label(p):
            entries[-1]["header"].append(p.plain)
        else:
            entries[-1]["body"].append(p)

    blocks = []
    for entry in entries:
        company, _, location = entry["company"].plain.partition(",")
        heading = f"### {company.strip()} — {location.strip()}"
        role = _role_line(entry["header"])
        blocks.append(f"{heading}\n{role}" if role else heading)
        blocks.extend(_render_experience_body(entry["body"]))
    return blocks


def _is_company(p: Para) -> bool:
    """A company line starts bold ('FPT Software' + ', Danang, Vietnam'), has no label colon."""
    if p.bullet:
        return False
    segs = [s for s in p.segments if s.text.strip()]
    return bool(segs) and segs[0].bold and "," in p.plain and ":" not in p.plain


def _segments_after(segments, n_chars):
    """Segments with the first n_chars of plain text removed."""
    out = []
    skipped = 0
    for seg in segments:
        if skipped >= n_chars:
            out.append(seg)
            continue
        if skipped + len(seg.text) <= n_chars:
            skipped += len(seg.text)
            continue
        cut = n_chars - skipped
        out.append(Segment(seg.text[cut:], seg.bold, seg.italic, seg.link))
        skipped = n_chars
    return out


def _has_label(p: Para) -> bool:
    return bool(re.match(r"^.{2,80}?:", p.plain))


def _render_experience_body(paras):
    """Intro paragraph, then **Subheading** blocks with bullets under each."""
    blocks, bullets = [], []
    intro_done = False
    seen_sub = False

    def flush():
        nonlocal bullets
        if bullets:
            blocks.append(bullets)
            bullets = []

    for p in paras:
        if p.bullet:
            # The first bullet before any subheading is the entry's summary sentence.
            if not seen_sub and not intro_done:
                flush()
                blocks.append(render_inline(p.segments, strip_bold=True))
                intro_done = True
            else:
                bullets.append(_bullet(p))
            continue

        label_m = re.match(r"^(.{2,80}?):(.*)$", p.plain)
        if label_m:
            flush()
            label = label_m.group(1).strip()
            blocks.append(f"**{label}**")
            seen_sub = True
            rest = label_m.group(2).strip()
            if rest:
                bullets.append(render_inline(_segments_after(p.segments, len(label_m.group(1)) + 1), strip_bold=True))
            continue

        flush()
        blocks.append(render_inline(p.segments, strip_bold=True))
    flush()
    return blocks


# ═══════════════════════════════════════════════════════════════
#  Contact header
# ═══════════════════════════════════════════════════════════════

def parse_header(paras):
    """Return (name, location, phone_line, links_line) from the preamble."""
    nonempty = [p for p in paras if not p.is_empty]
    name_para = nonempty[0]
    name = name_para.plain.title()
    location = normalize_space(nonempty[1].plain) if len(nonempty) > 1 else ""

    contact = next((p for p in nonempty if "Phone" in p.plain or "Email" in p.plain), None)
    phone = email = ""
    links = []
    if contact is not None:
        pm = re.search(r"Phone:\s*(\S+)", contact.plain)
        phone = pm.group(1) if pm else ""
        # Labels such as 'LinkedIn:' can be split across runs, so read the text
        # that precedes each hyperlink rather than one run at a time.
        preceding = ""
        for seg in contact.segments:
            if not seg.link:
                preceding += seg.text
                continue
            if seg.link.startswith("mailto:"):
                email = seg.link[len("mailto:"):]
            else:
                labels = CONTACT_LABEL_RE.findall(preceding)
                label = labels[-1].lower() if labels else ""
                link_label = {"linkedin": "LinkedIn", "website": "Website", "github": "GitHub"}.get(label, normalize_space(seg.text))
                links.append((link_label, seg.link))
            preceding = ""
    phone_line = f"Phone: {phone} | Email: <{email}>" if email else f"Phone: {phone}"
    links_line = " | ".join(f"[{label}]({url})" for label, url in links)
    return name, location, phone_line, links_line


# ═══════════════════════════════════════════════════════════════
#  Assembly
# ═══════════════════════════════════════════════════════════════

RENDERERS = {
    "Objective": render_objective,
    "Education": render_education,
    "Domain-Specific Background": render_labelled_bullets,
    "Professional Experience": render_experience,
}


def render_blocks_to_markdown(blocks) -> str:
    parts = []
    for block in blocks:
        if isinstance(block, list):
            parts.append("\n".join(f"- {b}" for b in block if b))
        elif block:
            parts.append(block)
    return "\n\n".join(parts)


def build_markdown(docx_path: Path) -> str:
    paras = _read_paragraphs(docx_path)
    contact_idx = next(i for i, p in enumerate(paras) if "Phone" in p.plain)
    name, location, phone_line, links_line = parse_header(paras[: contact_idx + 1])

    sections = split_sections(paras[contact_idx + 1 :])

    out = [f"# {name}", "", location, phone_line, links_line, "", "---", ""]
    for heading, body in sections:
        renderer = RENDERERS.get(heading, render_plain)
        content = render_blocks_to_markdown(renderer(body))
        out.append(f"## {heading}")
        out.append("")
        if content:
            out.append(content)
            out.append("")
        out.append("---")
        out.append("")

    # The source file ends its last section with a separator; keep one trailing newline.
    text = "\n".join(out).rstrip("-\n").rstrip() + "\n"
    return text


def main():
    parser = argparse.ArgumentParser(description="Convert the resume .docx to web markdown")
    parser.add_argument("--docx", type=Path, default=DEFAULT_DOCX)
    parser.add_argument("--md", type=Path, default=DEFAULT_MD)
    args = parser.parse_args()

    if not args.docx.exists():
        print(f"Error: {args.docx} not found", file=sys.stderr)
        sys.exit(1)

    markdown = build_markdown(args.docx)
    args.md.write_text(markdown, encoding="utf-8", newline="\n")
    print(f"Written: {args.md}")


if __name__ == "__main__":
    main()
