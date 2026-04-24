#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2026/3/18 10:00
@Author  : phase1
@File    : app_export_service.py
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from injector import inject

from internal.entity.app_entity import AppStatus, AppConfigType, DEFAULT_APP_CONFIG
from internal.exception import NotFoundException, ForbiddenException, ValidateErrorException
from internal.model import App, Account, AppConfigVersion, Dataset, ApiTool, Skill
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService


@inject
@dataclass
class AppExportService(BaseService):
    """应用导入导出服务"""
    db: SQLAlchemy

    def export_app(self, app_id: UUID, account: Account) -> dict[str, Any]:
        """导出应用为JSON"""
        # 1.验证应用存在和权限
        app = self.get(App, app_id)
        if not app:
            raise NotFoundException("该应用不存在")
        if app.account_id != account.id:
            raise ForbiddenException("当前账号无权限访问该应用")

        # 2.获取草稿配置
        draft_config = app.draft_app_config

        # 3.构建导出JSON
        export_data = {
            "version": "1.0",
            "type": "app",
            "name": app.name,
            "description": app.description,
            "icon": app.icons,
            "config": {
                "model_config": draft_config.model_config,
                "preset_prompt": draft_config.preset_prompt,
                "skills": draft_config.skills,
                "dialog_round": draft_config.dialog_round,
                "tools": draft_config.tools,
                "workflows": draft_config.workflows,
                "datasets": draft_config.datasets,
                "retrieval_config": draft_config.retrieval_config,
                "long_term_memory": draft_config.long_term_memory,
                "opening_statement": draft_config.opening_statement,
                "opening_questions": draft_config.opening_questions,
                "speech_to_text": draft_config.speech_to_text,
                "text_to_speech": draft_config.text_to_speech,
                "suggested_after_answer": draft_config.suggested_after_answer,
                "review_config": draft_config.review_config,
                "multi_agent_config": draft_config.multi_agent_config,
            },
            "exported_at": datetime.now().isoformat(),
        }

        return export_data

    def import_app(self, import_data: dict[str, Any], account: Account) -> dict[str, Any]:
        """从JSON导入应用"""
        # 1.验证导入数据基本结构
        if not import_data.get("version") or not import_data.get("type") == "app":
            raise ValidateErrorException("无效的导入文件格式")

        if not import_data.get("name"):
            raise ValidateErrorException("导入数据缺少应用名称")

        config = import_data.get("config", {})
        warnings = []

        # 2.验证工具引用
        valid_tools = []
        for tool_ref in config.get("tools", []):
            if isinstance(tool_ref, dict) and tool_ref.get("type") == "api_tool":
                provider_id = tool_ref.get("provider_id")
                if provider_id:
                    exists = self.db.session.query(ApiTool).filter(
                        ApiTool.id == provider_id
                    ).first()
                    if exists:
                        valid_tools.append(tool_ref)
                    else:
                        warnings.append(f"工具 {tool_ref.get('tool_name', '')} 不存在，已跳过")
            else:
                # 内置工具直接保留
                valid_tools.append(tool_ref)

        # 3.验证知识库引用
        valid_datasets = []
        for dataset_id in config.get("datasets", []):
            dataset = self.db.session.query(Dataset).filter(
                Dataset.id == dataset_id,
                Dataset.account_id == account.id,
            ).first()
            if dataset:
                valid_datasets.append(dataset_id)
            else:
                warnings.append(f"知识库 {dataset_id} 不存在或无权访问，已跳过")

        # 4.??????
        valid_skills = []
        for skill_id in config.get("skills", []):
            skill = self.db.session.query(Skill).filter(
                Skill.id == skill_id,
            ).first()
            if skill and (skill.account_id == account.id or skill.is_public):
                valid_skills.append(skill_id)
            else:
                warnings.append(f"?? {skill_id} ????????????")

        # 4.创建新应用
        with self.db.auto_commit():
            app = App(
                account_id=account.id,
                name=import_data.get("name", "导入的应用"),
                icons=import_data.get("icon", ""),
                description=import_data.get("description", ""),
                status=AppStatus.DRAFT,
            )
            self.db.session.add(app)
            self.db.session.flush()

            # 5.创建草稿配置
            app_config_version = AppConfigVersion(
                app_id=app.id,
                version=0,
                config_type=AppConfigType.DRAFT,
                model_config=config.get("model_config", {}),
                preset_prompt=config.get("preset_prompt", ""),
                skills=valid_skills,
                dialog_round=config.get("dialog_round", 5),
                tools=valid_tools,
                workflows=config.get("workflows", []),
                datasets=valid_datasets,
                retrieval_config=config.get("retrieval_config", {}),
                long_term_memory=config.get("long_term_memory", {}),
                opening_statement=config.get("opening_statement", ""),
                opening_questions=config.get("opening_questions", []),
                speech_to_text=config.get("speech_to_text", {}),
                text_to_speech=config.get("text_to_speech", {}),
                suggested_after_answer=config.get("suggested_after_answer", {"enable": True}),
                review_config=config.get("review_config", {}),
                multi_agent_config=config.get("multi_agent_config", {}),
            )
            self.db.session.add(app_config_version)

        return {
            "app_id": str(app.id),
            "name": app.name,
            "warnings": warnings,
        }
