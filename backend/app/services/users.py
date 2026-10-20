import re
from sqlalchemy import func, or_
from app.models.models import User
def normalize_phone(v:str)->str:
    d=re.sub(r"\D","",v.strip())
    if d.startswith("234") and len(d)>=12: d="0"+d[3:]
    return d
def normalize_identifier(v:str)->str: return v.strip().lower()
def resolve_user(db, identifier:str):
    raw=identifier.strip()
    if not raw: return None
    if "@" in raw: return db.query(User).filter(func.lower(User.email)==raw.lower()).first()
    phone=normalize_phone(raw)
    # Phone only when it looks like a phone (mostly digits, length >=7) to avoid username ambiguity
    digits=re.sub(r"\D","",raw)
    if len(digits)>=7 and re.fullmatch(r"[+0-9 ()-]+",raw):
        u=db.query(User).filter(User.phone==phone).first()
        return u
    return db.query(User).filter(func.lower(User.username)==raw.lower()).first()
def public_user(u):
    return {"id":u.id,"username":u.username,"display_name":u.display_name,"email":mask_email(u.email),"phone":mask_phone(u.phone),"is_demo":u.is_demo,"wallet_id":u.wallet.id if u.wallet else None,"balance":u.wallet.balance if u.wallet else None,"currency":u.wallet.currency if u.wallet else "NGN"}
def full_user(u): # for /me only: own email unmasked, never password hash
    d=public_user(u); d["email"]=u.email; d["phone"]=u.phone; return d
def mask_email(e):
    if not e or "@" not in e: return e
    a,b=e.split("@",1); return (a[:2]+"***@" + b) if len(a)>2 else (a[:1]+"***@"+b)
def mask_phone(p):
    return ("***"+p[-4:]) if p and len(p)>=4 else p
def serialize_user(u, mask=False): return public_user(u) if mask else full_user(u)
