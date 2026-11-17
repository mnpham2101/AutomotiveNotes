#!/usr/bin/env python3
"""
Resume generator — builds HTML resumes from Minh_Resume_for_web.md.

Usage from repository root:
    py tools/resume-generator/resume-generator.py resume-fpt-slide
    py tools/resume-generator/resume-generator.py resume-fpt-pdf
    py tools/resume-generator/resume-generator.py resume-vintage-slide
"""

import argparse
import base64
import re
import sys
from dataclasses import dataclass, field
from html import escape
from pathlib import Path

# ═══════════════════════════════════════════════════════════════
#  Data model
# ═══════════════════════════════════════════════════════════════

@dataclass
class Education:
    school: str
    date: str
    degree: str


@dataclass
class ExperienceSubsection:
    heading: str
    bullets: list


@dataclass
class Experience:
    company: str = ""
    location: str = ""
    role: str = ""
    dates: str = ""
    intro: str = ""
    subsections: list = field(default_factory=list)


@dataclass
class ResumeData:
    name: str = ""
    location: str = ""
    phone: str = ""
    email: str = ""
    links: list = field(default_factory=list)
    objective: str = ""
    education: list = field(default_factory=list)
    certifications: list = field(default_factory=list)
    projects: list = field(default_factory=list)
    background: list = field(default_factory=list)
    tools: list = field(default_factory=list)
    experience: list = field(default_factory=list)
    hobbies: list = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════
#  Markdown parser
# ═══════════════════════════════════════════════════════════════

def _strip_blank(lines):
    while lines and not lines[0].strip():
        lines = lines[1:]
    while lines and not lines[-1].strip():
        lines = lines[:-1]
    return lines


def _extract_paragraph(lines):
    return " ".join(l.strip() for l in lines if l.strip() and l.strip() != "---")


def _extract_bullets(lines):
    out = []
    for l in lines:
        m = re.match(r"^\s*[-•]\s+(.+)", l)
        if m:
            out.append(m.group(1).strip())
    return out


def _parse_education(lines):
    edu = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        m = re.match(r"\*\*(.+?)\*\*\s*[—–-]\s*(.+)", line)
        if m:
            school = m.group(1).strip()
            date = m.group(2).strip()
            degree = ""
            if i + 1 < len(lines):
                dm = re.match(r"^\*(.+)\*$", lines[i + 1].strip())
                if dm:
                    degree = dm.group(1).strip()
                    i += 1
            edu.append(Education(school, date, degree))
        i += 1
    return edu


def _parse_background(lines):
    out = []
    for l in lines:
        m = re.match(r"^\s*[-•]\s+\*\*(.+?):\*\*\s*(.+)", l)
        if m:
            out.append((m.group(1).strip(), m.group(2).strip()))
    return out


def _parse_tools(lines):
    tools = []
    for l in lines:
        m = re.match(r"^\s*[-•]\s+(.+)", l)
        if m:
            for item in re.split(r",\s+", m.group(1).strip()):
                item = item.strip()
                if item and item.lower() != "and":
                    parts = re.split(r"\s+and\s+", item)
                    tools.extend(p.strip() for p in parts if p.strip())
    return tools


def _parse_experience(lines):
    entries = []
    current = None
    current_subsection = None

    for line in lines:
        h3 = re.match(r"^###\s+(.+?)\s*[—–-]\s*(.+)", line)
        if h3:
            if current_subsection and current:
                current.subsections.append(current_subsection)
                current_subsection = None
            if current:
                entries.append(current)
            current = Experience(
                company=h3.group(1).strip(),
                location=h3.group(2).strip(),
            )
            continue

        if current is None:
            continue

        role_m = re.match(r"^\*\*(.+?)\*\*\s*[·]\s*(.+)", line)
        if role_m and not current.role:
            current.role = role_m.group(1).strip()
            current.dates = role_m.group(2).strip()
            continue

        sub_m = re.match(r"^\*\*(.+?)\*\*\s*$", line)
        if sub_m:
            if current_subsection:
                current.subsections.append(current_subsection)
            current_subsection = ExperienceSubsection(
                heading=sub_m.group(1).strip(), bullets=[]
            )
            continue

        bullet_m = re.match(r"^\s*[-•]\s+(.+)", line)
        if bullet_m:
            if current_subsection:
                current_subsection.bullets.append(bullet_m.group(1).strip())
            continue

        stripped = line.strip()
        if stripped and stripped != "---":
            if not current.intro:
                current.intro = stripped
            elif current.intro and not current_subsection:
                current.intro += " " + stripped

    if current_subsection and current:
        current.subsections.append(current_subsection)
    if current:
        entries.append(current)

    return entries


def parse_resume(md_path: Path) -> ResumeData:
    text = md_path.read_text(encoding="utf-8")
    lines = text.split("\n")
    data = ResumeData()

    i = 0
    while i < len(lines) and not lines[i].startswith("# "):
        i += 1
    if i < len(lines):
        data.name = lines[i].lstrip("# ").strip()
        i += 1

    contact_lines = []
    while i < len(lines) and lines[i].strip() != "---":
        if lines[i].strip():
            contact_lines.append(lines[i].strip())
        i += 1

    if contact_lines:
        data.location = contact_lines[0]
    if len(contact_lines) > 1:
        pm = re.search(r"Phone:\s*([^|]+)", contact_lines[1])
        if pm:
            data.phone = pm.group(1).strip()
        em = re.search(r"Email:\s*<?([^>|\s]+)>?", contact_lines[1])
        if em:
            data.email = em.group(1).strip()
    if len(contact_lines) > 2:
        for m in re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", contact_lines[2]):
            data.links.append((m.group(1), m.group(2)))

    sections = {}
    current_section = None
    section_lines = []

    while i < len(lines):
        if lines[i].startswith("## "):
            if current_section is not None:
                sections[current_section] = section_lines
            current_section = lines[i].lstrip("# ").strip().rstrip(":")
            section_lines = []
        elif current_section is not None:
            section_lines.append(lines[i])
        i += 1

    if current_section is not None:
        sections[current_section] = section_lines

    for name, slines in sections.items():
        nl = name.lower()
        if "objective" in nl:
            data.objective = _extract_paragraph(slines)
        elif "education" in nl:
            data.education = _parse_education(slines)
        elif "certification" in nl:
            data.certifications = _extract_bullets(slines)
        elif "project" in nl:
            data.projects = _extract_bullets(slines)
        elif "background" in nl:
            data.background = _parse_background(slines)
        elif "tool" in nl and "software" in nl:
            data.tools = _parse_tools(slines)
        elif "experience" in nl:
            data.experience = _parse_experience(slines)
        elif "hobb" in nl:
            data.hobbies = _extract_bullets(slines)

    return data


# ═══════════════════════════════════════════════════════════════
#  Theme & asset loaders
# ═══════════════════════════════════════════════════════════════

def parse_theme_colors(theme_path: Path) -> dict:
    text = theme_path.read_text(encoding="utf-8")
    m = re.search(r"```css\s*\n(.*?)```", text, re.DOTALL)
    if not m:
        return {}
    colors = {}
    for vm in re.finditer(r"(--[\w-]+):\s*(#[0-9A-Fa-f]+)", m.group(1)):
        colors[vm.group(1)] = vm.group(2)
    return colors


def load_logo_b64(logo_path: Path) -> str:
    raw = logo_path.read_bytes()
    return "data:image/png;base64," + base64.b64encode(raw).decode("ascii")


def css_vars_block(colors: dict) -> str:
    lines = ["  :root {"]
    for k, v in colors.items():
        lines.append(f"    {k}: {v};")
    lines.append("  }")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
#  Shared HTML utility functions
# ═══════════════════════════════════════════════════════════════

def esc(text: str) -> str:
    return escape(text, quote=True)


def html_document(title: str, favicon: str, style: str, body: str,
                  script: str = "") -> str:
    script_block = f"\n<script>\n{script}\n</script>" if script else ""
    return (
        f"<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n"
        f"<meta charset=\"utf-8\">\n"
        f"<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        f"<title>{esc(title)}</title>\n"
        f"<link rel=\"icon\" type=\"image/png\" href=\"{favicon}\">\n"
        f"<style>\n{style}\n</style>\n</head>\n<body>\n{body}"
        f"{script_block}\n</body>\n</html>\n"
    )


def create_brand_stripe() -> str:
    return (
        '<div class="brand-stripe" aria-hidden="true">\n'
        '  <span class="s-blue"></span>'
        '<span class="s-orange"></span>'
        '<span class="s-green"></span>\n'
        "</div>\n"
    )


def create_resume_title(data: ResumeData, logo_b64: str,
                        tagline: str = "") -> str:
    links_html = ""
    for label, url in data.links:
        links_html += (
            f'<a href="{esc(url)}">{esc(label)}</a>'
            '<span class="sep">|</span>\n            '
        )
    links_html = links_html.rstrip('<span class="sep">|</span>\n            ')

    return (
        '<div class="masthead">\n'
        "  <div>\n"
        f'    <h1>{esc(data.name)}</h1>\n'
        f'    <div class="tagline">{esc(tagline)}</div>\n'
        '    <div class="contact">\n'
        f"      <div>{esc(data.location)}</div>\n"
        f'      <div>Phone: {esc(data.phone)} '
        f'<span class="sep">|</span> '
        f'Email: <a href="mailto:{esc(data.email)}">{esc(data.email)}</a></div>\n'
        f"      <div>\n            {links_html}\n      </div>\n"
        "    </div>\n"
        "  </div>\n"
        f'  <img class="logo" src="{logo_b64}" alt="FPT logo">\n'
        "</div>\n"
    )


def create_section(title: str, content: str) -> str:
    return f'<section>\n  <h2>{esc(title)}</h2>\n  {content}\n</section>\n'


def create_role_line(role: str, dates: str) -> str:
    return (
        '<div class="role-line">\n'
        f'  <span class="role">{esc(role)}</span>\n'
        f'  <span class="dates">{esc(dates)}</span>\n'
        "</div>\n"
    )


def create_edu_entry(edu: Education) -> str:
    return (
        '<div class="edu-entry">\n'
        f"  {create_role_line(edu.school, edu.date)}"
        f'  <div class="degree">{esc(edu.degree)}</div>\n'
        "</div>\n"
    )


def create_chips(items: list) -> str:
    chips = "".join(f'<span class="chip">{esc(t)}</span>\n    ' for t in items)
    return f'<div class="chips">\n    {chips}</div>\n'


def create_bullet_list(items: list) -> str:
    lis = "".join(f"    <li>{esc(i)}</li>\n" for i in items)
    return f"  <ul>\n{lis}  </ul>\n"


def create_experience_block(exp: Experience, eyebrow: str = "") -> str:
    parts = []
    if eyebrow:
        parts.append(f'<div class="eyebrow">{esc(eyebrow)}</div>\n')
    parts.append(
        f"<h2>{esc(exp.company)} — {esc(exp.location)}</h2>\n"
    )
    parts.append(create_role_line(exp.role, exp.dates))
    if exp.intro:
        parts.append(f"<p>{esc(exp.intro)}</p>\n")
    for sub in exp.subsections:
        parts.append(f"<h4>{esc(sub.heading)}</h4>\n")
        parts.append(create_bullet_list(sub.bullets))
    return "".join(parts)


def create_pager_controls(slide_count: int) -> str:
    return (
        '<footer class="pager">\n'
        '  <button id="prev" aria-label="Previous page">&#8592;</button>\n'
        '  <div class="dots" id="dots"></div>\n'
        f'  <span class="count" id="count">1 / {slide_count}</span>\n'
        '  <button id="next" aria-label="Next page">&#8594;</button>\n'
        '  <span class="hint">use &#8592; &#8594; keys</span>\n'
        "</footer>\n"
    )


def create_slide_js() -> str:
    return """\
(function () {
  var slides = Array.prototype.slice.call(document.querySelectorAll('.slide'));
  var main = document.querySelector('main');
  var prevBtn = document.getElementById('prev');
  var nextBtn = document.getElementById('next');
  var countEl = document.getElementById('count');
  var dotsEl = document.getElementById('dots');
  var cur = 0;

  slides.forEach(function (s, i) {
    var dot = document.createElement('a');
    dot.className = 'dot';
    dot.href = '#' + s.id;
    dot.title = s.getAttribute('data-title');
    dot.setAttribute('aria-label', s.getAttribute('data-title'));
    dotsEl.appendChild(dot);
  });
  var dots = Array.prototype.slice.call(dotsEl.children);

  function show(i, updateHash) {
    cur = Math.max(0, Math.min(slides.length - 1, i));
    slides.forEach(function (s, idx) { s.classList.toggle('active', idx === cur); });
    dots.forEach(function (d, idx) { d.classList.toggle('active', idx === cur); });
    countEl.textContent = (cur + 1) + ' / ' + slides.length;
    prevBtn.disabled = cur === 0;
    nextBtn.disabled = cur === slides.length - 1;
    if (updateHash !== false) history.replaceState(null, '', '#' + slides[cur].id);
    main.scrollTop = 0;
  }

  function showFromHash() {
    var id = location.hash.slice(1);
    var i = slides.findIndex(function (s) { return s.id === id; });
    show(i >= 0 ? i : 0, false);
  }

  prevBtn.addEventListener('click', function () { show(cur - 1); });
  nextBtn.addEventListener('click', function () { show(cur + 1); });
  window.addEventListener('hashchange', showFromHash);
  document.addEventListener('keydown', function (e) {
    if (e.key === 'ArrowRight' || e.key === 'PageDown') show(cur + 1);
    else if (e.key === 'ArrowLeft' || e.key === 'PageUp') show(cur - 1);
    else if (e.key === 'Home') show(0);
    else if (e.key === 'End') show(slides.length - 1);
  });

  var touchX = null;
  main.addEventListener('touchstart', function (e) { touchX = e.changedTouches[0].clientX; }, { passive: true });
  main.addEventListener('touchend', function (e) {
    if (touchX === null) return;
    var dx = e.changedTouches[0].clientX - touchX;
    if (Math.abs(dx) > 60) show(cur + (dx < 0 ? 1 : -1));
    touchX = null;
  }, { passive: true });

  showFromHash();
})();"""


# ═══════════════════════════════════════════════════════════════
#  FPT base CSS (shared between slide & PDF)
# ═══════════════════════════════════════════════════════════════

def fpt_base_css(colors: dict) -> str:
    cv = css_vars_block(colors)
    return f"""{cv}

  * {{ margin: 0; padding: 0; box-sizing: border-box; }}

  body {{
    background: var(--fpt-bg);
    color: var(--fpt-text);
    font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
    font-size: 16px;
    line-height: 1.55;
  }}

  .brand-stripe {{ display: flex; height: 6px; }}
  .brand-stripe span {{ flex: 1; }}
  .brand-stripe .s-blue   {{ background: var(--fpt-dark-blue); }}
  .brand-stripe .s-orange {{ background: var(--fpt-orange); }}
  .brand-stripe .s-green  {{ background: var(--fpt-green); }}

  a {{ color: var(--fpt-dark-blue); text-decoration: none; border-bottom: 1px solid transparent; }}
  a:hover {{ color: var(--fpt-orange); border-bottom-color: var(--fpt-orange); }}

  .sep {{ color: var(--fpt-border); margin: 0 0.35rem; }}

  .eyebrow {{
    color: var(--fpt-orange);
    font-size: 0.8rem; font-weight: 700;
    letter-spacing: 0.12em; text-transform: uppercase;
    margin-bottom: 0.2rem;
  }}

  h2 {{
    color: var(--fpt-dark-blue);
    font-size: 1.45rem;
    padding-bottom: 0.25rem;
    border-bottom: 2px solid var(--fpt-orange);
    margin-bottom: 0.8rem;
  }}
  h2 + h2, section + section h2 {{ margin-top: 1.6rem; }}

  h4 {{
    color: var(--fpt-dark-blue);
    font-size: 1rem;
    margin: 0.9rem 0 0.2rem;
  }}

  p {{ margin: 0.35rem 0; }}
  ul {{ margin: 0.35rem 0 0.35rem 1.35rem; }}
  li {{ margin: 0.28rem 0; }}
  li::marker {{ color: var(--fpt-orange); }}
  li li::marker {{ color: var(--fpt-light-blue); }}

  .masthead {{
    display: flex; align-items: flex-start;
    justify-content: space-between; gap: 1.5rem;
    padding: 1rem 0 1.4rem; margin-bottom: 1.8rem;
    border-bottom: 3px solid var(--fpt-dark-blue);
  }}
  .masthead h1 {{ color: var(--fpt-dark-blue); font-size: 2.4rem; line-height: 1.15; }}
  .masthead .tagline {{ color: var(--fpt-gray); font-size: 1.1rem; margin-top: 0.15rem; }}
  .masthead .contact {{ margin-top: 0.8rem; font-size: 0.95rem; }}
  .masthead .contact div {{ margin-top: 0.15rem; }}
  .masthead img.logo {{ width: 130px; height: auto; flex-shrink: 0; margin-top: 0.4rem; }}

  .role-line {{
    display: flex; flex-wrap: wrap;
    justify-content: space-between; align-items: baseline;
    gap: 0.3rem 1rem;
  }}
  .role {{ font-weight: 600; }}
  .dates {{
    color: var(--fpt-bg); background: var(--fpt-green);
    font-size: 0.82rem; font-weight: 600;
    padding: 0.1rem 0.6rem; border-radius: 99px; white-space: nowrap;
  }}

  .chips {{ display: flex; flex-wrap: wrap; gap: 0.45rem; margin-top: 0.4rem; }}
  .chip {{
    border: 1.5px solid var(--fpt-light-blue);
    font-size: 0.88rem; padding: 0.18rem 0.7rem;
    border-radius: 99px; background: #fff;
  }}

  .edu-entry {{ margin-bottom: 0.6rem; }}
  .edu-entry .school {{ font-weight: 600; }}
  .edu-entry .degree {{ font-style: italic; color: var(--fpt-gray); }}

  @media (max-width: 640px) {{
    .masthead {{ flex-direction: column-reverse; }}
    .masthead img.logo {{ width: 92px; }}
    .masthead h1 {{ font-size: 1.9rem; }}
  }}

  @media print {{
    .dates {{ border: 1px solid var(--fpt-green); color: var(--fpt-green); background: #fff; }}
  }}"""


# ═══════════════════════════════════════════════════════════════
#  FPT Slide renderer
# ═══════════════════════════════════════════════════════════════

def fpt_slide_css(colors: dict) -> str:
    base = fpt_base_css(colors)
    return base + """

  html, body { height: 100%; }
  body { display: flex; flex-direction: column; }
  .brand-stripe { flex-shrink: 0; }

  .topbar {
    flex-shrink: 0; display: flex; align-items: center;
    gap: 1rem; padding: 0.6rem 1.4rem;
    border-bottom: 1px solid var(--fpt-border);
  }
  .topbar img { width: 56px; height: auto; }
  .topbar .who { line-height: 1.25; }
  .topbar .who strong { color: var(--fpt-dark-blue); font-size: 1.05rem; }
  .topbar .who span { display: block; color: var(--fpt-gray); font-size: 0.8rem; }
  .topbar nav { margin-left: auto; display: flex; flex-wrap: wrap; gap: 0.15rem 1rem; font-size: 0.9rem; }

  main { flex: 1; overflow-y: auto; scroll-behavior: smooth; }

  .slide {
    display: none; max-width: 860px; margin: 0 auto;
    padding: 2rem 2rem 2.5rem; animation: fadein 0.25s ease;
  }
  .slide.active { display: block; }
  @keyframes fadein { from { opacity: 0; transform: translateX(12px); } to { opacity: 1; transform: none; } }
  .slide section + section { margin-top: 1.8rem; }

  .pager {
    flex-shrink: 0; display: flex; align-items: center;
    justify-content: center; gap: 1rem; padding: 0.65rem 1rem;
    border-top: 1px solid var(--fpt-border);
  }
  .pager button {
    width: 42px; height: 42px; border-radius: 50%;
    border: 2px solid var(--fpt-dark-blue); background: #fff;
    color: var(--fpt-dark-blue); font-size: 1.25rem;
    line-height: 1; cursor: pointer; transition: all 0.15s;
  }
  .pager button:hover:not(:disabled) { border-color: var(--fpt-orange); color: #fff; background: var(--fpt-orange); }
  .pager button:disabled { border-color: var(--fpt-border); color: var(--fpt-border); cursor: default; }
  .dots { display: flex; gap: 0.5rem; }
  .dot {
    width: 12px; height: 12px; border-radius: 50%;
    border: 2px solid var(--fpt-light-blue); background: #fff; display: block;
  }
  .dot:hover { border-color: var(--fpt-orange); }
  .dot.active { background: var(--fpt-orange); border-color: var(--fpt-orange); }
  .count { font-size: 0.85rem; color: var(--fpt-gray); min-width: 3.2rem; text-align: center; }
  .hint { font-size: 0.75rem; color: var(--fpt-border); }

  @media (max-width: 640px) {
    .slide { padding: 1.3rem 1.1rem 2rem; }
    .topbar nav { display: none; }
    .dots { display: none; }
    .hint { display: none; }
  }

  @media print {
    body { display: block; }
    .topbar, .pager { display: none; }
    main { overflow: visible; }
    .slide { display: block; break-after: page; animation: none; }
  }"""


def _fpt_slide_topbar(data: ResumeData, logo_b64: str, tagline: str) -> str:
    nav_items = [
        ("about", "About"), ("education", "Education"),
        ("background", "Background"),
    ]
    for exp in data.experience:
        slug = exp.company.lower().replace(" ", "-")
        nav_items.append((f"exp-{slug}", exp.company))
    nav_items.append(("hobbies", "Hobbies"))

    links = " ".join(f'<a href="#{sid}">{esc(label)}</a>' for sid, label in nav_items)
    return (
        f'<header class="topbar">\n'
        f'  <img src="{logo_b64}" alt="FPT logo">\n'
        f'  <div class="who">\n'
        f"    <strong>{esc(data.name)}</strong>\n"
        f"    <span>{esc(tagline)}</span>\n"
        f"  </div>\n"
        f"  <nav>{links}</nav>\n"
        f"</header>\n"
    )


def render_fpt_slide(data: ResumeData, logo_b64: str, colors: dict) -> str:
    tagline = "C/C++ Developer"

    slides = []

    # Slide 1: masthead + objective
    slides.append(
        f'<section class="slide" id="about" data-title="{esc(data.name)} &amp; Objective">\n'
        f"{create_resume_title(data, logo_b64, tagline)}"
        f"{create_section('Objective', f'<p>{esc(data.objective)}</p>')}"
        f"</section>\n"
    )

    # Slide 2: education + certifications
    edu_html = "".join(create_edu_entry(e) for e in data.education)
    cert_html = create_bullet_list(data.certifications)
    slides.append(
        '<section class="slide" id="education" data-title="Education &amp; Certifications">\n'
        f"{create_section('Education', edu_html)}"
        f"{create_section('Certifications', cert_html)}"
        "</section>\n"
    )

    # Slide 3: projects (if present)
    if data.projects:
        proj_html = create_bullet_list(data.projects)
        slides.append(
            '<section class="slide" id="projects" data-title="Projects &amp; Awards">\n'
            f"{create_section('Individual Projects &amp; Award', proj_html)}"
            "</section>\n"
        )

    # Slide 4: background + tools
    bg_items = "".join(
        f"    <li><strong>{esc(d)}:</strong> {esc(desc)}</li>\n"
        for d, desc in data.background
    )
    bg_html = f"  <ul>\n{bg_items}  </ul>\n"
    tools_html = create_chips(data.tools)
    slides.append(
        '<section class="slide" id="background" data-title="Background &amp; Software Tools">\n'
        f"{create_section('Domain-Specific Background', bg_html)}"
        f"{create_section('Software Tools', tools_html)}"
        "</section>\n"
    )

    # Experience slides
    for exp in data.experience:
        slug = exp.company.lower().replace(" ", "-")
        slides.append(
            f'<section class="slide" id="exp-{esc(slug)}" data-title="{esc(exp.company)}">\n'
            f"{create_experience_block(exp, 'Professional Experience')}"
            "</section>\n"
        )

    # Hobbies slide
    hobby_html = create_bullet_list(data.hobbies)
    slides.append(
        '<section class="slide" id="hobbies" data-title="Hobbies and Other Activities">\n'
        f"{create_section('Hobbies and Other Activities', hobby_html)}"
        "</section>\n"
    )

    body = (
        create_brand_stripe()
        + _fpt_slide_topbar(data, logo_b64, tagline)
        + "\n<main>\n\n"
        + "\n".join(slides)
        + "\n</main>\n\n"
        + create_pager_controls(len(slides))
    )

    return html_document(
        title=f"{data.name} — Resume",
        favicon=logo_b64,
        style=fpt_slide_css(colors),
        body=body,
        script=create_slide_js(),
    )


# ═══════════════════════════════════════════════════════════════
#  FPT PDF renderer (scrollable single-page)
# ═══════════════════════════════════════════════════════════════

def fpt_pdf_css(colors: dict) -> str:
    base = fpt_base_css(colors)
    return base + """

  html { scroll-behavior: smooth; }

  .page { max-width: 900px; margin: 0 auto; padding: 2.2rem 2rem 3rem; }

  section { margin-bottom: 1.9rem; }

  h3 { color: var(--fpt-dark-blue); font-size: 1.1rem; margin: 1.1rem 0 0.2rem; }
  section > h3:first-of-type { margin-top: 0.2rem; }

  strong { color: inherit; }

  footer {
    border-top: 1px solid var(--fpt-border);
    margin-top: 2.5rem; padding-top: 0.8rem;
    font-size: 0.85rem; color: var(--fpt-gray);
    display: flex; justify-content: space-between;
    align-items: center; gap: 1rem;
  }
  footer img { width: 54px; height: auto; }

  @media (max-width: 640px) { .page { padding: 1.4rem 1.1rem 2rem; } }

  @media print {
    .page { max-width: none; padding: 0; }
    body { font-size: 11pt; }
    h2, h3, h4 { break-after: avoid; }
    .role-line, .edu-entry, li li { break-inside: avoid; }
    footer { margin-top: 1rem; }
  }"""


def render_fpt_pdf(data: ResumeData, logo_b64: str, colors: dict) -> str:
    tagline = "C/C++ Developer"

    sections = []

    sections.append(create_section("Objective", f"<p>{esc(data.objective)}</p>"))

    edu_html = "".join(create_edu_entry(e) for e in data.education)
    sections.append(create_section("Education", edu_html))
    sections.append(create_section("Certifications", create_bullet_list(data.certifications)))

    if data.projects:
        sections.append(
            create_section("Individual Projects &amp; Award", create_bullet_list(data.projects))
        )

    bg_items = "".join(
        f"    <li><strong>{esc(d)}:</strong> {esc(desc)}</li>\n"
        for d, desc in data.background
    )
    sections.append(create_section("Domain-Specific Background", f"  <ul>\n{bg_items}  </ul>\n"))
    sections.append(create_section("Software Tools", create_chips(data.tools)))

    # Experience
    exp_parts = []
    for exp in data.experience:
        exp_parts.append(f"<h3>{esc(exp.company)} — {esc(exp.location)}</h3>\n")
        exp_parts.append(create_role_line(exp.role, exp.dates))
        if exp.intro:
            exp_parts.append(f"<p>{esc(exp.intro)}</p>\n")
        for sub in exp.subsections:
            exp_parts.append(f"<h4>{esc(sub.heading)}</h4>\n")
            exp_parts.append(create_bullet_list(sub.bullets))
    sections.append(create_section("Professional Experience", "".join(exp_parts)))

    sections.append(
        create_section("Hobbies and Other Activities", create_bullet_list(data.hobbies))
    )

    body = (
        create_brand_stripe()
        + '\n<div class="page">\n\n'
        + f"  <header class=\"masthead\">\n"
        + f"    <div>\n"
        + f"      <h1>{esc(data.name)}</h1>\n"
        + f'      <div class="tagline">{esc(tagline)}</div>\n'
        + f'      <div class="contact">\n'
        + f"        <div>{esc(data.location)}</div>\n"
        + f'        <div>Phone: {esc(data.phone)} <span class="sep">|</span> '
        + f'Email: <a href="mailto:{esc(data.email)}">{esc(data.email)}</a></div>\n'
        + f"        <div>\n"
    )
    for label, url in data.links:
        body += f'          <a href="{esc(url)}">{esc(label)}</a><span class="sep">|</span>\n'
    body += (
        f"        </div>\n"
        + f"      </div>\n"
        + f"    </div>\n"
        + f'    <img class="logo" src="{logo_b64}" alt="FPT logo">\n'
        + f"  </header>\n\n"
        + "".join(f"  {s}" for s in sections)
        + f'\n  <footer>\n    <span>Generated from Minh_Resume_for_web.md</span>\n'
        + f'    <img src="{logo_b64}" alt="FPT logo">\n  </footer>\n\n'
        + "</div>\n"
    )

    return html_document(
        title=f"{data.name} — {tagline}",
        favicon=logo_b64,
        style=fpt_pdf_css(colors),
        body=body,
    )


# ═══════════════════════════════════════════════════════════════
#  Vintage slide renderer
# ═══════════════════════════════════════════════════════════════

VINTAGE_CSS = """\
  :root {
    --paper: #E9E0C8; --paper-2: #E1D5B4; --paper-3: #F1EAD7;
    --ink: #26221A; --ink-soft: #5A5241;
    --teal: #23564F; --teal-deep: #173A34;
    --gold: #B4822A; --rust: #9E4526;
    --line: #B9AC86; --shadow: rgba(38, 34, 26, .16);
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  html, body { height: 100%; }
  body {
    background: var(--teal-deep); color: var(--ink);
    font-family: "IBM Plex Sans", system-ui, sans-serif;
    -webkit-font-smoothing: antialiased; overflow: hidden;
  }

  .deck { position: fixed; inset: 0; }
  .slide {
    position: absolute; inset: 0; display: none;
    padding: clamp(24px,4.2vw,64px) clamp(26px,5vw,84px);
    background: radial-gradient(120% 130% at 12% 0%, #EFE7D0 0%, var(--paper) 42%, #E3D8BC 100%);
    animation: fade .5s ease both;
  }
  .slide.active { display: flex; flex-direction: column; }
  @keyframes fade { from { opacity:0; transform:translateY(6px); } to { opacity:1; transform:none; } }
  @media (prefers-reduced-motion:reduce) { .slide { animation:none; } }

  .slide::before {
    content: ""; position: absolute; inset: 0; pointer-events: none;
    background-image: linear-gradient(var(--line) 1px, transparent 1px),
                      linear-gradient(90deg, var(--line) 1px, transparent 1px);
    background-size: 44px 44px; opacity: .10;
    mask-image: radial-gradient(130% 120% at 80% 20%, #000 40%, transparent 92%);
    -webkit-mask-image: radial-gradient(130% 120% at 80% 20%, #000 40%, transparent 92%);
  }
  .slide::after {
    content: ""; position: absolute; inset: clamp(14px,2vw,30px);
    pointer-events: none; border: 1px solid transparent;
    background:
      linear-gradient(var(--teal),var(--teal)) top left/16px 1px no-repeat,
      linear-gradient(var(--teal),var(--teal)) top left/1px 16px no-repeat,
      linear-gradient(var(--teal),var(--teal)) top right/16px 1px no-repeat,
      linear-gradient(var(--teal),var(--teal)) top right/1px 16px no-repeat,
      linear-gradient(var(--teal),var(--teal)) bottom left/16px 1px no-repeat,
      linear-gradient(var(--teal),var(--teal)) bottom left/1px 16px no-repeat,
      linear-gradient(var(--teal),var(--teal)) bottom right/16px 1px no-repeat,
      linear-gradient(var(--teal),var(--teal)) bottom right/1px 16px no-repeat;
    opacity: .55;
  }
  .slide>* { position: relative; z-index: 2; }

  .top {
    display: flex; justify-content: space-between; align-items: flex-start;
    gap: 16px; flex: 0 0 auto;
    border-bottom: 1.5px solid var(--ink);
    padding-bottom: clamp(8px,1.1vw,14px);
  }
  .eyebrow {
    font-family: "IBM Plex Mono", monospace;
    font-size: clamp(9px,1.02vw,12.5px);
    letter-spacing: .24em; text-transform: uppercase;
    color: var(--teal); font-weight: 600;
    display: flex; align-items: center; gap: .7em;
  }
  .eyebrow .tick { width: 26px; height: 2px; background: var(--gold); display: inline-block; }
  .idx {
    font-family: "IBM Plex Mono", monospace;
    font-size: clamp(9px,1.02vw,12.5px);
    letter-spacing: .18em; color: var(--ink-soft);
    white-space: nowrap; text-align: right;
  }
  .idx b { color: var(--ink); }

  .h-sec {
    font-family: "Zilla Slab", serif; font-weight: 700;
    font-size: clamp(24px,3.9vw,50px);
    line-height: 1.02; letter-spacing: -.01em; color: var(--ink);
    margin-top: clamp(12px,1.8vw,26px); flex: 0 0 auto;
  }
  .h-sec .amp { color: var(--rust); }
  .sub {
    font-family: "IBM Plex Mono", monospace;
    font-size: clamp(10px,1.12vw,14px); color: var(--ink-soft);
    letter-spacing: .04em; margin-top: 6px;
  }

  .body { flex: 1 1 auto; display: flex; min-height: 0; margin-top: clamp(14px,2vw,30px); }

  .title-wrap { flex: 1 1 auto; display: flex; flex-direction: column; justify-content: center; }
  .kicker {
    font-family: "IBM Plex Mono", monospace; font-weight: 600;
    font-size: clamp(10px,1.25vw,15px); letter-spacing: .28em;
    text-transform: uppercase; color: var(--teal);
    margin-bottom: clamp(10px,1.5vw,18px);
    display: flex; align-items: center; gap: .8em; flex-wrap: wrap;
  }
  .kicker .dot { width: 7px; height: 7px; background: var(--gold); border-radius: 50%; }
  .name {
    font-family: "Zilla Slab", serif; font-weight: 700;
    font-size: clamp(46px,10.5vw,138px); line-height: .9;
    letter-spacing: -.02em; color: var(--ink);
  }
  .name .last { color: var(--teal); }
  .rule-lg {
    height: 3px; background: var(--ink);
    margin: clamp(16px,2.4vw,32px) 0; width: min(560px,70%);
    position: relative;
  }
  .rule-lg::after {
    content: ""; position: absolute; right: -1px; top: -4px;
    width: 11px; height: 11px; background: var(--gold); transform: rotate(45deg);
  }
  .lede {
    font-family: "Zilla Slab", serif; font-weight: 500;
    font-size: clamp(17px,2.55vw,32px); line-height: 1.3;
    color: var(--ink); max-width: 20ch;
  }
  .lede em { font-style: normal; color: var(--rust); }
  .contact {
    margin-top: clamp(22px,3.4vw,44px);
    display: flex; flex-wrap: wrap;
    gap: clamp(8px,1.2vw,16px) clamp(14px,2.2vw,30px);
    font-family: "IBM Plex Mono", monospace;
    font-size: clamp(10px,1.12vw,13.5px);
    color: var(--ink); letter-spacing: .02em;
  }
  .contact span { display: flex; align-items: center; gap: .55em; }
  .contact span::before { content: ""; width: 5px; height: 5px; background: var(--teal); flex: 0 0 auto; }

  .col { flex: 1 1 0; min-width: 0; display: flex; flex-direction: column; gap: clamp(10px,1.4vw,18px); }
  .cols-2 { display: grid; grid-template-columns: 1fr 1fr; gap: clamp(24px,3.6vw,58px); width: 100%; }
  .col-title {
    font-family: "IBM Plex Mono", monospace; font-weight: 600;
    font-size: clamp(10px,1.05vw,13px); letter-spacing: .18em;
    text-transform: uppercase; color: var(--teal);
    padding-bottom: 6px; border-bottom: 1px solid var(--line);
  }

  ul.items { list-style: none; display: flex; flex-direction: column; gap: clamp(9px,1.15vw,15px); }
  ul.items li {
    position: relative; padding-left: 1.5em;
    font-size: clamp(12.5px,1.42vw,18px); line-height: 1.4; color: var(--ink);
  }
  ul.items li::before {
    content: ""; position: absolute; left: 0; top: .5em;
    width: 8px; height: 8px; background: var(--gold); transform: rotate(45deg);
  }
  ul.items li b { font-weight: 700; color: var(--teal-deep); }
  ul.items li .n { color: var(--ink-soft); }

  .tags { display: flex; flex-wrap: wrap; gap: clamp(8px,1.1vw,13px); align-content: flex-start; }
  .tag {
    font-family: "IBM Plex Mono", monospace; font-weight: 500;
    font-size: clamp(11px,1.28vw,16px);
    padding: .5em .85em; border: 1.5px solid var(--ink);
    background: var(--paper-3); color: var(--ink);
    white-space: nowrap; box-shadow: 3px 3px 0 var(--shadow);
  }
  .tag.hi { background: var(--teal); color: var(--paper); border-color: var(--teal); }

  .domain { display: flex; flex-direction: column; gap: clamp(11px,1.5vw,19px); }
  .drow { display: flex; gap: clamp(12px,1.6vw,22px); align-items: baseline; }
  .dlabel {
    flex: 0 0 clamp(120px,15vw,210px);
    font-family: "Zilla Slab", serif; font-weight: 600;
    font-size: clamp(14px,1.7vw,22px); color: var(--teal-deep); line-height: 1.15;
  }
  .dtext { font-size: clamp(12px,1.38vw,17px); line-height: 1.4; color: var(--ink); }

  .job-head {
    display: flex; justify-content: space-between; align-items: baseline;
    gap: 14px; flex-wrap: wrap;
    border-bottom: 1px solid var(--line);
    padding-bottom: 6px; margin-bottom: clamp(8px,1vw,12px);
  }
  .job-co {
    font-family: "Zilla Slab", serif; font-weight: 700;
    font-size: clamp(16px,2vw,27px); color: var(--ink); line-height: 1.05;
  }
  .job-co .loc { font-family: "IBM Plex Sans"; font-weight: 400; font-size: .62em; color: var(--ink-soft); }
  .job-role {
    font-family: "IBM Plex Mono", monospace;
    font-size: clamp(10px,1.12vw,14px); color: var(--teal);
    font-weight: 600; margin-top: 3px; letter-spacing: .03em;
  }
  .job-date {
    font-family: "IBM Plex Mono", monospace;
    font-size: clamp(10px,1.1vw,13.5px); color: var(--rust);
    font-weight: 600; letter-spacing: .06em; white-space: nowrap;
  }
  .mini-title {
    font-family: "IBM Plex Mono", monospace; font-weight: 600;
    font-size: clamp(9.5px,1vw,12px); letter-spacing: .16em;
    text-transform: uppercase; color: var(--ink-soft); margin-bottom: 7px;
  }

  ul.tight { list-style: none; display: flex; flex-direction: column; gap: clamp(6px,.8vw,11px); }
  ul.tight li {
    position: relative; padding-left: 1.15em;
    font-size: clamp(11px,1.24vw,15.5px); line-height: 1.34; color: var(--ink);
  }
  ul.tight li::before {
    content: ""; position: absolute; left: 0; top: .5em;
    width: 6px; height: 6px; background: var(--teal); transform: rotate(45deg);
  }
  ul.tight li b { color: var(--teal-deep); font-weight: 700; }

  .stack { display: flex; flex-direction: column; gap: clamp(16px,2.1vw,30px); width: 100%; }

  .thanks { flex: 1 1 auto; display: flex; flex-direction: column; justify-content: center; }
  .thanks .big {
    font-family: "Zilla Slab", serif; font-weight: 700;
    font-size: clamp(34px,6.5vw,86px); line-height: .95;
    color: var(--ink); letter-spacing: -.02em;
  }
  .thanks .big em { font-style: normal; color: var(--teal); }
  .blog {
    margin-top: clamp(16px,2vw,26px);
    font-family: "IBM Plex Mono", monospace;
    font-size: clamp(12px,1.4vw,17px); color: var(--ink);
  }
  .blog a { color: var(--rust); text-decoration: none; border-bottom: 2px solid var(--gold); }

  .footer {
    position: fixed; left: 0; right: 0; bottom: 0; z-index: 40;
    display: flex; justify-content: space-between; align-items: center;
    padding: 10px clamp(20px,4vw,54px);
    font-family: "IBM Plex Mono", monospace;
    font-size: 11px; letter-spacing: .14em;
    color: var(--paper); pointer-events: none;
  }
  .footer .brand { opacity: .72; text-transform: uppercase; }
  .navbtns { display: flex; gap: 8px; pointer-events: auto; }
  .navbtns button {
    font-family: "IBM Plex Mono", monospace; font-size: 12px;
    background: transparent; color: var(--paper);
    border: 1.5px solid rgba(233,224,200,.5);
    width: 34px; height: 30px; cursor: pointer; transition: .15s; letter-spacing: 0;
  }
  .navbtns button:hover { background: var(--gold); border-color: var(--gold); color: #241d08; }
  .navbtns button:focus-visible { outline: 2px solid var(--gold); outline-offset: 2px; }
  .counter { pointer-events: none; }
  .counter b { color: var(--gold); }

  .progress { position: fixed; top: 0; left: 0; height: 3px; background: var(--gold); z-index: 50; transition: width .35s ease; }

  .dots {
    position: fixed; bottom: 46px; left: 50%; transform: translateX(-50%);
    z-index: 40; display: flex; gap: 9px; pointer-events: auto;
  }
  .dots button {
    width: 9px; height: 9px; border-radius: 50%;
    border: 1.4px solid rgba(233,224,200,.55);
    background: transparent; padding: 0; cursor: pointer; transition: .15s;
  }
  .dots button.on { background: var(--gold); border-color: var(--gold); transform: scale(1.15); }
  .dots button:focus-visible { outline: 2px solid var(--gold); outline-offset: 2px; }

  .hint {
    position: fixed; bottom: 44px; right: clamp(20px,4vw,54px); z-index: 40;
    font-family: "IBM Plex Mono", monospace;
    font-size: 10px; letter-spacing: .12em;
    color: var(--paper); opacity: .5; text-transform: uppercase;
  }

  @media (max-width:720px) {
    .cols-2 { grid-template-columns: 1fr; gap: clamp(14px,4vw,22px); }
    .body { overflow-y: auto; }
    .dlabel { flex-basis: 110px; }
    .hint { display: none; }
  }"""


def _vintage_slide_top(eyebrow_text: str, sec_num: int, total: int) -> str:
    n = str(sec_num).zfill(2)
    t = str(total).zfill(2)
    return (
        '<div class="top">\n'
        f'  <div class="eyebrow"><span class="tick"></span>{esc(eyebrow_text)}</div>\n'
        f'  <div class="idx">SEC <b>{n}</b> / {t}</div>\n'
        "</div>\n"
    )


def _vintage_job(exp: Experience) -> str:
    bullets = ""
    for sub in exp.subsections:
        for b in sub.bullets:
            bullets += f"  <li>{esc(b)}</li>\n"
    return (
        "<div>\n"
        '  <div class="job-head">\n'
        "    <div>\n"
        f'      <div class="job-co">{esc(exp.company)} '
        f'<span class="loc">— {esc(exp.location)}</span></div>\n'
        f'      <div class="job-role">{esc(exp.role)}</div>\n'
        "    </div>\n"
        f'    <div class="job-date">{esc(exp.dates)}</div>\n'
        "  </div>\n"
        f'  <ul class="tight">\n{bullets}  </ul>\n'
        "</div>\n"
    )


def render_vintage_slide(data: ResumeData) -> str:
    parts = data.name.split()
    first = parts[0] if parts else ""
    last = " ".join(parts[1:]) if len(parts) > 1 else ""

    slides = []
    total = 0

    # Count slides first
    total_slides = 5  # title, edu, background, tools, closing
    if data.projects:
        total_slides += 1
    exp_groups = []
    exps = list(data.experience)
    while exps:
        if len(exps) >= 2 and len(exps) != 3:
            exp_groups.append(exps[:2])
            exps = exps[2:]
        else:
            exp_groups.append([exps[0]])
            exps = exps[1:]
    total_slides += len(exp_groups)
    total = total_slides

    # 1: title
    contact_spans = [
        f"<span>{esc(data.location)}</span>",
        f"<span>{esc(data.phone)}</span>",
        f"<span>{esc(data.email)}</span>",
    ]
    for label, url in data.links:
        short = url.replace("https://", "").replace("http://", "").rstrip("/")
        if "linkedin" in url:
            short = "in/" + short.split("/in/")[-1].rstrip("/")
        elif "github" in url:
            short = "github.com/" + short.split("github.com/")[-1].rstrip("/")
        contact_spans.append(f"<span>{esc(short)}</span>")

    slides.append(
        '<section class="slide active">\n'
        '  <div class="title-wrap">\n'
        '    <div class="kicker">C / C++ <span class="dot"></span> Embedded Systems</div>\n'
        f'    <h1 class="name">{esc(first).upper()} <span class="last">{esc(last).upper()}</span></h1>\n'
        '    <div class="rule-lg"></div>\n'
        f'    <p class="lede">{esc(data.objective)}</p>\n'
        f'    <div class="contact">\n      {"".join(contact_spans)}\n    </div>\n'
        "  </div>\n"
        "</section>\n"
    )

    sec = 2

    # 2: education + certs
    edu_items = ""
    for e in data.education:
        edu_items += (
            f'  <li><b>{esc(e.degree)}</b><br>{esc(e.school)} '
            f'<span class="n">&middot; {esc(e.date)}</span></li>\n'
        )
    cert_items = ""
    for c in data.certifications:
        cert_items += f"  <li><b>{esc(c)}</b></li>\n"

    slides.append(
        '<section class="slide">\n'
        f"{_vintage_slide_top('Foundations', sec, total)}"
        '<h2 class="h-sec">Education <span class="amp">&amp;</span> Certifications</h2>\n'
        '<div class="body">\n'
        '  <div class="cols-2">\n'
        '    <div class="col">\n'
        '      <div class="col-title">Education</div>\n'
        f'      <ul class="items">\n{edu_items}      </ul>\n'
        "    </div>\n"
        '    <div class="col">\n'
        '      <div class="col-title">Certifications</div>\n'
        f'      <ul class="items">\n{cert_items}      </ul>\n'
        "    </div>\n"
        "  </div>\n"
        "</div>\n"
        "</section>\n"
    )
    sec += 1

    # Projects (optional)
    if data.projects:
        proj_items = ""
        for p in data.projects:
            proj_items += f"  <li>{esc(p)}</li>\n"
        slides.append(
            '<section class="slide">\n'
            f"{_vintage_slide_top('Achievements', sec, total)}"
            '<h2 class="h-sec">Projects <span class="amp">&amp;</span> Awards</h2>\n'
            '<div class="body">\n'
            f'  <ul class="items" style="justify-content:center;gap:clamp(14px,2vw,26px);">'
            f'\n{proj_items}  </ul>\n'
            "</div>\n"
            "</section>\n"
        )
        sec += 1

    # Background
    domain_rows = ""
    for d, desc in data.background:
        domain_rows += (
            '    <div class="drow">\n'
            f'      <div class="dlabel">{esc(d)}</div>\n'
            f'      <div class="dtext">{esc(desc)}</div>\n'
            "    </div>\n"
        )
    slides.append(
        '<section class="slide">\n'
        f"{_vintage_slide_top('Expertise', sec, total)}"
        '<h2 class="h-sec">Domain-Specific Background</h2>\n'
        '<div class="body">\n'
        f'  <div class="domain">\n{domain_rows}  </div>\n'
        "</div>\n"
        "</section>\n"
    )
    sec += 1

    # Tools
    tags = ""
    highlight = {"C/C++", "Rust", "C++ 17"}
    for t in data.tools:
        cls = "tag"
        for h in highlight:
            if h.lower() in t.lower():
                cls = "tag hi"
                break
        tags += f'    <span class="{cls}">{esc(t)}</span>\n'

    slides.append(
        '<section class="slide">\n'
        f"{_vintage_slide_top('Toolchain', sec, total)}"
        '<h2 class="h-sec">Software Tools</h2>\n'
        '<p class="sub">Languages, frameworks &amp; instruments in active use</p>\n'
        '<div class="body">\n'
        f'  <div class="tags" style="align-content:center;">\n{tags}  </div>\n'
        "</div>\n"
        "</section>\n"
    )
    sec += 1

    # Experience slides
    for group in exp_groups:
        content = '<div class="body" style="margin-top:clamp(10px,1.4vw,20px);">\n'
        if len(group) > 1:
            content += '  <div class="stack">\n'
        for exp in group:
            content += _vintage_job(exp)
        if len(group) > 1:
            content += "  </div>\n"
        content += "</div>\n"

        slides.append(
            '<section class="slide">\n'
            f"{_vintage_slide_top('Professional Experience', sec, total)}"
            f"{content}"
            "</section>\n"
        )
        sec += 1

    # Closing slide
    hobby_links = ""
    for h in data.hobbies:
        m = re.match(r"(.+?)\[(.+?)\]\((.+?)\)", h)
        if m:
            hobby_links = f'<a href="{esc(m.group(3))}">{esc(m.group(2))}</a>'
        else:
            m2 = re.search(r"\(([^)]+)\)", h)
            if m2:
                hobby_links = f'<a href="{esc(m2.group(1))}">{esc(m2.group(1))}</a>'

    contact_bottom = "".join(
        f"<span>{esc(s)}</span>"
        for s in [data.name, data.email, data.phone]
    )

    slides.append(
        '<section class="slide">\n'
        f"{_vintage_slide_top('Beyond Work', sec, total)}"
        '<h2 class="h-sec">Hobbies &amp; Other Activities</h2>\n'
        '<div class="thanks">\n'
        '  <div class="big">Let&rsquo;s build something <em>reliable.</em></div>\n'
        f'  <div class="blog">Writing technical blogs &rarr; {hobby_links}</div>\n'
        f'  <div class="contact" style="margin-top:clamp(20px,2.6vw,34px);">\n    {contact_bottom}\n  </div>\n'
        "</div>\n"
        "</section>\n"
    )

    deck = '<div class="deck" id="deck">\n' + "\n".join(slides) + "</div>\n"

    footer = (
        '<div class="dots" id="dots"></div>\n'
        '<div class="footer">\n'
        f'  <div class="brand">{esc(data.name)} &middot; Engineering Dossier</div>\n'
        f'  <div class="counter">SLIDE <b id="cur">01</b> / <span id="tot">{str(total).zfill(2)}</span></div>\n'
        '  <div class="navbtns">\n'
        '    <button id="prev" aria-label="Previous slide">&larr;</button>\n'
        '    <button id="next" aria-label="Next slide">&rarr;</button>\n'
        "  </div>\n"
        "</div>\n"
        '<div class="hint">&larr; &rarr; to navigate</div>\n'
    )

    js = """\
const slides = [...document.querySelectorAll('.slide')];
const total = slides.length;
let i = 0;
const cur = document.getElementById('cur');
const progress = document.getElementById('progress');
const dotsWrap = document.getElementById('dots');
document.getElementById('tot').textContent = String(total).padStart(2, '0');

slides.forEach((_, n) => {
  const b = document.createElement('button');
  b.setAttribute('aria-label', 'Go to slide ' + (n + 1));
  b.addEventListener('click', () => go(n));
  dotsWrap.appendChild(b);
});
const dots = [...dotsWrap.children];

function go(n) {
  i = (n + total) % total;
  slides.forEach((s, k) => s.classList.toggle('active', k === i));
  dots.forEach((d, k) => d.classList.toggle('on', k === i));
  cur.textContent = String(i + 1).padStart(2, '0');
  progress.style.width = ((i + 1) / total * 100) + '%';
}
const next = () => go(i + 1), prev = () => go(i - 1);
document.getElementById('next').addEventListener('click', next);
document.getElementById('prev').addEventListener('click', prev);
window.addEventListener('keydown', e => {
  if (e.key === 'ArrowRight' || e.key === 'PageDown' || e.key === ' ') { e.preventDefault(); next(); }
  else if (e.key === 'ArrowLeft' || e.key === 'PageUp') { e.preventDefault(); prev(); }
  else if (e.key === 'Home') { go(0); } else if (e.key === 'End') { go(total - 1); }
});
let x0 = null;
window.addEventListener('touchstart', e => x0 = e.touches[0].clientX, { passive: true });
window.addEventListener('touchend', e => {
  if (x0 === null) return; const dx = e.changedTouches[0].clientX - x0;
  if (Math.abs(dx) > 45) { dx < 0 ? next() : prev(); } x0 = null;
}, { passive: true });
go(0);"""

    fonts_link = (
        '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        '<link href="https://fonts.googleapis.com/css2?family=Zilla+Slab:wght@400;500;600;700'
        '&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600'
        '&display=swap" rel="stylesheet">\n'
    )

    return (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f'<title>{esc(data.name)} — Engineering Dossier</title>\n'
        f'{fonts_link}'
        f'<style>\n{VINTAGE_CSS}\n</style>\n'
        '</head>\n<body>\n'
        '<div class="progress" id="progress"></div>\n'
        f'{deck}\n{footer}\n'
        f'<script>\n{js}\n</script>\n'
        '</body>\n</html>\n'
    )


# ═══════════════════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════════════════

OUTPUT_MAP = {
    "resume-fpt-slide": "resume-fpt-slides.html",
    "resume-fpt-pdf": "resume-fpt-style.html",
    "resume-vintage-slide": "resume-vintage-style.html",
}


def main():
    parser = argparse.ArgumentParser(
        description="Generate HTML resumes from Minh_Resume_for_web.md"
    )
    parser.add_argument(
        "format",
        choices=list(OUTPUT_MAP.keys()),
        help="Output format to generate",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent.parent
    md_path = root / "doc" / "resume" / "Minh_Resume_for_web.md"
    assets_dir = Path(__file__).resolve().parent / "assets"
    theme_path = assets_dir / "fpt-theme-colors.md"
    logo_path = assets_dir / "fpt-logo.png"
    out_dir = root / "doc" / "resume"

    if not md_path.exists():
        print(f"Error: {md_path} not found", file=sys.stderr)
        sys.exit(1)

    data = parse_resume(md_path)

    if args.format in ("resume-fpt-slide", "resume-fpt-pdf"):
        if not theme_path.exists():
            print(f"Error: {theme_path} not found", file=sys.stderr)
            sys.exit(1)
        if not logo_path.exists():
            print(f"Error: {logo_path} not found", file=sys.stderr)
            sys.exit(1)

        colors = parse_theme_colors(theme_path)
        logo_b64 = load_logo_b64(logo_path)

        if args.format == "resume-fpt-slide":
            html = render_fpt_slide(data, logo_b64, colors)
        else:
            html = render_fpt_pdf(data, logo_b64, colors)
    else:
        html = render_vintage_slide(data)

    out_file = out_dir / OUTPUT_MAP[args.format]
    out_file.write_text(html, encoding="utf-8")
    print(f"Written: {out_file}")


if __name__ == "__main__":
    main()
