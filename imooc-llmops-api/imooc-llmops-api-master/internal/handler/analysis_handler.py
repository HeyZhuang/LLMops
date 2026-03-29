#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2025/12/09 0:49
@Author  : ccckz@protonmail.com
@File    : analysis_handler.py
"""
from dataclasses import dataclass
from uuid import UUID

from flask_login import login_required, current_user
from injector import inject

from internal.service import AnalysisService
from pkg.response import success_json


@inject
@dataclass
class AnalysisHandler:
    """统计分析处理器"""
    analysis_service: AnalysisService

    @login_required
    def get_app_analysis(self, app_id: UUID):
        """根据传递的应用id获取应用的统计信息"""
        app_analysis = self.analysis_service.get_app_analysis(app_id, current_user)
        return success_json(app_analysis)

    @login_required
    def get_token_cost_analysis(self, app_id: UUID):
        """获取应用Token成本分析"""
        token_cost = self.analysis_service.get_token_cost_analysis(app_id, current_user)
        return success_json(token_cost)
