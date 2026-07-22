# ISO 14229-1 (UDS) — Study Notes, Diagrams and Slides

Self-study material on **ISO 14229-1, Unified Diagnostic Services** — the application-layer
diagnostic protocol used to talk to automotive ECUs — plus how that protocol is implemented in
an AUTOSAR Classic ECU by the Dcm and Dem modules.

Notes are written against **ISO 14229-1:2013(E)** as the authoritative source. Clause and table
numbers throughout refer to that edition; the earlier ISO/DIS 14229-1:2011 draft numbers clauses
differently (its Diagnostic and Communication Management functional unit is Clause 10, not 9).

## Folder structure

```
ISO14229-uds/
├── uds/
│   ├── official docs/    the standards themselves, as PDFs — reference only, never edited
│   ├── markdowns/        knowledge notes — hand-written, the source of truth
│   └── asset/            diagrams — each .drawio source beside its rendered .svg
│
├── slides/               presentation decks — markdown source and the HTML built from it
│
└── tools/                build tooling
```

Two rules keep this tidy:

- **`official docs/` is read-only.** Everything else is derived from it.
- **`*.html` under `slides/` is generated.** Edit the `.md` and rebuild; never edit the HTML.

## The markdown notes

### `uds/markdowns/ISO_14229-1_UDS_Overview.md`

The main note. Written as concise conclusions with a clause reference after each claim, rather
than prose explanation — the intent is that any statement can be traced back to the PDF in one
lookup.

| Section               | Covers                                                                       |
| --------------------- | ---------------------------------------------------------------------------- |
| 1.1 General           | Client-server model, the six service primitives                              |
| 1.1.1                 | UDS on the OSI model, and where the AUTOSAR CAN stack sits                   |
| 1.2 Services          | Functional units; the 10 Diagnostic and Communication Management services    |
| 1.3 Basic UDS Message | A_SDU vs A_PDU, mandatory parameters, A_Data byte layout, per-service detail |
| 2                     | Dcm and Dem in AUTOSAR — placement, submodules, call flows                   |

Sources are mixed and the note says which is which:

- **ISO 14229-1:2013** — everything in Section 1. Quoted or paraphrased with clause/table numbers.
- **AUTOSAR CP SWS Dcm / Dem** — Section 2. ISO 14229-1 never mentions Dem at all.
- **Secondary web sources** — used only to corroborate AUTOSAR module placement and the
  aging/healing terminology; listed in the References section.

Where the standard is ambiguous or self-contradictory, the note says so rather than picking a
reading — see the ResponseOnEvent caveat at the end of the DiagnosticSessionControl subsection
(Figure 7 and Clause 9.10.1 rule f disagree).

### `slides/ISO_14229-1_UDS_Slides.md`

The same material as a deck: one-line bullets, four sections, a diagram per structural topic.
It mirrors the overview note but does not replace it — the note keeps the detail and the full
citations.

## Diagrams

Each diagram is a `.drawio` source and a rendered `.svg`. **Edit the `.drawio`, re-export the
`.svg`** — in draw.io, *File → Export as → SVG*, with *Include a copy of my diagram* ticked so the
SVG stays editable. The exported SVGs already embed their own source, so an `.svg` can also be
opened directly in draw.io and edited in place.

The `uds-slide-*` diagrams were split out of `uds-sdu-pdu-format` so each carries one idea at a
size that reads on a projector. Their palette follows the house style used elsewhere in
`doc/Standards` — Material blue-grey neutrals, navy headings, orange accent, DejaVu Sans.

## Building the slides

### Requirements

```
pip install markdown
```

Python 3 and the `markdown` package. Nothing else — no Node, no network, no draw.io CLI.

### Build

From this folder:

```
python tools/build_slides.py slides/ISO_14229-1_UDS_Slides.md slides/SLIDE_TEMPLATE.md
```

Output goes to `slides/`, one `.html` per input `.md`. Then just **open the `.html` file** —
double-click it, or drag it into a browser. No server, no local web host, no build watcher.

Each deck is a **single self-contained file**: CSS, JavaScript and every diagram are embedded
(images as base64 `data:` URIs), so there are no sibling assets to keep together and nothing is
fetched from the network. That makes the UDS deck ~3 MB. If you would rather keep it small, use:

```
python tools/build_slides.py slides/ISO_14229-1_UDS_Slides.md --no-inline
```

which copies the SVGs beside the HTML instead — still no server needed, but the folder must then
travel as a unit.

Other options: `-o OUTDIR` to write somewhere else.

### Editing a deck

Start from `slides/SLIDE_TEMPLATE.md`, which documents the conventions inline and builds on its
own so you can see the styling before writing content.

| Markdown                     | Becomes                                                                   |
| ---------------------------- | ------------------------------------------------------------------------- |
| `# Title`                    | The title slide. Exactly one, at the top.                                 |
| `## Section — Name`          | A section divider slide, and a group in the side navigation.              |
| `### Slide title`            | One slide. Everything up to the next `###` or `##` is its body.           |
| `> subtitle:` / `> footer:`  | Title-slide subtitle / footer repeated on every slide. Put under the `#`. |
| `> note: …`                  | Speaker note. Hidden on screen, printed in the handout.                   |
| `` `[Clause 9.2.1]` ``       | Source reference, rendered small at the bottom of the slide.              |
| `![alt](../uds/asset/x.svg)` | A figure. Paths are relative to the markdown file.                        |

Guidance that keeps slides readable:

- Three to five bullets, one line each. State the conclusion, not the reasoning.
- One figure per slide. **If a figure already shows a structure, do not also table its fields.**
- Tables only where content is genuinely tabular and the slide has no figure.

### Viewing and presenting

- Scroll, or use **↓ ↑ → ← Space PageUp/PageDown Home End** to move between slides.
- The sidebar lists every section and slide; the orange rail at the top tracks progress.
- **Print to PDF** for a handout — A4 landscape, one slide per page, with speaker notes made
  visible.
