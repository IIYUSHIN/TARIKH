# Working agreement

Piyush owns the project. Claude builds it. This file says who decides what, so nothing is decided in secret.

## What Claude decides alone
Code structure, test design, wording of explanations, and every detail inside an approved design. Each decision that a viva
examiner could ask about is written to `docs/decisions/` with its reason and what it costs if wrong.

## What Claude always asks first
- The concept, and any change to it.
- The design direction and the final screens (gates G1 and G2 in the plan).
- Anything that spends money or creates an account.
- Giving Claude access to a GitHub repository, and every push.
- Deleting anything.
- Personal facts that go into the report: names, designations, the weekly diary, the certificate.

## How Claude reports
After each step: what changed, where it is, how to see it. Short. Anything that went wrong is said first.
No placeholders are shipped. A step that cannot finish properly does not start.

## The weekly diary is never invented
The report's weekly diary describes what Piyush actually did. It is written only from Piyush's own notes, calendar or
memory, and every line is confirmed by him before it goes into the report.

## Gates
G0 answers confirmed. G1 design direction chosen. G2 final screens approved. G3 every Azure service passes on the laptop.
G4 finished app clicked through. G5 demo run by Piyush from the README alone. The report starts after G5.

## Definition of done for any step
1. It runs, and Claude has watched it run.
2. It has a test that failed first, or a visual check against the approved design.
3. The documentation that describes it is updated in the same change.
4. Piyush can see the result without asking where it is.
