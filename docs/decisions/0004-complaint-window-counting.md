# 0004 The complaint window excludes the cause-of-action date

**Status:** Accepted from secondary sources on 20 November 2026. Must be re-checked against the judgment's own text in step 13.

**Context:** Section 142(1)(b) requires the complaint within one month of the date on which the cause of action arises under
Section 138(c). The cause of action arises on the day after the drawer's 15 days to pay end.

In *Econ Antri Ltd. v. Rom Industries Ltd.* (Supreme Court, three judges, 26 August 2013), the Court held that the one-month
period is counted by excluding the date on which the cause of action arose, applying Section 9 of the General Clauses Act, 1897.
The worked dates recounted from *Saketh India Ltd. v. India Securities Ltd.*: notice received 29 September 1995, 15 days ended
14 October, cause of action 15 October, which is excluded; the complaint filed on 15 November was in time.

**Decision:** The new engine counts the complaint window as starting the day after the cause-of-action date and ending on the
same calendar day one month later. Example: payment period ends 18 November, cause of action 19 November, last day to file
19 December.

**Why:** It follows the Supreme Court's holding. v0 ended the window one day early (18 December).

**Cost if wrong:** If the reading is wrong, the screen shows a deadline a day late, which is the dangerous direction for an
advocate. Mitigation: the screen also states the rule used and the case, so the advocate can check it.

**Still open, to be researched in step 13:** the validity period of the cheque (RBI, three months) and how its first day is
counted; month-end handling when the target day does not exist; second and later presentations of the same cheque.

**Sources read so far (summaries and extracts, not the full judgment):** [Econ Antri summary](https://www.legalauthority.in/judgement/m-s-econ-antri-ltd-vs-m-s-rom-industries-ltd-6055),
[AIR 2013 SC 3283 headnote](https://www.aironline.in/legal-judgements/AIR+2013+SUPREME+COURT+3283).

## Implemented

20 Nov 2026: `app/deadlines.py` now ends the complaint month on the same calendar date (`month_after`) and keeps the one-day-earlier reading as `conservative_closes`, which the screens offer as "file by" so the advocate is never shown only one reading. Cheque validity keeps the banking convention (day before). Tests: `tests/test_deadlines.py` (5 new), full suite 109 passing.
