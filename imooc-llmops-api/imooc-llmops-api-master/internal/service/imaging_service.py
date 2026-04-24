#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Read-only planning service for the imaging domain.
"""
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import UUID
from uuid import uuid5, NAMESPACE_DNS

from injector import inject
from sqlalchemy import func, inspect

from internal.core.imaging import IMAGING_WORKFLOW_TEMPLATES
from internal.model import (
    App,
    Dataset,
    Document,
    Workflow,
    ImagingStudy,
    ImagingReport,
    ImagingReview,
)
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService


@inject
@dataclass
class ImagingService(BaseService):
    db: SQLAlchemy

    def _db_tables_ready(self) -> bool:
        inspector = inspect(self.db.engine)
        return inspector.has_table("imaging_report") and inspector.has_table("imaging_review")

    def _load_persisted_state(self, account_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
        if self._db_tables_ready():
            reports = {
                str(item.study_id): {
                    "content": item.draft_content,
                    "status": item.report_status,
                    "summary": item.doctor_notes,
                    "updated_at": int(item.updated_at.timestamp()) if item.updated_at else 0,
                }
                for item in self.db.session.query(ImagingReport).filter(
                    ImagingReport.study_id.isnot(None)
                ).all()
            }
            reviews = {
                str(item.study_id): {
                    "label": item.review_label,
                    "comment": item.comment,
                    "status": item.review_payload.get("status", item.review_label),
                    "updated_at": int(item.created_at.timestamp()) if item.created_at else 0,
                }
                for item in self.db.session.query(ImagingReview).filter(
                    ImagingReview.reviewer_id == UUID(account_id)
                ).all()
            }
            return reports, reviews

        account_state = self._load_state().get(account_id, {})
        return account_state.get("reports", {}), account_state.get("reviews", {})

    def _load_db_studies(self, account_id: str) -> list[dict[str, Any]]:
        if not inspect(self.db.engine).has_table("imaging_study"):
            return []

        studies = self.db.session.query(ImagingStudy).filter(
            ImagingStudy.account_id == UUID(account_id)
        ).order_by(ImagingStudy.study_time.desc().nullslast()).all()

        return [
            {
                "id": str(item.id),
                "patient_code": item.accession_number or item.patient_uid,
                "patient_name_masked": item.patient_name_masked,
                "modality": item.modality,
                "body_part": item.body_part,
                "study_description": item.study_description,
                "study_time": int(item.study_time.timestamp()) if item.study_time else 0,
                "status": item.processing_status,
                "quality_status": item.quality_status,
                "ai_summary": item.meta.get("ai_summary", ""),
                "findings_count": len(item.meta.get("findings", [])),
                "report_status": item.meta.get("report_status", "not_started"),
                "priority": item.meta.get("priority", "normal"),
            }
            for item in studies
        ]

    @staticmethod
    def _state_file() -> Path:
        return Path(__file__).resolve().parents[4] / "storage" / "imaging_demo_state.json"

    def _load_state(self) -> dict[str, Any]:
        state_file = self._state_file()
        if not state_file.exists():
            return {}

        try:
            return json.loads(state_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}

    def _save_state(self, state: dict[str, Any]) -> None:
        state_file = self._state_file()
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def _build_demo_studies(account_id: str) -> list[dict[str, Any]]:
        base_time = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
        seed = f"llmops-imaging-{account_id}"
        return [
            {
                "id": str(uuid5(NAMESPACE_DNS, f"{seed}-study-1")),
                "patient_code": "RAD-2026-0001",
                "patient_name_masked": "Zhang**",
                "modality": "CT",
                "body_part": "Chest",
                "study_description": "Chest CT plain scan for lung nodule follow-up",
                "study_time": int((base_time - timedelta(hours=2)).timestamp()),
                "status": "doctor_review",
                "quality_status": "qualified",
                "ai_summary": "Two pulmonary nodules detected in the right upper lobe. Report draft ready.",
                "findings_count": 2,
                "report_status": "draft_ready",
                "priority": "normal",
            },
            {
                "id": str(uuid5(NAMESPACE_DNS, f"{seed}-study-2")),
                "patient_code": "ER-2026-0148",
                "patient_name_masked": "Li**",
                "modality": "CT",
                "body_part": "Brain",
                "study_description": "Emergency non-contrast brain CT for dizziness and vomiting",
                "study_time": int((base_time - timedelta(hours=6)).timestamp()),
                "status": "ai_completed",
                "quality_status": "qualified",
                "ai_summary": "No clear intracranial hemorrhage detected. Manual review recommended.",
                "findings_count": 1,
                "report_status": "pending_draft",
                "priority": "urgent",
            },
            {
                "id": str(uuid5(NAMESPACE_DNS, f"{seed}-study-3")),
                "patient_code": "DR-2026-0233",
                "patient_name_masked": "Wang**",
                "modality": "DR",
                "body_part": "Chest",
                "study_description": "Chest radiograph for fever screening",
                "study_time": int((base_time - timedelta(days=1, hours=1)).timestamp()),
                "status": "awaiting_ai",
                "quality_status": "needs_review",
                "ai_summary": "Image quality check suggests slight motion artifacts. Awaiting manual confirmation.",
                "findings_count": 0,
                "report_status": "not_started",
                "priority": "normal",
            },
        ]

    def get_overview(self, account) -> dict[str, Any]:
        total_apps = self.db.session.query(func.count(App.id)).filter(App.account_id == account.id).scalar() or 0
        total_datasets = self.db.session.query(func.count(Dataset.id)).filter(Dataset.account_id == account.id).scalar() or 0
        total_documents = self.db.session.query(func.count(Document.id)).filter(Document.account_id == account.id).scalar() or 0
        total_workflows = self.db.session.query(func.count(Workflow.id)).filter(Workflow.account_id == account.id).scalar() or 0

        return {
            "title": "AI 医院影像智能处理中心",
            "summary": (
                "围绕真实医院影像科流程建设影像接入、AI 辅助检出、报告草拟、"
                "知识问答和审计分析能力，优先完成胸部 CT 报告助手的 MVP 闭环。"
            ),
            "positioning": [
                "影像接入与质控中心",
                "结构化报告与医生审核工作台",
                "面向医院私有化部署的影像 AI 平台",
            ],
            "scenes": [
                {
                    "name": "影像接入",
                    "value": "01",
                    "description": "支持 PACS、RIS 和手工上传，统一管理 DICOM 检查、序列和实例。",
                },
                {
                    "name": "辅助检出",
                    "value": "02",
                    "description": "优先支持胸部 CT 肺结节和头颅 CT 出血筛查等高价值窄场景。",
                },
                {
                    "name": "报告草拟",
                    "value": "03",
                    "description": "结合 AI 结果、指南知识库和医院模板生成报告初稿，由医生确认。",
                },
                {
                    "name": "质控分析",
                    "value": "04",
                    "description": "统计采纳率、误报漏报、耗时与访问日志，形成闭环分析能力。",
                },
            ],
            "phases": [
                {
                    "key": "phase-0",
                    "title": "Phase 0 影像基础设施",
                    "goal": "让平台具备真实影像数据管理能力。",
                    "deliverables": ["DICOM 导入", "检查和序列管理", "脱敏策略", "审计日志"],
                },
                {
                    "key": "phase-1",
                    "title": "Phase 1 报告助手 MVP",
                    "goal": "先落地低风险、高频价值的影像报告场景。",
                    "deliverables": ["模板管理", "指南知识库", "报告草稿生成", "医生编辑审核"],
                },
                {
                    "key": "phase-2",
                    "title": "Phase 2 专病 AI 检出",
                    "goal": "接入专病模型并形成医生反馈闭环。",
                    "deliverables": ["专病推理服务", "病灶标注可视化", "误报漏报反馈", "效果统计"],
                },
                {
                    "key": "phase-3",
                    "title": "Phase 3 医院系统集成",
                    "goal": "与 PACS、RIS、HIS 打通真实院内链路。",
                    "deliverables": ["PACS 对接", "RIS 回写", "高危告警", "多院区权限隔离"],
                },
            ],
            "guardrails": [
                "AI 结果仅作辅助参考，正式报告必须由医生确认。",
                "患者数据默认走脱敏和审计，优先支持院内私有化部署。",
                "正式环境模型版本和提示词版本需要可追溯、可回滚。",
            ],
            "metrics": {
                "apps": int(total_apps),
                "datasets": int(total_datasets),
                "documents": int(total_documents),
                "workflows": int(total_workflows),
                "workflow_templates": len(IMAGING_WORKFLOW_TEMPLATES),
            },
            "mvp": {
                "name": "胸部 CT 影像报告智能助手",
                "value": (
                    "优先建设 DICOM 上传、检查列表、知识库驱动的报告草稿、"
                    "医生审核和审计追踪的完整闭环。"
                ),
            },
        }

    def get_workflow_templates(self) -> list[dict[str, Any]]:
        templates = []
        for key, item in IMAGING_WORKFLOW_TEMPLATES.items():
            templates.append({
                "key": key,
                "name": item["name"],
                "scene": item["scene"],
                "steps": item["steps"],
                "outputs": item["outputs"],
            })
        return templates

    @staticmethod
    def get_mvp_tasks() -> list[dict[str, Any]]:
        return [
            {
                "key": "m1",
                "title": "影像基础设施",
                "owner": "Backend",
                "items": ["DICOM 导入", "检查/序列/实例模型", "脱敏与审计"],
            },
            {
                "key": "m2",
                "title": "影像中心前端",
                "owner": "Frontend",
                "items": ["影像中心规划页", "检查列表页", "报告工作台原型"],
            },
            {
                "key": "m3",
                "title": "报告助手闭环",
                "owner": "Backend + LLM",
                "items": ["模板管理", "知识库检索", "报告草稿生成", "医生审核保存"],
            },
            {
                "key": "m4",
                "title": "专病模型接入",
                "owner": "Algorithm",
                "items": ["推理服务", "结构化发现", "误报漏报反馈"],
            },
        ]

    def get_studies(self, account) -> list[dict[str, Any]]:
        studies = self._load_db_studies(str(account.id))
        if not studies:
            studies = self._build_demo_studies(str(account.id))
        reports, reviews = self._load_persisted_state(str(account.id))

        for study in studies:
            report = reports.get(study["id"])
            if report:
                study["report_status"] = report.get("status", study["report_status"])
                study["ai_summary"] = report.get("summary", study["ai_summary"])

            review = reviews.get(study["id"])
            if review:
                study["status"] = review.get("status", study["status"])

        return studies

    def get_study_detail(self, study_id: str, account) -> dict[str, Any]:
        studies = self._load_db_studies(str(account.id))
        if not studies:
            studies = self._build_demo_studies(str(account.id))
        study = next((item for item in studies if item["id"] == study_id), None)
        if study is None:
            study = studies[0]

        if study["body_part"] == "Chest":
            findings = [
                {
                    "title": "Right upper lobe nodule",
                    "confidence": 0.93,
                    "description": "8 mm solid nodule with clear margin in the apical segment.",
                },
                {
                    "title": "Right upper lobe micronodule",
                    "confidence": 0.74,
                    "description": "3 mm tiny nodule, follow-up suggested according to guideline.",
                },
            ]
            report_draft = (
                "Findings: Small solid pulmonary nodules are seen in the right upper lobe, "
                "largest about 8 mm. No pleural effusion or enlarged mediastinal lymph nodes. "
                "Impression: Right upper lobe pulmonary nodules, recommend follow-up with low-dose CT."
            )
        elif study["body_part"] == "Brain":
            findings = [
                {
                    "title": "No definite acute hemorrhage",
                    "confidence": 0.88,
                    "description": "No obvious hyperdense hemorrhagic focus identified on the current scan.",
                },
            ]
            report_draft = (
                "Findings: Brain parenchyma density is generally symmetric. No definite acute hemorrhage seen. "
                "Ventricular system is not enlarged. Impression: No obvious acute intracranial hemorrhage on current CT."
            )
        else:
            findings = [
                {
                    "title": "Quality warning",
                    "confidence": 0.67,
                    "description": "Mild motion artifact affects the lower lung field visibility.",
                },
            ]
            report_draft = (
                "Findings: Mild motion artifact is present. No large focal consolidation is clearly identified. "
                "Impression: Recommend clinician correlation and repeat image if clinically indicated."
            )

        reports, reviews = self._load_persisted_state(str(account.id))
        report_state = reports.get(study["id"], {})
        review_state = reviews.get(study["id"], {})

        return {
            **study,
            "series": [
                {"name": "Series 1", "images": 126, "slice_thickness": "1.0 mm"},
                {"name": "Series 2", "images": 126, "slice_thickness": "5.0 mm"},
            ],
            "findings": findings,
            "report_draft": {
                "status": report_state.get("status", study["report_status"]),
                "content": report_state.get("content", report_draft),
                "template_name": f"{study['body_part']} Standard Report Template",
                "template_version": "v1.0",
            },
            "timeline": [
                {"label": "Study imported", "value": "Completed"},
                {"label": "Quality check", "value": study["quality_status"]},
                {"label": "AI inference", "value": review_state.get("status", study["status"])},
                {"label": "Doctor review", "value": report_state.get("status", study["report_status"])},
            ],
            "review": {
                "label": review_state.get("label", ""),
                "comment": review_state.get("comment", ""),
                "updated_at": review_state.get("updated_at", 0),
            },
        }

    def save_report_draft(self, study_id: str, content: str, account) -> dict[str, Any]:
        if self._db_tables_ready():
            report = self.db.session.query(ImagingReport).filter(
                ImagingReport.study_id == UUID(study_id)
            ).one_or_none()
            if report is None:
                report = self.create(
                    ImagingReport,
                    study_id=UUID(study_id),
                    template_name="Imaging Draft Template",
                    template_version="v1.0",
                    generation_source="doctor_editing",
                    report_status="doctor_editing",
                    draft_content=content,
                    doctor_notes="Doctor updated the report draft and saved the latest version.",
                )
            else:
                self.update(
                    report,
                    draft_content=content,
                    report_status="doctor_editing",
                    doctor_notes="Doctor updated the report draft and saved the latest version.",
                )
            return {
                "study_id": study_id,
                "status": "doctor_editing",
                "updated_at": int(report.updated_at.timestamp()) if report.updated_at else 0,
            }

        state = self._load_state()
        account_state = state.setdefault(str(account.id), {})
        reports = account_state.setdefault("reports", {})
        reports[study_id] = {
            "content": content,
            "status": "doctor_editing",
            "summary": "Doctor updated the report draft and saved the latest version.",
            "updated_at": int(datetime.now().timestamp()),
        }
        self._save_state(state)
        return {
            "study_id": study_id,
            "status": "doctor_editing",
            "updated_at": reports[study_id]["updated_at"],
        }

    def submit_review(self, study_id: str, label: str, comment: str, account) -> dict[str, Any]:
        status_map = {
            "approved": "doctor_reviewed",
            "needs_revision": "doctor_revision_needed",
            "rejected": "doctor_rejected",
        }
        review_status = status_map.get(label, "doctor_reviewed")

        if self._db_tables_ready():
            report = self.db.session.query(ImagingReport).filter(
                ImagingReport.study_id == UUID(study_id)
            ).one_or_none()
            if report is None:
                report = self.create(
                    ImagingReport,
                    study_id=UUID(study_id),
                    template_name="Imaging Draft Template",
                    template_version="v1.0",
                    generation_source="doctor_review",
                    report_status="signed" if label == "approved" else "doctor_editing",
                    draft_content="",
                    doctor_notes="Doctor review submitted.",
                )
            else:
                self.update(
                    report,
                    report_status="signed" if label == "approved" else "doctor_editing",
                    doctor_notes=comment or "Doctor review submitted.",
                )

            review = self.db.session.query(ImagingReview).filter(
                ImagingReview.study_id == UUID(study_id),
                ImagingReview.reviewer_id == account.id,
            ).one_or_none()
            payload = {"status": review_status}
            if review is None:
                review = self.create(
                    ImagingReview,
                    study_id=UUID(study_id),
                    report_id=report.id,
                    reviewer_id=account.id,
                    review_type="doctor_review",
                    review_label=label,
                    comment=comment,
                    review_payload=payload,
                )
            else:
                self.update(
                    review,
                    review_label=label,
                    comment=comment,
                    review_payload=payload,
                    report_id=report.id,
                )
            return {
                "study_id": study_id,
                "label": label,
                "status": review_status,
                "updated_at": int(review.created_at.timestamp()) if review.created_at else 0,
            }

        state = self._load_state()
        account_state = state.setdefault(str(account.id), {})
        reviews = account_state.setdefault("reviews", {})
        reports = account_state.setdefault("reports", {})

        reviews[study_id] = {
            "label": label,
            "comment": comment,
            "status": review_status,
            "updated_at": int(datetime.now().timestamp()),
        }

        report = reports.setdefault(study_id, {})
        report["status"] = "signed" if label == "approved" else "doctor_editing"
        report["updated_at"] = int(datetime.now().timestamp())
        if label == "approved":
            report["summary"] = "Doctor approved the draft. Study is ready for final archive."
        elif label == "needs_revision":
            report["summary"] = "Doctor requested revisions before final signing."
        else:
            report["summary"] = "Doctor rejected the current draft and requested manual rewrite."

        self._save_state(state)
        return {
            "study_id": study_id,
            "label": label,
            "status": reviews[study_id]["status"],
            "updated_at": reviews[study_id]["updated_at"],
        }
