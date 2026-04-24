#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Imaging domain models for hospital imaging workflows.
"""
from sqlalchemy import (
    Column,
    UUID,
    String,
    Text,
    Integer,
    Boolean,
    DateTime,
    PrimaryKeyConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB

from internal.extension.database_extension import db


class ImagingStudy(db.Model):
    __tablename__ = "imaging_study"
    __table_args__ = (PrimaryKeyConstraint("id", name="pk_imaging_study_id"),)

    id = Column(UUID, nullable=False, server_default=text("uuid_generate_v4()"))
    account_id = Column(UUID, nullable=False)
    tenant_id = Column(UUID, nullable=True)
    study_uid = Column(String(255), nullable=False, server_default=text("''::character varying"))
    accession_number = Column(String(255), nullable=False, server_default=text("''::character varying"))
    patient_uid = Column(String(255), nullable=False, server_default=text("''::character varying"))
    patient_name_masked = Column(String(255), nullable=False, server_default=text("''::character varying"))
    modality = Column(String(64), nullable=False, server_default=text("'CT'::character varying"))
    body_part = Column(String(128), nullable=False, server_default=text("''::character varying"))
    study_description = Column(Text, nullable=False, server_default=text("''::text"))
    source_type = Column(String(64), nullable=False, server_default=text("'manual_upload'::character varying"))
    quality_status = Column(String(64), nullable=False, server_default=text("'pending'::character varying"))
    processing_status = Column(String(64), nullable=False, server_default=text("'waiting'::character varying"))
    study_time = Column(DateTime, nullable=True)
    meta = Column("metadata", JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    tags = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(0)"),
        server_onupdate=text("CURRENT_TIMESTAMP(0)"),
    )
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP(0)"))


class ImagingSeries(db.Model):
    __tablename__ = "imaging_series"
    __table_args__ = (PrimaryKeyConstraint("id", name="pk_imaging_series_id"),)

    id = Column(UUID, nullable=False, server_default=text("uuid_generate_v4()"))
    study_id = Column(UUID, nullable=False)
    series_uid = Column(String(255), nullable=False, server_default=text("''::character varying"))
    series_number = Column(Integer, nullable=False, server_default=text("0"))
    series_description = Column(Text, nullable=False, server_default=text("''::text"))
    slice_thickness = Column(String(64), nullable=False, server_default=text("''::character varying"))
    image_count = Column(Integer, nullable=False, server_default=text("0"))
    orientation = Column(String(64), nullable=False, server_default=text("''::character varying"))
    meta = Column("metadata", JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(0)"),
        server_onupdate=text("CURRENT_TIMESTAMP(0)"),
    )
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP(0)"))


class ImagingInstance(db.Model):
    __tablename__ = "imaging_instance"
    __table_args__ = (PrimaryKeyConstraint("id", name="pk_imaging_instance_id"),)

    id = Column(UUID, nullable=False, server_default=text("uuid_generate_v4()"))
    study_id = Column(UUID, nullable=False)
    series_id = Column(UUID, nullable=False)
    sop_instance_uid = Column(String(255), nullable=False, server_default=text("''::character varying"))
    instance_number = Column(Integer, nullable=False, server_default=text("0"))
    file_path = Column(Text, nullable=False, server_default=text("''::text"))
    thumbnail_path = Column(Text, nullable=False, server_default=text("''::text"))
    window_width = Column(String(64), nullable=False, server_default=text("''::character varying"))
    window_center = Column(String(64), nullable=False, server_default=text("''::character varying"))
    meta = Column("metadata", JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(0)"),
        server_onupdate=text("CURRENT_TIMESTAMP(0)"),
    )
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP(0)"))


class ImagingAiResult(db.Model):
    __tablename__ = "imaging_ai_result"
    __table_args__ = (PrimaryKeyConstraint("id", name="pk_imaging_ai_result_id"),)

    id = Column(UUID, nullable=False, server_default=text("uuid_generate_v4()"))
    study_id = Column(UUID, nullable=False)
    series_id = Column(UUID, nullable=True)
    model_name = Column(String(255), nullable=False, server_default=text("''::character varying"))
    model_version = Column(String(255), nullable=False, server_default=text("''::character varying"))
    task_type = Column(String(64), nullable=False, server_default=text("'detection'::character varying"))
    finding_type = Column(String(128), nullable=False, server_default=text("''::character varying"))
    confidence = Column(String(32), nullable=False, server_default=text("'0'::character varying"))
    result_status = Column(String(64), nullable=False, server_default=text("'completed'::character varying"))
    findings = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    measurements = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    overlays = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    summary = Column(Text, nullable=False, server_default=text("''::text"))
    raw_payload = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP(0)"))


class ImagingReport(db.Model):
    __tablename__ = "imaging_report"
    __table_args__ = (PrimaryKeyConstraint("id", name="pk_imaging_report_id"),)

    id = Column(UUID, nullable=False, server_default=text("uuid_generate_v4()"))
    study_id = Column(UUID, nullable=False)
    template_name = Column(String(255), nullable=False, server_default=text("''::character varying"))
    template_version = Column(String(64), nullable=False, server_default=text("'v1'::character varying"))
    generation_source = Column(String(64), nullable=False, server_default=text("'ai_draft'::character varying"))
    report_status = Column(String(64), nullable=False, server_default=text("'draft'::character varying"))
    draft_content = Column(Text, nullable=False, server_default=text("''::text"))
    final_content = Column(Text, nullable=False, server_default=text("''::text"))
    doctor_notes = Column(Text, nullable=False, server_default=text("''::text"))
    model_snapshot = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    prompt_snapshot = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    signed_by = Column(UUID, nullable=True)
    signed_at = Column(DateTime, nullable=True)
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(0)"),
        server_onupdate=text("CURRENT_TIMESTAMP(0)"),
    )
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP(0)"))


class ImagingReview(db.Model):
    __tablename__ = "imaging_review"
    __table_args__ = (PrimaryKeyConstraint("id", name="pk_imaging_review_id"),)

    id = Column(UUID, nullable=False, server_default=text("uuid_generate_v4()"))
    study_id = Column(UUID, nullable=False)
    ai_result_id = Column(UUID, nullable=True)
    report_id = Column(UUID, nullable=True)
    reviewer_id = Column(UUID, nullable=False)
    review_type = Column(String(64), nullable=False, server_default=text("'doctor_review'::character varying"))
    review_label = Column(String(64), nullable=False, server_default=text("'accepted'::character varying"))
    has_false_positive = Column(Boolean, nullable=False, server_default=text("false"))
    has_missed_finding = Column(Boolean, nullable=False, server_default=text("false"))
    comment = Column(Text, nullable=False, server_default=text("''::text"))
    review_payload = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP(0)"))


class ImagingAuditLog(db.Model):
    __tablename__ = "imaging_audit_log"
    __table_args__ = (PrimaryKeyConstraint("id", name="pk_imaging_audit_log_id"),)

    id = Column(UUID, nullable=False, server_default=text("uuid_generate_v4()"))
    study_id = Column(UUID, nullable=True)
    operator_id = Column(UUID, nullable=False)
    action = Column(String(128), nullable=False, server_default=text("''::character varying"))
    target_type = Column(String(64), nullable=False, server_default=text("''::character varying"))
    target_id = Column(UUID, nullable=True)
    source_ip = Column(String(64), nullable=False, server_default=text("''::character varying"))
    success = Column(Boolean, nullable=False, server_default=text("true"))
    details = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP(0)"))
