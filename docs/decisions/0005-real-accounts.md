# 0005. Real accounts, not a demo

Status: accepted, 21 November 2026

## Context
The owner's review of v2: the product read as a demo ("Open the demo", sample data in the browser, nothing saved). A real
service needs a person to create an account, open matters and come back to them.

## Decision
- Accounts live in the same SQLite file as matters (`app/accounts.py`). Passwords are hashed with scrypt from the
  standard library (n=2^14, r=8, p=1, 16-byte salt); comparison is constant-time.
- A session is a 32-byte random token in an HttpOnly, SameSite=Lax cookie, valid 14 days. Signing out deletes it.
- Every matter has an `owner`. A request for another person's matter answers 404.
- The desk's own data (parties, court, stage, hearings, settlement, approvals, entered dates) lives in `Matter.profile`
  and every change writes the audit table.
- A static copy of the site (for example the shared artifact link) has no server. The desk then opens in an honest
  **preview** with sample matters and says that nothing is saved.

## Alternatives rejected
- Microsoft Entra External ID for sign-in: right for production, but it needs a tenant and app registration the owner
  cannot set up inside the internship's time, and it would hide the auth flow the report must explain.
- Keeping matters in the browser: nothing would survive a cleared cache or a second device.

## Costs if wrong
No password reset or email verification yet; one SQLite file limits the service to one machine. Both are listed in the
report's future work. Moving to Entra External ID changes `accounts.py` and the middleware only.
