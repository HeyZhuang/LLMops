#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2026/3/18 10:00
@Author  : phase1
@File    : app_export_handler.py
"""
from dataclasses import dataclass
from uuid import UUID

from flask import request
from flask_login import login_required, current_user
from injector import inject

from internal.service.app_export_service import AppExportService
from pkg.response import success_json


@inject
@dataclass
class AppExportHandler:
    """应用导入导出处理器"""
    app_export_service: AppExportService

    @login_required
    def export_app(self, app_id: UUID):
        """导出应用为JSON"""
        export_data = self.app_export_service.export_app(app_id, current_user)
        return success_json(export_data)

    @login_required
    def import_app(self):
        """从JSON导入应用"""
        import_data = request.get_json(force=True)
        result = self.app_export_service.import_app(import_data, current_user)
        return success_json(result)
