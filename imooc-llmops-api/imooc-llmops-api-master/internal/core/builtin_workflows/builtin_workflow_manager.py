#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2026/3/18 10:00
@Author  : LLMOps
@File    : builtin_workflow_manager.py
"""
import os

import yaml
from injector import inject, singleton
from pydantic import BaseModel, Field

from internal.core.builtin_apps.entities.category_entity import CategoryEntity
from internal.core.builtin_workflows.entities.builtin_workflow_entity import BuiltinWorkflowEntity


@inject
@singleton
class BuiltinWorkflowManager(BaseModel):
    """内置工作流模板管理器"""
    builtin_workflow_map: dict[str, BuiltinWorkflowEntity] = Field(default_factory=dict)
    categories: list[CategoryEntity] = Field(default_factory=list)

    def __init__(self, **kwargs):
        """构造函数，初始化对应的builtin_workflow_map"""
        super().__init__(**kwargs)
        self._init_categories()
        self._init_builtin_workflow_map()

    def get_builtin_workflow(self, builtin_workflow_id: str) -> BuiltinWorkflowEntity:
        """根据传递的id获取内置工作流模板信息"""
        return self.builtin_workflow_map.get(builtin_workflow_id, None)

    def get_builtin_workflows(self) -> list[BuiltinWorkflowEntity]:
        """获取内置工作流模板实体列表信息"""
        return [entity for entity in self.builtin_workflow_map.values()]

    def get_categories(self) -> list[CategoryEntity]:
        """获取内置工作流模板分类列表信息"""
        return self.categories

    def _init_builtin_workflow_map(self):
        """初始化所有内置工作流模板信息"""
        if self.builtin_workflow_map:
            return

        current_path = os.path.abspath(__file__)
        parent_path = os.path.dirname(current_path)
        builtin_workflows_yaml_path = os.path.join(parent_path, "builtin_workflows")

        for filename in os.listdir(builtin_workflows_yaml_path):
            if filename.endswith(".yaml") or filename.endswith(".yml"):
                file_path = os.path.join(builtin_workflows_yaml_path, filename)

                with open(file_path, encoding="utf-8") as f:
                    builtin_workflow = yaml.safe_load(f)

                self.builtin_workflow_map[builtin_workflow.get("id")] = BuiltinWorkflowEntity(**builtin_workflow)

    def _init_categories(self):
        """初始化内置工作流模板分类列表信息"""
        if self.categories:
            return

        current_path = os.path.abspath(__file__)
        parent_path = os.path.dirname(current_path)
        categories_yaml_path = os.path.join(parent_path, "categories", "categories.yaml")

        with open(categories_yaml_path, encoding="utf-8") as f:
            categories = yaml.safe_load(f)

        for category in categories:
            self.categories.append(CategoryEntity(**category))
