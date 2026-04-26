#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2025/10/25 0:21
@Author  : ccckz@protonmail.com
@File    : auth_schema.py
"""
from flask_wtf import FlaskForm
from marshmallow import Schema, fields
from wtforms import StringField
from wtforms.validators import DataRequired, Email, Length, regexp

from pkg.password import password_pattern


class PasswordLoginReq(FlaskForm):
    """账号密码登录请求结构"""

    email = StringField("email", validators=[
        DataRequired("登录邮箱不能为空"),
        Email("登录邮箱格式错误"),
        Length(min=5, max=254, message="登录邮箱长度应为 5-254 个字符"),
    ])
    password = StringField("password", validators=[
        DataRequired("账号密码不能为空"),
        regexp(regex=password_pattern, message="密码最少包含一个字母、一个数字，并且长度为 8-16"),
    ])


class SendRegisterCodeReq(FlaskForm):
    """发送注册验证码请求结构"""

    email = StringField("email", validators=[
        DataRequired("注册邮箱不能为空"),
        Email("注册邮箱格式错误"),
        Length(min=5, max=254, message="注册邮箱长度应为 5-254 个字符"),
    ])


class RegisterReq(FlaskForm):
    """邮箱验证码注册请求结构"""

    name = StringField("name", validators=[
        DataRequired("账号名称不能为空"),
        Length(min=2, max=30, message="账号名称长度应为 2-30 个字符"),
    ])
    email = StringField("email", validators=[
        DataRequired("注册邮箱不能为空"),
        Email("注册邮箱格式错误"),
        Length(min=5, max=254, message="注册邮箱长度应为 5-254 个字符"),
    ])
    code = StringField("code", validators=[
        DataRequired("邮箱验证码不能为空"),
        regexp(regex=r"^\d{6}$", message="邮箱验证码必须为 6 位数字"),
    ])
    password = StringField("password", validators=[
        DataRequired("账号密码不能为空"),
        regexp(regex=password_pattern, message="密码最少包含一个字母、一个数字，并且长度为 8-16"),
    ])


class PasswordLoginResp(Schema):
    """账号登录响应结构"""

    access_token = fields.String()
    expire_at = fields.Integer()
