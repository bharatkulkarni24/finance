Functional requirements — Sri Lakshmi Venkateshwara Finance

Status legend: not-started | in-progress | completed

1. Core UI/DB
- Replace members list with provided 12 names (completed)
- DB seeded with joined_date = 2025-03-30, initial deposit 25000, shares Apr-2025→Jun-2026 (completed)

2. Authentication & Roles
- Admin login via name + ADMIN_PIN (completed)
- Member login via name (completed)

3. Payments / Requests
- Members can submit payment requests with screenshot and optional txn_date (completed)
- Admin can approve requests (completed)
- Admin can reject requests with reason (completed)
- Members can cancel their pending requests (completed)

4. Date handling
- txn_date selectable when submitting payment/loan requests (completed)
- Validate txn_date client-side to prevent future dates (completed)

5. Profile
- Members can edit phone/dob/address (completed)
- Members can upload profile photo (upload endpoint exists; UI wired) (completed)

6. Admin features
- Admin panel shows pending payments and loans (completed)
- Admin can add funds (completed)
- Admin stats: total collected, deposit/share breakdown, loan lent/outstanding (completed)
- Admin direct entry: record payment on behalf of a member (auto-approved) with share, fine, loan, interest (completed)
- Hardlock / Investment section: dual-purpose support for one-time FD investments and monthly schemes (gold investment). Monthly schemes allow adding varying amount installments via + button, with batch closing at maturity. Interest rate optional (0 for gold schemes) (completed)

7. UX
- Replace alerts with toast notifications (completed)
- Add hero background & animations (completed)
- Kannada translations + toggle (completed for core keys; expand as needed)

8. Logging & Diagnostics
- Server logging to logs/server.log (completed)
- Admin logs endpoint (completed)
- Client-side error reporting endpoint (completed)

Notes & next actions:
- Expand Kannada translations across all UI strings (low effort; I can add more keys).
- Replace `prompt()` usages for admin inputs with modals (recommended for UX).
- Add automated unit/functional tests for critical flows (login, submit/approve/reject/cancel request).
- Consider stronger auth (sessions, passwords) for production.

Update this file as features are completed or changed.
