#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2026/3/18 10:00
@Author  : phase1
@File    : prompt_template_schema.py
"""
from flask_wtf import FlaskForm
from marshmallow import Schema, fields, pre_dump
from wtforms import StringField, BooleanField
from wtforms.validators import DataRequired, Length, Optional

from internal.lib.helper import datetime_to_timestamp
from internal.model.prompt_template import PromptTemplate
from pkg.paginator import PaginatorReq


class CreatePromptTemplateReq(FlaskForm):
    """创建Prompt模板请求"""
    name = StringField("name", validators=[
        DataRequired("模板名称不能为空"),
        Length(max=255, message="模板名称长度不能超过255个字符"),
    ])
    description = StringField("description", default="", validators=[Optional()])
    content = StringField("content", validators=[
        DataRequired("模板内容不能为空"),
    ])
    category = StringField("category", default="", validators=[Optional()])
    is_public = BooleanField("is_public", default=False)


class UpdatePromptTemplateReq(FlaskForm):
    """更新Prompt模板请求"""
    name = StringField("name", validators=[
        DataRequired("模板名称不能为空"),
        Length(max=255, message="模板名称长度不能超过255个字符"),
    ])
    description = StringField("description", default="", validators=[Optional()])
    content = StringField("content", validators=[
        DataRequired("模板内容不能为空"),
    ])
    category = StringField("category", default="", validators=[Optional()])
    is_public = BooleanField("is_public", default=False)


class GetPromptTemplatesWithPageReq(PaginatorReq):
    """获取模板分页列表请求"""
    search_word = StringField("search_word", default="", validators=[Optional()])
    category = StringField("category", default="", validators=[Optional()])


class GetPromptTemplateResp(Schema):
    """获取Prompt模板响应"""
    id = fields.UUID(dump_default="")
    name = fields.String(dump_default="")
    description = fields.String(dump_default="")
    content = fields.String(dump_default="")
    category = fields.String(dump_default="")
    is_public = fields.Boolean(dump_default=False)
    updated_at = fields.Integer(dump_default=0)
    created_at = fields.Integer(dump_default=0)

    @pre_dump
    def process_data(self, data: PromptTemplate, **kwargs):
        return {
            "id": data.id,
            "name": data.name,
            "description": data.description,
            "content": data.content,
            "category": data.category,
            "is_public": data.is_public,
            "updated_at": datetime_to_timestamp(data.updated_at),
            "created_at": datetime_to_timestamp(data.created_at),
        }
