import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import String, DateTime, ForeignKey, Numeric, UniqueConstraint, Index, JSON, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
def uid() -> str: return str(uuid.uuid4())
def now() -> datetime: return datetime.now(timezone.utc)
class User(Base):
    __tablename__="users"
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    username:Mapped[str]=mapped_column(String(40),unique=True,index=True)  # stored normalized lowercase
    display_name:Mapped[str]=mapped_column(String(100))
    email:Mapped[str]=mapped_column(String(255),unique=True,index=True)     # normalized lowercase
    phone:Mapped[str|None]=mapped_column(String(30),unique=True,index=True,nullable=True)
    password_hash:Mapped[str|None]=mapped_column(String(255),nullable=True) # None only for demo users
    is_demo:Mapped[bool]=mapped_column(Boolean,default=False,index=True)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
    wallet:Mapped["Wallet"]=relationship(back_populates="user",uselist=False)
class Wallet(Base):
    __tablename__="wallets"
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    user_id:Mapped[str]=mapped_column(ForeignKey("users.id"),unique=True,index=True)
    currency:Mapped[str]=mapped_column(String(3),default="NGN")
    balance:Mapped[Decimal]=mapped_column(Numeric(14,2),default=Decimal("0.00"))
    opening_balance:Mapped[Decimal]=mapped_column(Numeric(14,2),default=Decimal("0.00")) # seed opening, reconciliation base
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
    updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now,onupdate=now)
    user:Mapped[User]=relationship(back_populates="wallet")
    __table_args__=(__import__("sqlalchemy").CheckConstraint("balance >= 0",name="ck_wallet_nonnegative"),)
class Transfer(Base):
    __tablename__="transfers"
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    sender_wallet_id:Mapped[str]=mapped_column(ForeignKey("wallets.id"),index=True)
    recipient_wallet_id:Mapped[str]=mapped_column(ForeignKey("wallets.id"),index=True)
    amount:Mapped[Decimal]=mapped_column(Numeric(14,2))
    currency:Mapped[str]=mapped_column(String(3),default="NGN")
    description:Mapped[str|None]=mapped_column(Text,nullable=True)
    status:Mapped[str]=mapped_column(String(20),default="COMPLETED",index=True) # COMPLETED | REJECTED
    idempotency_key:Mapped[str]=mapped_column(String(100))
    request_hash:Mapped[str]=mapped_column(String(64))
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now,index=True)
    completed_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True)
    __table_args__=(UniqueConstraint("sender_wallet_id","idempotency_key",name="uq_transfer_idempotency"),__import__("sqlalchemy").CheckConstraint("amount > 0",name="ck_transfer_positive"),__import__("sqlalchemy").CheckConstraint("sender_wallet_id <> recipient_wallet_id",name="ck_no_self_transfer"))
class LedgerEntry(Base):
    __tablename__="ledger_entries"
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    transfer_id:Mapped[str]=mapped_column(ForeignKey("transfers.id"),index=True)
    wallet_id:Mapped[str]=mapped_column(ForeignKey("wallets.id"),index=True)
    entry_type:Mapped[str]=mapped_column(String(10)) # DEBIT (-amount) | CREDIT (+amount)
    amount:Mapped[Decimal]=mapped_column(Numeric(14,2)) # signed amount; pair sums to zero
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
class Session(Base):
    __tablename__="sessions"
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    user_id:Mapped[str]=mapped_column(ForeignKey("users.id"),index=True)
    session_token_hash:Mapped[str]=mapped_column(String(64),unique=True,index=True)
    started_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
    last_seen_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
    expires_at:Mapped[datetime]=mapped_column(DateTime(timezone=True))
    ended_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True)
class AnalyticsEvent(Base):
    __tablename__="analytics_events"
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    session_id:Mapped[str|None]=mapped_column(ForeignKey("sessions.id"),nullable=True,index=True)
    user_id:Mapped[str|None]=mapped_column(ForeignKey("users.id"),nullable=True,index=True)
    event_type:Mapped[str]=mapped_column(String(60),index=True)
    event_properties:Mapped[dict]=mapped_column(JSON,default=dict)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now,index=True)
