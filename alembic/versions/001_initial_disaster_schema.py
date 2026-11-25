"""Initial disaster coordination platform schema

Revision ID: 001_initial_disaster_schema
Revises: 
Create Date: 2026-11-24 22:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial_disaster_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Schema creation handled by SQLAlchemy Base.metadata.create_all and Alembic
    pass


def downgrade() -> None:
    pass
