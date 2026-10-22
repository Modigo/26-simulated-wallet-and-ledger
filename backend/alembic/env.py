from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__),".."))
from app.core.database import Base
from app.models import models  # noqa
config=context.config
config.set_main_option("sqlalchemy.url", os.getenv("DATABASE_URL","sqlite:///./ledgerlab.db"))
target_metadata=Base.metadata
def run_migrations_offline():
    context.configure(url=config.get_main_option("sqlalchemy.url"),target_metadata=target_metadata,literal_binds=True)
    with context.begin_transaction(): context.run_migrations()
def run_migrations_online():
    cfg=config.get_section(config.config_ini_section,{}); cfg["sqlalchemy.url"]=config.get_main_option("sqlalchemy.url")
    eng=engine_from_config(cfg,prefix="sqlalchemy.",poolclass=pool.NullPool)
    with eng.connect() as c:
        context.configure(connection=c,target_metadata=target_metadata)
        with context.begin_transaction(): context.run_migrations()
if context.is_offline_mode(): run_migrations_offline()
else: run_migrations_online()
