#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2026/4/24 16:00
@Author  : ccckz@protonmail.com
@File    : consult_center_service.py
"""
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from injector import inject
from sqlalchemy import func, desc

from internal.entity.app_entity import AppStatus
from internal.entity.workflow_entity import WorkflowStatus
from internal.model import App, Conversation, Dataset, Document, Message, Segment, Workflow
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService


@inject
@dataclass
class ConsultCenterService(BaseService):
    """会诊中枢首页聚合服务"""
    db: SQLAlchemy

    def get_overview(self, account) -> dict[str, Any]:
        """聚合会诊中枢首页所需的指标、最近资源和建议动作。"""
        now = datetime.now()
        seven_days_ago = now - timedelta(days=7)

        total_apps = self.db.session.query(func.count(App.id)).filter(App.account_id == account.id).scalar() or 0
        published_apps = (
            self.db.session.query(func.count(App.id))
            .filter(App.account_id == account.id, App.status == AppStatus.PUBLISHED)
            .scalar()
            or 0
        )
        total_datasets = self.db.session.query(func.count(Dataset.id)).filter(Dataset.account_id == account.id).scalar() or 0
        total_documents = self.db.session.query(func.count(Document.id)).filter(Document.account_id == account.id).scalar() or 0
        total_workflows = self.db.session.query(func.count(Workflow.id)).filter(Workflow.account_id == account.id).scalar() or 0
        published_workflows = (
            self.db.session.query(func.count(Workflow.id))
            .filter(Workflow.account_id == account.id, Workflow.status == WorkflowStatus.PUBLISHED)
            .scalar()
            or 0
        )
        recent_messages = (
            self.db.session.query(func.count(Message.id))
            .filter(Message.created_by == account.id, Message.created_at >= seven_days_ago, Message.answer != "")
            .scalar()
            or 0
        )
        recent_conversations = (
            self.db.session.query(func.count(Conversation.id))
            .filter(Conversation.created_by == account.id, Conversation.created_at >= seven_days_ago)
            .scalar()
            or 0
        )
        total_token_count = (
            self.db.session.query(func.coalesce(func.sum(Message.total_token_count), 0))
            .filter(Message.created_by == account.id, Message.created_at >= seven_days_ago)
            .scalar()
            or 0
        )
        total_latency = (
            self.db.session.query(func.coalesce(func.avg(Message.latency), 0))
            .filter(Message.created_by == account.id, Message.created_at >= seven_days_ago, Message.answer != "")
            .scalar()
            or 0
        )
        document_character_count = (
            self.db.session.query(func.coalesce(func.sum(Document.character_count), 0))
            .filter(Document.account_id == account.id)
            .scalar()
            or 0
        )
        dataset_hit_count = (
            self.db.session.query(func.coalesce(func.sum(Segment.hit_count), 0))
            .filter(Segment.account_id == account.id)
            .scalar()
            or 0
        )

        daily_activity = []
        for day in range(7):
            day_start = now.date() - timedelta(days=6 - day)
            start_at = datetime.combine(day_start, datetime.min.time())
            end_at = start_at + timedelta(days=1)
            count = (
                self.db.session.query(func.count(Message.id))
                .filter(
                    Message.created_by == account.id,
                    Message.created_at >= start_at,
                    Message.created_at < end_at,
                    Message.answer != "",
                )
                .scalar()
                or 0
            )
            daily_activity.append({
                "date": day_start.isoformat(),
                "count": int(count),
            })

        recent_apps = [
            {
                "id": str(app.id),
                "name": app.name,
                "description": app.description,
                "status": app.status,
                "created_at": int(app.created_at.timestamp()) if app.created_at else 0,
            }
            for app in self.db.session.query(App).filter(App.account_id == account.id).order_by(desc("created_at")).limit(4)
        ]
        recent_datasets = [
            {
                "id": str(dataset.id),
                "name": dataset.name,
                "description": dataset.description,
                "document_count": dataset.document_count,
                "hit_count": dataset.hit_count,
                "created_at": int(dataset.created_at.timestamp()) if dataset.created_at else 0,
            }
            for dataset in self.db.session.query(Dataset).filter(Dataset.account_id == account.id).order_by(desc("created_at")).limit(4)
        ]
        recent_workflows = [
            {
                "id": str(workflow.id),
                "name": workflow.name,
                "description": workflow.description,
                "status": workflow.status,
                "created_at": int(workflow.created_at.timestamp()) if workflow.created_at else 0,
            }
            for workflow in self.db.session.query(Workflow).filter(Workflow.account_id == account.id).order_by(desc("created_at")).limit(4)
        ]

        recommended_actions = []
        if total_datasets == 0:
            recommended_actions.append("Import clinical guideline datasets")
        if total_workflows == 0:
            recommended_actions.append("Create an MDT orchestration workflow")
        if total_apps == 0:
            recommended_actions.append("Create the first consult app")
        if not recommended_actions:
            recommended_actions.extend([
                "Refine the review gate for high-risk consults",
                "Connect more evidence sources to Graph RAG",
            ])

        return {
            "summary": {
                "total_apps": int(total_apps),
                "published_apps": int(published_apps),
                "total_datasets": int(total_datasets),
                "total_documents": int(total_documents),
                "total_workflows": int(total_workflows),
                "published_workflows": int(published_workflows),
                "recent_messages": int(recent_messages),
                "recent_conversations": int(recent_conversations),
                "total_token_count": int(total_token_count),
                "average_latency": float(total_latency) if total_latency else 0.0,
                "document_character_count": int(document_character_count),
                "dataset_hit_count": int(dataset_hit_count),
            },
            "daily_activity": daily_activity,
            "recent_items": {
                "apps": recent_apps,
                "datasets": recent_datasets,
                "workflows": recent_workflows,
            },
            "recommended_actions": recommended_actions,
        }
