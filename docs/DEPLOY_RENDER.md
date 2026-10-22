# Deploy LedgerLab to Render — step by step

Architecture on Render: `ledgerlab-db` (PostgreSQL) + `ledgerlab-api` (FastAPI) + `ledgerlab-web` (Next.js).
The browser only talks to the frontend; Next.js proxies `/api/*` server-side to the backend
(`BACKEND_INTERNAL_URL`), so login cookies stay on the frontend domain. Demo data is seeded
automatically on every backend start (`python -m app.seed` is idempotent — redeploys never duplicate
demo users and never touch registered users).

## Step 0 — Put the code on GitHub (Render deploys from Git)
```bash
cd ledgerlab
git init && git add . && git commit -m "LedgerLab MVP"
git branch -M main
git remote add origin https://github.com/<your-username>/ledgerlab.git   # create the empty repo on github.com first
git push -u origin main
```

## Option A — Blueprint (fastest, recommended)
1. Go to https://dashboard.render.com → sign in with GitHub.
2. **New → Blueprint** → select your `ledgerlab` repository.
3. Render reads `render.yaml` in the repo root and proposes 3 resources: `ledgerlab-db`, `ledgerlab-api`, `ledgerlab-web`. Names matter: if you rename a service here, afterwards update
   `BACKEND_INTERNAL_URL` (on ledgerlab-web) and `CORS_ORIGINS` (on ledgerlab-api) to the real `*.onrender.com` URLs and redeploy.
4. **Apply / Create.** Free instances spin down when idle — the first request after idle can take ~30–60s.
5. Wait for `ledgerlab-db` (Available), then `ledgerlab-api` (Live), then `ledgerlab-web` (Live) — in that order.

## Option B — Manual (same result, more clicks)
1. **New → PostgreSQL** → name `ledgerlab-db` → Create. Open it → copy the **Internal Database URL**.
2. **New → Web Service** → connect the repo → Name `ledgerlab-api`, Root Directory `backend`, Runtime `Python 3`,
   Build `pip install -r requirements.txt`, Start `python -m app.seed && uvicorn app.main:app --host 0.0.0.0 --port $PORT`, Health Check Path `/health`.
   Environment: `DATABASE_URL` = the Internal Database URL from step 1 (paste as-is — the app converts it to the psycopg-3 form),
   `SESSION_SECRET` = run locally `python -c "import secrets; print(secrets.token_urlsafe(48))"` and paste the output,
   `COOKIE_SECURE=true`, `CORS_ORIGINS=https://<your-frontend>.onrender.com` (fill in after step 3, then redeploy this service).
3. **New → Web Service** → Name `ledgerlab-web`, Root Directory `frontend`, Runtime `Node`,
   Build `npm install && npm run build`, Start `npm start`.
   Environment: `BACKEND_INTERNAL_URL=https://<your-backend>.onrender.com`, `NODE_VERSION=20`.
   ⚠️ `BACKEND_INTERNAL_URL` is baked in at **build** time: if you change it later, use **Manual Deploy → Clear build cache & deploy**.

## Step 3 — Verify (in this order)
1. `https://ledgerlab-api.onrender.com/health` → `{"status":"ok",...}` (wake it first if it slept).
2. `https://ledgerlab-api.onrender.com/api/v1/demo-users` → 4 demo users with balances (means Postgres + seed worked).
3. `https://ledgerlab-web.onrender.com` → Demo tab → Enter **adaeze** (₦250,000) → Send ₦1,000 to `bello` → Dashboard updates.
4. Register a new account → ₦0.00 wallet → log out → log back in. Refresh the page — you stay logged in.
5. Redeploy test: Render → ledgerlab-api → **Manual Deploy** → after it is Live, balances and registered users are unchanged.

## Troubleshooting
| Symptom | Cause / fix |
|---|---|
| api build or boot fails with `No module named psycopg2` / driver error | Old deploy before the URL fix — redeploy latest code; the app now rewrites `postgres://…` to `postgresql+psycopg://…` automatically. |
| web loads but "Cannot reach the LedgerLab backend" / demo list empty | `BACKEND_INTERNAL_URL` wrong or backend asleep/down. Open the api `/health` URL directly, fix the variable, then **Clear build cache & deploy** the web service. |
| Register/login spins then 401/cookie errors | `COOKIE_SECURE` must be `true` on Render (HTTPS), and you must always use the `https://` frontend URL, not http. |
| First page load very slow | Free instance was asleep. Wait ~60s and refresh; upgrade the plan or keep defaults knowing this is expected on free tier. |
| Demo users missing after deploy | Check ledgerlab-api logs for `Seed complete (idempotent)`; the start command runs the seed — if the start command was edited, restore it. |
| CORS error in browser console | Browser should only call the frontend domain (same-origin `/api`). If you changed the frontend to call the api domain directly, set `CORS_ORIGINS` on ledgerlab-api to the exact frontend origin and redeploy. |

## After it works
- Render → ledgerlab-api → Settings → Health Check Path should be `/health`.
- Never commit a real `.env`; all secrets live in Render's Environment tab only.
- Remember: SIMULATION MODE — no real money; demo identities are classroom access, not production authentication.
