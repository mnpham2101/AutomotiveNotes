# ISO 11898 (CAN) — Diagrams and Slides

Self-study material on **CAN, the Controller Area Network** — the bus every automotive ECU sits on,
and the layer underneath the UDS diagnostics covered in [`../ISO14229-UDS`](../ISO14229-UDS).

The slides go bottom-up: the wire, the voltages, the frame, arbitration, acknowledgement — then
the hand-off to UDS. Notes are written against **ISO 11898-1** (data link layer and physical
signalling) and **ISO 11898-2** (high-speed physical layer), with **ISO 15765-2** as the transport
layer that carries UDS over CAN.

## Folder structure

```
ISO11898-CAN/
├── official docs/        the standards themselves, as PDFs — reference only, never edited
├── asset/                diagrams — each .drawio source beside its rendered .svg
├── slides/               presentations — markdown source and the HTML built from it
└── tools/                build tooling
```

Two rules keep this tidy, same as the UDS folder:

- **`official docs/` is read-only.** Everything else is derived from it.
- **`*.html` under `slides/` is generated.** Edit the `.md` and rebuild; never edit the HTML.

## The slides

### `slides/CAN_Protocol_Slides.md`

Eight sections, 44 slides:

| Section | Covers |
| --- | --- |
| 1 — What CAN is | Bosch 1983–86, application domains, and CAN compared with SPI / I²C / UART |
| 2 — Two protocols, two standards | ISO 11898-1 vs -2, high-speed vs low-speed FT, and **ISO 15765-2** for UDS |
| 3 — Layer 1 | the scope of layer 1, bus topology and termination, differential signalling |
| 4 — Recessive and dominant | the termination as a *pull-together*, Kirchhoff, the 0.9 V / 0.5 V thresholds |
| 5 — The frame | standard and extended field maps, the four frame types, bit stuffing |
| 6 — Arbitration | bitwise, non-destructive, and its advantages and disadvantages |
| 7 — Acknowledgement | the ACK slot, and the limits of what it proves |
| 8 — Takeaways | six things worth remembering, plus references |

The recurring theme is that almost everything in CAN follows from one asymmetry — **dominant
overrides recessive** — so arbitration, the ACK slot and the error frame are all the same trick.

## Diagrams

Seven diagrams in `asset/`, each a `.drawio` source beside its rendered `.svg`:

| File | Shows |
| --- | --- |
| `can-network-layout` | four nodes on a linear bus, controller/transceiver split, 120 Ω at both ends |
| `can-bus-levels` | CAN_H and CAN_L waveforms, the resulting V_diff, receiver thresholds |
| `can-termination-kirchhoff` | dominant vs recessive driver states with the KCL/KVL current loop |
| `can-frame-structure` | standard and extended data frame field maps with bit counts |
| `can-arbitration` | three nodes arbitrating bit by bit; two lose, lowest ID wins |
| `can-ack-slot` | transmitter releases the slot, receivers overwrite it dominant |
| `can-uds-layers` | OSI layers, the ISO standard owning each, and the AUTOSAR module |

**Edit the `.drawio`, then re-export the `.svg`** — in draw.io, *File → Export as → SVG*. Palette
follows the house style used across `doc/Standards`: Material blue-grey neutrals, navy headings,
orange accent, DejaVu Sans.

> The `.svg` files here were authored by hand rather than exported from draw.io, so unlike the
> UDS assets they do **not** embed a copy of their own diagram source. The `.drawio` beside each
> one carries the same shapes on the same coordinates and is the file to edit.

## Building the slides

### Requirements

```
pip install markdown
```

Python 3 and the `markdown` package. Nothing else — no Node, no network, no draw.io CLI.

### Build

From this folder:

```
python tools/build_slides.py slides/CAN_Protocol_Slides.md
```

Then just **open the `.html`** — double-click it, or drag it into a browser. No server needed.

The build is a **single self-contained file**: CSS, JavaScript and every diagram are embedded
(images as base64 `data:` URIs), so nothing is fetched from the network and there are no sibling
assets to keep together. Use `--no-inline` to copy the SVGs beside the HTML instead, and
`-o OUTDIR` to write somewhere else.

`tools/build_slides.py` is the same builder as `../ISO14229-UDS/tools/`, vendored here so this
folder builds on its own — keep the two copies identical. `slides/SLIDE_TEMPLATE.md` documents
the markdown conventions inline.

### Maths

Formulas are written as LaTeX between `$…$` (inline) or `$$…$$` (centred display) and are
rendered to HTML and CSS **at build time**:

```
$$\Gamma = \frac{Z_L - Z_0}{Z_L + Z_0}$$
```

The supported subset is deliberately small — `\frac`, `\sqrt`, `\text`, sub- and superscripts,
Greek letters by name, and the usual relation symbols. That is enough for the physics in these
slides and it avoids pulling in KaTeX or MathJax, either of which would need a webfont and break
the single-offline-file rule. Anything unrecognised falls through as literal text.

### Viewing and presenting

- Scroll, or use **↓ ↑ → ← Space PageUp/PageDown Home End** to move between slides.
- The sidebar lists every section and slide; the orange rail at the top tracks progress.
- **Print to PDF** for a handout — A4 landscape, one slide per page, with speaker notes visible.

## References

- **ISO 11898-1** — Road vehicles, CAN: data link layer and physical signalling
- **ISO 11898-2** — high-speed medium access unit
- **ISO 11898-3** — low-speed, fault-tolerant medium-dependent interface *(withdrawn)*
- **ISO 15765-2:2016** — Diagnostic communication over CAN (DoCAN): transport protocol and network
  layer services — the PDF in `official docs/`
- **ISO 15765-4** — DoCAN requirements for emissions-related systems
- **ISO 14229-1 / ISO 14229-3** — UDS services, and UDSonCAN
- **Bosch CAN Specification 2.0** (1991) — the original, still the clearest description of arbitration
