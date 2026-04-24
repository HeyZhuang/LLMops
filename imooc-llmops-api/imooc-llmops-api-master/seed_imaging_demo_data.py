#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Seed imaging demo data into database tables when available."""

import os
import sys
from datetime import datetime, timedelta
from uuid import uuid5, NAMESPACE_DNS

import dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

dotenv.load_dotenv()

from app.http.app import app  # noqa: E402
from internal.model import Account, ImagingStudy  # noqa: E402
from internal.extension.database_extension import db  # noqa: E402


def build_demo_rows(account_id):
    base_time = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
    seed = f"llmops-imaging-{account_id}"
    return [
        {
            "id": uuid5(NAMESPACE_DNS, f"{seed}-study-1"),
            "study_uid": f"{seed}-study-uid-1",
            "accession_number": "RAD-2026-0001",
            "patient_uid": "P-0001",
            "patient_name_masked": "Zhang**",
            "modality": "CT",
            "body_part": "Chest",
            "study_description": "Chest CT plain scan for lung nodule follow-up",
            "quality_status": "qualified",
            "processing_status": "doctor_review",
            "study_time": base_time - timedelta(hours=2),
            "meta": {
                "priority": "normal",
                "report_status": "draft_ready",
                "ai_summary": "Two pulmonary nodules detected in the right upper lobe. Report draft ready.",
                "findings": ["Right upper lobe nodule", "Right upper lobe micronodule"],
            },
        },
        {
            "id": uuid5(NAMESPACE_DNS, f"{seed}-study-2"),
            "study_uid": f"{seed}-study-uid-2",
            "accession_number": "ER-2026-0148",
            "patient_uid": "P-0002",
            "patient_name_masked": "Li**",
            "modality": "CT",
            "body_part": "Brain",
            "study_description": "Emergency non-contrast brain CT for dizziness and vomiting",
            "quality_status": "qualified",
            "processing_status": "ai_completed",
            "study_time": base_time - timedelta(hours=6),
            "meta": {
                "priority": "urgent",
                "report_status": "pending_draft",
                "ai_summary": "No clear intracranial hemorrhage detected. Manual review recommended.",
                "findings": ["No definite acute hemorrhage"],
            },
        },
        {
            "id": uuid5(NAMESPACE_DNS, f"{seed}-study-3"),
            "study_uid": f"{seed}-study-uid-3",
            "accession_number": "DR-2026-0233",
            "patient_uid": "P-0003",
            "patient_name_masked": "Wang**",
            "modality": "DR",
            "body_part": "Chest",
            "study_description": "Chest radiograph for fever screening",
            "quality_status": "needs_review",
            "processing_status": "awaiting_ai",
            "study_time": base_time - timedelta(days=1, hours=1),
            "meta": {
                "priority": "normal",
                "report_status": "not_started",
                "ai_summary": "Image quality check suggests slight motion artifacts. Awaiting manual confirmation.",
                "findings": [],
            },
        },
    ]


def main():
    with app.app_context():
        account = db.session.query(Account).order_by(Account.created_at.asc()).first()
        if account is None:
            print("No account found. Create a user first before seeding imaging demo data.")
            sys.exit(1)

        rows = build_demo_rows(account.id)
        created = 0
        updated = 0

        for row in rows:
            study = db.session.get(ImagingStudy, row["id"])
            if study is None:
                study = ImagingStudy(account_id=account.id, **row)
                db.session.add(study)
                created += 1
            else:
                for key, value in row.items():
                    setattr(study, key, value)
                updated += 1

        db.session.commit()
        print(f"Seeded imaging demo data for account {account.id}. created={created}, updated={updated}")


if __name__ == "__main__":
    main()
