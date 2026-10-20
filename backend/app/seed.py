"""Idempotent seed: safe to rerun; never touches registered users."""
from decimal import Decimal
from app.core.database import SessionLocal, Base, engine
from app.models.models import User, Wallet
from app.services.analytics import record  # noqa
DEMO=[
 ("adaeze","Adaeze Nwosu","Adaeze.Nwosu@example.com","08030000001","250000.00"),
 ("bello","Bello Adebayo","Bello.Adebayo@example.com","08030000002","180000.00"),
 ("Covenant","Ebri Covenant","Covenant@example.com","08030000003","120000.00"),
 ("louis","Oyinkepreye Louis","louis@example.com","08030000004","75000.00"),
]
def seed():
    Base.metadata.create_all(bind=engine); db=SessionLocal()
    try:
        for username,name,email,phone,balance in DEMO:
            u=db.query(User).filter_by(username=username).first()
            if not u:
                u=User(username=username,display_name=name,email=email,phone=phone,is_demo=True); db.add(u); db.flush(); db.add(Wallet(user_id=u.id,balance=Decimal(balance),opening_balance=Decimal(balance)))
        db.commit(); print("Seed complete (idempotent). Demo users:", [d[0] for d in DEMO])
    finally: db.close()
if __name__=="__main__": seed()
