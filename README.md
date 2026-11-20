# Tarikh — cheque-bounce case desk

A working tool for an advocate handling a dishonoured cheque under Section 138 of the Negotiable Instruments Act. It reads
the cheque, the bank's return memo and the demand notice; counts the statutory windows; drafts a cited brief for the advocate
to approve; takes the client's account by voice in English, Hindi or Punjabi (masking personal details before any model
sees it); and answers questions about the matter through an agent that can only read that matter's facts and its deadlines.

Built for the Microsoft Azure AI Fundamentals (AI-901) industrial internship, Chandigarh University, 3 July – 31 October 2026.
Student: Piyush Kumar Brahmbhatt, UID 24BAI70769, 24AML4 A, B.Tech CSE (AIML). Program leader: Hari Haran.

## Azure services used, and why each is needed

| Need in the matter | Service | Where in the code |
|---|---|---|
| Read cheque, memo, notice into fields with the place on the page | Azure Content Understanding (custom analyzers) | `app/services/extraction.py` |
| Mask names, numbers, addresses in the client's account | Azure AI Language (PII) | `app/services/language.py` |
| Client's spoken account to text; approved brief read aloud | Azure Speech (fast transcription, neural voices) | `app/services/speech.py` |
| Draft the brief; look at the cheque image | Foundry model deployment (gpt-4.1) | `app/services/reasoning.py` |
| Ask questions about one matter | Foundry Agent Service (function tools) | `app/services/agent.py` |

The deadlines are **not** model output. They come from a rule engine with written tests (`app/deadlines.py`).

## Run it

1. Azure setup, once: [docs/azure-setup.md](docs/azure-setup.md) (about 30 minutes, verified against Microsoft's documentation).
2. `python -m tools.check_setup` until every line says PASS.
3. `python -m uvicorn app.main:build_app --factory --port 8000`, then open <http://localhost:8000>.

Recording and replay: in live mode every Azure reply is saved under `data/cassettes/`. Set `TARIKH_MODE=replay` to run the whole
app from those recordings with no network; a banner on every screen says it is a replay.

## Tests

`pytest` runs 90+ checks, including browser tests of the real front end in Chromium (`pip install playwright` then
`playwright install chromium`). Azure is never called by the tests; the test doubles live only in `tests/`.

## Design

[DESIGN.md](DESIGN.md) records every visual decision and why. Fonts are self-hosted (Newsreader, IBM Plex Sans and Mono; Noto
for Devanagari and Gurmukhi), licences in `app/static/fonts/`.

## Limits stated plainly

Court holidays and condonation of delay are for the advocate to confirm. Sources disagree on whether Section 138's text says three
or six months for cheque validity; the app uses the three months in force through RBI's validity rule and flags it. This is a
student project and not legal advice. All sample papers are fictional and labelled so.
