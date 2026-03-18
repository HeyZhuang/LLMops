#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2026/3/18 10:00
@Author  : LLMOps
@File    : builtin_workflow_handler.py
"""
from dataclasses import dataclass

from flask_login import login_required, current_user
from injector import inject

from internal.schema.builtin_workflow_schema import (
    GetBuiltinWorkflowCategoriesResp,
    GetBuiltinWorkflowsResp,
    AddBuiltinWorkflowToSpaceReq,
)
from internal.service import BuiltinWorkflowService
from pkg.response import success_json, validate_error_json


@inject
@dataclass
class BuiltinWorkflowHandler:
    """LLMOps内置工作流模板处理器"""
    builtin_workflow_service: BuiltinWorkflowService

    @login_required
    def get_builtin_workflow_categories(self):
        """获取内置工作流模板分类列表信息"""
        categories = self.builtin_workflow_service.get_categories()
        resp = GetBuiltinWorkflowCategoriesResp(many=True)
        return success_json(resp.dump(categories))

    @login_required
    def get_builtin_workflows(self):
        """获取所有内置工作流模板列表信息"""
        builtin_workflows = self.builtin_workflow_service.get_builtin_workflows()
        resp = GetBuiltinWorkflowsResp(many=True)
        return success_json(resp.dump(builtin_workflows))

    @login_required
    def add_builtin_workflow_to_space(self):
        """将指定的内置工作流模板添加到个人空间"""
        req = AddBuiltinWorkflowToSpaceReq()
        if not req.validate():
            return validate_error_json(req.errors)

        workflow = self.builtin_workflow_service.add_builtin_workflow_to_space(
            req.builtin_workflow_id.data, current_user
        )

        return success_json({"id": workflow.id})
