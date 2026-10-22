import hashlib, json
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from app.models.models import Wallet, Transfer, LedgerEntry
from app.core.config import settings
from app.services.analytics import record
def request_hash(recipient_wallet_id, amount, description):
    payload=json.dumps({"r":recipient_wallet_id,"a":str(amount),"d":description or ""},sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()
def create_transfer(db, sender_user, recipient_user, amount:Decimal, description, idempotency_key, session_id=None):
    if recipient_user.id==sender_user.id: raise HTTPException(400,{"code":"SELF_TRANSFER","message":"You cannot send money to yourself"})
    if amount<=0: raise HTTPException(422,{"code":"INVALID_AMOUNT","message":"Amount must be greater than zero"})
    if amount>Decimal(settings.max_transfer_ngn): raise HTTPException(422,{"code":"AMOUNT_TOO_LARGE","message":"Amount exceeds the simulation maximum"})
    if not sender_user.wallet or not recipient_user.wallet: raise HTTPException(404,{"code":"WALLET_NOT_FOUND","message":"Wallet not found"})
    if sender_user.wallet.currency!=recipient_user.wallet.currency: raise HTTPException(400,{"code":"CURRENCY_MISMATCH","message":"Cross-currency transfers are not supported"})
    rh=request_hash(recipient_user.wallet.id,amount,description)
    existing=db.query(Transfer).filter_by(sender_wallet_id=sender_user.wallet.id,idempotency_key=idempotency_key).first()
    if existing:
        if existing.request_hash!=rh: raise HTTPException(409,{"code":"IDEMPOTENCY_CONFLICT","message":"This idempotency key was already used with a different transfer"})
        record(db,"transfer_retry_detected",sender_user.id,session_id,{"transfer_id":existing.id}); db.commit(); return existing, True
    # Deterministic lock order prevents deadlocks (PostgreSQL FOR UPDATE)
    wallets=db.query(Wallet).filter(Wallet.id.in_([sender_user.wallet.id,recipient_user.wallet.id])).order_by(Wallet.id).with_for_update().all()
    by_id={w.id:w for w in wallets}
    sw, rw = by_id[sender_user.wallet.id], by_id[recipient_user.wallet.id]
    if sw.balance < amount:
        # Persist a REJECTED attempt for audit, with no ledger entries / no balance change
        t=Transfer(sender_wallet_id=sw.id,recipient_wallet_id=rw.id,amount=amount,description=description,status="REJECTED",idempotency_key=idempotency_key,request_hash=rh)
        db.add(t); record(db,"transfer_rejected",sender_user.id,session_id,{"reason":"insufficient_funds"}); db.commit()
        raise HTTPException(422,{"code":"INSUFFICIENT_FUNDS","message":"Insufficient balance for this transfer","transfer_id":t.id})
    try:
        sw.balance-=amount; rw.balance+=amount
        t=Transfer(sender_wallet_id=sw.id,recipient_wallet_id=rw.id,amount=amount,description=description,status="COMPLETED",idempotency_key=idempotency_key,request_hash=rh,completed_at=datetime.now(timezone.utc))
        db.add(t); db.flush()
        db.add_all([LedgerEntry(transfer_id=t.id,wallet_id=sw.id,entry_type="DEBIT",amount=-amount),LedgerEntry(transfer_id=t.id,wallet_id=rw.id,entry_type="CREDIT",amount=amount)])
        record(db,"transfer_submitted",sender_user.id,session_id,{"transfer_id":t.id}); record(db,"transfer_succeeded",sender_user.id,session_id,{"transfer_id":t.id})
        db.commit(); db.refresh(t); return t, False
    except IntegrityError:
        db.rollback()
        existing=db.query(Transfer).filter_by(sender_wallet_id=sender_user.wallet.id,idempotency_key=idempotency_key).first()
        if existing and existing.request_hash==rh: return existing, True
        if existing: raise HTTPException(409,{"code":"IDEMPOTENCY_CONFLICT","message":"Duplicate key with different payload"})
        raise
    except Exception:
        db.rollback(); raise
def reconcile_wallet(db, wallet):
    total=db.query(LedgerEntry).filter_by(wallet_id=wallet.id).all()
    derived=wallet.opening_balance+sum((e.amount for e in total),Decimal("0.00"))
    return {"wallet_id":wallet.id,"stored_balance":wallet.balance,"ledger_derived_balance":derived,"opening_balance":wallet.opening_balance,"discrepancy":wallet.balance-derived,"ok":wallet.balance==derived}
