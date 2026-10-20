import os, uuid
os.environ["DATABASE_URL"]="sqlite:///./test_ledgerlab.db"
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import Base, engine, SessionLocal
from app.seed import seed
from app.models.models import Wallet, LedgerEntry, User
from app.services.transfers import reconcile_wallet

@pytest.fixture(scope="session", autouse=True)
def setup():
    Base.metadata.drop_all(bind=engine); Base.metadata.create_all(bind=engine); seed(); yield

client=TestClient(app)
def demo_login(username="adaeze"):
    users=client.get("/api/v1/demo-users").json(); u=[x for x in users if x["username"]==username][0]
    c=TestClient(app); r=c.post("/api/v1/sessions", json={"user_id":u["id"]}); assert r.status_code==201; return c,u
def reg(c=None, suffix=None):
    c=c or TestClient(app); s=suffix or uuid.uuid4().hex[:8]
    r=c.post("/api/v1/auth/register", json={"display_name":"Test User","username":f"user{s}","email":f"user{s}@example.com","phone":"0809"+s[:7],"password":"Ledger"+"123!"})
    assert r.status_code==201, r.text; return c,r.json()["user"]

def test_health_and_demo(): assert client.get("/health").json()["status"]=="ok"; assert len(client.get("/api/v1/demo-users").json())>=4
def test_valid_transfer_and_ledger():
    a,_=demo_login("adaeze"); before=a.get("/api/v1/auth/me").json()
    key="key-"+uuid.uuid4().hex
    r=a.post("/api/v1/transfers", json={"recipient_identifier":"bello","amount":"1000.00","description":"demo","idempotency_key":key}); assert r.status_code==201, r.text
    tid=r.json()["id"]; detail=a.get(f"/api/v1/transfers/{tid}"); assert detail.status_code==200
    entries=detail.json()["ledger_entries"]; assert len(entries)==2 and sum(float(e["amount"]) for e in entries)==0
    # idempotent replay
    r2=a.post("/api/v1/transfers", json={"recipient_identifier":"bello","amount":"1000.00","description":"demo","idempotency_key":key}); assert r2.json()["id"]==tid and r2.json()["idempotent_replay"] is True
    # conflict
    r3=a.post("/api/v1/transfers", json={"recipient_identifier":"bello","amount":"2000.00","description":"demo","idempotency_key":key}); assert r3.status_code==409
def test_recipient_by_email_and_phone():
    a,_=demo_login("Covenant"); assert a.get("/api/v1/users/resolve",params={"identifier":"Bello.Adebayo@example.com"}).status_code==200
    assert a.get("/api/v1/users/resolve",params={"identifier":"+234 803 000 0002"}).status_code==200
    assert a.get("/api/v1/users/resolve",params={"identifier":"nobody"}).status_code==404
def test_validation_self_insufficient():
    a,me=demo_login("louis")
    assert a.post("/api/v1/transfers",json={"recipient_identifier":"louis","amount":"10","idempotency_key":"k-"+uuid.uuid4().hex}).status_code==400
    assert a.post("/api/v1/transfers",json={"recipient_identifier":"adaeze","amount":"0","idempotency_key":"k-"+uuid.uuid4().hex}).status_code in (400,422)
    assert a.post("/api/v1/transfers",json={"recipient_identifier":"adaeze","amount":"9999999","idempotency_key":"k-"+uuid.uuid4().hex}).status_code==422
    assert a.post("/api/v1/transfers",json={"recipient_identifier":"adaeze","amount":"10.123","idempotency_key":"k-"+uuid.uuid4().hex}).status_code==422
def test_register_zero_balance_duplicates_authz():
    c,u=reg(); me=c.get("/api/v1/auth/me"); assert me.status_code==200 and float(me.json()["balance"])==0
    dup=TestClient(app).post("/api/v1/auth/register",json={"display_name":"Dup","username":u["username"].upper(),"email":"other@example.com","password":"Ledger"+"123!"}); assert dup.status_code==409
    dup2=TestClient(app).post("/api/v1/auth/register",json={"display_name":"Dup","username":"another"+uuid.uuid4().hex[:5],"email":u["email"].upper(),"password":"Ledger"+"123!"}); assert dup2.status_code==409
    bad=TestClient(app).post("/api/v1/auth/login",json={"identifier":u["username"],"password":"wrong"}); assert bad.status_code==401
    other,_=demo_login("adaeze"); assert other.get(f"/api/v1/wallets/{u['wallet_id']}").status_code==403
    assert "password" not in str(me.json()).lower()
def test_registered_can_receive_and_reconcile():
    sender,_=demo_login("adaeze"); c,u=reg()
    r=sender.post("/api/v1/transfers",json={"recipient_identifier":u["username"],"amount":"500","idempotency_key":"k-"+uuid.uuid4().hex}); assert r.status_code==201, r.text
    assert float(c.get("/api/v1/auth/me").json()["balance"])==500
    db=SessionLocal(); w=db.query(Wallet).filter_by(user_id=u["id"]).first(); rec=reconcile_wallet(db,w); assert rec["ok"]; db.close()
def test_unauthenticated_and_logout():
    assert TestClient(app).get("/api/v1/auth/me").status_code==401
    c,u=reg(); assert c.post("/api/v1/auth/logout").status_code==200; assert c.get("/api/v1/auth/me").status_code==401
def test_pagination_empty():
    c,u=reg(); r=c.get(f"/api/v1/wallets/{u['wallet_id']}/transactions"); assert r.status_code==200 and r.json()["total"]==0 and r.json()["items"]==[]
