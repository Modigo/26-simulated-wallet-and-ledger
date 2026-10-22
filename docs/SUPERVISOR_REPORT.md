# LedgerLab — Simulated Wallet and Transaction Ledger
### Project Report — SIMULATION MODE: NO REAL MONEY IS PROCESSED AT ANY POINT

**Team:** Okwe David (@dokwe) — Technical Lead · Victor Asibe (@vasibe) — Registration & Transfer Experience · Ebri Covenant — Frontend Dashboard & History · Oyinkepreye Louis (@Olouis) — Project Lead, Analytics & QA
**Stack:** Next.js 14 (App Router, TypeScript, Tailwind CSS, Framer Motion, Lucide) · FastAPI (Python, Pydantic, SQLAlchemy 2, Alembic, Argon2id) · PostgreSQL (Neon) · Render (web services) · Pytest

## 1. Abstract
LedgerLab is a teaching-grade fintech simulation that demonstrates how digital money actually moves: account registration and demo identities, recipient resolution, atomic double-entry transfers, idempotent retries, a verifiable ledger, transaction history, and simulation analytics — deployed live on Render with a Neon PostgreSQL database.

## 2. Problem statement and objectives
Novices often see only the surface of fintech apps. LedgerLab makes the invisible parts visible: (1) money moves as balanced ledger entries, not by editing a number; (2) a transfer is atomic — it completes fully or not at all; (3) retries must never double-charge (idempotency); (4) balances must always reconcile with the ledger; (5) users must never reach another user's wallet.

## 3. System architecture
Browser → Next.js frontend → same-origin `/api/*` server-side proxy → FastAPI → SQLAlchemy → Neon PostgreSQL. The proxy keeps session cookies on the frontend domain and avoids CORS exposure of credentials. Key flows: a transfer request derives the sender from the server-side session (never from the request body), locks both wallets in deterministic ID order (`SELECT … FOR UPDATE`), checks funds, then writes the balance updates, the transfer record, and a paired DEBIT (−amount) / CREDIT (+amount) ledger entry in **one database transaction** — any failure rolls everything back. Signed ledger entries per transfer sum to exactly zero, and `opening_balance + Σ(signed entries) = stored balance` is verified by a reconciliation function and by automated tests.

## 4. Data model
`users` (username/email/phone unique & normalized, Argon2id password hash — plaintext is never stored, `is_demo` flag) · `wallets` (one per user, NGN, `balance`, `opening_balance`, non-negative check constraint) · `transfers` (sender/recipient wallets, Decimal amount, status COMPLETED/REJECTED, `idempotency_key` + `request_hash`, unique `(sender_wallet, idempotency_key)`) · `ledger_entries` (signed double-entry rows per transfer) · `sessions` (only the SHA-256 hash of the session token is stored; expiry + explicit end) · `analytics_events` (server-side product events, isolated so analytics failures can never affect money movement). Money is always `NUMERIC(14,2)`/Decimal — never floats.

## 5. Key features implemented
- **Two access modes:** one-click seeded demo accounts and real registration/login (new wallets start at ₦0.00; duplicate username/email/phone rejected case-insensitively with clear inline messages).
- **Seeded demo users (current):** dokwe — Okwe David (Dokwe.david@example.com, 08030000002, ₦250,000) · victor — Victor Asibe (Victor.Aibe@example.com, 08030000001, ₦180,000) · Covenant — Ebri Covenant (Covenant@example.com, 08030000003, ₦120,000) · louis — Oyinkepreye Louis (louis@example.com, 08030000004, ₦75,000). Seeding is idempotent and now *identity-syncing*: renaming a demo user updates the existing row (matched by username/email/phone) while preserving wallet, balance, and history — this fixed a real production crash (`UniqueViolation` on phone) encountered during deployment.
- **Recipient resolution:** by username, email, or Nigerian phone (`+234…`/`234…` normalized to `0…`), case-insensitive, no partial matching — now resolving **automatically as the user types** (debounced live lookup with searching/found/not-found states, giving a real-time feel without introducing websocket infrastructure the project deliberately avoids).
- **Transfers:** full validation (self-transfer, zero/negative, >2 decimal places, maximum, insufficient funds), review-and-confirm step, stable idempotency key per logical transfer — replaying the same key returns the original result (`idempotent_replay`), reusing it with a different payload returns HTTP 409.
- **History & analytics:** newest-first pagination, status/direction filters, transaction detail drawer showing the paired ledger entries, and a simulation-analytics view (volumes, counts, rejected attempts, session times).
- **Sessions:** tab-scoped — a session persists across refreshes and in-app navigation, ends on logout/tab close/new tab, and starting a new session invalidates the previous one; registered credentials persist in PostgreSQL for seamless re-login.
- **Experience:** dark petroleum-navy/teal fintech palette with amber simulation labelling, **light/dark mode toggle** (remembered per browser), animated balance changes, loading skeletons, a **first-time visitor walkthrough** (4 steps), and a cold-start "waking up the demo server" state with automatic retries instead of a false error.

## 6. Deployment and operational findings
Frontend and backend run as Render web services; the database was migrated from Render PostgreSQL to **Neon PostgreSQL** (serverless, does not expire like free Render Postgres). Migration assessment: Neon is fully compatible — connection is via `DATABASE_URL` (`postgres://` URLs are normalized to the psycopg-3 driver form automatically, and Neon's `sslmode=require` parameter is passed through). **Two caveats found and handled:** (1) Neon's pooled (`-pooler`) endpoint is recommended for the API; direct connections also work at this scale. (2) The remaining "slow first load" is **not** the database: Render free web services sleep after inactivity, so the first request waits 30–60s for the backend to wake. The UI now retries for up to ~60s showing a waking-up state. Permanent elimination requires either a paid (always-on) Render plan for `ledgerlab-api`, or an external uptime ping (e.g. a free cron hitting `/health` every ~10 minutes) — a configuration choice, not a code defect. Each manual redeploy during the incident was a workaround for this sleep behaviour, not a requirement.

## 7. Testing
Automated backend suite (Pytest, 9 tests — all passing) covers: happy-path transfer with balanced ledger entries, recipient resolution by username/email/phone, self/zero/over-precision/insufficient-funds rejection, idempotent replay and payload-conflict (409), registration with ₦0 wallet, duplicate username/email rejection, Argon2id login/logout, seamless re-login after logout, tab-scoped cookie properties, cross-user wallet authorization (403), empty-history pagination, and ledger reconciliation. The frontend production build passes. End-to-end flows (demo entry, registration, transfer, both-side balance check) were additionally exercised in a real browser against the running stack.

## 8. Security considerations and limitations
Passwords use Argon2id; only token hashes are stored; cookies are HTTP-only (+Secure in production); wallet/transfer endpoints enforce ownership from the session, never client-supplied IDs; explicit CORS origins; lightweight in-memory rate limiting. **Limitations (stated openly):** demo identities are intentionally password-less for classroom use and are not production authentication; no email verification, MFA, or regulatory compliance is implemented; free-tier hosting sleeps; PostgreSQL is the sole source of truth — running the API without it is blocked by a startup guard because ephemeral SQLite silently discarded registered users during early deployment testing.

## 9. Team contributions
David Okwe (lead): architecture, API contract, transfer/ledger core, locking, idempotency, integration. Ebri Covenant: dashboard, summary cards, history & detail views, responsive states. Victor Asibe: registration/login and transfer UI, recipient lookup, confirmation/retry UX. Oyinkepreye Louis (project lead): coordination, analytics/session UI, seed & demo data verification, QA execution, documentation and demo readiness.

## 10. Conclusion and future work
LedgerLab meets its MVP objectives live in production. Natural next steps: always-on hosting (or scheduled health pings) to remove cold starts, websocket/SSE push for instant recipient-side balance updates, deposits/withdrawals against a simulated provider, richer analytics charts, and a PostgreSQL-backed concurrency test in CI.

## Appendix A — 60-second verification
`GET /health` → `{"status":"ok","service":"LedgerLab","simulation":true}` · `GET /api/v1/demo-users` → 4 users · in the app: enter as `dokwe`, send ₦5,000 to `victor`, open the transaction to see DEBIT/CREDIT sum to ₦0.00, log in as `victor` to see ₦185,000.
## Appendix B — Repository guide
`backend/app` (API, services, models), `frontend/src` (UI), `docs/` (architecture, API, demo script, testing, deployment, this report), `render.yaml` (one-click Render Blueprint). Setup: `docs/TESTING.md`; deployment: `docs/DEPLOY_RENDER.md`.
