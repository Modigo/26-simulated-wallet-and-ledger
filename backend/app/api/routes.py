from datetime import datetime, timezone, timedelta
from decimal import Decimal
from collections import defaultdict
import time
from fastapi import APIRouter, Depends, HTTPException, Request, Response, Query
from sqlalchemy.orm import Session as DBS
from sqlalchemy import or_, func
from app.core.database import get_db
from app.core.config import settings
from app.core.security import hash_password, verify_password, new_token, token_hash
from app.core.deps import get_current_user, get_current_session, require_own_wallet
from app.models.models import User, Wallet, Transfer, LedgerEntry, Session, AnalyticsEvent
from app.schemas.schemas import RegisterIn, LoginIn, DemoSessionIn, TransferIn
from app.services.users import resolve_user, public_user, full_user, normalize_phone
from app.services.transfers import create_transfer, reconcile_wallet
from app.services.analytics import record
router=APIRouter(prefix="/api/v1")
hits=defaultdict(list)
def rate_limit(request, key, limit=30, window=60):
    now=time.time(); ip=request.client.host if request.client else "unknown"; k=f"{key}:{ip}"
    hits[k]=[t for t in hits[k] if now-t<window]
    if len(hits[k])>=limit: raise HTTPException(429,{"code":"RATE_LIMITED","message":"Too many requests. Please wait and try again."})
    hits[k].append(now)
def start_session(db, response, user, request):
    token=new_token(); s=Session(user_id=user.id,session_token_hash=token_hash(token),expires_at=datetime.now(timezone.utc)+timedelta(hours=settings.session_ttl_hours))
    db.add(s); record(db,"demo_session_started" if user.is_demo else "session_started",user.id,None,{}); db.commit(); db.refresh(s)
    # analytics session link fix
    ev=db.query(AnalyticsEvent).filter_by(user_id=user.id,session_id=None).order_by(AnalyticsEvent.created_at.desc()).first()
    if ev: ev.session_id=s.id; db.commit()
    response.set_cookie("ledgerlab_session",token,httponly=True,secure=settings.cookie_secure,samesite="lax",max_age=settings.session_ttl_hours*3600,path="/")
    return s
def transfer_out(db,t,wallet_id=None):
    sw=db.get(Wallet,t.sender_wallet_id); rw=db.get(Wallet,t.recipient_wallet_id)
    direction=None
    if wallet_id: direction="OUTGOING" if t.sender_wallet_id==wallet_id else "INCOMING"
    return {"id":t.id,"reference":t.id,"sender_wallet_id":t.sender_wallet_id,"recipient_wallet_id":t.recipient_wallet_id,"sender":public_user(sw.user) if sw else None,"recipient":public_user(rw.user) if rw else None,"amount":t.amount,"currency":t.currency,"description":t.description,"status":t.status,"direction":direction,"created_at":t.created_at,"completed_at":t.completed_at}
@router.get("/demo-users")
def demo_users(db:DBS=Depends(get_db)): return [full_user(u) for u in db.query(User).filter_by(is_demo=True).order_by(User.username).all()]  # demo contacts are fictional example.com data, shown in full so presenters can demonstrate lookup
@router.post("/auth/register",status_code=201)
def register(payload:RegisterIn,request:Request,response:Response,db:DBS=Depends(get_db)):
    rate_limit(request,"register",10)
    if db.query(User).filter(func.lower(User.username)==payload.username).first(): raise HTTPException(409,{"code":"USERNAME_TAKEN","message":"That username is already taken"})
    if db.query(User).filter(func.lower(User.email)==payload.email).first(): raise HTTPException(409,{"code":"EMAIL_TAKEN","message":"That email is already registered"})
    phone=normalize_phone(payload.phone) if payload.phone else None
    if phone and db.query(User).filter_by(phone=phone).first(): raise HTTPException(409,{"code":"PHONE_TAKEN","message":"That phone number is already registered"})
    u=User(username=payload.username,display_name=payload.display_name.strip(),email=payload.email,phone=phone,password_hash=hash_password(payload.password),is_demo=False)
    db.add(u); db.flush(); db.add(Wallet(user_id=u.id,balance=Decimal("0.00"),opening_balance=Decimal("0.00"))); db.commit(); db.refresh(u)
    s=start_session(db,response,u,request); return {"user":full_user(u),"session_id":s.id}
@router.post("/auth/login")
def login(payload:LoginIn,request:Request,response:Response,db:DBS=Depends(get_db)):
    rate_limit(request,"login",20)
    u=resolve_user(db,payload.identifier)
    if not u or u.is_demo or not verify_password(payload.password,u.password_hash): raise HTTPException(401,{"code":"INVALID_CREDENTIALS","message":"Invalid credentials"})
    s=start_session(db,response,u,request); return {"user":full_user(u),"session_id":s.id}
@router.post("/auth/logout")
def logout(response:Response,session=Depends(get_current_session),db:DBS=Depends(get_db)):
    session.ended_at=datetime.now(timezone.utc); db.commit(); response.delete_cookie("ledgerlab_session",path="/"); return {"ok":True}
@router.get("/auth/me")
def me(user=Depends(get_current_user)): return full_user(user)
@router.get("/users/me")
def users_me(user=Depends(get_current_user)): return full_user(user)
@router.get("/users/resolve")
def resolve(identifier:str,request:Request,db:DBS=Depends(get_db),user=Depends(get_current_user),session=Depends(get_current_session)):
    rate_limit(request,"resolve",60); u=resolve_user(db,identifier)
    if not u:
        record(db,"recipient_lookup_failed",user.id,session.id,{}); db.commit(); raise HTTPException(404,{"code":"RECIPIENT_NOT_FOUND","message":"No user matches that username, email or phone number"})
    record(db,"recipient_lookup_succeeded",user.id,session.id,{"recipient_id":u.id}); db.commit(); return public_user(u)
@router.post("/sessions",status_code=201)
def demo_session(payload:DemoSessionIn,request:Request,response:Response,db:DBS=Depends(get_db)):
    rate_limit(request,"demo",30); u=db.get(User,payload.user_id)
    if not u or not u.is_demo: raise HTTPException(404,{"code":"DEMO_USER_NOT_FOUND","message":"Demo account not found"})
    s=start_session(db,response,u,request); return {"user":full_user(u),"session_id":s.id,"started_at":s.started_at,"last_seen_at":s.last_seen_at}
@router.patch("/sessions/{session_id}/heartbeat")
def heartbeat(session_id:str,session=Depends(get_current_session),db:DBS=Depends(get_db)):
    if session.id!=session_id: raise HTTPException(403,{"code":"FORBIDDEN","message":"Session mismatch"})
    session.last_seen_at=datetime.now(timezone.utc); db.commit(); return {"ok":True,"last_seen_at":session.last_seen_at}
@router.post("/sessions/{session_id}/end")
def end_session(session_id:str,response:Response,session=Depends(get_current_session),db:DBS=Depends(get_db)):
    if session.id!=session_id: raise HTTPException(403,{"code":"FORBIDDEN","message":"Session mismatch"})
    session.ended_at=datetime.now(timezone.utc); db.commit(); response.delete_cookie("ledgerlab_session",path="/"); return {"ok":True}
@router.get("/wallets/{wallet_id}")
def wallet(wallet_id:str,user=Depends(get_current_user),db:DBS=Depends(get_db)):
    require_own_wallet(wallet_id,user); w=user.wallet
    return {"id":w.id,"user_id":w.user_id,"currency":w.currency,"balance":w.balance,"created_at":w.created_at,"updated_at":w.updated_at,"reconciliation":reconcile_wallet(db,w)}
@router.get("/wallets/{wallet_id}/summary")
def summary(wallet_id:str,user=Depends(get_current_user),db:DBS=Depends(get_db)):
    require_own_wallet(wallet_id,user)
    ts=db.query(Transfer).filter(or_(Transfer.sender_wallet_id==wallet_id,Transfer.recipient_wallet_id==wallet_id),Transfer.status=="COMPLETED").all()
    out=[t for t in ts if t.sender_wallet_id==wallet_id]; inc=[t for t in ts if t.recipient_wallet_id==wallet_id]
    return {"wallet_id":wallet_id,"balance":user.wallet.balance,"currency":"NGN","total_transfers":len(ts),"outgoing_count":len(out),"incoming_count":len(inc),"outgoing_amount":sum((t.amount for t in out),Decimal("0")),"incoming_amount":sum((t.amount for t in inc),Decimal("0"))}
@router.get("/wallets/{wallet_id}/transactions")
def txns(wallet_id:str,page:int=Query(1,ge=1),page_size:int=Query(10,ge=1,le=50),status:str|None=None,direction:str|None=None,q:str|None=None,user=Depends(get_current_user),session=Depends(get_current_session),db:DBS=Depends(get_db)):
    require_own_wallet(wallet_id,user)
    query=db.query(Transfer).filter(or_(Transfer.sender_wallet_id==wallet_id,Transfer.recipient_wallet_id==wallet_id))
    if status: query=query.filter(Transfer.status==status.upper())
    if direction=="OUTGOING": query=query.filter(Transfer.sender_wallet_id==wallet_id)
    if direction=="INCOMING": query=query.filter(Transfer.recipient_wallet_id==wallet_id)
    total=query.count(); items=query.order_by(Transfer.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
    if q:
        items=[t for t in items if q.lower() in t.id.lower() or q.lower() in (t.description or "").lower()]; total=len(items)
    try: record(db,"transaction_history_viewed",user.id,session.id,{}); db.commit()
    except Exception: db.rollback()
    return {"items":[transfer_out(db,t,wallet_id) for t in items],"page":page,"page_size":page_size,"total":total,"pages":(total+page_size-1)//page_size if total else 0}
@router.post("/transfers",status_code=201)
def make_transfer(payload:TransferIn,request:Request,user=Depends(get_current_user),session=Depends(get_current_session),db:DBS=Depends(get_db)):
    rate_limit(request,"transfer",60)
    recipient=resolve_user(db,payload.recipient_identifier)
    if not recipient: raise HTTPException(404,{"code":"RECIPIENT_NOT_FOUND","message":"Recipient not found"})
    t,replayed=create_transfer(db,user,recipient,payload.amount,payload.description,payload.idempotency_key,session.id)
    return {**transfer_out(db,t,user.wallet.id),"idempotent_replay":replayed}
@router.get("/transfers/{transfer_id}")
def get_transfer(transfer_id:str,user=Depends(get_current_user),db:DBS=Depends(get_db)):
    t=db.get(Transfer,transfer_id)
    if not t: raise HTTPException(404,{"code":"NOT_FOUND","message":"Transfer not found"})
    if user.wallet.id not in (t.sender_wallet_id,t.recipient_wallet_id): raise HTTPException(403,{"code":"FORBIDDEN","message":"You are not a participant in this transfer"})
    entries=db.query(LedgerEntry).filter_by(transfer_id=t.id).all()
    return {**transfer_out(db,t,user.wallet.id),"ledger_entries":[{"id":e.id,"wallet_id":e.wallet_id,"entry_type":e.entry_type,"amount":e.amount,"created_at":e.created_at} for e in entries]}
@router.get("/analytics/summary")
def analytics_summary(user=Depends(get_current_user),db:DBS=Depends(get_db)):
    done=db.query(Transfer).filter_by(status="COMPLETED").all(); rejected=db.query(Transfer).filter_by(status="REJECTED").count()
    mine=[t for t in done if user.wallet and user.wallet.id in (t.sender_wallet_id,t.recipient_wallet_id)]
    out=[t for t in mine if t.sender_wallet_id==user.wallet.id]; inc=[t for t in mine if t.recipient_wallet_id==user.wallet.id]
    sessions=db.query(Session).filter_by(user_id=user.id).order_by(Session.started_at.desc()).first()
    return {"label":"Simulation analytics","total_successful_transfers":len(done),"total_volume":sum((t.amount for t in done),Decimal("0")),"rejected_attempts":rejected,"my_outgoing_count":len(out),"my_incoming_count":len(inc),"my_outgoing_amount":sum((t.amount for t in out),Decimal("0")),"my_incoming_amount":sum((t.amount for t in inc),Decimal("0")),"recent_activity":len(mine),"current_session_started_at":sessions.started_at if sessions else None,"current_session_last_seen_at":sessions.last_seen_at if sessions else None}
@router.get("/analytics/events")
def events(user=Depends(get_current_user),db:DBS=Depends(get_db),limit:int=Query(20,ge=1,le=100)):
    ev=db.query(AnalyticsEvent).filter_by(user_id=user.id).order_by(AnalyticsEvent.created_at.desc()).limit(limit).all()
    return [{"id":e.id,"event_type":e.event_type,"event_properties":e.event_properties,"created_at":e.created_at} for e in ev]
