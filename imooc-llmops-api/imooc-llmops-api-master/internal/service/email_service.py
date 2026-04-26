#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2026/4/26 14:30
@Author  : OpenAI
@File    : email_service.py
"""
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage

from flask import current_app

from internal.exception import FailException


@dataclass
class EmailService:
    """邮件服务"""

    def send_register_code(self, email: str, code: str, expire_seconds: int) -> None:
        """发送注册验证码邮件"""
        expire_minutes = max(1, expire_seconds // 60)
        subject = "LLMOps 注册验证码"
        content = (
            "您好，欢迎体验帅壮壮的超级agent网站\n\n"
            f"您的注册验证码为：{code}\n"
            f"验证码将在 {expire_minutes} 分钟后失效，请尽快完成注册。\n\n"
            "如果这不是您的操作，请忽略本邮件。"
        )
        self.send_email(email, subject, content)

    def send_email(self, to_email: str, subject: str, content: str) -> None:
        """发送邮件"""
        smtp_host = current_app.config.get("SMTP_HOST")
        smtp_port = int(current_app.config.get("SMTP_PORT", 587))
        smtp_user = current_app.config.get("SMTP_USER")
        smtp_password = current_app.config.get("SMTP_PASSWORD")
        smtp_use_tls = current_app.config.get("SMTP_USE_TLS", True)
        smtp_use_ssl = current_app.config.get("SMTP_USE_SSL", False)
        mail_from = current_app.config.get("MAIL_FROM") or smtp_user

        if not smtp_host or not mail_from:
            raise FailException("邮件服务未配置，请先完善 SMTP 参数")

        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = mail_from
        message["To"] = to_email
        message.set_content(content)

        try:
            if smtp_use_ssl:
                with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15) as server:
                    if smtp_user and smtp_password:
                        server.login(smtp_user, smtp_password)
                    server.send_message(message)
                return

            with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
                server.ehlo()
                if smtp_use_tls:
                    server.starttls()
                    server.ehlo()
                if smtp_user and smtp_password:
                    server.login(smtp_user, smtp_password)
                server.send_message(message)
        except Exception as exc:
            current_app.logger.exception("Failed to send email")
            raise FailException(f"邮件发送失败: {exc}") from exc
