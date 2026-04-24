#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2025/12/01 16:18
@Author  : ccckz@protonmail.com
@File    : chat.py
"""
import os
from typing import Tuple

import tiktoken
from langchain_openai import ChatOpenAI

from internal.core.language_model.entities.model_entity import BaseLanguageModel


class Chat(ChatOpenAI, BaseLanguageModel):
    """DeepSeek聊天模型"""

    def __init__(self, **kwargs):
        api_key = os.environ.get("DEEPSEEK_API_KEY")
        base_url = os.environ.get("DEEPSEEK_API_BASE", "https://api.deepseek.com")

        if "top_p" in kwargs:
            try:
                top_p = float(kwargs["top_p"])
                if top_p <= 0.0:
                    kwargs["top_p"] = 0.01
                elif top_p > 1.0:
                    kwargs["top_p"] = 1.0
            except (ValueError, TypeError):
                pass

        if api_key:
            kwargs["api_key"] = api_key
        if base_url:
            kwargs["base_url"] = base_url

        super().__init__(**kwargs)

    def _get_encoding_model(self) -> Tuple[str, tiktoken.Encoding]:
        """DeepSeek 的模型名不在 tiktoken 内置映射时回退到 gpt-3.5-turbo。"""
        model_name = "gpt-3.5-turbo"
        return model_name, tiktoken.encoding_for_model(model_name)
