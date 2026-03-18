#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2026/3/18 10:00
@Author  : LLMOps
@File    : builtin_workflow_schema.py
"""
from flask_wtf import FlaskForm
from marshmallow import Schema, fields, pre_dump
from wtforms import StringField
from wtforms.validators import DataRequired, UUID

from internal.core.builtin_apps.entities.category_entity import CategoryEntity
from internal.core.builtin_workflows.entities.builtin_workflow_entity import BuiltinWorkflowEntity


class GetBuiltinWorkflowCategoriesResp(Schema):
    """获取内置工作流模板分类列表响应"""
    category = fields.String(dump_default="")
    name = fields.String(dump_default="")

    @pre_dump
    def process_data(self, data: CategoryEntity, **kwargs):
        return data.model_dump()


class GetBuiltinWorkflowsResp(Schema):
    """获取内置工作流模板实体列表响应"""
    id = fields.String(dump_default="")
    category = fields.String(dump_default="")
    name = fields.String(dump_default="")
    tool_call_name = fields.String(dump_default="")
    icon = fields.String(dump_default="")
    description = fields.String(dump_default="")
    node_count = fields.Integer(dump_default=0)
    author = fields.String(dump_default="")
    created_at = fields.Integer(dump_default=0)

    @pre_dump
    def process_data(self, data: BuiltinWorkflowEntity, **kwargs):
        return {
            **data.model_dump(include={"id", "category", "name", "tool_call_name", "icon", "description", "author", "created_at"}),
            "node_count": len(data.draft_graph.get("nodes", [])),
        }


class AddBuiltinWorkflowToSpaceReq(FlaskForm):
    """添加内置工作流模板到个人空间请求"""
    builtin_workflow_id = StringField("builtin_workflow_id", default="", validators=[
        DataRequired("内置工作流模板id不能为空"),
        UUID("内置工作流模板id格式必须为UUID"),
    ])
