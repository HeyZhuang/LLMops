#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2025/8/12 10:43
@Author  : ccckz@protonmail.com
@File    : upload_file_entity.py
"""

ALLOWED_IMAGE_EXTENSION = ["jpg", "jpeg", "png", "webp", "gif", "svg"]
ALLOWED_DOCUMENT_IMAGE_EXTENSION = ["jpg", "jpeg", "png", "webp", "gif", "bmp", "tif", "tiff"]
ALLOWED_DOCUMENT_EXTENSION = [
    "txt",
    "markdown",
    "md",
    "pdf",
    "html",
    "htm",
    "xlsx",
    "xls",
    "doc",
    "docx",
    "csv",
    *ALLOWED_DOCUMENT_IMAGE_EXTENSION,
]
