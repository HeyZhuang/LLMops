#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2026/3/18 10:00
@Author  : phase1
@File    : feedback_service.py
"""
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from injector import inject
from sqlalchemy import func

from internal.exception import NotFoundException, ForbiddenException
from internal.model import Account, Message
from internal.model.message_feedback import MessageFeedback
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService


@inject
@dataclass
class FeedbackService(BaseService):
    """消息反馈服务"""
    db: SQLAlchemy

    def create_or_update_feedback(
            self, message_id: UUID, rating: str, content: str, account: Account,
    ) -> MessageFeedback:
        """创建或更新消息反馈"""
        # 1.验证消息存在性
        message = self.get(Message, message_id)
        if not message:
            raise NotFoundException("该消息不存在")

        # 2.查找是否已有反馈
        feedback = self.db.session.query(MessageFeedback).filter(
            MessageFeedback.message_id == message_id,
            MessageFeedback.created_by == account.id,
        ).one_or_none()

        # 3.存在则更新，不存在则创建
        if feedback:
            self.update(feedback, rating=rating, content=content)
        else:
            feedback = self.create(
                MessageFeedback,
                app_id=message.app_id,
                conversation_id=message.conversation_id,
                message_id=message_id,
                rating=rating,
                content=content,
                created_by=account.id,
            )

        return feedback

    def get_feedback(self, message_id: UUID, account: Account) -> MessageFeedback:
        """获取消息反馈"""
        feedback = self.db.session.query(MessageFeedback).filter(
            MessageFeedback.message_id == message_id,
            MessageFeedback.created_by == account.id,
        ).one_or_none()

        return feedback

    def get_feedback_stats(self, app_id: UUID, account: Account) -> dict[str, Any]:
        """获取应用反馈统计"""
        # 1.统计like数量
        like_count = self.db.session.query(func.count(MessageFeedback.id)).filter(
            MessageFeedback.app_id == app_id,
            MessageFeedback.rating == "like",
        ).scalar()

        # 2.统计dislike数量
        dislike_count = self.db.session.query(func.count(MessageFeedback.id)).filter(
            MessageFeedback.app_id == app_id,
            MessageFeedback.rating == "dislike",
        ).scalar()

        # 3.计算总数和满意度
        total = like_count + dislike_count
        satisfaction_rate = float(like_count / total) if total > 0 else 0

        return {
            "like_count": like_count,
            "dislike_count": dislike_count,
            "total_count": total,
            "satisfaction_rate": satisfaction_rate,
        }
