"""initial (delegates to model metadata for MVP brevity)
Revision ID: 0001
"""
revision="0001"; down_revision=None; branch_labels=None; depends_on=None
from alembic import op
from app.core.database import Base
from app.models import models  # noqa
def upgrade(): Base.metadata.create_all(bind=op.get_bind())
def downgrade(): Base.metadata.drop_all(bind=op.get_bind())
