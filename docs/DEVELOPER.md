# Tarikh: developer guide

What was built, why, where it lives, and how a request moves through it. Read this first; the decision records in
`docs/decisions/` hold the reasoning behind each choice.

## 1. The system in one picture

```
Browser (site/dist)                         Tarikh server (FastAPI, app/)                 Microsoft Azure (one Foundry resource)
───────────────────                         ─────────────────────────────                 ─────────────────────────────────────
Marketing pages, Check (engine.js) ──────── static files
Sign up / Sign in ─────── /api/auth/* ───── accounts.py (scrypt, sessions) ── SQLite
Desk (app.js) ─────────── /api/desk/* ───── desk.py view ◄── store.py ◄───── SQLite (matters, audit)
   upload a paper ─────── /api/matters/{id}/documents ── pipeline.add_document ── Extractor ──► Content Understanding
                                                                                              (or the model, decision 0006)
                                                         └ inspect_cheque_image ──► Foundry model (vision)
   client's voice ─────── /api/matters/{id}/voice ─────── Transcriber ──► Speech (fast transcription)
                                                         TextAnalyzer.redact_pii ──► AI Language (PII)
   AI brief ───────────── /api/matters/{id}/brief ─────── Reasoner.draft_brief ──► Foundry model (JSON schema)
                                                         validate_brief: drop any sentence without a real source
   Ask the file ───────── /api/matters/{id}/ask ───────── Assistant ──► Foundry Agent Service, 2 read-only tools
   deadlines ─────────── computed in deadlines.py (server) and engine.js (browser), same tests, no model
```

Every Azure call goes through a **Recorder** (`app/services/recorder.py`). In live mode it saves each reply to
`data/cassettes`; in replay mode it serves them back. Tests never call Azure; they use doubles in `tests/doubles.py`.

## 2. How a request moves: uploading a cheque

1. `app.js` posts the file to `POST /api/matters/{id}/documents` with `doc_type=cheque`.
2. The session middleware in `main.py` finds the user from the `tarikh_session` cookie; `own()` returns 404 if the matter
   belongs to someone else.
3. `Pipeline.add_document` checks the bytes (not the file name) to learn the real type, rejects empty, oversized and HEIC
   files with a reason, then calls the extractor.
4. The extractor returns `Fact`s: value, confidence, the box on the page, and a plain-language flag where a person must
   check (ambiguous day/month, not read, read without a box). Dates no paper shows are created as **manual** facts.
5. For a cheque image, the model also lists what it sees (signature, date, crossing). If that fails, the facts are kept
   and a warning is returned.
6. The store saves the document and writes `document_added` to the audit table.
7. The browser reloads the matter view (`GET /api/desk/{id}`); the deadlines are recounted from the new facts.

## 3. Where each thing lives

| File | Responsibility |
|---|---|
| `app/main.py` | Routes, session middleware, ownership checks, error mapping, static mounting, `build_app` wiring |
| `app/accounts.py` | Users and sessions. scrypt hashing, 14-day HttpOnly cookie, constant-time compare |
| `app/store.py` | Matters as JSON documents in SQLite, the append-only audit table, profile updates |
| `app/desk.py` | The flat matter view the desk renders, sample matters, return-file import |
| `app/deadlines.py` | The rule engine: validity, notice, payment, complaint windows (decision 0004) |
| `app/matter_dates.py` | Reads dates from papers first, then the advocate's entries; never invents one |
| `app/pipeline.py` | The workflow in order: papers, voice, brief, approval, ask |
| `app/analyzers.py` | The fields read from each paper, and the Content Understanding analyzer definitions |
| `app/services/*.py` | One adapter per Azure service, each behind a protocol in `base.py` |
| `site/build.py` | Renders Jinja templates in `site/src` to `site/dist` |
| `site/src/assets/engine.js` | The browser copy of the rule engine (same worked examples as Python) |
| `site/src/assets/site.js` | Header and mega menu, reveal, live clocks table, Check, sign-in forms |
| `site/src/assets/app.js` | The desk: Today, Matters, Matter, Diary, Drafts, Portfolio, command palette |
| `site/src/assets/data.js` | Fictional sample data, used for the static preview and to seed sample matters |

## 4. API reference

All routes take and return JSON unless noted. Every `/api` route except the five auth routes needs a session.

| Method and path | Does |
|---|---|
| `POST /api/auth/signup` | Create an account (`name, email, password, chambers, kind`) and sign in |
| `POST /api/auth/signin` / `signout` | Start or end a session |
| `GET /api/me` | The signed-in user, the mode and the server's today |
| `GET /api/desk` | Every matter of the user, as views |
| `GET /api/desk/{id}` | One matter view with its activity log |
| `PATCH /api/desk/{id}` | Parties, court, stage, contacts, entered dates |
| `POST /api/desk/{id}/hearings` | Record a hearing and fix the next date |
| `POST /api/desk/{id}/settlement` | Record settlement terms and instalments paid |
| `POST /api/desk/{id}/drafts/approve` | Approve a draft by name |
| `POST /api/desk/samples` | Load the 13 sample matters once |
| `POST /api/desk/import` | Import a return file (CSV) or the sample file |
| `POST /api/desk/assign` | Allocate matters to a panel advocate |
| `POST /api/matters` | Open a matter |
| `POST /api/matters/{id}/documents` | Upload and read a paper (multipart) |
| `PATCH /api/facts/{id}` | Correct or enter a fact (dates validated) |
| `POST /api/matters/{id}/voice` | Transcribe and mask a client's account (multipart) |
| `POST /api/matters/{id}/brief` / `approve` | Draft the AI brief / approve it |
| `POST /api/matters/{id}/ask` | Ask the file through the agent |
| `POST /api/matters/{id}/speak` | Read an approved brief aloud (audio/mpeg) |

## 5. Rules the code keeps

- **A date is never guessed.** A date that is not a valid ISO date is treated as missing, not repaired.
- **A sentence needs a source.** `validate_brief` drops any claim that cites no fact or an unknown fact id, and lists it.
- **Privacy before drafting.** Voice text is masked by AI Language before any model sees it. If masking fails, nothing
  is sent on.
- **Your matters are yours.** A matter of another account answers 404, not 403, so its existence is not revealed.
- **Errors say what to do.** Every user-facing error is a sentence with a remedy, never a code.

## 6. Configuration

See `.env.example`. `TARIKH_MODE` is `live` or `replay`. `TARIKH_EXTRACTOR` is `content_understanding` or `model`
(decision 0006). Data lives in `data/` (SQLite, uploads, cassettes). Nothing secret is stored in the repository; Azure is
reached with Microsoft Entra ID through `DefaultAzureCredential` after `az login`.
