#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2025/10/25 0:16
@Author  : ccckz@protonmail.com
@File    : auth_handler.py
"""
from dataclasses import dataclass

from flask_login import login_required, logout_user
from injector import inject

from internal.schema.auth_schema import (
    PasswordLoginReq,
    PasswordLoginResp,
    RegisterReq,
    SendRegisterCodeReq,
)
from internal.service import AccountService
from pkg.response import success_json, success_message, validate_error_json


@inject
@dataclass
class AuthHandler:
    """LLMOps 平台认证处理器"""

    account_service: AccountService

    def send_register_code(self):
        """发送注册邮箱验证码"""
        req = SendRegisterCodeReq()
        if not req.validate():
            return validate_error_json(req.errors)

        self.account_service.send_register_code(req.email.data)
        return success_message("验证码已发送，请注意查收邮箱")

    def register(self):
        """邮箱验证码注册"""
        req = RegisterReq()
        if not req.validate():
            return validate_error_json(req.errors)

        credential = self.account_service.register_by_email(
            req.name.data,
            req.email.data,
            req.password.data,
            req.code.data,
        )
        resp = PasswordLoginResp()
        return success_json(resp.dump(credential))

    def password_login(self):
        """账号密码登录"""
        req = PasswordLoginReq()
        if not req.validate():
            return validate_error_json(req.errors)

        credential = self.account_service.password_login(req.email.data, req.password.data)
        resp = PasswordLoginResp()
        return success_json(resp.dump(credential))

    @login_required
    def logout(self):
        """退出登录"""
        logout_user()
        return success_message("退出登录成功")
