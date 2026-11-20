# Tarikh — Design Language

Maturity: L0 (no prior language). This file is the language. Tokens live in `app/static/css/tokens.css`.

## Read
Case-management tool · one advocate (and a junior) working a Section 138 cheque-dishonour matter · exact, accountable,
printed-record feel · family: editorial ledger / court docket (not SaaS dashboard).
Dials: Creativity **balanced** (bold only in the type and the stamp), Density **packed but ruled** (ledger rows),
Variance **uniform**, Motion **static by default**, kinetic only where it explains a date.

**Theme statement: exact, accountable, docket.**
Test: a decision is rejected if it makes the screen friendlier than it is precise (soft gradients, mascots), or louder
than a court clerk (animated celebrations, emoji).

Context overrides style: legal and trust-critical → no glass, no neon, no AI-purple, no playful rounded type; accessibility
(WCAG AA) is a hard floor; nothing is a decision made by colour alone.

## Reference traits (clustered, not copied)
- Indian court cause-lists and cheque-return memos: dense ruled rows, numerals set in monospace, rubber-stamp marks.
- Law-report and gazette typography (Caslon-era readers): serif with real optical sizing, small caps for labels.
- Bank passbooks / double-entry ledgers: double rule under totals, right-aligned figures, hairline columns.
- Railway timetable (outside category): one shared axis carrying many rows, read left to right.
- Surviving cluster: ruled rows, tabular figures, one axis for time, marks made by hand (stamp, tick, pen).

## Colour — three meanings, nothing else is coloured
| Token | Hex | Meaning | Contrast |
|---|---|---|---|
| `--paper` | #F4EFE4 | page | ink on paper 16.0:1 |
| `--raised` | #FBF8F1 | the scan viewer and the brief (the "sheet") | |
| `--sunken` | #EAE3D3 | wells, table heads | ink-3 on sunken 5.6:1 |
| `--rule` | #D6CCB6 | hairlines (decorative) | |
| `--ink` / `-2` / `-3` | #17140F / #3B362D / #5E5748 | text; ink-3 is the quietest text | 16.0 / 10.5 / 6.2 : 1 |
| `--ink-4` | #7D7564 | glyphs, input borders, axis ticks. Never text | 4.0:1 (≥3:1 non-text) |
| `--stamp` | #A3221B on #F1D9D0 | **deadline**: a window that is open, closing, or missed | 6.5 / 5.6 : 1 |
| `--verified` | #2D5B39 on #DCE5D2 | **a human checked this**, or a window that was met | 6.9 / 6.1 : 1 |
| `--pen` | #1F3C66 on #D9E0EA | **provenance**: where on the paper a value was read | 9.7 / 8.3 : 1 |

No dark mode: the product's metaphor is paper, it is printed and screenshotted into a report, and a second palette
would double the contrast checking for no user need. Large red areas are forbidden; red is a stamp, a rule, a word.

## Type
- **Newsreader** (variable, optical size) — display and reading text. Display uses `font-optical-sizing:auto` at ≥28px
  with tight tracking (−0.01em); body uses the text optical size at 17–19px, line-height 1.55, measure ≤ 62ch.
- **IBM Plex Sans** 400/500/600 — interface labels, buttons, table heads (13–14px, small caps via letter-spacing .06em
  uppercase for labels).
- **IBM Plex Mono** 400/500 — every number, date, cheque number, citation, with `font-variant-numeric: tabular-nums`.
- **Noto Sans Devanagari / Gurmukhi** — loaded only through unicode-range when a Hindi or Punjabi transcript is shown;
  sit second in the stack so Latin stays Newsreader.
- Latin-ext subsets are included deliberately: the **₹** sign is not in the base Latin subset of any of these fonts.
- Fraunces, Inter, Space Grotesk and system-ui-as-brand are rejected as the current default of generated sites.
Scale (1.2): 12 · 14 · 16 · 19 · 23 · 28 · 40 · 56. **Only four are used in screens** (Rams: nothing in between is
indecision): display 40 (matter title, the answer line), title 23 (section heads), body 19/17 (reading) and label 13
(sans caps, mono figures). 56 is the wordmark on the Matters page only. Weights: 400/500/600 sans; 380–560 serif.

## Layout
- Page max 1280px, 12 columns, 24px gutter, 4px base unit (scale 4/8/12/16/24/32/48/64/96).
- **Matters** (home): a single ruled table — matter, parties, the complaint window status, papers, last action. No cards.
- **Matter** (desk), top to bottom:
  1. Header: title (display serif), parties in mono small caps, approval stamp state.
  2. **The clock** — full-width timeline. One shared date axis, four ruled rows (cheque validity · demand notice ·
     drawer's 15 days · complaint). Today is a vertical pen-ink line that can be dragged or moved with ←/→ (1 day) and
     PgUp/PgDn (7 days). The date field beside it is a real input for keyboard users. Statuses are words first
     ("Open — 29 days left") then colour.
  3. Two columns from 960px: left **the papers** (sticky scan viewer, tabs per document, polygon highlight); right **the
     ledger** (facts as ruled rows: label · value · confidence in mono · verify control).
  4. **The brief** — set like a typed memo on the raised sheet; each sentence ends in source chips (`cheque · No.`).
  5. **Ask the desk** — one input, answer shows the tool calls it made (name, args, result) beneath, collapsed.
  6. **The client's account** — record/upload, transcript original + redacted version side by side.
  7. **Safeguards** — the six Responsible AI principles, each with the concrete thing in this product (not a poster).
- Below 960px: single column; the scan viewer becomes a full-width sheet opened from a fact's "Show on paper".
- Radius 2px everywhere, one token. No shadows: depth is hairline rules, the raised/sunken fills, and a 1px ink rule for
  the sheet edge. Double rule (3px ink + 1px gap) is reserved for the approved brief and totals.

## Signature marks
- **Stamp**: bordered (1.5px stamp-red, double inset), mono uppercase 12px, rotated −2°, used for exactly: window status
  CLOSING / EXPIRED, and APPROVED on the brief (green variant). Static; it appears by a 140ms opacity step, not a bang.
- **Tick**: hand-drawn SVG tick in verified green beside a human-checked fact.
- **Source chip**: pen-blue underlined mono reference; hover or focus lights its polygon on the scan (pen-bg at 35% with a
  1px pen outline).
- **Wordmark**: "Tarikh" in Newsreader italic with तारीख in Noto Sans Devanagari at 60% size beside it; no logo glyph.

## Motion
Static by default. Permitted: polygon highlight fade 140ms; timeline marker follows the pointer 1:1 (no easing);
window bars re-measure over 140ms when the date changes; status stamp opacity step. `prefers-reduced-motion`: all
durations 0. No loading spinners: progress is a ruled bar with named stages ("Reading cheque · Reading memo …").

## Copy (law-office plain)
Verbs and nouns of the work: "Add the cheque", "Check", "Show on paper", "Approve brief". Errors say what happened and
what to do ("The photo is HEIC, which Azure cannot read. Share it as JPEG or upload a PDF."). Uncertainty is stated as
a reading ("Read as 004718, 62% sure — check against the paper"). AI is never decorated: no sparkle icon, no "magic",
no avatar; model-made text carries "Drafted by gpt-4.1 · not yet approved". Dates in the UI: `21 Nov 2026`, ISO in mono
only inside the ledger inputs. Hindi and Punjabi labels appear only where the client's own words are shown.

## Anti-slop register (each is a defect if found)
Gradient or glass surfaces · purple/indigo accent · pill-shaped buttons everywhere · icon-in-a-circle cards · emoji ·
"Welcome back 👋" · lorem ipsum or placeholder gray boxes · Inter or Fraunces · sparkles · robot or chat-bubble avatar ·
drop shadows · centered hero with gradient headline · equal three-card feature rows · stock illustrations · "Seamless /
Supercharge / Unlock" · progress spinners without a stage name · colour as the only carrier of status.

## Accessibility floor
Text ≥ 4.5:1, non-text ≥ 3:1 (computed above). Every control reachable and operable by keyboard, visible 2px pen focus
ring offset 2px. Timeline has a text equivalent table. Status never by colour alone. Touch targets ≥ 44px at phone width.
`lang` set per transcript (`hi`, `pa`). Polygons have text alternatives (the fact label and value).

## Imagery
Only the user's own scans and the fictional sample papers. No decorative imagery. Empty states are typographic.

## Council review (Ive · Rams · Hadid · Ingels · Norman) — decisions taken
| Lens | Finding | Decision |
|---|---|---|
| Ive (material) | The material is paper and ink, so controls must press, not lift. | Buttons are ruled rectangles; `:active` shifts 1px down and fills `--sunken`. No hover lift anywhere. Radius stays 2px. |
| Rams (restraint) | Eight type sizes was indecision. Seven sections is a lot. | Four sizes in use (above). Voice and Safeguards fold under one "Record and safeguards" rail on desktop so the desk shows five rooms, not seven. |
| Hadid (movement) | The first viewport must be an arrival, not a form. | **Answer line** above the clock, in display serif: "Complaint window open. Closes 18 Dec 2026, 27 days left." (or "Cannot be worked out: the notice delivery date is missing."). The clock bleeds past the 1280px page to the screen edge (the one grid-break). |
| Ingels (delight) | Function can carry the play. | The clock is also a calculator: drag *today* and the answer line rewrites itself. Matters page offers "Open the fictional sample matter" so a viva demo starts in one click. Empty states are typographic and name the next paper to add. |
| Norman (affordance) | Editable and clickable things must look so; nothing else may. | Fact values are underlined inputs (ink-4 rule), "Show on paper" is a pen-blue link, the scrub handle has grip ridges and `ew-resize`, non-interactive stamps have no hover state. Approve is disabled with the reason printed beside it (no brief / no name); the brief header says "3 facts not yet checked" until every fact is checked or edited. |
Tensions named: Rams vs Ingels resolved by making the delight the date scrub itself; Hadid vs Rams resolved by a dramatic
structure (full-bleed clock) with a quiet surface (hairlines, no fills louder than `--sunken`).
