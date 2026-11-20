
## Implemented

20 Nov 2026: `app/deadlines.py` now ends the complaint month on the same calendar date (`month_after`) and keeps the one-day-earlier reading as `conservative_closes`, which the screens offer as "file by" so the advocate is never shown only one reading. Cheque validity keeps the banking convention (day before). Tests: `tests/test_deadlines.py` (5 new), full suite 109 passing.
