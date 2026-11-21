# Tarikh

**The litigation platform for cheque-bounce cases in India.** Tarikh reads the cheque, the bank's return memo and the
demand notice, counts every deadline under Section 138 of the Negotiable Instruments Act, drafts the papers an advocate
needs, keeps the hearing diary and prices a settlement. It is built on Microsoft Azure AI as the industrial internship
project for Microsoft Azure AI Fundamentals (AI-901).

- A model reads. A rule counts. A person decides. No model ever produces a deadline.
- Every fact keeps its source: the paper and the box it was read from, or the person who entered it.
- Nothing is filed or sent by Tarikh. Drafts leave draft only when an advocate approves them by name.

## Run it on Windows

You need Python 3.11 or newer and Git. Open **PowerShell**:

```powershell
git clone https://github.com/IIYUSHIN/TARIKH.git
cd TARIKH
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If PowerShell refuses to run `Activate.ps1`, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, answer `Y`,
and try again.

### With Azure (the real thing)

1. Follow [docs/azure-setup.md](docs/azure-setup.md) once. It creates the Foundry project, the three model deployments
   and your access roles, and it ends with your `.env` file.
2. Sign in to Azure from the same PowerShell window: `az login`
3. Check every Azure service with one command. Each line says PASS, or what to fix:
   ```powershell
   python -m tools.check_setup
   ```
4. Start Tarikh:
   ```powershell
   python -m uvicorn app.main:build_app --factory --port 8000
   ```
5. Open <http://localhost:8000>, choose **Start free**, create your account, and open your first matter.

### Without Azure (recorded replies)

Every Azure reply from a live run is saved under `data/cassettes`. To run the whole app offline from those recordings:

```powershell
$env:TARIKH_MODE = "replay"
python -m uvicorn app.main:build_app --factory --port 8000
```

## What is where

| Folder | What it holds |
|---|---|
| `app/` | The server: accounts, matters, the deadline engine, the pipeline and one adapter per Azure service |
| `site/` | The website and the desk: templates, one stylesheet, the browser engine, the build script, browser tests |
| `tests/` | 108 server checks and 9 desk browser checks, run with `pytest` |
| `tools/` | `check_setup` (tests each Azure service), `deploy_models`, `make_samples` |
| `samples/` | Fictional papers, sample matters and a sample return file |
| `docs/` | Engineering record: architecture, decisions, design system, research, Azure guide, testing, prompt ledger |
| `report/` | The project report and the script that builds it |

## Tests

```powershell
pytest                                  # server: accounts, engine, pipeline, Azure adapters (with doubles)
cd site; python build.py; python -m pytest tests; node --test tests/engine.test.js
```

The site tests drive a real browser against both the static site and a running Tarikh server, end to end: sign up,
load samples, enter a date, record a hearing, open a matter, import a return file, allocate, sign out.

## The report

```powershell
python -m report.figures                # diagrams, all in greys so they print in black and white
python -m report.screenshots            # captures the running platform (fictional sample matters)
python -m report.metrics 108 9 17       # measures response times and code size (test counts from pytest --collect-only)
python -m report.build_report --final   # .docx and .pdf; refuses if any open marker remains or the body leaves 20-30 pages
python -m report.print_plan             # which pages need colour ink, plus a colour-only and a black-and-white-only PDF
```

## Read next

- [docs/DEVELOPER.md](docs/DEVELOPER.md): how it is built, how a request moves, where each thing lives
- [docs/decisions/](docs/decisions/): why each important choice was made, and what it costs
- [docs/design/system.md](docs/design/system.md): the design system
- [docs/requirements/prompt-ledger.md](docs/requirements/prompt-ledger.md): every instruction from the project owner, and its status

Not legal advice. Every party, lender and case number in the samples is fictional.
