"""Seed/sync the four demo identities. Safe to rerun; never touches registered users or balances.

Demo identity fields (username/display_name/email/phone) are SYNCED to the values below on every
run: a demo user is matched by username OR email OR phone, so renaming a demo user in this file
updates the existing row (and keeps its wallet/balance/history) instead of trying to INSERT a
duplicate and crashing on the unique phone/email constraints.
"""
from decimal import Decimal
from sqlalchemy import or_
from app.core.database import SessionLocal, Base, engine
from app.models.models import User, Wallet
DEMO=[
 ("dokwe","Okwe David","Dokwe.david@example.com","08030000002","250000.00"),
 ("victor","Victor Asibe","Victor.Aibe@example.com","08030000001","180000.00"),
 ("Covenant","Ebri Covenant","Covenant@example.com","08030000003","120000.00"),
 ("louis","Oyinkepreye Louis","louis@example.com","08030000004","75000.00"),
]
def seed():
    Base.metadata.create_all(bind=engine); db=SessionLocal()
    try:
        for username,name,email,phone,balance in DEMO:
            u=db.query(User).filter(or_(User.username==username,User.email==email,User.phone==phone)).first()
            if u and not u.is_demo:
                print(f"WARNING: skipping demo '{username}': {email}/{phone} belongs to a registered user"); continue
            if not u:
                u=User(username=username,display_name=name,email=email,phone=phone,is_demo=True); db.add(u); db.flush()
                db.add(Wallet(user_id=u.id,balance=Decimal(balance),opening_balance=Decimal(balance)))
            else:  # sync identity only — wallet, balance and history are deliberately preserved
                u.username, u.display_name, u.email, u.phone = username, name, email, phone
                if not u.wallet:
                    db.add(Wallet(user_id=u.id,balance=Decimal(balance),opening_balance=Decimal(balance)))
        db.commit(); print("Seed complete (idempotent, identity-synced). Demo users:", [d[0] for d in DEMO])
    finally: db.close()
if __name__=="__main__": seed()
