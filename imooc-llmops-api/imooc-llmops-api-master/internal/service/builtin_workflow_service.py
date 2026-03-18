#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2026/3/18 10:00
@Author  : LLMOps
@File    : builtin_workflow_service.py
"""
from dataclasses import dataclass

from injector import inject

from internal.core.builtin_apps.entities.category_entity import CategoryEntity
from internal.core.builtin_workflows import BuiltinWorkflowManager
from internal.core.builtin_workflows.entities.builtin_workflow_entity import BuiltinWorkflowEntity
from internal.entity.workflow_entity import WorkflowStatus, DEFAULT_WORKFLOW_CONFIG
from internal.exception import NotFoundException, ValidateErrorException
from internal.model import Account, Workflow
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService


@inject
@dataclass
class BuiltinWorkflowService(BaseService):
    """内置工作流模板服务"""
    db: SQLAlchemy
    builtin_workflow_manager: BuiltinWorkflowManager

    def get_categories(self) -> list[CategoryEntity]:
        """获取分类列表信息"""
        return self.builtin_workflow_manager.get_categories()

    def get_builtin_workflows(self) -> list[BuiltinWorkflowEntity]:
        """获取所有内置工作流模板实体信息列表"""
        return self.builtin_workflow_manager.get_builtin_workflows()

    def add_builtin_workflow_to_space(self, builtin_workflow_id: str, account: Account) -> Workflow:
        """将指定的内置工作流模板添加到个人空间下"""
        # 1.获取内置工作流模板信息，并检测是否存在
        builtin_workflow = self.builtin_workflow_manager.get_builtin_workflow(builtin_workflow_id)
        if not builtin_workflow:
            raise NotFoundException("该内置工作流模板不存在，请核实后重试")

        # 2.检查tool_call_name是否已存在（避免重复）
        check_workflow = self.db.session.query(Workflow).filter(
            Workflow.tool_call_name == builtin_workflow.tool_call_name,
            Workflow.account_id == account.id,
        ).one_or_none()
        if check_workflow:
            raise ValidateErrorException(f"在当前账号下已创建[{builtin_workflow.tool_call_name}]工作流，不支持重名")

        # 3.创建工作流记录
        workflow = self.create(Workflow, **{
            "account_id": account.id,
            "name": builtin_workflow.name,
            "tool_call_name": builtin_workflow.tool_call_name,
            "icon": builtin_workflow.icon,
            "description": builtin_workflow.description,
            "draft_graph": builtin_workflow.draft_graph,
            "graph": DEFAULT_WORKFLOW_CONFIG.get("graph", {}),
            "is_debug_passed": False,
            "status": WorkflowStatus.DRAFT,
        })

        return workflow
