# Tarikh website: brief and design system

Decided 20 Nov 2026. This is the public face of Tarikh as a service: a website with a landing page and inner pages, plus the app pages that sit behind "Open the desk". The screens designed earlier (desk, brief, the long table) are the product shown inside it.

## 1. What the company says

**Name.** Tarikh. In Hindi and Urdu, the word for a date, and the word a court gives when it sets the next hearing.

**One line.** Every date in a bounced-cheque case, counted and traced.

**Two lines.** Give Tarikh the cheque, the bank's return memo and the demand notice. It reads them, shows where each fact came from, counts the four legal clocks, and drafts a short brief your advocate can check line by line.

**Who it speaks to.** Advocates and their juniors in India who handle Section 138 cheque-bounce complaints. Second voice: the clerk who prepares the file.

**What it promises.** Nothing is invented. Nothing is filed or sent. The advocate approves by name.

**What it refuses to claim.** No legal advice. No outcome prediction. No customer logos, no testimonials, no invented numbers. It is a working prototype built on Microsoft Azure AI, and the site says so in the footer and on the contact page.

**Voice.** Plain, exact, a little dry. Short sentences. Dates written as "19 Dec". Sentence case everywhere. The advocate's words, not software words: "papers", "notice", "memo", not "documents", "artifacts", "entities".

## 2. Sitemap

| Page | Purpose | Reader leaves knowing |
|------|---------|-----------------------|
| Home | Make the idea land in one scroll; let them move the dates | That four clocks start when a cheque bounces, and that Tarikh counts them and shows its work |
| The desk (Product) | Show the three product screens with the reasoning behind each | What they would do on Monday |
| How the clocks are counted | The public explainer, with rule register and the live table | Every rule, its source and how sure we are |
| Trust | The six responsible-AI principles as product behaviours | Where AI is used, and where it is deliberately not |
| Security and privacy | Data flow, privacy pass, identity, audit | What leaves the machine and what never does |
| Docs (How it is built) | Architecture, services, how to run it | How the pipeline works; links to GitHub |
| About | Why this exists and who built it | A real person built it, and why |
| Contact | Request a walkthrough | How to reach the builder; prototype status |
| Privacy, Terms | Honest short texts | Prototype terms |
| 404 | A designed dead end | Where to go next |
| App: Docket, Matter, Brief | The product in demo mode | The real thing, on the sample matter |

## 3. The home page, section by section

1. **Threshold.** A large Bodoni headline: "Four clocks start the day a cheque bounces." The word Tarikh in Devanagari beneath the wordmark. One line of sub-copy. Two actions: "Move the dates" (scrolls to the table) and "Open the desk". A stamp settles into place on load.
2. **The four clocks.** Four statutory periods set as huge numerals (3 months, 30 days, 15 days, 1 month), each with one plain sentence and its section. This is the problem, shown without an adjective.
3. **From paper to brief.** Scroll-led, four steps: Read, Trace, Count, Brief. The left column holds the words; the right shows the real product component for that step, switching as you scroll.
4. **The long table.** The live scrubber, full width, on the sample matter. Drag a pin and the clocks, the stamp and the sentence follow.
5. **Every sentence has a source.** A dark section. The brief with numbered notes; one sentence struck out because no paper supports it.
6. **Where AI is used, and where it is not.** Two columns. Used: reading papers, hearing a voice note, hiding personal details, drafting from facts, answering questions about one file. Not used: counting dates, deciding what is legal, filing, sending.
7. **Built on Azure AI.** A ruled list of services, each with its job in Tarikh (Content Understanding, Language PII detection, Speech, Foundry model, Foundry Agent Service).
8. **Close.** "Put your own matter on the table." Two actions: Open the desk; Talk to the builder.

## 4. Design system

**Idea.** The date is the material. Time is the only thing that gets colour.

**Colour.** Paper `#F4EFE5`, paper-deep `#ECE5D4`, ink `#15120D`, ink-2 `#4A453B`, ink-3 `#6A6455`, rule `#D5CCB8`. The urgency ramp: calm `#1F3A93`, running short `#8A5A00`, urgent `#C0301C`, ended `#6A6455`. The inverted section uses ink as ground with paper text and lighter ramp values (`#9DB4FF`, `#E0A445`, `#FF7A63`). All text pairs pass 4.5:1; large text passes 3:1.

**Type.** Bodoni Moda for display (headlines, dates, numerals). Instrument Sans for interface and body. Tabular figures everywhere a number lines up. Devanagari and Gurmukhi fall back to Noto families when needed. Fonts are self-hosted: faster, private, offline-safe.

**Scale.** Four sizes only for display (clamp 56 to 168, 40 to 72, 28 to 40, 22), three for text (13, 16, 18). No in-between sizes.

**Space.** 8-point base. Sections 128 px apart on desktop, 80 on phone. Dense inside, airy between.

**Shape.** Two-pixel radius or none. Hairline rules instead of cards. Pills are pins and stamps, never buttons.

**Grid.** 12 columns, 1320 px max, 64 px gutters at desktop, 20 px on phone. One element per page is allowed to break the grid.

**Motion.** Four named motions, each with a job. Settle: content rises 12 px and fades in, 480 ms, once. Stamp: the stamp lands from 1.12 scale with a half-degree overshoot. Scrub: pins and bars follow the pointer with no easing, so it feels like a physical object. Reveal: a struck-out sentence is struck as you reach it. Under reduced motion every one becomes an instant state change.

**Imagery.** Only the product itself and the three fictional papers. No stock photos, no illustrations, no abstract blobs.

**Components.** Wordmark, nav, button (solid and outline), pin, stamp, clock row, paper viewer, claim line, source chip, ledger table, ruled list, principle block, footer.

## 5. What is deliberately absent

No gradient washes. No glow. No purple. No rounded-card grids with icon tiles. No "trusted by" strip. No testimonial carousel. No cookie banner (there are no cookies). No chat bubble in the corner. No newsletter pop-up. No emoji. No count-up statistics. No fake dashboard screenshots; every screen is live.

## 6. Technical decisions

- Static site, generated from partials by `site/build.py` (Jinja2). No front-end framework, no tracker, no third-party request.
- One shared stylesheet and one shared script. The date engine is a single dependency-free file, `site/src/assets/engine.js`, tested with `node --test`, used by the home table, the clocks page and the app pages. It follows `app/deadlines.py`.
- The app pages run in demo mode on the sample matter. Wiring to the FastAPI service comes with the pipeline slices.
- Accessibility: keyboard order, visible focus, `aria-live` for the changing sentence, `prefers-reduced-motion`, 200% zoom, contrast checked.
- Languages: English now. Hindi labels for the nav and the hero are included from the start; full Hindi and Punjabi copy arrives with module M08.
