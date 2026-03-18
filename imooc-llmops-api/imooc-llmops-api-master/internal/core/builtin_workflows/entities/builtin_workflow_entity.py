#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2026/3/18 10:00
@Author  : LLMOps
@File    : builtin_workflow_entity.py
"""
from typing import Any

from pydantic import BaseModel, Field


class BuiltinWorkflowEntity(BaseModel):
    """内置工作流模板实体类"""
    id: str = Field(default="")
    category: str = Field(default="")
    name: str = Field(default="")
    tool_call_name: str = Field(default="")
    icon: str = Field(default="")
    description: str = Field(default="")
    draft_graph: dict[str, Any] = Field(default_factory=lambda: {"nodes": [], "edges": []})
    author: str = Field(default="LLMOps-Platform")
    created_at: int = Field(default=0)
