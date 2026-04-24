#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Predefined workflow templates for imaging use cases.
"""

IMAGING_WORKFLOW_TEMPLATES = {
    "chest_ct_report_assistant": {
        "name": "Chest CT Report Assistant",
        "scene": "Radiology report drafting for chest CT",
        "steps": [
            "dicom_import",
            "dicom_anonymize",
            "study_metadata_extract",
            "series_select",
            "lung_window_preprocess",
            "lesion_detection",
            "history_report_retrieve",
            "guideline_retrieve",
            "report_draft_generate",
            "doctor_review",
            "archive_and_audit",
        ],
        "outputs": [
            "structured_findings",
            "report_draft",
            "review_trace",
        ],
    },
    "emergency_brain_ct_triage": {
        "name": "Emergency Brain CT Triage",
        "scene": "Emergency high-risk finding triage for brain CT",
        "steps": [
            "pacs_listener",
            "head_ct_identify",
            "hemorrhage_screening",
            "high_risk_alert",
            "doctor_notification",
            "manual_confirmation",
            "feedback_capture",
            "audit_log_archive",
        ],
        "outputs": [
            "triage_label",
            "alert_record",
            "doctor_feedback",
        ],
    },
}
