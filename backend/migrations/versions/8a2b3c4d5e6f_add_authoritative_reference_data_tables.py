"""Add Authoritative Reference Data Tables for Phase 2

Revision ID: 8a2b3c4d5e6f
Revises: 6923ff566fc0
Create Date: 2026-10-28 12:20:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '8a2b3c4d5e6f'
down_revision: Union[str, Sequence[str], None] = '6923ff566fc0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. institution_reference_records
    op.create_table(
        'institution_reference_records',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('aicte_permanent_id', sa.String(length=100), nullable=False),
        sa.Column('legal_name', sa.String(length=255), nullable=False),
        sa.Column('institution_type', sa.String(length=100), nullable=False),
        sa.Column('state', sa.String(length=100), nullable=False),
        sa.Column('district_or_city', sa.String(length=100), nullable=False),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('normalized_name', sa.String(length=255), nullable=False),
        sa.Column('normalized_city', sa.String(length=100), nullable=False),
        sa.Column('normalized_state', sa.String(length=100), nullable=False),
        sa.Column('standing_status', sa.String(length=50), nullable=False, server_default='Approved'),
        sa.Column('established_year', sa.Integer(), nullable=True),
        sa.Column('initial_approval_year', sa.Integer(), nullable=True),
        sa.Column('latest_approval_year', sa.Integer(), nullable=True),
        sa.Column('verification_status', sa.String(length=50), nullable=False, server_default='OFFICIAL_VERIFIED'),
        sa.Column('source_provenance', sa.String(length=150), nullable=False, server_default='AICTE Central Regulatory Registry'),
        sa.Column('source_document_ref', sa.String(length=150), nullable=True),
        sa.Column('data_freshness_date', sa.DateTime(), nullable=False),
        sa.Column('is_official', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('institution_reference_records', schema=None) as batch_op:
        batch_op.create_index('ix_inst_ref_perm_id', ['aicte_permanent_id'], unique=True)
        batch_op.create_index('ix_inst_ref_norm_name', ['normalized_name'], unique=False)
        batch_op.create_index('ix_inst_ref_norm_city', ['normalized_city'], unique=False)
        batch_op.create_index('ix_inst_ref_norm_state', ['normalized_state'], unique=False)

    # 2. approved_programmes
    op.create_table(
        'approved_programmes',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('institution_reference_id', sa.String(length=36), nullable=False),
        sa.Column('programme_name', sa.String(length=150), nullable=False),
        sa.Column('course_name', sa.String(length=200), nullable=False),
        sa.Column('level', sa.String(length=50), nullable=False),
        sa.Column('approved_intake', sa.Integer(), nullable=False),
        sa.Column('nri_quota_approved', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('nri_quota_intake', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('pio_fn_quota_approved', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('pio_fn_quota_intake', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('accreditation_status', sa.String(length=100), nullable=False, server_default='Non-Accredited'),
        sa.Column('accreditation_valid_until', sa.DateTime(), nullable=True),
        sa.Column('academic_year', sa.String(length=20), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['institution_reference_id'], ['institution_reference_records.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('approved_programmes', schema=None) as batch_op:
        batch_op.create_index('ix_appr_prog_inst_ref_id', ['institution_reference_id'], unique=False)

    # 3. institution_approval_history
    op.create_table(
        'institution_approval_history',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('institution_reference_id', sa.String(length=36), nullable=False),
        sa.Column('academic_year', sa.String(length=20), nullable=False),
        sa.Column('eoa_application_number', sa.String(length=100), nullable=True),
        sa.Column('eoa_issue_date', sa.DateTime(), nullable=True),
        sa.Column('effective_start_date', sa.DateTime(), nullable=False),
        sa.Column('effective_end_date', sa.DateTime(), nullable=False),
        sa.Column('total_sanctioned_intake', sa.Integer(), nullable=False),
        sa.Column('approval_type', sa.String(length=100), nullable=False, server_default='Extension of Approval'),
        sa.Column('issuing_authority', sa.String(length=150), nullable=False),
        sa.Column('is_latest', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['institution_reference_id'], ['institution_reference_records.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('institution_approval_history', schema=None) as batch_op:
        batch_op.create_index('ix_inst_appr_hist_ref_id', ['institution_reference_id'], unique=False)
        batch_op.create_index('ix_inst_appr_hist_ay', ['academic_year'], unique=False)


def downgrade() -> None:
    op.drop_table('institution_approval_history')
    op.drop_table('approved_programmes')
    op.drop_table('institution_reference_records')
