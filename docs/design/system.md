# Tarikh design system

## Concept
The Indian tear-off wall calendar. A case is a sequence of dates; the calendar leaf is the brand's object. Black weekday
numerals, red Sundays, a red binding strip, a perforated edge. Time is the only thing that is ever coloured.

## Mark and wordmark
A red leaf with two white binding rings and the Devanagari ता, followed by the wordmark **Tarikh** in Schibsted Grotesk
800 and, where space allows, तारीख़ in Tiro Devanagari Hindi. Favicon: the leaf without lettering.

## Colour
| Token | Value | Use |
|---|---|---|
| `--bk` | #0B0B0B | Ink, dark bands, sidebar |
| `--wh` | #FFFFFF | Paper |
| `--g50` to `--g700` | warm greys | Surfaces, lines, secondary text |
| `--red` | #E2321B | The one signal: urgency, primary action, the brand leaf |
| `--amber` | #B06E00 | Running short, or needs a person's entry |
| `--green` | #17804A | Settled, approved |
No gradients, no purple, no beige page backgrounds. Text contrast meets WCAG AA on both bands.

## Type
Schibsted Grotesk for all text (400 to 900); Anton only for calendar numerals and big figures; JetBrains Mono for case
data, section numbers and labels; Tiro Devanagari Hindi for Hindi. Four display sizes (`h-xl`, `h-l`, `h-m`, `h-s`) and
three text sizes (`lede`, body, `small`). All fonts are self-hosted; no third-party request leaves the page.

## Layout and motion
12-column, 1360 px maximum, gutter 20 to 56 px, sections 88 to 168 px apart. Radius: 999 px for actions, 10 to 16 px for
panels, 4 to 6 px for paper. Motion has four names: **settle** (content rises 16 px into place), **tear** (a calendar leaf
tears off), **unfold** (the mega menu opens by height, items stagger by 40 ms), **slide** (the sidebar marker follows the
pointer; the rail folds to 76 px). All motion stops under `prefers-reduced-motion`.

## Components
Calendar leaf, live clocks table, app window, chip (calm, warn, hot, ok, gone), KPI, list, data table, month grid, fact
table with source tags, document sheet with marked facts, settlement calculator, command palette, rail sidebar.

## Words
Plain, short, specific. Buttons are verbs ("Open a matter", "Save hearing"). Errors say what to do. No invented
customers, logos, testimonials or numbers; every market figure carries its source.
