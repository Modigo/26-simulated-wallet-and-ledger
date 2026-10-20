from datetime import datetime, timezone
from fastapi import Request, HTTPException, Depends
from sqlalchemy.orm import Session as DBSession
from app.core.database import get_db
from app.core.security import token_hash
from app.models.models import Session, User
def get_current_session(request:Request, db:DBSession=Depends(get_db)):
    token=request.cookies.get("ledgerlab_session")
    if not token: raise HTTPException(401,{"code":"INVALID_SESSION","message":"Please sign in again"})
    s=db.query(Session).filter_by(session_token_hash=token_hash(token)).first()
    exp=s.expires_at.replace(tzinfo=timezone.utc) if s and s.expires_at and s.expires_at.tzinfo is None else (s.expires_at if s else None)
    if not s or s.ended_at is not None or exp < datetime.now(timezone.utc):
        raise HTTPException(401,{"code":"SESSION_EXPIRED","message":"Session expired. Please sign in again"})
    s.last_seen_at=datetime.now(timezone.utc); db.commit()
    return s
def get_current_user(session=Depends(get_current_session), db:DBSession=Depends(get_db)):
    u=db.get(User, session.user_id)
    if not u: raise HTTPException(401,{"code":"INVALID_SESSION","message":"User not found"})
    return u
def require_own_wallet(wallet_id:str, user):
    if not user.wallet or user.wallet.id!=wallet_id: raise HTTPException(403,{"code":"FORBIDDEN","message":"You can only access your own wallet"})
