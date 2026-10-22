# Edge cases (all covered in `backend/tests/test_ledgerlab.py` unless noted)
| # | Case | Expected | Test |
|---|---|---|---|
|1|Valid transfer|201, balances ±amount, 2 ledger entries sum 0|test_valid_transfer_and_ledger|
|2-4|Recipient by username/email/phone (+234 normalized)|200 resolve|test_recipient_by_email_and_phone|
|5|Unknown recipient|404, no changes|same|
|6|Self-transfer|400|test_validation_self_insufficient|
|7-8|Zero / 3-decimal amount|422|same|
|9|Insufficient funds|422, REJECTED row, no ledger entries|same + ledger test|
|10|Concurrent spend|PostgreSQL row locks serialize; run pytest with PG DATABASE_URL (unverified here)|manual/PG|
|11-13|Double-submit / same key same payload / different payload|replay original / 409|test_valid_transfer_and_ledger|
|14,17|Mid-transfer DB error|full rollback (single transaction)|design; reconcile test|
|15|Timeout after commit|retry same key returns original|idempotent replay test|
|16|Refresh after transfer|server state persists (cookie session)|test via /auth/me|
|18|Pagination & empty history|page metadata, empty list|test_pagination_empty|
|19,31|Invalid/expired session|401|test_unauthenticated_and_logout|
|20|Analytics failure|transfer unaffected (isolated writes)|design|
|21|Reconciliation|opening + Σsigned entries = balance|test_registered_can_receive_and_reconcile|
|22,32|Other user's wallet|403|test_register_zero_balance_duplicates_authz|
|23-30,33-34|Registration, duplicates (case-insensitive), ₦0 wallet, hashing (Argon2id, never returned), login/logout, registered send/receive, reseed safety|as specified|register tests; reseed = run seed twice, registered balances unchanged (manual check in TEAM_PLAN)|
