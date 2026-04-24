#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask_wtf import FlaskForm
from marshmallow import Schema, fields, pre_dump
from wtforms import StringField, BooleanField
from wtforms.validators import DataRequired, Length, Optional

from internal.lib.helper import datetime_to_timestamp
from internal.model.skill import Skill
from pkg.paginator import PaginatorReq


class CreateSkillReq(FlaskForm):
    name = StringField(
        "name",
        validators=[
            DataRequired("skill name is required"),
            Length(max=255, message="skill name must be <= 255 chars"),
        ],
    )
    description = StringField("description", default="", validators=[Optional()])
    content = StringField(
        "content",
        validators=[DataRequired("skill content is required")],
    )
    category = StringField("category", default="", validators=[Optional()])
    is_public = BooleanField("is_public", default=False)


class UpdateSkillReq(FlaskForm):
    name = StringField(
        "name",
        validators=[
            DataRequired("skill name is required"),
            Length(max=255, message="skill name must be <= 255 chars"),
        ],
    )
    description = StringField("description", default="", validators=[Optional()])
    content = StringField(
        "content",
        validators=[DataRequired("skill content is required")],
    )
    category = StringField("category", default="", validators=[Optional()])
    is_public = BooleanField("is_public", default=False)


class GetSkillsWithPageReq(PaginatorReq):
    search_word = StringField("search_word", default="", validators=[Optional()])
    category = StringField("category", default="", validators=[Optional()])


class GetSkillResp(Schema):
    id = fields.UUID(dump_default="")
    name = fields.String(dump_default="")
    description = fields.String(dump_default="")
    content = fields.String(dump_default="")
    category = fields.String(dump_default="")
    is_public = fields.Boolean(dump_default=False)
    updated_at = fields.Integer(dump_default=0)
    created_at = fields.Integer(dump_default=0)

    @pre_dump
    def process_data(self, data: Skill, **kwargs):
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
