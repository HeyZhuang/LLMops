"""add imaging domain tables

Revision ID: a1b2c3d4e5f6
Revises: 9f8e7d6c5b4a
Create Date: 2026-04-24 18:20:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "9f8e7d6c5b4a"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "imaging_study",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("account_id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=True),
        sa.Column("study_uid", sa.String(length=255), nullable=False, server_default=sa.text("''::character varying")),
        sa.Column("accession_number", sa.String(length=255), nullable=False, server_default=sa.text("''::character varying")),
        sa.Column("patient_uid", sa.String(length=255), nullable=False, server_default=sa.text("''::character varying")),
        sa.Column("patient_name_masked", sa.String(length=255), nullable=False, server_default=sa.text("''::character varying")),
        sa.Column("modality", sa.String(length=64), nullable=False, server_default=sa.text("'CT'::character varying")),
        sa.Column("body_part", sa.String(length=128), nullable=False, server_default=sa.text("''::character varying")),
        sa.Column("study_description", sa.Text(), nullable=False, server_default=sa.text("''::text")),
        sa.Column("source_type", sa.String(length=64), nullable=False, server_default=sa.text("'manual_upload'::character varying")),
        sa.Column("quality_status", sa.String(length=64), nullable=False, server_default=sa.text("'pending'::character varying")),
        sa.Column("processing_status", sa.String(length=64), nullable=False, server_default=sa.text("'waiting'::character varying")),
        sa.Column("study_time", sa.DateTime(), nullable=True),
        sa.Column("metadata", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("tags", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP(0)")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP(0)")),
        sa.PrimaryKeyConstraint("id", name="pk_imaging_study_id"),
    )

    op.create_table(
        "imaging_series",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("study_id", sa.UUID(), nullable=False),
        sa.Column("series_uid", sa.String(length=255), nullable=False, server_default=sa.text("''::character varying")),
        sa.Column("series_number", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("series_description", sa.Text(), nullable=False, server_default=sa.text("''::text")),
        sa.Column("slice_thickness", sa.String(length=64), nullable=False, server_default=sa.text("''::character varying")),
        sa.Column("image_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("orientation", sa.String(length=64), nullable=False, server_default=sa.text("''::character varying")),
        sa.Column("metadata", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP(0)")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP(0)")),
        sa.PrimaryKeyConstraint("id", name="pk_imaging_series_id"),
    )

    op.create_table(
        "imaging_instance",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("study_id", sa.UUID(), nullable=False),
        sa.Column("series_id", sa.UUID(), nullable=False),
        sa.Column("sop_instance_uid", sa.String(length=255), nullable=False, server_default=sa.text("''::character varying")),
        sa.Column("instance_number", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("file_path", sa.Text(), nullable=False, server_default=sa.text("''::text")),
        sa.Column("thumbnail_path", sa.Text(), nullable=False, server_default=sa.text("''::text")),
        sa.Column("window_width", sa.String(length=64), nullable=False, server_default=sa.text("''::character varying")),
        sa.Column("window_center", sa.String(length=64), nullable=False, server_default=sa.text("''::character varying")),
        sa.Column("metadata", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP(0)")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP(0)")),
        sa.PrimaryKeyConstraint("id", name="pk_imaging_instance_id"),
    )

    op.create_table(
        "imaging_ai_result",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("study_id", sa.UUID(), nullable=False),
        sa.Column("series_id", sa.UUID(), nullable=True),
        sa.Column("model_name", sa.String(length=255), nullable=False, server_default=sa.text("''::character varying")),
        sa.Column("model_version", sa.String(length=255), nullable=False, server_default=sa.text("''::character varying")),
        sa.Column("task_type", sa.String(length=64), nullable=False, server_default=sa.text("'detection'::character varying")),
        sa.Column("finding_type", sa.String(length=128), nullable=False, server_default=sa.text("''::character varying")),
        sa.Column("confidence", sa.String(length=32), nullable=False, server_default=sa.text("'0'::character varying")),
        sa.Column("result_status", sa.String(length=64), nullable=False, server_default=sa.text("'completed'::character varying")),
        sa.Column("findings", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("measurements", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("overlays", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("summary", sa.Text(), nullable=False, server_default=sa.text("''::text")),
        sa.Column("raw_payload", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP(0)")),
        sa.PrimaryKeyConstraint("id", name="pk_imaging_ai_result_id"),
    )

    op.create_table(
        "imaging_report",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("study_id", sa.UUID(), nullable=False),
        sa.Column("template_name", sa.String(length=255), nullable=False, server_default=sa.text("''::character varying")),
        sa.Column("template_version", sa.String(length=64), nullable=False, server_default=sa.text("'v1'::character varying")),
        sa.Column("generation_source", sa.String(length=64), nullable=False, server_default=sa.text("'ai_draft'::character varying")),
        sa.Column("report_status", sa.String(length=64), nullable=False, server_default=sa.text("'draft'::character varying")),
        sa.Column("draft_content", sa.Text(), nullable=False, server_default=sa.text("''::text")),
        sa.Column("final_content", sa.Text(), nullable=False, server_default=sa.text("''::text")),
        sa.Column("doctor_notes", sa.Text(), nullable=False, server_default=sa.text("''::text")),
        sa.Column("model_snapshot", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("prompt_snapshot", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("signed_by", sa.UUID(), nullable=True),
        sa.Column("signed_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP(0)")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP(0)")),
        sa.PrimaryKeyConstraint("id", name="pk_imaging_report_id"),
    )

    op.create_table(
        "imaging_review",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("study_id", sa.UUID(), nullable=False),
        sa.Column("ai_result_id", sa.UUID(), nullable=True),
        sa.Column("report_id", sa.UUID(), nullable=True),
        sa.Column("reviewer_id", sa.UUID(), nullable=False),
        sa.Column("review_type", sa.String(length=64), nullable=False, server_default=sa.text("'doctor_review'::character varying")),
        sa.Column("review_label", sa.String(length=64), nullable=False, server_default=sa.text("'accepted'::character varying")),
        sa.Column("has_false_positive", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("has_missed_finding", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("comment", sa.Text(), nullable=False, server_default=sa.text("''::text")),
        sa.Column("review_payload", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP(0)")),
        sa.PrimaryKeyConstraint("id", name="pk_imaging_review_id"),
    )

    op.create_table(
        "imaging_audit_log",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("study_id", sa.UUID(), nullable=True),
        sa.Column("operator_id", sa.UUID(), nullable=False),
        sa.Column("action", sa.String(length=128), nullable=False, server_default=sa.text("''::character varying")),
        sa.Column("target_type", sa.String(length=64), nullable=False, server_default=sa.text("''::character varying")),
        sa.Column("target_id", sa.UUID(), nullable=True),
        sa.Column("source_ip", sa.String(length=64), nullable=False, server_default=sa.text("''::character varying")),
        sa.Column("success", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("details", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP(0)")),
        sa.PrimaryKeyConstraint("id", name="pk_imaging_audit_log_id"),
    )


def downgrade():
    op.drop_table("imaging_audit_log")
    op.drop_table("imaging_review")
    op.drop_table("imaging_report")
    op.drop_table("imaging_ai_result")
    op.drop_table("imaging_instance")
    op.drop_table("imaging_series")
    op.drop_table("imaging_study")
