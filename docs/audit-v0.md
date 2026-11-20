# Audit of v0 (git tag `v0-discarded`)

Written 20 November 2026 before any rebuild work. Facts only.

## What exists
107 tracked files: a FastAPI app (`app/`), adapters for five Azure services (`app/services/`), a deadline engine
(`app/deadlines.py`), a hand-written front end (`app/static/`), 104 tests (`tests/`), a report builder (`report/`),
a viva sheet, and an Azure setup guide.

## What was proven, and how

| Part | Proven by | Not proven |
| --- | --- | --- |
| Deadline engine | Unit tests with boundary cases | That the rules are legally right (see finding 3) |
| Azure adapters | Tests against test doubles in `tests/doubles.py` | That any of them works against a real Azure account |
| Front end | Chromium tests and an accessibility scan, against test doubles | That the design is good. The owner never saw it, and rejected it on sight. |
| Report | Builds to 32 pages and passes the Word schema check | Its content. Several parts were placeholders. |

## Findings

1. **Nothing has ever run against real Azure.** `data/cassettes/` does not exist. Every green test used a double.
2. **The design was chosen alone.** A cream "paper" theme was picked without showing the owner any alternative. It was
   rejected. All of v0's design is discarded, including `DESIGN.md`.
3. **The complaint window is one day early.** v0 counted one month from the cause-of-action date itself. The Supreme Court
   in *Econ Antri Ltd. v. Rom Industries Ltd.* (26 August 2013) held that the cause-of-action date is excluded. For a
   15-day payment period that ended on 18 November, v0 shows the complaint deadline as 18 December. The rule gives
   19 December. v0's note that a court "might count a day sooner" was wrong for this window. See decision 0004.
4. **The chosen region may not be allowed.** v0 picked Southeast Asia from Microsoft's documents. Student subscriptions
   enforce a short, per-subscription list of allowed regions, and Content Understanding is offered in only 12 regions. See
   decision 0003.
5. **The weekly diary in the v0 report was a guess.** It described plausible weeks, not real ones. It must never be written
   that way. See `docs/WORKING.md`.
6. **No developer map.** There is a README and a setup guide, but no list of decisions, no reasons, no data-flow guide.
7. **The viva sheet contains statements not yet re-verified**, for example claims about which regions lack which services.

## What is reusable, after review
The deadline engine's structure and boundary-test style, the adapter layout, the record-and-replay idea, and the sample-paper
generator. Each is re-reviewed in step 48 of the plan and kept only if it survives the research in `docs/research/`.
