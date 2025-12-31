"""add_email_phone_to_user

Revision ID: 7d5e5413c12a
Revises: ad89488edf1f
Create Date: 2025-12-31 14:35:34.683060

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7d5e5413c12a'
down_revision: Union[str, Sequence[str], None] = 'ad89488edf1f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 添加 email 和 phone 字段到 user 表
    op.add_column('user', sa.Column('email', sa.String(), nullable=True))
    op.add_column('user', sa.Column('phone', sa.String(), nullable=True))
    
    # 为 email 字段创建索引
    op.create_index(op.f('ix_user_email'), 'user', ['email'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # 删除索引
    op.drop_index(op.f('ix_user_email'), table_name='user')
    
    # 删除字段
    op.drop_column('user', 'phone')
    op.drop_column('user', 'email')
