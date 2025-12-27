#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2025/11/25 22:39
@Author  : ccckz@protonmail.com
@File    : start_entity.py
"""
from langchain_core.pydantic_v1 import Field

from internal.core.workflow.entities.node_entity import BaseNodeData
from internal.core.workflow.entities.variable_entity import VariableEntity


class StartNodeData(BaseNodeData):
    """开始节点数据"""
    inputs: list[VariableEntity] = Field(default_factory=list)  # 开始节点的输入变量信息
