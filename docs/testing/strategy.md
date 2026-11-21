# Testing

| Layer | Where | What it proves | Count |
|---|---|---|---|
| Rule engine (Python) | `tests/test_deadlines.py` | Every window against worked examples, including the Econ Antri reading | part of 114 |
| Rule engine (JS) | `site/tests/engine.test.js` | The browser engine gives the same dates | 11 |
| Accounts and desk API | `tests/test_accounts.py` | Sign-up, sign-in, sign-out, isolation between accounts, entries, hearings, settlement, approvals, import | 7 |
| Pipeline and adapters | `tests/test_api.py`, `test_extraction.py`, `test_reasoning.py`, `test_speech.py`, `test_agent_tools.py`, `test_recorder.py` | Upload checks, source-or-drop brief, masking first, agent tools read-only, record/replay | rest of 114 |
| Website and desk (static) | `site/tests/test_site.py` | Live table, Check, calculator, ordering, drafts gate, allocation, palette, links, no third-party requests, phone menu, reduced motion | 16 |
| End to end (server) | `site/tests/test_live.py` | A browser signs up and works a matter through a running server | 1 |
| Azure, for real | `python -m tools.check_setup` | One real call to each Azure service, PASS or the fix | 6 checks |

Tests never call Azure. The Azure adapters are tested with recorded replies and doubles; the real calls are proved by
`check_setup` on the owner's machine and by the recorded evidence run.
