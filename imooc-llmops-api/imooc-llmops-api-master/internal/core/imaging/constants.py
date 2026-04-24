#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Domain constants for hospital imaging workflows.
"""

IMAGING_MODALITIES = [
    "CT",
    "MR",
    "CR",
    "DR",
    "US",
    "XA",
]

IMAGING_SOURCE_TYPES = [
    "manual_upload",
    "pacs",
    "ris",
    "dicomweb",
]

IMAGING_QUALITY_STATUSES = [
    "pending",
    "qualified",
    "needs_review",
    "rejected",
]

IMAGING_PROCESSING_STATUSES = [
    "waiting",
    "importing",
    "preprocessing",
    "inferencing",
    "reviewing",
    "completed",
    "failed",
]

IMAGING_REPORT_STATUSES = [
    "draft",
    "doctor_editing",
    "doctor_reviewed",
    "signed",
    "archived",
]

IMAGING_REVIEW_LABELS = [
    "accepted",
    "rejected",
    "false_positive",
    "missed_finding",
]
