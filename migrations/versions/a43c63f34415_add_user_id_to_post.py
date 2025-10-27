"""Add user_id to Post

Revision ID: a43c63f34415
Revises: f07b510733f7
Create Date: 2025-10-26 15:44:09.132736
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a43c63f34415'
down_revision = 'f07b510733f7'
branch_labels = None
depends_on = None


def upgrade():
    # 1️⃣ Add user_id as nullable first to avoid NOT NULL constraint error
    with op.batch_alter_table('post', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_post_user_id', 'user', ['user_id'], ['id'])
        batch_op.drop_column('author_id')

    # 2️⃣ Set a default user_id (like admin=1) for existing posts
    op.execute("UPDATE post SET user_id = 1 WHERE user_id IS NULL;")

    # 3️⃣ Now enforce NOT NULL
    with op.batch_alter_table('post', schema=None) as batch_op:
        batch_op.alter_column('user_id', nullable=False)


def downgrade():
    # Properly revert the upgrade
    with op.batch_alter_table('post', schema=None) as batch_op:
        batch_op.add_column(sa.Column('author_id', sa.Integer(), nullable=True))
        batch_op.drop_constraint('fk_post_user_id', type_='foreignkey')
        batch_op.drop_column('user_id')
