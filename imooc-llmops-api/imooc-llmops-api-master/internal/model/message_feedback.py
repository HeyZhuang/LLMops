#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2026/3/18 10:00
@Author  : phase1
@File    : message_feedback.py
"""
from sqlalchemy import (
    Column,
    UUID,
    String,
    Text,
    DateTime,
    PrimaryKeyConstraint,
    text,
)

from internal.extension.database_extension import db


class MessageFeedback(db.Model):
    """消息反馈模型"""
    __tablename__ = "message_feedback"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_message_feedback_id"),
    )

    id = Column(UUID, nullable=False, server_default=text("uuid_generate_v4()"))
    app_id = Column(UUID, nullable=False)
    conversation_id = Column(UUID, nullable=False)
    message_id = Column(UUID, nullable=False)
    rating = Column(String(20), nullable=False, server_default=text("''::character varying"))  # like / dislike
    content = Column(Text, nullable=False, server_default=text("''::text"))  # 反馈内容
    created_by = Column(UUID, nullable=False)
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP(0)'),
        server_onupdate=text('CURRENT_TIMESTAMP(0)'),
    )
    created_at = Column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP(0)'))
