#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2025/8/30 13:35
@Author  : ccckz@protonmail.com
@File    : embeddings_service.py
"""
import os
from dataclasses import dataclass

import tiktoken
from injector import inject
from langchain.embeddings import CacheBackedEmbeddings
from langchain_community.storage import RedisStore
from langchain_core.embeddings import Embeddings
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from redis import Redis


@inject
@dataclass
class EmbeddingsService:
    """文本嵌入模型服务"""
    _store: RedisStore
    _embeddings: Embeddings
    _cache_backed_embeddings: CacheBackedEmbeddings

    def __init__(self, redis: Redis):
        """构造函数，初始化文本嵌入模型客户端、存储器、缓存客户端"""
        self._store = RedisStore(client=redis)
        # 使用 Hugging Face Inference API（通过 API 调用，不消耗本地算力）
        # 需要设置环境变量 HUGGINGFACEHUB_API_TOKEN 或通过参数传递
        huggingface_api_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")
        if not huggingface_api_token:
            raise ValueError(
                "HUGGINGFACEHUB_API_TOKEN environment variable is required. "
                "Please set it with your Hugging Face Access Token. "
                "Get your token from: https://huggingface.co/settings/tokens"
            )
        
        self._embeddings = HuggingFaceEndpointEmbeddings(
            model="intfloat/multilingual-e5-large",
            task="feature-extraction",
            huggingfacehub_api_token=huggingface_api_token,
        )
        # 使用本地 Hugging Face 模型（已弃用，会消耗本地算力）
        # self._embeddings = HuggingFaceEmbeddings(
        #     model_name="Alibaba-NLP/gte-multilingual-base",
        #     cache_folder=os.path.join(os.getcwd(), "internal", "core", "embeddings"),
        #     model_kwargs={
        #         "trust_remote_code": True,
        #     }
        # )
        # 使用 OpenAI 模型（已弃用，需要 OPENAI_API_KEY）
        # self._embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self._cache_backed_embeddings = CacheBackedEmbeddings.from_bytes_store(
            self._embeddings,
            self._store,
            namespace="embeddings",
        )

    @classmethod
    def calculate_token_count(cls, query: str) -> int:
        """计算传入文本的token数"""
        encoding = tiktoken.encoding_for_model("gpt-3.5")
        return len(encoding.encode(query))

    @property
    def store(self) -> RedisStore:
        return self._store

    @property
    def embeddings(self) -> Embeddings:
        return self._embeddings

    @property
    def cache_backed_embeddings(self) -> CacheBackedEmbeddings:
        return self._cache_backed_embeddings
