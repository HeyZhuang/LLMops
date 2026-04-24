#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Imaging planning endpoints.
"""
from dataclasses import dataclass

from flask import request
from flask_login import login_required, current_user
from injector import inject

from internal.service import ImagingService
from pkg.response import success_json, success_message


@inject
@dataclass
class ImagingHandler:
    imaging_service: ImagingService

    @login_required
    def get_overview(self):
        return success_json(self.imaging_service.get_overview(current_user))

    @login_required
    def get_workflow_templates(self):
        return success_json(self.imaging_service.get_workflow_templates())

    @login_required
    def get_mvp_tasks(self):
        return success_json(self.imaging_service.get_mvp_tasks())

    @login_required
    def get_studies(self):
        return success_json(self.imaging_service.get_studies(current_user))

    @login_required
    def get_study_detail(self, study_id: str):
        return success_json(self.imaging_service.get_study_detail(study_id, current_user))

    @login_required
    def save_report_draft(self, study_id: str):
        payload = request.get_json(silent=True) or {}
        content = str(payload.get("content", "")).strip()
        self.imaging_service.save_report_draft(study_id, content, current_user)
        return success_message("报告草稿已保存")

    @login_required
    def submit_review(self, study_id: str):
        payload = request.get_json(silent=True) or {}
        label = str(payload.get("label", "approved")).strip()
        comment = str(payload.get("comment", "")).strip()
        self.imaging_service.submit_review(study_id, label, comment, current_user)
        return success_message("审核结果已提交")
