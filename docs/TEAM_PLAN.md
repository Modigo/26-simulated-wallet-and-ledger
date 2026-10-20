# Team plan (Tue MVP → Fri demo)
## David Okwe (@dokwe) — technical lead, 3+ yrs
Owns: `backend/app/services/transfers.py`, `models/`, `core/` (config/security/deps), API contract (`docs/API.md`), integration, final review. Acceptance: atomicity/idempotency tests pass; reviews every change to shared files (`routes.py`, schemas, `App.tsx` shell).
## Ebri Covenant — frontend dashboard & history (~3 mo)
Owns: dashboard/summary cards, transaction list + detail drawer, responsive/loading/empty/error states in `frontend/src/components/App.tsx` (dashboard/history sections) + `lib/api.ts` types. Acceptance: balances from API only (no hardcoded amounts), mobile layout works, empty history state shows.
## Victor Asibe (@vasibe) — registration & transfer experience (~3 mo)
Owns: Welcome/register/login UI, recipient lookup, amount validation, review/confirm/retry UX in `App.tsx` (Welcome/SendMoney). David reviews anything touching auth or transfer authorization. Acceptance: duplicate/invalid-credential states visible; idempotency key reused on retry.
## Oyinkepreye Louis (@Olouis) — coordination, analytics & QA (~3 mo)
Owns: analytics/session UI, seed verification (`python -m app.seed` twice → no duplicates), test execution checklist, README/demo script. Acceptance: `docs/EDGE_CASES.md` all rows checked; demo script rehearsed end-to-end.
**Shared-file rule:** only David merges changes to `routes.py`, `transfers.py`, `models.py`; others open small PRs with the test command they ran. Dependencies: API contract (David, Tue AM) → frontend workstreams → QA pass (Louis, Thu) → demo rehearsal (Fri).
