#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bootstrap or update the initial admin account for Docker/Ubuntu deployments.
"""
import base64
import os
import secrets
import sys

import dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    dotenv.load_dotenv()

    admin_name = os.getenv("LLMOPS_ADMIN_NAME", "admin").strip() or "admin"
    admin_email = os.getenv("LLMOPS_ADMIN_EMAIL", "admin@llmops.local").strip().lower()
    admin_password = os.getenv("LLMOPS_ADMIN_PASSWORD", "").strip()
    admin_avatar = os.getenv("LLMOPS_ADMIN_AVATAR", "").strip()

    if not admin_password:
        print("LLMOPS_ADMIN_PASSWORD is empty, skip bootstrap admin.")
        return

    from app.http.app import app
    from internal.extension.database_extension import db
    from internal.model import Account
    from pkg.password.password import hash_password

    salt = secrets.token_bytes(16)
    password_hashed = hash_password(admin_password, salt)
    password_base64 = base64.b64encode(password_hashed).decode()
    salt_base64 = base64.b64encode(salt).decode()

    with app.app_context():
        account = db.session.query(Account).filter(Account.email == admin_email).one_or_none()
        if account is None:
            account = Account(
                name=admin_name,
                email=admin_email,
                avatar=admin_avatar,
                password=password_base64,
                password_salt=salt_base64,
                last_login_ip="127.0.0.1",
            )
            db.session.add(account)
            action = "created"
        else:
            account.name = admin_name
            account.avatar = admin_avatar
            account.password = password_base64
            account.password_salt = salt_base64
            action = "updated"

        db.session.commit()

    print(f"Bootstrap admin {action}: {admin_email}")


if __name__ == "__main__":
    main()
