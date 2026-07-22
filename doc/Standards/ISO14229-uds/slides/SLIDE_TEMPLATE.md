# Deck Title Goes Here

> subtitle: One line describing the deck
> footer: Source / author / date — shown on every slide

<!--
  SLIDE DECK TEMPLATE
  Build:  python tools/build_slides.py <this-file.md> [more.md ...]
  Style:  colours and fonts derived from BTC_phan_hoi_V2X_team.pdf

  CONVENTIONS
    #   H1      Deck title. Exactly one, at the top. Becomes the title slide.
    ##  H2      Section. Groups the slides under it; becomes a divider slide
                and one entry in the side navigation.
    ### H3      One slide. Everything until the next ### or ## is its body.

    > subtitle: …   only under the H1 — title-slide subtitle
    > footer:   …   only under the H1 — repeated on every slide
    > note: …       anywhere in a slide — speaker note, hidden on screen,
                    visible when printing and in the notes panel

  SLIDE BODY — keep it sparse
    - 3 to 5 bullets, one line each. No paragraphs.
    - One figure per slide: ![alt](../uds/asset/diagram.svg)
    - If a figure already shows the structure, do NOT also table its fields.
    - Tables only when the content is genuinely tabular and the slide has no figure.
    - `[Clause 9.2.1]` in backticks at the end = source reference, rendered small.
-->

## Section — First Topic

### A slide with bullets

- Keep each bullet to one line.
- State the conclusion, not the reasoning.
- Bold the **one term** that matters most.
- Three to five bullets is the working limit.

`[Source reference]`

### A slide with a figure

![Describe the figure here — swap this for your own diagram](../uds/asset/uds-slide-adata.svg)

- One or two bullets that add what the figure cannot show.
- Do not restate the figure's labels.

`[Source reference]`

> note: Speaker notes go here — the detail you say out loud but do not put on screen.

### A slide with a table

| Column | Column |
| --- | --- |
| Value | Value |
| Value | Value |

- One closing bullet drawing the conclusion from the table.

## Section — Second Topic

### Another slide

- Sections group slides on the same topic.
- Start a new `##` whenever the topic changes.

### Takeaways

- Close every deck with the three or four things worth remembering.
- One line each.
