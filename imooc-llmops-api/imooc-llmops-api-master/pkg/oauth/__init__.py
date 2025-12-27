#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2025/10/25 14:48
@Author  : ccckz@protonmail.com
@File    : __init__.py.py
"""
from .github_oauth import GithubOAuth
from .oauth import OAuthUserInfo, OAuth

__all__ = ["OAuthUserInfo", "OAuth", "GithubOAuth"]
