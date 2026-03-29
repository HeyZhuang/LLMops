#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2026/3/18 10:00
@Author  : phase1
@File    : prompt_template_handler.py
"""
from dataclasses import dataclass
from uuid import UUID

from flask_login import login_required, current_user
from injector import inject

from internal.schema.prompt_template_schema import (
    CreatePromptTemplateReq,
    UpdatePromptTemplateReq,
    GetPromptTemplatesWithPageReq,
    GetPromptTemplateResp,
)
from internal.service.prompt_template_service import PromptTemplateService
from pkg.response import success_json, validate_error_json, success_message


@inject
@dataclass
class PromptTemplateHandler:
    """Prompt模板处理器"""
    prompt_template_service: PromptTemplateService

    @login_required
    def get_prompt_templates_with_page(self):
        """获取模板分页列表"""
        req = GetPromptTemplatesWithPageReq()
        if not req.validate():
            return validate_error_json(req.errors)

        page_model = self.prompt_template_service.get_prompt_templates_with_page(req, current_user)

        resp = GetPromptTemplateResp()
        return success_json({
            "list": resp.dump(page_model.list, many=True),
            "paginator": {
                "total_page": page_model.paginator.total_page,
                "total_record": page_model.paginator.total_record,
                "current_page": page_model.paginator.current_page,
                "page_size": page_model.paginator.page_size,
            },
        })

    @login_required
    def create_prompt_template(self):
        """创建模板"""
        req = CreatePromptTemplateReq()
        if not req.validate():
            return validate_error_json(req.errors)

        template = self.prompt_template_service.create_prompt_template(
            name=req.name.data,
            content=req.content.data,
            account=current_user,
            description=req.description.data or "",
            category=req.category.data or "",
            is_public=req.is_public.data or False,
        )

        resp = GetPromptTemplateResp()
        return success_json(resp.dump(template))

    @login_required
    def get_prompt_template(self, template_id: UUID):
        """获取模板详情"""
        template = self.prompt_template_service.get_prompt_template(template_id, current_user)
        resp = GetPromptTemplateResp()
        return success_json(resp.dump(template))

    @login_required
    def update_prompt_template(self, template_id: UUID):
        """更新模板"""
        req = UpdatePromptTemplateReq()
        if not req.validate():
            return validate_error_json(req.errors)

        template = self.prompt_template_service.update_prompt_template(
            template_id=template_id,
            account=current_user,
            name=req.name.data,
            content=req.content.data,
            description=req.description.data or "",
            category=req.category.data or "",
            is_public=req.is_public.data or False,
        )

        resp = GetPromptTemplateResp()
        return success_json(resp.dump(template))

    @login_required
    def delete_prompt_template(self, template_id: UUID):
        """删除模板"""
        self.prompt_template_service.delete_prompt_template(template_id, current_user)
        return success_message("模板删除成功")
