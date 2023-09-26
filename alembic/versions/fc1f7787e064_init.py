"""Initialize

Revision ID: fc1f7787e064
Revises: 
Create Date: 2020-06-18 12:45:54.016010

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'fc1f7787e064'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():

    # install extensions on database server
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "ltree"')


def downgrade():
    pass