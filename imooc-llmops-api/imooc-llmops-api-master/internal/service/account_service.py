#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2025/10/25 10:49
@Author  : ccckz@protonmail.com
@File    : account_service.py
"""
import base64
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from flask import current_app, request
from injector import inject
from redis import Redis

from internal.exception import FailException
from internal.model import Account, AccountOAuth
from pkg.password import compare_password, hash_password
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService
from .email_service import EmailService
from .jwt_service import JwtService


@inject
@dataclass
class AccountService(BaseService):
    """账号服务"""

    db: SQLAlchemy
    redis_client: Redis
    jwt_service: JwtService
    email_service: EmailService

    @staticmethod
    def normalize_email(email: str) -> str:
        """规范化邮箱"""
        return email.strip().lower()

    @staticmethod
    def generate_register_code() -> str:
        """生成 6 位数字验证码"""
        return "".join(secrets.choice("0123456789") for _ in range(6))

    @staticmethod
    def build_register_code_cache_key(email: str) -> str:
        """生成注册验证码缓存 key"""
        return f"auth:register:code:{email}"

    @staticmethod
    def build_register_cooldown_cache_key(email: str) -> str:
        """生成注册验证码冷却缓存 key"""
        return f"auth:register:cooldown:{email}"

    def get_account(self, account_id: UUID) -> Account:
        """根据 id 获取账号"""
        return self.get(Account, account_id)

    def get_account_oauth_by_provider_name_and_openid(
        self,
        provider_name: str,
        openid: str,
    ) -> AccountOAuth:
        """根据 provider 和 openid 获取第三方授权记录"""
        return self.db.session.query(AccountOAuth).filter(
            AccountOAuth.provider == provider_name,
            AccountOAuth.openid == openid,
        ).one_or_none()

    def get_account_by_email(self, email: str) -> Account:
        """根据邮箱查询账号"""
        return self.db.session.query(Account).filter(
            Account.email == self.normalize_email(email),
        ).one_or_none()

    def create_account(self, **kwargs) -> Account:
        """创建账号"""
        if "email" in kwargs:
            kwargs["email"] = self.normalize_email(kwargs["email"])
        return self.create(Account, **kwargs)

    def update_password(self, password: str, account: Account) -> Account:
        """更新账号密码"""
        salt = secrets.token_bytes(16)
        base64_salt = base64.b64encode(salt).decode()

        password_hashed = hash_password(password, salt)
        base64_password_hashed = base64.b64encode(password_hashed).decode()

        self.update_account(account, password=base64_password_hashed, password_salt=base64_salt)
        return account

    def update_account(self, account: Account, **kwargs) -> Account:
        """更新账号信息"""
        self.update(account, **kwargs)
        return account

    def issue_token(self, account: Account) -> dict[str, Any]:
        """签发登录凭证"""
        expire_at = int((datetime.now() + timedelta(days=30)).timestamp())
        payload = {
            "sub": str(account.id),
            "iss": "llmops",
            "exp": expire_at,
        }
        access_token = self.jwt_service.generate_token(payload)

        self.update(
            account,
            last_login_at=datetime.now(),
            last_login_ip=request.remote_addr,
        )

        return {
            "expire_at": expire_at,
            "access_token": access_token,
        }

    def send_register_code(self, email: str) -> None:
        """发送注册验证码"""
        email = self.normalize_email(email)
        if self.get_account_by_email(email):
            raise FailException("该邮箱已注册，请直接登录")

        cooldown_key = self.build_register_cooldown_cache_key(email)
        if self.redis_client.get(cooldown_key):
            raise FailException("验证码发送过于频繁，请稍后再试")

        code = self.generate_register_code()
        expire_seconds = int(current_app.config.get("REGISTER_CODE_EXPIRE_SECONDS", 300))
        resend_seconds = int(current_app.config.get("REGISTER_CODE_RESEND_SECONDS", 60))

        self.redis_client.setex(self.build_register_code_cache_key(email), expire_seconds, code)
        self.redis_client.setex(cooldown_key, resend_seconds, "1")
        self.email_service.send_register_code(email, code, expire_seconds)

    def verify_register_code(self, email: str, code: str) -> None:
        """校验注册验证码"""
        email = self.normalize_email(email)
        register_code = self.redis_client.get(self.build_register_code_cache_key(email))
        if register_code is None:
            raise FailException("验证码已失效，请重新获取")

        cached_code = register_code.decode("utf-8") if isinstance(register_code, bytes) else str(register_code)
        if cached_code != code:
            raise FailException("验证码错误，请重新输入")

    def register_by_email(self, name: str, email: str, password: str, code: str) -> dict[str, Any]:
        """邮箱验证码注册"""
        email = self.normalize_email(email)
        if self.get_account_by_email(email):
            raise FailException("该邮箱已注册，请直接登录")

        self.verify_register_code(email, code)

        account = self.create_account(
            name=name.strip(),
            email=email,
            avatar="",
        )
        self.update_password(password, account)
        self.redis_client.delete(self.build_register_code_cache_key(email))

        return self.issue_token(account)

    def password_login(self, email: str, password: str) -> dict[str, Any]:
        """根据邮箱密码登录账号"""
        email = self.normalize_email(email)
        account = self.get_account_by_email(email)
        if not account:
            raise FailException("账号不存在或者密码错误，请核实后重试")

        if not account.is_password_set or not compare_password(
            password,
            account.password,
            account.password_salt,
        ):
            raise FailException("账号不存在或者密码错误，请核实后重试")

        return self.issue_token(account)
