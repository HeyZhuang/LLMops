#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2026/3/18 10:00
@Author  : phase1
@File    : feedback_schema.py
"""
from flask_wtf import FlaskForm
from marshmallow import Schema, fields, pre_dump
from wtforms import StringField
from wtforms.validators import DataRequired, Optional, AnyOf

from internal.lib.helper import datetime_to_timestamp
from internal.model.message_feedback import MessageFeedback


class CreateFeedbackReq(FlaskForm):
    """创建/更新消息反馈请求"""
    rating = StringField("rating", validators=[
        DataRequired("评价类型不能为空"),
        AnyOf(["like", "dislike"], message="评价类型只能是like或dislike"),
    ])
    content = StringField("content", default="", validators=[Optional()])


class GetFeedbackResp(Schema):
    """获取消息反馈响应"""
    id = fields.UUID(dump_default="")
    message_id = fields.UUID(dump_default="")
    rating = fields.String(dump_default="")
    content = fields.String(dump_default="")
    created_at = fields.Integer(dump_default=0)

    @pre_dump
    def process_data(self, data: MessageFeedback, **kwargs):
        return {
            "id": data.id,
            "message_id": data.message_id,
            "rating": data.rating,
            "content": data.content,
            "created_at": datetime_to_timestamp(data.created_at),
        }
