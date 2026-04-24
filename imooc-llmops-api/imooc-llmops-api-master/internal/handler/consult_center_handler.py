#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2026/4/24 16:00
@Author  : ccckz@protonmail.com
@File    : consult_center_handler.py
"""
from dataclasses import dataclass

from flask_login import login_required, current_user
from injector import inject

from internal.service import ConsultCenterService
from pkg.response import success_json


@inject
@dataclass
class ConsultCenterHandler:
    """会诊中枢聚合接口"""
    consult_center_service: ConsultCenterService

    @login_required
    def get_overview(self):
        """获取会诊中枢首页聚合数据"""
        overview = self.consult_center_service.get_overview(current_user)
        return success_json(overview)
