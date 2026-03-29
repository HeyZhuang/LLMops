#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2026/3/18 10:00
@Author  : phase1
@File    : feedback_handler.py
"""
from dataclasses import dataclass
from uuid import UUID

from flask_login import login_required, current_user
from injector import inject

from internal.schema.feedback_schema import CreateFeedbackReq, GetFeedbackResp
from internal.service.feedback_service import FeedbackService
from pkg.response import success_json, validate_error_json


@inject
@dataclass
class FeedbackHandler:
    """消息反馈处理器"""
    feedback_service: FeedbackService

    @login_required
    def create_feedback(self, message_id: UUID):
        """创建/更新消息反馈"""
        req = CreateFeedbackReq()
        if not req.validate():
            return validate_error_json(req.errors)

        feedback = self.feedback_service.create_or_update_feedback(
            message_id=message_id,
            rating=req.rating.data,
            content=req.content.data or "",
            account=current_user,
        )

        resp = GetFeedbackResp()
        return success_json(resp.dump(feedback))

    @login_required
    def get_feedback(self, message_id: UUID):
        """获取消息反馈"""
        feedback = self.feedback_service.get_feedback(message_id, current_user)

        if not feedback:
            return success_json(None)

        resp = GetFeedbackResp()
        return success_json(resp.dump(feedback))

    @login_required
    def get_feedback_stats(self, app_id: UUID):
        """获取应用反馈统计"""
        stats = self.feedback_service.get_feedback_stats(app_id, current_user)
        return success_json(stats)
