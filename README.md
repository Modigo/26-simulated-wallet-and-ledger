# LedgerLab — SIMULATION MODE — NO REAL MONEY
Explore how simulated digital money transfers, transaction ledgers, and balance consistency work. **Never use this to process real funds.**

## Features
Demo accounts (adaeze ₦250,000 · bello ₦180,000 · Covenant ₦120,000 · louis ₦75,000), real registration (Argon2id password hash, ₦0 wallet), login/logout, HTTP-only session cookie (only SHA-256 token hash stored), recipient lookup by username/email/Nigerian phone, atomic double-entry transfers, idempotency, history with filters/pagination/detail, simulation analytics, reconciliation (`opening_balance + sum(signed ledger entries) = balance`; DEBIT is negative, CREDIT positive, each pair sums to zero).

## Prerequisites
Python 3.12+, Node 20+, PostgreSQL 16 (or Docker). Local quickstart below uses SQLite so the team can run today without Docker; concurrency semantics are PostgreSQL-grade in Docker/production (see Known limitations).

## Setup & run (local, verified)
```bash
cd backend && python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m app.seed
uvicorn app.main:app --reload --port 8000        # terminal 1 — API docs: http://localhost:8000/docs , health: /health
cd ../frontend && npm install && npm run dev      # terminal 2 — http://localhost:3000
```
## PostgreSQL / Docker
`docker compose up --build` from repo root (db + backend + frontend). Or set `DATABASE_URL=postgresql+psycopg://...` in `backend/.env`, then `alembic upgrade head && python -m app.seed`.
Migrations: Alembic env in `backend/alembic/` (initial revision delegates to model metadata). Reseed: `python -m app.seed` (idempotent, never touches registered users). Destructive local reset only: `LEDGERLAB_ALLOW_RESET=YES_I_UNDERSTAND python reset_db.py`.

## Environment variables
Backend (`backend/.env`): `DATABASE_URL`, `SESSION_SECRET` (generate: `python -c "import secrets; print(secrets.token_urlsafe(48))"`), `CORS_ORIGINS` (comma list, explicit), `COOKIE_SECURE` (`true` in production), `SESSION_TTL_HOURS`. Frontend: `BACKEND_INTERNAL_URL` (server-side proxy target, default `http://127.0.0.1:8000`). No secrets are exposed to the browser.

## Tests
Step-by-step local testing (two terminals, click-through checks, troubleshooting): see `docs/TESTING.md`.

```bash
cd backend && python -m pytest -q   # verified in this workspace: 8 passed (SQLite)
cd ../frontend && npm run build     # verified: production build succeeds
```
PostgreSQL locking tests: run the same pytest suite with `DATABASE_URL=postgresql+psycopg://...` against a disposable test DB — **not yet verified here (no PostgreSQL in this sandbox)**.

## Deployment (manual, not performed here)
**Render step-by-step (Blueprint + manual + verification + troubleshooting): see `docs/DEPLOY_RENDER.md`.**
- DB: create PostgreSQL on Neon/Supabase; copy its connection string (use `postgresql+psycopg://`).
- Backend (Render): build `pip install -r requirements.txt`, start `python -m app.seed && uvicorn app.main:app --host 0.0.0.0 --port $PORT`; set env vars above with `COOKIE_SECURE=true` and CORS = your Vercel URL; health check `/health`.
- Frontend (Vercel): root `frontend/`, set `BACKEND_INTERNAL_URL=https://<your-render-backend>`; the Next rewrite proxies `/api/*` so cookies stay same-origin.
- Checklist: backend `/health` OK → `/docs` loads → demo login → transfer → balances change → refresh persists. Troubleshooting: 401 = cookie/CORS origin mismatch; 500 on register = DB URL scheme; empty demo list = seed not run.

## API
See `docs/API.md`; live OpenAPI at `/docs`. Base path `/api/v1`.

## Security limitations (read this)
Demo mode lets anyone enter a seeded demo identity — by design for classroom demos, **not** production authentication. Registered mode uses Argon2id + hashed session tokens + HTTP-only cookies + ownership checks, but there is no email verification, MFA, or compliance controls. Do not deploy as a real financial service. Phone normalization: digits only; `+234…`/`234…` → leading `0` (Nigerian numbers); usernames/emails are case-insensitive; no partial matching.

## Docs
`docs/ARCHITECTURE.md`, `docs/API.md`, `docs/DEMO_SCRIPT.md`, `docs/FILE_GUIDE.md`, `docs/TEAM_PLAN.md`, `docs/EDGE_CASES.md`, `docs/LEARNING_GUIDE.md`.
