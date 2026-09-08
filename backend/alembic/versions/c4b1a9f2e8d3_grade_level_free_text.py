"""grade_level becomes free text (school-defined grade labels allowed)

Revision ID: c4b1a9f2e8d3
Revises: db5791264280
Create Date: 2026-09-07
"""

import sqlalchemy as sa
from alembic import op

revision = "c4b1a9f2e8d3"
down_revision = "db5791264280"
branch_labels = None
depends_on = None

GRADE_CHECK = "grade_level IN ('K', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12')"


def upgrade() -> None:
    for table in ("students", "courses"):
        with op.batch_alter_table(table) as batch_op:
            batch_op.drop_constraint(f"ck_{table}_grade_level", type_="check")
            batch_op.alter_column(
                "grade_level",
                existing_type=sa.String(length=2),
                type_=sa.String(length=20),
                existing_nullable=False,
            )


def downgrade() -> None:
    for table in ("students", "courses"):
        with op.batch_alter_table(table) as batch_op:
            batch_op.alter_column(
                "grade_level",
                existing_type=sa.String(length=20),
                type_=sa.String(length=2),
                existing_nullable=False,
            )
            batch_op.create_check_constraint(
                f"ck_{table}_grade_level", GRADE_CHECK
            )