#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask import current_app


def get_shared_medical_account_id() -> str:
    return (current_app.config.get("SHARED_MEDICAL_ACCOUNT_ID") or "").strip()


def is_shared_medical_owner(account_id) -> bool:
    shared_account_id = get_shared_medical_account_id()
    return bool(shared_account_id) and str(account_id) == shared_account_id

