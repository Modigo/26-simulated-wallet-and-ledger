"""DESTRUCTIVE local-only reset. Requires explicit env confirmation."""
import os
from app.core.database import Base, engine
from app.models import models  # noqa
if os.getenv("LEDGERLAB_ALLOW_RESET")!="YES_I_UNDERSTAND":
    raise SystemExit("Refusing reset. Set LEDGERLAB_ALLOW_RESET=YES_I_UNDERSTAND (local dev only).")
Base.metadata.drop_all(bind=engine); Base.metadata.create_all(bind=engine); print("Database reset.")
