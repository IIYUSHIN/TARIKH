# Tarikh — Cheque-Bounce Case Desk: Design

Date: 2026-11-20 · Owner: Piyush Kumar Brahmbhatt (UID 24BAI70769, 24AML4 A, B.Tech CSE AIML)
Purpose: Industrial Internship project + report, Microsoft Azure AI Fundamentals (AI-901). Viva on 21 Nov 2026.

## 1. Intent and why
A lawyer opening a cheque-bounce matter (Section 138, Negotiable Instruments Act, 1881) receives paper:
the cheque, the bank's return memo, a demand notice, and a client's account of events, often spoken, often in
Hindi or Punjabi. The matter lives or dies on three statutory windows, so the lawyer must (a) read the forms
correctly, (b) compute the dates correctly, (c) never lose track of a window.
Tarikh does the reading, transcribing, redacting and drafting, and computes the dates in ordinary code.
The lawyer stays in charge: every extracted fact links to the place in the source document it came from,
and nothing is final until the lawyer approves it.

Why this project for AI-901: the exam is now 40–45% concepts + Responsible AI and 55–60% building with
Microsoft Foundry in Python (chat client via Foundry SDK, single agent, text analysis, speech, vision,
Content Understanding). Each of those has a real job in this pipeline, so every line is explainable in the viva.

## 2. Goals
- G1. Upload cheque / return memo / demand notice (scan or photo) → structured fields via Content Understanding,
  each field linked to its source region on the document.
- G2. Client voice note (English/Hindi/Punjabi) → transcript (Speech) → PII redaction + entities + key phrases (Language).
- G3. Case brief drafted by a Foundry-deployed model under a strict system prompt; every claim carries a source reference.
- G4. Deadline engine in plain Python (no model): cheque validity, notice window, payment window, complaint window;
  shows the earlier (safer) date; unit-tested.
- G5. A single Foundry agent the lawyer can question about the matter; it calls the deadline engine as a tool.
- G6. Brief read aloud (Speech synthesis) for the client.
- G7. Responsible AI is visible in the product, mapped one-to-one to the six principles.
- G8. Viva-proof: works live, and replays a previously recorded real run if venue internet fails (clearly labelled).
- G9. UI of award-site quality: considered, specific to the domain, no template look.
- G10. 20–30 page report in the Chandigarh University format, plus a viva Q&A sheet.

## 3. Non-goals
- No legal advice, no case-outcome prediction, no drafting of court filings.
- No user accounts, multi-tenancy, cloud storage, or deployment to Azure App Service. Runs on the candidate's laptop.
- No custom model training; no machine-learning domain (removed from AI-901).
- Cheque bounce only (Section 138). Other matter types are future work.

## 4. Anti-goals (a failure even if it "works")
- Anything that looks AI-generated: gradient hero, glass cards, emoji icons, sparkle/“magic” copy, stock illustration,
  default Inter/Space Grotesk, three-icon feature grids, lorem ipsum, fake testimonials.
- Any number, date or statute reference in the UI or report that was not verified against a source.
- Real client data anywhere. All sample documents are fictional and labelled.
- Letting a model compute a statutory date.
- Padding the report: every page must carry real project work.

## 5. Constraints
- Exam in about one day; report must be printable before then.
- The build workspace cannot reach Azure. Everything except live Azure calls is built and tested here;
  the candidate runs a smoke test on their laptop and records the evidence run.
- Student subscription: limited credit, possible model-quota limits, possible region limits.
- Candidate must be able to explain every component: plain code, small files, no framework magic.

## 6. Approaches considered
A. **Pipeline in code, agent at the end (chosen).** Orchestrate Content Understanding → Speech → Language → model
   in a deterministic Python pipeline; one agent only for the lawyer's Q&A. Predictable, debuggable, each service
   demonstrable on its own, maps cleanly to AI-901 objectives.
B. Single agent orchestrates everything via tools. Fewer lines, but non-deterministic order, harder to demo,
   harder to test, and the agent would be trusted with legal steps. Rejected.
C. Portal-only, no code. Misses the Python/Foundry SDK objectives and the “lightweight client app” skill. Rejected.

## 7. Decisions (my calls, to be marked as such in the report)
- Name: **Tarikh** (Hindi/Urdu “date”; the product is about dates). Candidate may rename.
- Stack: Python 3.12, FastAPI, SQLite, static front end (hand-written HTML/CSS/JS, no build step, libraries vendored).
- Auth to Azure: Entra ID via `az login` / DefaultAzureCredential (SDK supports Entra ID only). No keys in files.
- Services: Content Understanding (documents/images), Azure Speech (STT with language identification, TTS),
  Azure Language (PII, entities, key phrases, summarization), Foundry model deployment (multimodal: cheque image
  inspection + brief + translation), Foundry agent (function tool: deadlines).
- Statute knowledge: a short, hand-verified digest of Ss.138–142 NI Act held in the agent/brief prompt with source
  citations. No vector store (extra moving parts, no gain at this size).
- Deadline conventions: notice ≤30 days from receipt of bank memo; 15 days to pay counted from the day after
  receipt of notice; complaint within one month from the day after the 15 days end. The UI shows the safer
  (earlier) date, states the rule used, and flags court-holiday and delay-condonation as “lawyer to confirm”.
- Record/replay: every live run can be saved as an evidence folder; replay mode serves it back with a visible
  “Replay of recorded run, <timestamp>” banner. Used for viva insurance and for report screenshots.
- Safeguards mapped to six principles: fairness (no party-based scoring; neutral language checks), reliability &
  safety (deadline engine tested; model never computes dates; refusal of legal advice), privacy & security (PII
  redacted before model sees text; data stays on laptop; keyless auth), inclusiveness (Hindi/Punjabi voice in,
  spoken brief out, keyboard-navigable, contrast-checked), transparency (source links, “drafted by model”,
  model/deployment named), accountability (lawyer approval gate + audit log).

## 8. Interface direction (details fixed by design pass before building)
Editorial legal-ledger look: warm paper and near-black ink, one court-stamp red reserved for deadlines, a second
muted green for “verified”. A serif with real character for display, a mono for citations and figures, a quiet
text sans. Two screens only: Matters, and Matter (documents with source highlighting / facts / the three-window
timeline / brief / ask / voice / safeguards). Signature interactions: hover a fact → its region lights on the scan;
scrub “today” along the timeline and watch windows open and close. Motion only where it explains.
Copy in plain law-office language. Fonts self-hosted.

## 9. Testing
- Deadline engine: table-driven unit tests from worked examples in published sources, plus month-end and leap-year cases.
- Pipeline and API: tests with service doubles that exist only in tests, never shipped as product behaviour.
- UI: rendered in a headless browser at desktop and phone widths, checked for layout, keyboard order, contrast.
- Live Azure: `check_setup.py` smoke test on the candidate’s laptop, one call per service, readable errors.

## 10. Report plan
CU format: cover, bonafide, declaration, abstract, contents, abbreviations, chapters, appendices, references.
Times New Roman 12, 1.5 spacing, A4, footer with name/UID/specialization, roman numerals for front matter.
Ch1 Introduction · Ch2 Weekly Report (3 Jul–31 Oct 2026, day-by-day) · Ch3 Requirements and Design ·
Ch4 Implementation · Ch5 Testing, Results and Responsible AI · Ch6 Conclusions and Recommendations.
Appendices: AI-901 syllabus, certificate, setup and sample outputs. Figures and tables drawn by us; every outside
fact cited.

## 11. Risks and what I will do
- Hindi/Punjabi PII support in Azure Language may be partial → verify before coding; if partial, translate first
  then redact, and say so in the report.
- Model quota on a student subscription → app takes the deployment name from config; choose whatever deploys.
- Content Understanding region → confirm before the candidate creates resources.
- Foundry SDK moves fast → code against the installed package and its own docs, not memory.
- Deadline counting ambiguity (month-end, day of receipt) → conservative date + stated rule + tests.
- Weekly diary: I draft it from the AI-901 learning progression; candidate must edit it to match what they did.

## 12. Left to the builder / candidate
Builder: exact SDK calls, fonts, palette values, file layout. Candidate: Azure account, Foundry project,
logo file, Program Leader’s designation, degree wording (B.E. vs B.Tech as printed on the marksheet),
course certificate image, and review of the weekly diary.
