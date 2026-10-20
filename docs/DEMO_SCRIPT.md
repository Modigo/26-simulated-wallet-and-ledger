# 3–5 minute demo script
1. (30s) Point at **SIMULATION MODE — NO REAL MONEY**. Enter demo as **adaeze** (₦250,000).
2. (60s) Send money → recipient `bello` (show it also resolves by `Bello.Adebayo@example.com` and `+234 803 000 0002`) → ₦5,000, description "Friday demo" → Review → Confirm. Balance animates to ₦245,000.
3. (45s) History → open the transaction → show reference, both participants, DEBIT −5,000 / CREDIT +5,000 ledger entries summing to zero.
4. (45s) Log out, enter as **bello**: balance ₦185,000, incoming +₦5,000 in history — both sides reconcile.
5. (45s) Duplicate protection: explain the idempotency key is fixed per logical transfer; retrying (e.g. after a timeout) returns the original with `idempotent_replay`, never a second debit. (DevTools: replay the POST in the backend tests — `test_valid_transfer_and_ledger`.)
6. (30s) Failure case: try sending ₦999,999 from louis → **Insufficient balance**, form preserved, no ledger entries, balance unchanged.
7. (30s) Analytics tab: simulation metrics + session times. Close with limitations: demo identities are classroom-only; no real money, no external banks; production would need real auth, compliance, and operations.
Also demo registration: Register → ₦0 wallet → receive ₦500 from adaeze → log out/in, history persists.
