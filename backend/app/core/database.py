from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import settings
import os
if os.getenv("RENDER") and settings.sqlalchemy_url.startswith("sqlite"):
    raise RuntimeError("DATABASE_URL is not set to PostgreSQL on Render — registered users would be wiped on every restart. Attach the ledgerlab-db database (render.yaml does this automatically).")
connect_args = {"check_same_thread": False} if settings.sqlalchemy_url.startswith("sqlite") else {}
engine = create_engine(settings.sqlalchemy_url, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
class Base(DeclarativeBase): pass
def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()
