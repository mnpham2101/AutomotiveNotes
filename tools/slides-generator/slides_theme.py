"""Visual theme for the HTML slide builder.

Edit this file to change colours, fonts, spacing, or slide behaviour.
CSS custom properties in :root are the primary tuning knobs.
"""

# ---------------------------------------------------------------------------
# Colour tokens and global styles
# ---------------------------------------------------------------------------
CSS = """
:root {
  /* --- brand colours --- */
  --ink:          #263238;
  --ink-2:        #37474f;
  --muted:        #607d8b;
  --faint:        #90a4ae;
  --rule:         #b0bec5;
  --rule-soft:    #cfd8dc;
  --wash:         #eceff1;
  --page:         #f7f9fb;
  --navy:         #14337a;
  --blue:         #1565c0;
  --blue-wash:    #e3f2fd;
  --accent:       #f26f21;
  --accent-dark:  #e65100;
  --accent-wash:  #fff3e0;
  --green:        #2e7d32;
  --green-wash:   #e8f5e9;
  --red:          #c62828;

  /* --- typography --- */
  --font: "DejaVu Sans", Verdana, Geneva, sans-serif;
  --mono: "DejaVu Sans Mono", Consolas, monospace;
}

/* ------------------------------------------------------------------ reset */
* { box-sizing: border-box }
html, body { margin: 0; padding: 0 }
/* sidebar links are plain anchors; without this they jump instead of gliding */
html { scroll-behavior: smooth }
@media (prefers-reduced-motion: reduce) { html { scroll-behavior: auto } }
body {
  background: var(--wash);
  color: var(--ink);
  font-family: var(--font);
  font-size: 16px;
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
}

/* ------------------------------------------------------------------ shell */
.shell {
  display: grid;
  grid-template-columns: 264px 1fr;
  min-height: 100vh;
}

/* ------------------------------------------------------------------- nav  */
nav {
  background: var(--ink);
  color: #fff;
  padding: 26px 0 40px;
  position: sticky;
  top: 0;
  height: 100vh;
  overflow-y: auto;
}
nav .brand {
  padding: 0 22px 18px;
  border-bottom: 1px solid rgba(255,255,255,.14);
  margin-bottom: 14px;
}
nav .brand b   { display: block; font-size: 15px; line-height: 1.35 }
nav .brand span { display: block; color: var(--faint); font-size: 11.5px; margin-top: 6px }
nav .grp {
  color: var(--accent);
  font-size: 10.5px;
  letter-spacing: .10em;
  text-transform: uppercase;
  padding: 16px 22px 6px;
  font-weight: 700;
}
nav a {
  display: block;
  color: #cfd8dc;
  text-decoration: none;
  font-size: 13px;
  padding: 6px 22px 6px 26px;
  border-left: 3px solid transparent;
}
nav a:hover { color: #fff; background: rgba(255,255,255,.06) }
nav a.on    { color: #fff; border-left-color: var(--accent); background: rgba(242,111,33,.14) }

main { padding: 0 }
.rail { position: fixed; top: 0; left: 264px; right: 0; height: 3px; background: transparent; z-index: 20 }
.rail i { display: block; height: 100%; width: 0; background: var(--accent) }

/* ----------------------------------------------------------------- slides */
.slide {
  min-height: 100vh;
  padding: 64px 76px 92px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  background: var(--page);
  border-bottom: 1px solid var(--rule-soft);
  position: relative;
  scroll-margin-top: 0;
}
.slide-inner { max-width: 1080px; width: 100%; margin: 0 auto }

.slide h2 {
  margin: 0 0 30px;
  font-size: 34px;
  line-height: 1.2;
  color: var(--navy);
  font-weight: 700;
  letter-spacing: -.01em;
}
.slide h2::after {
  content: "";
  display: block;
  width: 64px;
  height: 4px;
  background: var(--accent);
  margin-top: 16px;
  border-radius: 2px;
}

/* bullet lists */
.slide ul { margin: 0; padding-left: 0; list-style: none }
.slide li {
  position: relative;
  padding: 0 0 0 30px;
  margin: 0 0 14px;
  font-size: 19px;
  line-height: 1.5;
}
.slide li::before {
  content: "";
  position: absolute;
  left: 6px;
  top: .62em;
  width: 8px;
  height: 8px;
  background: var(--accent);
  border-radius: 50%;
}
/* nested levels: indent, shrink, fade the marker so hierarchy reads on a projector */
.slide li ul  { margin: 12px 0 0; padding-left: 14px }
.slide li li  { font-size: 16.5px; margin-bottom: 9px }
.slide li li::before { width: 6px; height: 6px; background: var(--faint) }
.slide li li li::before { background: transparent; border: 1.5px solid var(--faint) }

.slide li blockquote {
  margin: 12px 0 0;
  padding: 2px 0 2px 16px;
  border-left: 3px solid var(--rule-soft);
}
.slide li blockquote p { font-size: 17px; margin: 0; color: var(--ink-2) }
.slide li strong { color: var(--navy) }

.slide p    { font-size: 18px }
.slide code {
  font-family: var(--mono);
  font-size: .88em;
  background: var(--blue-wash);
  color: var(--blue);
  padding: 2px 6px;
  border-radius: 3px;
}
.slide a {
  color: var(--blue);
  text-decoration: none;
  border-bottom: 1px solid var(--accent);
  padding-bottom: 1px;
}
.slide a:hover { color: var(--accent-dark); border-bottom-color: var(--accent-dark) }

figure { margin: 0 0 26px; text-align: center }
figure img {
  max-width: 100%;
  height: auto;
  border: 1px solid var(--rule-soft);
  border-radius: 4px;
  background: #fff;
}

table {
  border-collapse: collapse;
  width: 100%;
  margin: 0 0 22px;
  font-size: 16px;
  background: #fff;
}
th {
  background: var(--ink);
  color: #fff;
  text-align: left;
  padding: 11px 14px;
  font-weight: 700;
  font-size: 14px;
}
td {
  padding: 10px 14px;
  border-bottom: 1px solid var(--rule-soft);
  vertical-align: top;
}
tr:nth-child(even) td { background: var(--page) }
td strong { color: var(--accent-dark) }

/* source reference chip */
.ref { margin-top: 26px; font-family: var(--mono); font-size: 12.5px; color: var(--muted) }
.ref::before { content: "▸ "; color: var(--accent) }

/* speaker notes: hidden on screen, shown on print */
.note { display: none }

/* ------------------------------------------------------------------ maths */
/* $…$ inline and $$…$$ display, rendered at build time to HTML+CSS.
   No KaTeX, no MathJax, no webfont — the deck stays a single offline file. */
.math {
  font-family: "DejaVu Serif", Cambria, Georgia, "Times New Roman", serif;
  font-style: normal;
  line-height: 1.3;
  white-space: nowrap;
  color: var(--ink);
}
.math i { font-style: italic }
.math .mo    { margin: 0 .2em }
.math .mo.un { margin: 0 .02em 0 0 }  /* unary sign hugs its operand */
.math sub, .math sup { font-size: .64em; line-height: 0 }
.math sub { vertical-align: -.3em }
.math sup { vertical-align: .52em }
.math .msp  { display: inline-block; width: .24em }
.math .mtxt { font-family: var(--font); font-size: .84em; font-style: normal }
.math .frac {
  display: inline-block;
  vertical-align: middle;
  text-align: center;
  margin: 0 .2em;
}
.math .frac .fn { display: block; padding: 0 .45em .16em }
.math .frac .fd { display: block; padding: .16em .45em 0; border-top: 1.7px solid currentColor }
/* radical: flex so the vinculum meets the top of the sign at any radicand height */
.math .sqrt {
  display: inline-flex;
  align-items: stretch;
  white-space: nowrap;
  vertical-align: middle;
}
.math .sqrt .sr {
  display: flex;
  align-items: center;
  font-size: 1.25em;
  line-height: .85;
  margin-right: -.04em;
}
.math .sqrt.tall .sr { font-size: 2.5em; line-height: .78 }
.math .sqrt .rad {
  display: flex;
  align-items: center;
  align-self: stretch;
  border-top: 1.6px solid currentColor;
  padding: 0 .3em 0 .06em;
}
.math-display {
  display: block;
  text-align: center;
  font-size: 30px;
  margin: 26px 0 24px;
  color: var(--navy);
}
.slide li .math-display { font-size: 25px; margin: 15px 0 13px }
th .math, td .math { font-size: .95em }

/* ------------------------------------------------------------------ footer */
.foot {
  position: absolute;
  left: 76px;
  right: 76px;
  bottom: 26px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 11.5px;
  color: var(--faint);
  border-top: 1px solid var(--rule-soft);
  padding-top: 10px;
}
.foot .n { font-family: var(--mono) }

/* --------------------------------------------------------- title & divider */
.slide.title {
  background: var(--ink);
  color: #fff;
  text-align: center;
}
.slide.title h1 {
  margin: 0;
  font-size: 50px;
  line-height: 1.15;
  color: #fff;
  font-weight: 700;
  letter-spacing: -.02em;
}
.slide.title .bar  { width: 96px; height: 5px; background: var(--accent); margin: 26px auto; border-radius: 3px }
.slide.title .sub  { font-size: 21px; color: var(--rule) }
.slide.title .meta { margin-top: 44px; font-size: 12.5px; color: var(--faint); font-family: var(--mono) }
.slide.title .foot { display: none }

.slide.divider { background: var(--navy); color: #fff }
.slide.divider .kicker {
  font-size: 12px;
  letter-spacing: .16em;
  text-transform: uppercase;
  color: var(--accent);
  font-weight: 700;
  margin-bottom: 14px;
}
.slide.divider h2         { color: #fff; font-size: 42px }
.slide.divider h2::after  { background: var(--accent) }
.slide.divider ol         { margin: 26px 0 0; padding-left: 20px; color: var(--rule); font-size: 17px }
.slide.divider li         { font-size: 17px }
.slide.divider li::before { background: var(--rule) }

/* ------------------------------------------------------------------- print */
@media print {
  nav, .rail { display: none }
  .shell { display: block }
  body  { background: #fff }
  .slide {
    min-height: auto;
    height: 19.0cm;
    page-break-after: always;
    break-after: page;
    padding: 36px 44px 60px;
    border: 0;
  }
  .slide h2       { font-size: 26px }
  .slide li       { font-size: 15px; margin-bottom: 9px }
  .slide.title h1 { font-size: 38px }
  .math-display        { font-size: 21px; margin: 16px 0 14px }
  .slide li .math-display { font-size: 18px; margin: 10px 0 9px }
  .note {
    display: block;
    margin-top: 18px;
    padding: 10px 14px;
    background: var(--wash);
    border-left: 3px solid var(--faint);
    font-size: 12px;
    color: var(--ink-2);
  }
  .foot { left: 44px; right: 44px; bottom: 16px }
  @page { size: A4 landscape; margin: 8mm }
}

/* ----------------------------------------------------------------- mobile */
@media (max-width: 900px) {
  .shell { grid-template-columns: 1fr }
  nav { position: static; height: auto }
  .rail { left: 0 }
  .slide { padding: 44px 26px 80px; min-height: auto }
  .slide h2 { font-size: 26px }
  .slide li { font-size: 16px }
  .foot { left: 26px; right: 26px }
}
"""

# ---------------------------------------------------------------------------
# Keyboard navigation + scroll-spy
# ---------------------------------------------------------------------------
JS = """
(function () {
  var slides = [].slice.call(document.querySelectorAll('.slide'));
  var links  = [].slice.call(document.querySelectorAll('nav a'));
  var bar    = document.querySelector('.rail i');

  function current() {
    var best = 0, bd = 1e9;
    slides.forEach(function (s, i) {
      var d = Math.abs(s.getBoundingClientRect().top);
      if (d < bd) { bd = d; best = i; }
    });
    return best;
  }

  function sync() {
    var i = current();
    links.forEach(function (a) { a.classList.toggle('on', a.dataset.i === String(i)); });
    if (bar) bar.style.width = (slides.length < 2 ? 100 : (i / (slides.length - 1)) * 100) + '%';
  }

  addEventListener('scroll', sync, { passive: true });
  addEventListener('resize', sync);
  addEventListener('keydown', function (e) {
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    var i = current(), t = null;
    if (e.key === 'ArrowDown'  || e.key === 'ArrowRight' || e.key === ' '    || e.key === 'PageDown') t = i + 1;
    if (e.key === 'ArrowUp'    || e.key === 'ArrowLeft'  || e.key === 'PageUp')                       t = i - 1;
    if (e.key === 'Home') t = 0;
    if (e.key === 'End')  t = slides.length - 1;
    if (t === null) return;
    e.preventDefault();
    slides[Math.max(0, Math.min(slides.length - 1, t))].scrollIntoView({ behavior: 'smooth' });
  });

  sync();
})();
"""
