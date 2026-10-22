# API (`/api/v1`, errors are `{"detail":{"code","message"}}`)
| Method & path | Auth | Success | Errors |
|---|---|---|---|
| GET `/health` | – | 200 | – |
| GET `/demo-users` | – | 200 list (masked contacts) | – |
| POST `/auth/register` `{display_name,username,email,phone?,password}` | – | 201 + user (₦0 wallet), sets cookie | 409 duplicate username/email/phone, 422 weak/invalid |
| POST `/auth/login` `{identifier,password}` | – | 200 + user | 401 invalid credentials (generic) |
| POST `/auth/logout` | cookie | 200 | 401 |
| GET `/auth/me`, GET `/users/me` | cookie | 200 own profile (no password hash, ever) | 401 |
| POST `/sessions` `{user_id}` (demo users only) | – | 201 | 404 non-demo/unknown |
| PATCH `/sessions/{id}/heartbeat`, POST `/sessions/{id}/end` | owner | 200 | 403 mismatch |
| GET `/users/resolve?identifier=` | cookie | 200 masked recipient | 404 |
| GET `/wallets/{id}`, `/wallets/{id}/summary`, `/wallets/{id}/transactions?page&page_size&status&direction` | owner only | 200 | 403 other user's wallet |
| POST `/transfers` `{recipient_identifier,amount,description?,idempotency_key}` | cookie | 201 transfer (+`idempotent_replay`) | 400 self, 404 recipient, 409 idempotency conflict, 422 insufficient/invalid amount |
| GET `/transfers/{id}` | participant | 200 + ledger entries | 403/404 |
| GET `/analytics/summary`, `/analytics/events` | cookie | 200 simulation metrics (retries never double-count: counts are over Transfer rows, replays create none) | 401 |
Example transfer: `{"recipient_identifier":"bello","amount":"1000.00","description":"Demo","idempotency_key":"<uuid per logical transfer>"}` → `{"status":"COMPLETED","amount":"1000.00","currency":"NGN",...}`.
