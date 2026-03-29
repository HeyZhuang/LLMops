#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2026/3/18 10:00
@Author  : phase1
@File    : prompt_template_service.py
"""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from injector import inject
from sqlalchemy import desc, or_

from internal.exception import NotFoundException, ForbiddenException
from internal.model import Account
from internal.model.prompt_template import PromptTemplate
from internal.schema.prompt_template_schema import GetPromptTemplatesWithPageReq
from pkg.paginator import Paginator, PageModel
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService


@inject
@dataclass
class PromptTemplateService(BaseService):
    """Prompt模板服务"""
    db: SQLAlchemy

    def get_prompt_templates_with_page(
            self, req: GetPromptTemplatesWithPageReq, account: Account,
    ) -> PageModel:
        """获取模板分页列表"""
        # 1.构建查询 - 显示自己的或公开的
        query = self.db.session.query(PromptTemplate).filter(
            or_(
                PromptTemplate.account_id == account.id,
                PromptTemplate.is_public == True,
            )
        )

        # 2.搜索过滤
        if req.search_word.data:
            query = query.filter(
                PromptTemplate.name.ilike(f"%{req.search_word.data}%")
            )

        # 3.分类过滤
        if req.category.data:
            query = query.filter(PromptTemplate.category == req.category.data)

        # 4.排序
        query = query.order_by(desc(PromptTemplate.updated_at))

        # 5.分页
        paginator = Paginator(db=self.db, req=req)
        templates = paginator.paginate(query)

        return PageModel(list=templates, paginator=paginator)

    def create_prompt_template(
            self, name: str, content: str, account: Account,
            description: str = "", category: str = "", is_public: bool = False,
    ) -> PromptTemplate:
        """创建Prompt模板"""
        return self.create(
            PromptTemplate,
            account_id=account.id,
            name=name,
            description=description,
            content=content,
            category=category,
            is_public=is_public,
        )

    def get_prompt_template(self, template_id: UUID, account: Account) -> PromptTemplate:
        """获取模板详情"""
        template = self.get(PromptTemplate, template_id)
        if not template:
            raise NotFoundException("该模板不存在")
        # 只有作者或公开模板可以查看
        if template.account_id != account.id and not template.is_public:
            raise ForbiddenException("无权访问该模板")
        return template

    def update_prompt_template(
            self, template_id: UUID, account: Account,
            name: str = None, content: str = None,
            description: str = None, category: str = None, is_public: bool = None,
    ) -> PromptTemplate:
        """更新模板"""
        template = self.get(PromptTemplate, template_id)
        if not template:
            raise NotFoundException("该模板不存在")
        if template.account_id != account.id:
            raise ForbiddenException("无权修改该模板")

        update_fields = {}
        if name is not None:
            update_fields["name"] = name
        if content is not None:
            update_fields["content"] = content
        if description is not None:
            update_fields["description"] = description
        if category is not None:
            update_fields["category"] = category
        if is_public is not None:
            update_fields["is_public"] = is_public
        update_fields["updated_at"] = datetime.now()

        return self.update(template, **update_fields)

    def delete_prompt_template(self, template_id: UUID, account: Account) -> PromptTemplate:
        """删除模板"""
        template = self.get(PromptTemplate, template_id)
        if not template:
            raise NotFoundException("该模板不存在")
        if template.account_id != account.id:
            raise ForbiddenException("无权删除该模板")
        return self.delete(template)
