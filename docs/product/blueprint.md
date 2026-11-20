# Tarikh blueprint: fifty modules

Status: draft 1, 20 Nov 2026. Supersedes the "three small directions" framing. Nothing here is built yet.
Domain: Microsoft Azure AI Fundamentals (AI-901). Product: a case desk for Section 138 cheque-bounce matters.

## What Tarikh is, in one paragraph

A lawyer gives Tarikh the three papers of a bounced-cheque case (cheque, bank return memo, demand notice) and, if they like, a voice note from the client. Tarikh reads the papers, shows exactly where each fact was found, computes the four legal clocks with plain arithmetic, and drafts a short brief in which every sentence is tied to a paper or is dropped. The advocate approves it by name. Nothing is invented, nothing is filed, and the lawyer stays in charge.

## The twenty minds this blueprint is written for

Each owns one question. A module is not done until its owner's question has an answer.

| # | Role | Question they own |
|---|------|-------------------|
| 1 | Product lead | Would an advocate in Chandigarh use this on Monday? |
| 2 | Legal domain lead | Is every rule cited, dated and conservative? |
| 3 | Brand director | Does it look like nothing else in legal software? |
| 4 | Art director | Is every screen composed, not assembled? |
| 5 | Typographer | Is the type chosen for this job, in three scripts? |
| 6 | Colour lead | Is colour spent only where it carries meaning (time)? |
| 7 | Motion designer | Does movement explain, never decorate? |
| 8 | Interaction designer | Can the advocate test a "what if" in one gesture? |
| 9 | Content designer | Is every sentence short, true and in the advocate's words? |
| 10 | Accessibility lead | Does it work by keyboard, screen reader and at 200% zoom? |
| 11 | Solutions architect | Is there one clear path from paper to brief? |
| 12 | Azure AI engineer | Does each AI-901 skill appear where it earns its place? |
| 13 | Backend engineer | Is the pipeline in code, not in a prompt? |
| 14 | Frontend engineer | Is the UI fast, small and honest about state? |
| 15 | Data and evaluation lead | Can we prove extraction and briefs are faithful? |
| 16 | Security and privacy lead | Does personal data stay out of places it should not go? |
| 17 | Responsible-AI lead | Is each of the six principles visible in the product? |
| 18 | QA lead | Do golden cases pin every legal edge? |
| 19 | Technical writer | Can the owner explain every file to an examiner? |
| 20 | Examiner's advocate | What is the hardest question the viva will ask, and is the answer in the product? |

## Layers and modules

Skill column: AI-901 domain (D1 = identify AI concepts 40-45%, D2 = implement solutions in Microsoft Foundry 55-60%).

### Layer 1. Brand and experience (8)

| ID | Module | What it is | Skill |
|----|--------|------------|-------|
| M01 | Identity | Name, mark, voice, the idea "the date is the material" | |
| M02 | Type system | Display serif, text sans, tabular figures, Devanagari and Gurmukhi fallbacks | |
| M03 | Urgency ramp | One colour system where hue appears only as days run out; contrast-checked | |
| M04 | Motion language | Four named motions (settle, scrub, stamp, reveal); all reduce to nothing under reduced-motion | |
| M05 | Component kit | Date, period bar, paper viewer, claim line, source chip, approval block | |
| M06 | State library | Empty, loading, partial read, low confidence, offline, error: all designed | |
| M07 | Story page | One scroll-driven page that explains the product to a visitor in 90 seconds | |
| M08 | Language layer | English first; Hindi and Punjabi for labels and the read-aloud voice | D2 text and speech |

### Layer 2. Intake: from paper to facts (7)

| ID | Module | What it is | Skill |
|----|--------|------------|-------|
| M09 | Capture | Upload, phone photo, PDF; deskew and size checks before any service call | D2 vision |
| M10 | Classifier | Decides cheque, memo, notice or other; says "other" instead of guessing | D2 extraction |
| M11 | Field extraction | Azure Content Understanding analyzers per paper type, with confidence per field | D2 extraction |
| M12 | Provenance | Every field keeps page, box and confidence; "Show on paper" outlines it | D1 transparency |
| M13 | Correction | Advocate fixes a field; everything downstream recomputes; the fix is logged | D1 accountability |
| M14 | Voice note | Client's voice note to text (Azure Speech), Hindi, Punjabi, English | D2 speech |
| M15 | Privacy pass | Azure AI Language PII detection and masking before any text reaches a model | D1 privacy |

### Layer 3. The law engine (7)

| ID | Module | What it is | Skill |
|----|--------|------------|-------|
| M16 | Rule registry | Each rule: text, source, date checked, how sure we are | |
| M17 | Window engine | The four clocks as pure functions; no model, no network | D1 what AI is not for |
| M18 | Day-count conventions | First day excluded; month ends; the one-day cases, shown conservatively | |
| M19 | Court calendar | Holidays and Saturdays flagged; never silently shifted | |
| M20 | Multiple presentations | Re-presented cheques and fresh notices handled as separate cycles | |
| M21 | Explainer | "How this is counted": the arithmetic as a sentence, with the rule behind it | D1 transparency |
| M22 | Scrubber | Drag any date, see every clock move; runs in the browser from the same rules | |

### Layer 4. Drafting and the brief (6)

| ID | Module | What it is | Skill |
|----|--------|------------|-------|
| M23 | Brief writer | Foundry chat model drafts from structured facts only | D2 generative |
| M24 | Source-or-drop | Every sentence must cite a paper, a typed fact or a rule; the rest is removed and listed | D1 reliability |
| M25 | Ingredient check | Section 138 ingredients as a checklist, each ticked from evidence or left open | |
| M26 | Exhibit index | Papers numbered A, B, C with what each proves | |
| M27 | Approval gate | Named advocate approves; time and version stored; edits reopen the gate | D1 accountability |
| M28 | Export | Brief to PDF and to calendar (ICS) with the clocks as events | |

### Layer 5. Agent and voice (5)

| ID | Module | What it is | Skill |
|----|--------|------------|-------|
| M29 | Matter agent | Foundry Agent Service with two read-only tools bound to one matter | D2 agents |
| M30 | Ask the file | Questions answered with citations; "not in the papers" is a valid answer | D2 generative |
| M31 | Read aloud | Neural voice reads the approved brief; locked until approval | D2 speech |
| M32 | Talk to the file | Speak a question, hear the answer; same agent, same limits | D2 speech |
| M33 | Guardrails | Content safety, prompt-injection fencing for text inside papers, refusal of legal conclusions | D1 safety |

### Layer 6. Platform (7)

| ID | Module | What it is | Skill |
|----|--------|------------|-------|
| M34 | API | FastAPI with typed models for every response | |
| M35 | Store | SQLite for matters, facts, claims, approvals | |
| M36 | Audit log | Append-only record of every read, edit, approval | D1 accountability |
| M37 | Identity | Entra ID with DefaultAzureCredential; no keys in code | D1 security |
| M38 | Cassettes | Record and replay of every Azure call so tests and demos run offline | |
| M39 | Settings | One typed settings file; clear message for each missing value | |
| M40 | Health | One check per service that makes a real call and prints PASS or the fix | |

### Layer 7. Quality (5)

| ID | Module | What it is | Skill |
|----|--------|------------|-------|
| M41 | Golden cases | Twenty matters with known answers, including every edge in M18 to M20 | |
| M42 | Extraction eval | Field accuracy and confidence calibration on a labelled sample set | D1 reliability |
| M43 | Faithfulness eval | Share of brief sentences with a valid source; target 100% after the drop step | D1 reliability |
| M44 | Accessibility audit | Keyboard run, screen-reader run, contrast, 200% zoom, reduced motion | D1 inclusiveness |
| M45 | Visual checks | Screenshots of every state at three widths, reviewed by eye | |

### Layer 8. Delivery and learning (5)

| ID | Module | What it is | Skill |
|----|--------|------------|-------|
| M46 | Developer guide | Map of every file, why it exists, how to run it on Windows | |
| M47 | Decision log | One short record per real choice, including the ones that were reversed | |
| M48 | Report | 20 to 30 pages in the university format, written from the finished app | |
| M49 | Viva pack | Hard questions with answers pointing at real code and real screens | |
| M50 | Release | Public repository, tagged release, one zip of everything | |

## AI-901 coverage

Every skill in the official outline is touched by at least one module above; the matrix with the skill text is `docs/research/01-ai901-coverage.md`. Responsible AI is not a chapter: fairness (M13, M42), reliability and safety (M17, M24, M33, M43), privacy and security (M15, M37), inclusiveness (M08, M44), transparency (M12, M21), accountability (M27, M36).

## Left out on purpose

No chatbot home screen. No "AI insights" panel. No case-outcome prediction. No automatic filing or sending. No multi-user permissions beyond one advocate. No payment or billing. Each would add surface and remove trust.

## Order of work

Layer 3 first (the part that must be right), then 2, 4 and 6 together as the pipeline, then 5, then 1 applied on top of a working app, with 7 running throughout and 8 written from what exists. Design for 1 starts now because the engine's output shape decides the screens.
