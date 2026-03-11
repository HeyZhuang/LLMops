#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2025/8/30 13:35
@Author  : ccckz@protonmail.com
@File    : embeddings_service.py
"""
import json
import os
from dataclasses import dataclass
from typing import List

import requests
import tiktoken
from injector import inject
from langchain.embeddings import CacheBackedEmbeddings
from langchain_community.storage import RedisStore
from langchain_core.embeddings import Embeddings
from redis import Redis


class HuggingFaceRouterEmbeddings(Embeddings):
    """通过 requests 直接调用 HuggingFace Router Inference API 的 Embeddings 实现，
    不依赖 huggingface_hub / langchain-huggingface 的版本。"""

    def __init__(self, model: str, api_token: str, api_url: str = "https://router.huggingface.co"):
        self.model = model
        self.api_url = api_url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        }

    def _post(self, payload: dict) -> list:
        """发送请求到 HuggingFace Inference API"""
        url = f"{self.api_url}/hf-inference/models/{self.model}"
        response = requests.post(url, headers=self.headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        texts = [text.replace("\n", " ") for text in texts]
        result = self._post({"inputs": texts})
        # 批量文本返回 list[list[float]]，直接返回
        return result

    def embed_query(self, text: str) -> List[float]:
        result = self._post({"inputs": text})
        # 单文本返回 list[float]（1024维扁平数组），直接返回
        return result


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

        self._embeddings = HuggingFaceRouterEmbeddings(
            model="intfloat/multilingual-e5-large",
            api_token=huggingface_api_token,
            api_url=os.getenv("HF_INFERENCE_ENDPOINT", "https://router.huggingface.co"),
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
