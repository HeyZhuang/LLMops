#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2026/4/24 12:10
@Author  : codex
@File    : skill.py
"""
from sqlalchemy import (
    Column,
    UUID,
    String,
    Text,
    DateTime,
    Boolean,
    PrimaryKeyConstraint,
    text,
)

from internal.extension.database_extension import db


class Skill(db.Model):
    """技能库模型"""
    __tablename__ = "skill"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_skill_id"),
    )

    id = Column(UUID, nullable=False, server_default=text("uuid_generate_v4()"))
    account_id = Column(UUID, nullable=False)
    name = Column(String(255), nullable=False, server_default=text("''::character varying"))
    description = Column(Text, nullable=False, server_default=text("''::text"))
    content = Column(Text, nullable=False, server_default=text("''::text"))
    category = Column(String(100), nullable=False, server_default=text("''::character varying"))
    is_public = Column(Boolean, nullable=False, server_default=text("false"))
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(0)"),
        server_onupdate=text("CURRENT_TIMESTAMP(0)"),
    )
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP(0)"))
