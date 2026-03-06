"""add_clinic_hours_and_appointment_updates

Revision ID: 0004_scheduling
Revises: 0003_previous_migration   ← ajuste para o ID real da última migration
Create Date: 2025-07-01 00:00:00.000000

Mudanças:
  1. Cria tabela `clinic_hours`
  2. Adiciona colunas na tabela `appointments`:
       - patient_phone (TEXT)
       - notes (TEXT, nullable)
       - confirmed_at (TIMESTAMP, nullable)  ← se ainda não existir
  3. Adiciona coluna `pending_confirmation` (JSONB) em `conversation_status`
  4. Garante que `appointments.status` tem os valores corretos
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# Alembic metadata
revision = "0004_scheduling"
down_revision = "0003_previous_migration"   # ← substitua pelo ID real
branch_labels = None
depends_on = None


def upgrade():
    # ── 1. clinic_hours ─────────────────────────────────────────────────────
    op.create_table(
        "clinic_hours",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.String(255), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("day_of_week", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("slot_duration_minutes", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
    )
    op.create_index("ix_clinic_hours_tenant_id", "clinic_hours", ["tenant_id"])
    op.create_unique_constraint("uq_tenant_day", "clinic_hours", ["tenant_id", "day_of_week"])

    # ── 2. appointments — colunas extras ────────────────────────────────────
    # patient_phone (obrigatório para integração com bot)
    op.add_column(
        "appointments",
        sa.Column("patient_phone", sa.String(20), nullable=True),
    )
    # notes
    op.add_column(
        "appointments",
        sa.Column("notes", sa.Text(), nullable=True),
    )
    # confirmed_at (adicionar somente se não existir)
    try:
        op.add_column(
            "appointments",
            sa.Column("confirmed_at", sa.DateTime(), nullable=True),
        )
    except Exception:
        pass  # já existe

    # ── 3. conversation_status — pending_confirmation ────────────────────────
    op.add_column(
        "conversation_status",
        sa.Column("pending_confirmation", JSONB, nullable=True),
    )

    # ── 4. Seed default clinic hours (Segunda–Sexta, 08:00–18:00, 30 min) ───
    # OPCIONAL: descomente se quiser popular automaticamente para tenants existentes
    #
    # op.execute("""
    #     INSERT INTO clinic_hours (tenant_id, day_of_week, start_time, end_time, slot_duration_minutes, is_active)
    #     SELECT id, d, '08:00', '18:00', 30, true
    #     FROM tenants
    #     CROSS JOIN generate_series(0, 4) AS d
    #     ON CONFLICT (tenant_id, day_of_week) DO NOTHING;
    # """)


def downgrade():
    op.drop_column("conversation_status", "pending_confirmation")
    op.drop_column("appointments", "notes")
    op.drop_column("appointments", "patient_phone")
    try:
        op.drop_column("appointments", "confirmed_at")
    except Exception:
        pass
    op.drop_constraint("uq_tenant_day", "clinic_hours", type_="unique")
    op.drop_index("ix_clinic_hours_tenant_id", table_name="clinic_hours")
    op.drop_table("clinic_hours")