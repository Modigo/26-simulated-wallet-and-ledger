# Step-by-step: test LedgerLab locally

> The #1 cause of "demo account does not enter" / "sign up failed": only the frontend is running, the backend was started from the wrong folder, or `npm start` is serving an old build. Follow the two-terminal setup exactly.

## Terminal 1 — backend (always start this FIRST)
```bash
cd ledgerlab/backend
pip install -r requirements.txt
python -m app.seed
uvicorn app.main:app --reload --port 8000
```
Check: open http://localhost:8000/health → `{"status":"ok"}`. API explorer: http://localhost:8000/docs

## Terminal 2 — frontend
```bash
cd ledgerlab/frontend
npm install
npm run dev            # use dev for local testing; npm start serves a STALE build unless you ran npm run build again
```
Open http://localhost:3000

## Click-through tests (in order)
1. **Demo login / redirect:** Demo tab → Enter on `adaeze` → you must land on the Dashboard (₦250,000). If you stay on the welcome screen, read the red error box (it now states the exact cause) and check Terminal 1.
2. **Register:** Register tab → Display name `New Tester`, Username `newtester` (lowercase, no spaces), Email `newtester@example.com`, Phone optional, Password at least 8 chars with a letter + number e.g. `Ledger123`, same in Confirm → Create account → Dashboard with **₦0.00**. Weak passwords, duplicate usernames/emails and mismatched confirms now show the exact reason in a red box above the form.
3. **Log out / log in:** Log out (top right) → Log in tab → `newtester` + your password → Dashboard again, history intact. Refresh the page — you stay logged in.
4. **Transfer:** log in as demo `adaeze` → Send money → recipient `newtester` (also try `newtester@example.com`) → ₦1,000 → Review → Confirm → balance ₦249,000. Log in as `newtester` → ₦1,000 received, History shows it.
5. **Failure case:** as `louis`, try ₦999,999 → "Insufficient balance", balance unchanged.
6. **Automated:** `cd ledgerlab/backend && python -m pytest -q` → `8 passed`. `cd ../frontend && npm run build` → success.

## If something fails
| Symptom | Fix |
|---|---|
| "Cannot reach the LedgerLab backend" | Terminal 1 is not running, or runs on another port. Restart it from `ledgerlab/backend`. |
| "No demo accounts loaded" | Run `python -m app.seed` in `ledgerlab/backend`, refresh. |
| Register stays on the form | Read the red box: it names the exact field (password length, duplicate username/email, password mismatch). |
| Page looks old after code changes | You used `npm start`. Use `npm run dev`, or `npm run build && npm start`. Hard-refresh (Ctrl+Shift+R). |
| Port already in use | Stop the old process (Ctrl+C in its terminal) before restarting; only ONE backend on 8000 and ONE frontend on 3000. |
