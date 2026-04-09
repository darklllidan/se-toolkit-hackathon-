"""Seed all dorm resources (study rooms, washers, dryers)

Revision ID: 0004
Revises: 0003
Create Date: 2026-04-09
"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None

DORM_FLOORS = {1: 4, 2: 4, 3: 4, 4: 4, 5: 5, 6: 13, 7: 13}


def upgrade() -> None:
    conn = op.get_bind()
    for dorm, max_floor in DORM_FLOORS.items():
        for floor in range(1, max_floor + 1):
            loc = f"Dorm {dorm}, Floor {floor}"
            rows = [
                (f"Study Room D{dorm}-F{floor}", "study_room",      loc, 6),
                (f"Washer D{dorm}-F{floor}-1",   "washing_machine", loc, 1),
                (f"Washer D{dorm}-F{floor}-2",   "washing_machine", loc, 1),
                (f"Dryer D{dorm}-F{floor}-1",    "dryer",           loc, 1),
                (f"Dryer D{dorm}-F{floor}-2",    "dryer",           loc, 1),
            ]
            for name, cat, location, capacity in rows:
                conn.execute(sa.text(
                    "INSERT INTO resources (id, name, category, location, capacity, status) "
                    "VALUES (gen_random_uuid(), :name, CAST(:cat AS resource_category), :loc, :cap, 'available') "
                    "ON CONFLICT DO NOTHING"
                ).bindparams(name=name, cat=cat, loc=location, cap=capacity))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text(
        "DELETE FROM resources WHERE location ~ '^Dorm [1-7], Floor'"
    ))
