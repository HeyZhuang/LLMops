#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Seed a BlueFocus-style enterprise agent demo for an existing account.

The seeded demo contains:
1. A published workflow tool
2. A custom API plugin provider with two demo tools
3. A RAG dataset with document, segments, and keyword table
4. A published app binding workflow + plugin + dataset
5. A debugger conversation with sample agent reasoning records
"""
from __future__ import annotations

import json
import os
import uuid
from copy import deepcopy
from pathlib import Path
from typing import Any

import dotenv
import jieba.analyse
import psycopg2
from psycopg2.extras import Json

from internal.entity.app_entity import DEFAULT_APP_CONFIG


ROOT = Path(__file__).resolve().parent
ENV_PATH = ROOT / ".env"
NAMESPACE = uuid.uuid5(uuid.NAMESPACE_DNS, "bluefocus-agent-demo")


def load_env() -> None:
    dotenv.load_dotenv(ENV_PATH)


def deterministic_uuid(key: str) -> str:
    return str(uuid.uuid5(NAMESPACE, key))


def build_openapi_schema() -> str:
    schema = {
        "openapi": "3.0.3",
        "info": {
            "title": "BlueFocus Demo Collaboration Plugin",
            "version": "1.0.0",
            "description": "Demo plugin endpoints for campaign collaboration showcase.",
        },
        "servers": [{"url": "https://jsonplaceholder.typicode.com"}],
        "paths": {
            "/posts/1": {
                "get": {
                    "operationId": "getDemoClientBrief",
                    "summary": "Get a demo client brief",
                    "responses": {
                        "200": {
                            "description": "Demo client brief payload",
                        }
                    },
                }
            },
            "/todos/1": {
                "get": {
                    "operationId": "getDemoTodoStatus",
                    "summary": "Get a demo execution todo status",
                    "responses": {
                        "200": {
                            "description": "Demo todo status payload",
                        }
                    },
                }
            },
        },
    }
    return json.dumps(schema, ensure_ascii=False)


def ref_input(node_id: str, var_name: str) -> dict[str, Any]:
    return {
        "type": "ref",
        "content": {
            "ref_node_id": node_id,
            "ref_var_name": var_name,
        },
    }


def literal_input() -> dict[str, Any]:
    return {
        "type": "literal",
        "content": "",
    }


def build_workflow_graph() -> dict[str, Any]:
    start_id = deterministic_uuid("workflow-start")
    plan_id = deterministic_uuid("workflow-plan")
    sync_id = deterministic_uuid("workflow-sync")
    end_id = deterministic_uuid("workflow-end")

    return {
        "nodes": [
            {
                "id": start_id,
                "node_type": "start",
                "title": "开始",
                "description": "接收品牌传播任务输入",
                "position": {"x": 0, "y": 160},
                "inputs": [
                    {
                        "name": "campaign_goal",
                        "description": "战役目标",
                        "required": True,
                        "type": "string",
                        "value": literal_input(),
                        "meta": {},
                    },
                    {
                        "name": "audience",
                        "description": "目标受众",
                        "required": True,
                        "type": "string",
                        "value": literal_input(),
                        "meta": {},
                    },
                    {
                        "name": "deadline",
                        "description": "交付期限",
                        "required": False,
                        "type": "string",
                        "value": literal_input(),
                        "meta": {},
                    },
                ],
            },
            {
                "id": plan_id,
                "node_type": "llm",
                "title": "生成战役拆解",
                "description": "拆解目标、节奏和内容动作",
                "position": {"x": 320, "y": 160},
                "inputs": [
                    {
                        "name": "campaign_goal",
                        "description": "战役目标",
                        "required": True,
                        "type": "string",
                        "value": ref_input(start_id, "campaign_goal"),
                        "meta": {},
                    },
                    {
                        "name": "audience",
                        "description": "目标受众",
                        "required": True,
                        "type": "string",
                        "value": ref_input(start_id, "audience"),
                        "meta": {},
                    },
                    {
                        "name": "deadline",
                        "description": "交付期限",
                        "required": False,
                        "type": "string",
                        "value": ref_input(start_id, "deadline"),
                        "meta": {},
                    },
                ],
                "prompt": (
                    "你是蓝色光标企业传播项目经理，请根据输入生成一份可执行战役计划，输出包含：\n"
                    "1. 战役目标拆解\n"
                    "2. 关键里程碑\n"
                    "3. 内容生产动作\n"
                    "4. 风险提醒\n\n"
                    "战役目标：{{campaign_goal}}\n"
                    "目标受众：{{audience}}\n"
                    "交付期限：{{deadline}}"
                ),
                "outputs": [
                    {
                        "name": "output",
                        "value": {"type": "generated", "content": ""},
                    }
                ],
                "model_config": deepcopy(DEFAULT_APP_CONFIG["model_config"]),
            },
            {
                "id": sync_id,
                "node_type": "llm",
                "title": "生成协同清单",
                "description": "把规划转成跨团队协同任务",
                "position": {"x": 640, "y": 160},
                "inputs": [
                    {
                        "name": "campaign_plan",
                        "description": "战役计划",
                        "required": True,
                        "type": "string",
                        "value": ref_input(plan_id, "output"),
                        "meta": {},
                    }
                ],
                "prompt": (
                    "请把下面的战役计划整理为项目协同清单，分别给出策略、创意、媒介、客户四类角色的动作项，"
                    "每项都要标注优先级和交付产物。\n\n{{campaign_plan}}"
                ),
                "outputs": [
                    {
                        "name": "output",
                        "value": {"type": "generated", "content": ""},
                    }
                ],
                "model_config": deepcopy(DEFAULT_APP_CONFIG["model_config"]),
            },
            {
                "id": end_id,
                "node_type": "end",
                "title": "结束",
                "description": "输出协同结果",
                "position": {"x": 960, "y": 160},
                "outputs": [
                    {
                        "name": "answer",
                        "description": "最终结果",
                        "required": True,
                        "type": "string",
                        "value": ref_input(sync_id, "output"),
                        "meta": {},
                    }
                ],
            },
        ],
        "edges": [
            {
                "id": deterministic_uuid("workflow-edge-1"),
                "source": start_id,
                "target": plan_id,
                "source_type": "start",
                "target_type": "llm",
            },
            {
                "id": deterministic_uuid("workflow-edge-2"),
                "source": plan_id,
                "target": sync_id,
                "source_type": "llm",
                "target_type": "llm",
            },
            {
                "id": deterministic_uuid("workflow-edge-3"),
                "source": sync_id,
                "target": end_id,
                "source_type": "llm",
                "target_type": "end",
            },
        ],
    }


def build_segments() -> list[dict[str, Any]]:
    rows = []
    segment_texts = [
        (
            "蓝色光标企业传播Agent的核心能力包括：对话中自动识别用户意图，"
            "必要时先进行知识库检索，再视情况调用插件获取外部数据，最后将复杂任务转交工作流拆解。"
        ),
        (
            "在RAG检索策略上，本演示应用优先使用全文检索模式，确保在本地开发环境中也能稳定命中文档片段，"
            "适合展示企业知识问答、SOP查询、项目背景回溯等典型场景。"
        ),
        (
            "在插件协同场景里，Agent可以调用外部API获取客户简报、执行状态、排期信息等实时数据，"
            "并将这些信息与内部知识库内容进行合并总结，形成可执行建议。"
        ),
        (
            "在工作流协同场景里，Agent会把复杂需求转为结构化流程，输出战役目标、里程碑、角色动作和风险提示，"
            "帮助团队从单轮问答升级为可落地的协作编排。"
        ),
    ]

    for index, content in enumerate(segment_texts, start=1):
        keywords = jieba.analyse.extract_tags(content, topK=10)
        rows.append(
            {
                "id": deterministic_uuid(f"segment-{index}"),
                "node_id": deterministic_uuid(f"segment-node-{index}"),
                "position": index,
                "content": content,
                "character_count": len(content),
                "token_count": max(1, len(content) // 2),
                "keywords": keywords,
                "hash": deterministic_uuid(f"segment-hash-{index}"),
            }
        )
    return rows


class Seeder:
    def __init__(self, conn: psycopg2.extensions.connection):
        self.conn = conn
        self.cur = conn.cursor()

    def fetchone(self, sql: str, params: tuple[Any, ...]) -> Any:
        self.cur.execute(sql, params)
        return self.cur.fetchone()

    def execute(self, sql: str, params: tuple[Any, ...]) -> None:
        self.cur.execute(sql, params)

    def get_account(self, email: str) -> tuple[str, str]:
        row = self.fetchone(
            "select id::text, email from account where email = %s limit 1",
            (email,),
        )
        if not row:
            raise SystemExit(f"Account not found for email: {email}")
        return row[0], row[1]

    def upsert_workflow(self, account_id: str) -> str:
        workflow_id = deterministic_uuid("workflow")
        graph = build_workflow_graph()
        row = self.fetchone(
            "select id::text from workflow where id = %s::uuid limit 1",
            (workflow_id,),
        )
        params = (
            account_id,
            "BlueFocus·品牌战役协同工作流",
            "bluefocus_campaign_sync_workflow",
            "https://placehold.co/600x600/0f766e/ffffff?text=BlueFocus+WF",
            "将传播需求拆解为目标、里程碑、团队动作与风险提示的演示工作流。",
            Json(graph),
            Json(graph),
            workflow_id,
        )
        if row:
            self.execute(
                """
                update workflow
                   set account_id = %s::uuid,
                       name = %s,
                       tool_call_name = %s,
                       icon = %s,
                       description = %s,
                       graph = %s,
                       draft_graph = %s,
                       is_debug_passed = true,
                       status = 'published',
                       published_at = now(),
                       updated_at = now()
                 where id = %s::uuid
                """,
                params,
            )
        else:
            self.execute(
                """
                insert into workflow (
                    account_id, name, tool_call_name, icon, description, graph, draft_graph,
                    is_debug_passed, status, published_at, updated_at, created_at, id
                ) values (
                    %s::uuid, %s, %s, %s, %s, %s, %s,
                    true, 'published', now(), now(), now(), %s::uuid
                )
                """,
                params,
            )
        return workflow_id

    def upsert_plugin(self, account_id: str) -> tuple[str, dict[str, str]]:
        provider_id = deterministic_uuid("plugin-provider")
        schema = build_openapi_schema()
        provider_row = self.fetchone(
            "select id::text from api_tool_provider where id = %s::uuid limit 1",
            (provider_id,),
        )
        provider_params = (
            account_id,
            "BlueFocus·外部协同演示插件",
            "https://placehold.co/600x600/1d4ed8/ffffff?text=BlueFocus+Plugin",
            "演示 Agent 在会话中调用外部插件获取简报和执行状态。",
            schema,
            Json([]),
            provider_id,
        )
        if provider_row:
            self.execute(
                """
                update api_tool_provider
                   set account_id = %s::uuid,
                       name = %s,
                       icon = %s,
                       description = %s,
                       openapi_schema = %s,
                       headers = %s,
                       updated_at = now()
                 where id = %s::uuid
                """,
                provider_params,
            )
            self.execute(
                "delete from api_tool where provider_id = %s::uuid",
                (provider_id,),
            )
        else:
            self.execute(
                """
                insert into api_tool_provider (
                    account_id, name, icon, description, openapi_schema, headers,
                    updated_at, created_at, id
                ) values (
                    %s::uuid, %s, %s, %s, %s, %s,
                    now(), now(), %s::uuid
                )
                """,
                provider_params,
            )

        tool_rows = [
            {
                "id": deterministic_uuid("plugin-tool-brief"),
                "name": "getDemoClientBrief",
                "description": "获取演示客户简报数据",
                "url": "https://jsonplaceholder.typicode.com/posts/1",
                "method": "GET",
                "parameters": [],
            },
            {
                "id": deterministic_uuid("plugin-tool-status"),
                "name": "getDemoTodoStatus",
                "description": "获取演示执行状态数据",
                "url": "https://jsonplaceholder.typicode.com/todos/1",
                "method": "GET",
                "parameters": [],
            },
        ]

        tool_ids: dict[str, str] = {}
        for item in tool_rows:
            self.execute(
                """
                insert into api_tool (
                    id, account_id, provider_id, name, description, url, method, parameters,
                    updated_at, created_at
                ) values (
                    %s::uuid, %s::uuid, %s::uuid, %s, %s, %s, %s, %s,
                    now(), now()
                )
                """,
                (
                    item["id"],
                    account_id,
                    provider_id,
                    item["name"],
                    item["description"],
                    item["url"],
                    item["method"],
                    Json(item["parameters"]),
                ),
            )
            tool_ids[item["name"]] = item["id"]

        return provider_id, tool_ids

    def upsert_dataset(self, account_id: str) -> str:
        dataset_id = deterministic_uuid("dataset")
        process_rule_id = deterministic_uuid("process-rule")
        upload_file_id = deterministic_uuid("upload-file")
        document_id = deterministic_uuid("document")
        segment_rows = build_segments()

        if self.fetchone("select id::text from dataset where id = %s::uuid", (dataset_id,)):
            self.execute(
                """
                update dataset
                   set account_id = %s::uuid,
                       name = %s,
                       icon = %s,
                       description = %s,
                       updated_at = now()
                 where id = %s::uuid
                """,
                (
                    account_id,
                    "BlueFocus 品牌传播知识库",
                    "https://placehold.co/600x600/f59e0b/ffffff?text=BlueFocus+RAG",
                    "用于演示企业 Agent 在对话中结合 RAG、插件和工作流完成协同决策。",
                    dataset_id,
                ),
            )
        else:
            self.execute(
                """
                insert into dataset (
                    id, account_id, name, icon, description, updated_at, created_at
                ) values (
                    %s::uuid, %s::uuid, %s, %s, %s, now(), now()
                )
                """,
                (
                    dataset_id,
                    account_id,
                    "BlueFocus 品牌传播知识库",
                    "https://placehold.co/600x600/f59e0b/ffffff?text=BlueFocus+RAG",
                    "用于演示企业 Agent 在对话中结合 RAG、插件和工作流完成协同决策。",
                ),
            )

        if self.fetchone("select id::text from process_rule where id = %s::uuid", (process_rule_id,)):
            self.execute(
                """
                update process_rule
                   set account_id = %s::uuid,
                       dataset_id = %s::uuid,
                       mode = 'automic',
                       rule = %s,
                       updated_at = now()
                 where id = %s::uuid
                """,
                (account_id, dataset_id, Json({"mode": "demo"}), process_rule_id),
            )
        else:
            self.execute(
                """
                insert into process_rule (
                    id, account_id, dataset_id, mode, rule, updated_at, created_at
                ) values (
                    %s::uuid, %s::uuid, %s::uuid, 'automic', %s, now(), now()
                )
                """,
                (process_rule_id, account_id, dataset_id, Json({"mode": "demo"})),
            )

        if self.fetchone("select id::text from upload_file where id = %s::uuid", (upload_file_id,)):
            self.execute(
                """
                update upload_file
                   set account_id = %s::uuid,
                       name = %s,
                       key = %s,
                       size = %s,
                       extension = %s,
                       mime_type = %s,
                       hash = %s,
                       updated_at = now()
                 where id = %s::uuid
                """,
                (
                    account_id,
                    "bluefocus_agent_demo.md",
                    "demo/bluefocus_agent_demo.md",
                    2048,
                    "md",
                    "text/markdown",
                    deterministic_uuid("upload-file-hash"),
                    upload_file_id,
                ),
            )
        else:
            self.execute(
                """
                insert into upload_file (
                    id, account_id, name, key, size, extension, mime_type, hash, updated_at, created_at
                ) values (
                    %s::uuid, %s::uuid, %s, %s, %s, %s, %s, %s, now(), now()
                )
                """,
                (
                    upload_file_id,
                    account_id,
                    "bluefocus_agent_demo.md",
                    "demo/bluefocus_agent_demo.md",
                    2048,
                    "md",
                    "text/markdown",
                    deterministic_uuid("upload-file-hash"),
                ),
            )

        if self.fetchone("select id::text from document where id = %s::uuid", (document_id,)):
            self.execute(
                """
                update document
                   set account_id = %s::uuid,
                       dataset_id = %s::uuid,
                       upload_file_id = %s::uuid,
                       process_rule_id = %s::uuid,
                       batch = %s,
                       name = %s,
                       position = 1,
                       character_count = %s,
                       token_count = %s,
                       enabled = true,
                       status = 'completed',
                       parsing_completed_at = now(),
                       splitting_completed_at = now(),
                       indexing_completed_at = now(),
                       completed_at = now(),
                       updated_at = now()
                 where id = %s::uuid
                """,
                (
                    account_id,
                    dataset_id,
                    upload_file_id,
                    process_rule_id,
                    "bluefocus-demo-batch",
                    "BlueFocus Agent 演示知识文档",
                    sum(item["character_count"] for item in segment_rows),
                    sum(item["token_count"] for item in segment_rows),
                    document_id,
                ),
            )
        else:
            self.execute(
                """
                insert into document (
                    id, account_id, dataset_id, upload_file_id, process_rule_id, batch, name, position,
                    character_count, token_count, parsing_completed_at, splitting_completed_at,
                    indexing_completed_at, completed_at, enabled, status, updated_at, created_at
                ) values (
                    %s::uuid, %s::uuid, %s::uuid, %s::uuid, %s::uuid, %s, %s, 1,
                    %s, %s, now(), now(), now(), now(), true, 'completed', now(), now()
                )
                """,
                (
                    document_id,
                    account_id,
                    dataset_id,
                    upload_file_id,
                    process_rule_id,
                    "bluefocus-demo-batch",
                    "BlueFocus Agent 演示知识文档",
                    sum(item["character_count"] for item in segment_rows),
                    sum(item["token_count"] for item in segment_rows),
                ),
            )

        self.execute("delete from segment where document_id = %s::uuid", (document_id,))
        for item in segment_rows:
            self.execute(
                """
                insert into segment (
                    id, account_id, dataset_id, document_id, node_id, position, content,
                    character_count, token_count, keywords, hash, hit_count, enabled,
                    processing_started_at, indexing_completed_at, completed_at, status,
                    updated_at, created_at
                ) values (
                    %s::uuid, %s::uuid, %s::uuid, %s::uuid, %s::uuid, %s, %s,
                    %s, %s, %s, %s, 0, true,
                    now(), now(), now(), 'completed',
                    now(), now()
                )
                """,
                (
                    item["id"],
                    account_id,
                    dataset_id,
                    document_id,
                    item["node_id"],
                    item["position"],
                    item["content"],
                    item["character_count"],
                    item["token_count"],
                    Json(item["keywords"]),
                    item["hash"],
                ),
            )

        keyword_table: dict[str, list[str]] = {}
        for item in segment_rows:
            for keyword in item["keywords"]:
                keyword_table.setdefault(keyword, []).append(item["id"])

        if self.fetchone("select id::text from keyword_table where dataset_id = %s::uuid", (dataset_id,)):
            self.execute(
                """
                update keyword_table
                   set keyword_table = %s,
                       updated_at = now()
                 where dataset_id = %s::uuid
                """,
                (Json(keyword_table), dataset_id),
            )
        else:
            self.execute(
                """
                insert into keyword_table (id, dataset_id, keyword_table, updated_at, created_at)
                values (%s::uuid, %s::uuid, %s, now(), now())
                """,
                (deterministic_uuid("keyword-table"), dataset_id, Json(keyword_table)),
            )

        return dataset_id

    def upsert_app(
        self,
        account_id: str,
        workflow_id: str,
        provider_id: str,
        dataset_id: str,
    ) -> str:
        app_id = deterministic_uuid("app")
        app_config_id = deterministic_uuid("app-config")
        draft_config_id = deterministic_uuid("app-config-draft")
        published_config_id = deterministic_uuid("app-config-published")
        debug_conversation_id = deterministic_uuid("debug-conversation")

        tools_config = [
            {
                "type": "api_tool",
                "provider_id": provider_id,
                "tool_id": "getDemoClientBrief",
                "params": {},
            },
            {
                "type": "api_tool",
                "provider_id": provider_id,
                "tool_id": "getDemoTodoStatus",
                "params": {},
            },
        ]

        payload = deepcopy(DEFAULT_APP_CONFIG)
        payload.update(
            {
                "dialog_round": 6,
                "preset_prompt": (
                    "你是 BlueFocus 企业传播 Agent。请优先判断用户问题是否需要知识库检索、插件调用或工作流拆解：\n"
                    "1. 涉及平台能力、SOP、项目背景时，先检索知识库；\n"
                    "2. 涉及外部简报、执行状态时，调用插件；\n"
                    "3. 涉及复杂项目推进时，调用工作流生成协同方案；\n"
                    "4. 回答时要把你实际采用的协同路径总结清楚。"
                ),
                "tools": tools_config,
                "workflows": [workflow_id],
                "datasets": [dataset_id],
                "retrieval_config": {
                    "retrieval_strategy": "full_text",
                    "k": 5,
                    "score": 0,
                },
                "long_term_memory": {"enable": True},
                "opening_statement": (
                    "这里是 BlueFocus 企业传播 Agent 演示台。我可以在一次对话里结合知识库、"
                    "外部插件和工作流，把普通问答升级为真正的项目协同。"
                ),
                "opening_questions": [
                    "请基于平台能力帮我策划一场 AI 品牌传播战役。",
                    "你能同时调用知识库、插件和工作流做一次完整协同演示吗？",
                    "请根据企业传播场景给我拆一版跨团队执行方案。",
                ],
            }
        )

        if self.fetchone("select id::text from app where id = %s::uuid", (app_id,)):
            self.execute(
                """
                update app
                   set account_id = %s::uuid,
                       app_config_id = %s::uuid,
                       draft_app_config_id = %s::uuid,
                       debug_conversation_id = %s::uuid,
                       name = %s,
                       icons = %s,
                       description = %s,
                       status = 'published',
                       updated_at = now()
                 where id = %s::uuid
                """,
                (
                    account_id,
                    app_config_id,
                    draft_config_id,
                    debug_conversation_id,
                    "BlueFocus·企业传播Agent演示台",
                    "https://placehold.co/600x600/111827/ffffff?text=BlueFocus+Agent",
                    "一个可在单次对话中同时调用 Workflow、RAG、插件的企业级 Agent 演示应用。",
                    app_id,
                ),
            )
        else:
            self.execute(
                """
                insert into app (
                    id, account_id, app_config_id, draft_app_config_id, debug_conversation_id,
                    name, icons, description, token, status, updated_at, created_at
                ) values (
                    %s::uuid, %s::uuid, %s::uuid, %s::uuid, %s::uuid,
                    %s, %s, %s, '', 'published', now(), now()
                )
                """,
                (
                    app_id,
                    account_id,
                    app_config_id,
                    draft_config_id,
                    debug_conversation_id,
                    "BlueFocus·企业传播Agent演示台",
                    "https://placehold.co/600x600/111827/ffffff?text=BlueFocus+Agent",
                    "一个可在单次对话中同时调用 Workflow、RAG、插件的企业级 Agent 演示应用。",
                ),
            )

        self.execute("delete from app_dataset_join where app_id = %s::uuid", (app_id,))
        self.execute(
            """
            insert into app_dataset_join (id, app_id, dataset_id, updated_at, created_at)
            values (%s::uuid, %s::uuid, %s::uuid, now(), now())
            """,
            (deterministic_uuid("app-dataset-join"), app_id, dataset_id),
        )

        self._upsert_app_config_row(app_config_id, app_id, payload)
        self._upsert_app_config_version_row(draft_config_id, app_id, 0, "draft", payload)
        self._upsert_app_config_version_row(published_config_id, app_id, 1, "published", payload)

        return app_id

    def _upsert_app_config_row(self, table_id: str, app_id: str, payload: dict[str, Any]) -> None:
        if self.fetchone("select id::text from app_config where id = %s::uuid", (table_id,)):
            self.execute(
                """
                update app_config
                   set app_id = %s::uuid,
                       model_config = %s,
                       dialog_round = %s,
                       preset_prompt = %s,
                       skills = %s,
                       tools = %s,
                       workflows = %s,
                       retrieval_config = %s,
                       long_term_memory = %s,
                       opening_statement = %s,
                       opening_questions = %s,
                       speech_to_text = %s,
                       text_to_speech = %s,
                       suggested_after_answer = %s,
                       review_config = %s,
                       multi_agent_config = %s,
                       updated_at = now()
                 where id = %s::uuid
                """,
                (
                    app_id,
                    Json(payload["model_config"]),
                    payload["dialog_round"],
                    payload["preset_prompt"],
                    Json(payload["skills"]),
                    Json(payload["tools"]),
                    Json(payload["workflows"]),
                    Json(payload["retrieval_config"]),
                    Json(payload["long_term_memory"]),
                    payload["opening_statement"],
                    Json(payload["opening_questions"]),
                    Json(payload["speech_to_text"]),
                    Json(payload["text_to_speech"]),
                    Json(payload["suggested_after_answer"]),
                    Json(payload["review_config"]),
                    Json(payload["multi_agent_config"]),
                    table_id,
                ),
            )
        else:
            self.execute(
                """
                insert into app_config (
                    id, app_id, model_config, dialog_round, preset_prompt, skills, tools, workflows,
                    retrieval_config, long_term_memory, opening_statement, opening_questions,
                    speech_to_text, text_to_speech, suggested_after_answer, review_config,
                    multi_agent_config, updated_at, created_at
                ) values (
                    %s::uuid, %s::uuid, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, now(), now()
                )
                """,
                (
                    table_id,
                    app_id,
                    Json(payload["model_config"]),
                    payload["dialog_round"],
                    payload["preset_prompt"],
                    Json(payload["skills"]),
                    Json(payload["tools"]),
                    Json(payload["workflows"]),
                    Json(payload["retrieval_config"]),
                    Json(payload["long_term_memory"]),
                    payload["opening_statement"],
                    Json(payload["opening_questions"]),
                    Json(payload["speech_to_text"]),
                    Json(payload["text_to_speech"]),
                    Json(payload["suggested_after_answer"]),
                    Json(payload["review_config"]),
                    Json(payload["multi_agent_config"]),
                ),
            )

    def _upsert_app_config_version_row(
        self,
        row_id: str,
        app_id: str,
        version: int,
        config_type: str,
        payload: dict[str, Any],
    ) -> None:
        if self.fetchone("select id::text from app_config_version where id = %s::uuid", (row_id,)):
            self.execute(
                """
                update app_config_version
                   set app_id = %s::uuid,
                       model_config = %s,
                       dialog_round = %s,
                       preset_prompt = %s,
                       skills = %s,
                       tools = %s,
                       workflows = %s,
                       datasets = %s,
                       retrieval_config = %s,
                       long_term_memory = %s,
                       opening_statement = %s,
                       opening_questions = %s,
                       speech_to_text = %s,
                       text_to_speech = %s,
                       suggested_after_answer = %s,
                       review_config = %s,
                       multi_agent_config = %s,
                       version = %s,
                       config_type = %s,
                       updated_at = now()
                 where id = %s::uuid
                """,
                (
                    app_id,
                    Json(payload["model_config"]),
                    payload["dialog_round"],
                    payload["preset_prompt"],
                    Json(payload["skills"]),
                    Json(payload["tools"]),
                    Json(payload["workflows"]),
                    Json(payload["datasets"]),
                    Json(payload["retrieval_config"]),
                    Json(payload["long_term_memory"]),
                    payload["opening_statement"],
                    Json(payload["opening_questions"]),
                    Json(payload["speech_to_text"]),
                    Json(payload["text_to_speech"]),
                    Json(payload["suggested_after_answer"]),
                    Json(payload["review_config"]),
                    Json(payload["multi_agent_config"]),
                    version,
                    config_type,
                    row_id,
                ),
            )
        else:
            self.execute(
                """
                insert into app_config_version (
                    id, app_id, model_config, dialog_round, preset_prompt, skills, tools, workflows,
                    datasets, retrieval_config, long_term_memory, opening_statement, opening_questions,
                    speech_to_text, text_to_speech, suggested_after_answer, review_config,
                    multi_agent_config, version, config_type, updated_at, created_at
                ) values (
                    %s::uuid, %s::uuid, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, now(), now()
                )
                """,
                (
                    row_id,
                    app_id,
                    Json(payload["model_config"]),
                    payload["dialog_round"],
                    payload["preset_prompt"],
                    Json(payload["skills"]),
                    Json(payload["tools"]),
                    Json(payload["workflows"]),
                    Json(payload["datasets"]),
                    Json(payload["retrieval_config"]),
                    Json(payload["long_term_memory"]),
                    payload["opening_statement"],
                    Json(payload["opening_questions"]),
                    Json(payload["speech_to_text"]),
                    Json(payload["text_to_speech"]),
                    Json(payload["suggested_after_answer"]),
                    Json(payload["review_config"]),
                    Json(payload["multi_agent_config"]),
                    version,
                    config_type,
                ),
            )

    def upsert_debug_conversation(self, account_id: str, app_id: str) -> str:
        conversation_id = deterministic_uuid("debug-conversation")
        message_id = deterministic_uuid("debug-message")

        if self.fetchone("select id::text from conversation where id = %s::uuid", (conversation_id,)):
            self.execute(
                """
                update conversation
                   set app_id = %s::uuid,
                       name = %s,
                       summary = %s,
                       is_pinned = true,
                       is_deleted = false,
                       invoke_from = 'debugger',
                       created_by = %s::uuid,
                       updated_at = now()
                 where id = %s::uuid
                """,
                (
                    app_id,
                    "BlueFocus 企业传播 Agent 综合协同演示",
                    "演示一次会话中同时调用 RAG、插件和工作流的效果。",
                    account_id,
                    conversation_id,
                ),
            )
        else:
            self.execute(
                """
                insert into conversation (
                    id, app_id, name, summary, is_pinned, is_deleted, invoke_from,
                    created_by, updated_at, created_at
                ) values (
                    %s::uuid, %s::uuid, %s, %s, true, false, 'debugger',
                    %s::uuid, now(), now()
                )
                """,
                (
                    conversation_id,
                    app_id,
                    "BlueFocus 企业传播 Agent 综合协同演示",
                    "演示一次会话中同时调用 RAG、插件和工作流的效果。",
                    account_id,
                ),
            )

        answer_text = (
            "我已经完成一次完整协同演示：先从知识库提取了平台能力说明，确认该应用支持对话中联动 RAG、"
            "插件与工作流；随后调用了外部协同演示插件获取客户简报与执行状态；最后触发品牌战役协同工作流，"
            "把需求拆解成目标、里程碑、角色动作和风险提示。这样的平台不再只是聊天机器人，而是真正能组织知识、"
            "调度工具、编排任务的企业 Agent 工作台。"
        )
        query_text = "请你演示一下这个应用如何同时调用 workflow、RAG 和插件来完成一次企业传播任务协同。"

        if self.fetchone("select id::text from message where id = %s::uuid", (message_id,)):
            self.execute(
                """
                update message
                   set app_id = %s::uuid,
                       conversation_id = %s::uuid,
                       invoke_from = 'debugger',
                       created_by = %s::uuid,
                       query = %s,
                       message = %s,
                       answer = %s,
                       message_token_count = 120,
                       answer_token_count = 220,
                       latency = 2.35,
                       status = 'normal',
                       total_token_count = 340,
                       updated_at = now()
                 where id = %s::uuid
                """,
                (
                    app_id,
                    conversation_id,
                    account_id,
                    query_text,
                    Json(
                        [
                            {"role": "user", "content": query_text},
                            {"role": "assistant", "content": answer_text},
                        ]
                    ),
                    answer_text,
                    message_id,
                ),
            )
        else:
            self.execute(
                """
                insert into message (
                    id, app_id, conversation_id, invoke_from, created_by, query, message,
                    message_token_count, message_unit_price, message_price_unit,
                    answer, answer_token_count, answer_unit_price, answer_price_unit,
                    latency, is_deleted, status, error, total_token_count, total_price,
                    updated_at, created_at
                ) values (
                    %s::uuid, %s::uuid, %s::uuid, 'debugger', %s::uuid, %s, %s,
                    120, 0.0, 0.0, %s, 220, 0.0, 0.0,
                    2.35, false, 'normal', '', 340, 0.0,
                    now(), now()
                )
                """,
                (
                    message_id,
                    app_id,
                    conversation_id,
                    account_id,
                    query_text,
                    Json(
                        [
                            {"role": "user", "content": query_text},
                            {"role": "assistant", "content": answer_text},
                        ]
                    ),
                    answer_text,
                ),
            )

        self.execute("delete from message_agent_thought where message_id = %s::uuid", (message_id,))
        thought_rows = [
            {
                "id": deterministic_uuid("thought-1"),
                "position": 1,
                "event": "agent_thought",
                "thought": "用户想验证这个平台能否在一次对话里串起 RAG、插件和工作流，我需要先确认平台能力，再组织一次完整协同路径。",
                "observation": "",
                "tool": "",
                "tool_input": {},
                "answer": "先检查平台能力并设计协同路径。",
            },
            {
                "id": deterministic_uuid("thought-2"),
                "position": 2,
                "event": "dataset_retrieval",
                "thought": "",
                "observation": "知识库命中内容：该应用支持先检索知识库、再调用插件、最后触发工作流进行任务拆解。",
                "tool": "dataset_retrieval",
                "tool_input": {"query": "平台如何同时调用 workflow rag 插件"},
                "answer": "",
            },
            {
                "id": deterministic_uuid("thought-3"),
                "position": 3,
                "event": "agent_action",
                "thought": "需要外部演示数据增强说明，调用插件获取客户简报。",
                "observation": "插件返回演示简报数据，说明外部协同接口可在对话中被调用并参与总结。",
                "tool": "getDemoClientBrief",
                "tool_input": {},
                "answer": "",
            },
            {
                "id": deterministic_uuid("thought-4"),
                "position": 4,
                "event": "agent_action",
                "thought": "为了把复杂需求变成执行方案，调用品牌战役协同工作流。",
                "observation": "工作流生成了目标拆解、里程碑、角色动作和风险提示。",
                "tool": "wf_bluefocus_campaign_sync_workflow",
                "tool_input": {
                    "campaign_goal": "展示企业级 Agent 平台能力",
                    "audience": "潜在客户与内部业务团队",
                    "deadline": "本周内",
                },
                "answer": "",
            },
            {
                "id": deterministic_uuid("thought-5"),
                "position": 5,
                "event": "agent_message",
                "thought": "",
                "observation": "",
                "tool": "",
                "tool_input": {},
                "answer": answer_text,
            },
        ]

        for item in thought_rows:
            self.execute(
                """
                insert into message_agent_thought (
                    id, app_id, conversation_id, message_id, invoke_from, created_by, position,
                    event, thought, observation, tool, tool_input, message, message_token_count,
                    message_unit_price, message_price_unit, answer, answer_token_count,
                    answer_unit_price, answer_price_unit, total_token_count, total_price,
                    latency, updated_at, created_at
                ) values (
                    %s::uuid, %s::uuid, %s::uuid, %s::uuid, 'debugger', %s::uuid, %s,
                    %s, %s, %s, %s, %s, %s, 0,
                    0.0, 0.0, %s, 0,
                    0.0, 0.0, 0, 0.0,
                    0.4, now(), now()
                )
                """,
                (
                    item["id"],
                    app_id,
                    conversation_id,
                    message_id,
                    account_id,
                    item["position"],
                    item["event"],
                    item["thought"],
                    item["observation"],
                    item["tool"],
                    Json(item["tool_input"]),
                    Json([]),
                    item["answer"],
                ),
            )

        return conversation_id


def main() -> None:
    load_env()
    dsn = os.environ["SQLALCHEMY_DATABASE_URI"]
    target_email = "chen@bluefocus.cn"

    conn = psycopg2.connect(dsn)
    conn.autocommit = False
    try:
        seeder = Seeder(conn)
        account_id, _ = seeder.get_account(target_email)
        workflow_id = seeder.upsert_workflow(account_id)
        provider_id, _ = seeder.upsert_plugin(account_id)
        dataset_id = seeder.upsert_dataset(account_id)
        app_id = seeder.upsert_app(account_id, workflow_id, provider_id, dataset_id)
        conversation_id = seeder.upsert_debug_conversation(account_id, app_id)
        conn.commit()

        print("BlueFocus demo seed completed")
        print(f"email={target_email}")
        print(f"app_id={app_id}")
        print(f"workflow_id={workflow_id}")
        print(f"provider_id={provider_id}")
        print(f"dataset_id={dataset_id}")
        print(f"conversation_id={conversation_id}")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
