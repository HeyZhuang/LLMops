#!/usr/bin/env python
# -*- coding: utf-8 -*-
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from injector import inject
from sqlalchemy import desc, or_

from internal.exception import ForbiddenException, NotFoundException
from internal.model import Account
from internal.model.skill import Skill
from internal.schema.skill_schema import GetSkillsWithPageReq
from pkg.paginator import Paginator, PageModel
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService


@inject
@dataclass
class SkillService(BaseService):
    db: SQLAlchemy

    def get_skills_with_page(self, req: GetSkillsWithPageReq, account: Account) -> PageModel:
        query = self.db.session.query(Skill).filter(
            or_(
                Skill.account_id == account.id,
                Skill.is_public == True,
            )
        )

        if req.search_word.data:
            query = query.filter(Skill.name.ilike(f"%{req.search_word.data}%"))

        if req.category.data:
            query = query.filter(Skill.category == req.category.data)

        query = query.order_by(desc(Skill.updated_at))

        paginator = Paginator(db=self.db, req=req)
        skills = paginator.paginate(query)
        return PageModel(list=skills, paginator=paginator)

    def create_skill(
        self,
        name: str,
        content: str,
        account: Account,
        description: str = "",
        category: str = "",
        is_public: bool = False,
    ) -> Skill:
        return self.create(
            Skill,
            account_id=account.id,
            name=name,
            description=description,
            content=content,
            category=category,
            is_public=is_public,
        )

    def get_skill(self, skill_id: UUID, account: Account) -> Skill:
        skill = self.get(Skill, skill_id)
        if not skill:
            raise NotFoundException("skill not found")
        if skill.account_id != account.id and not skill.is_public:
            raise ForbiddenException("forbidden")
        return skill

    def update_skill(
        self,
        skill_id: UUID,
        account: Account,
        name: str = None,
        content: str = None,
        description: str = None,
        category: str = None,
        is_public: bool = None,
    ) -> Skill:
        skill = self.get(Skill, skill_id)
        if not skill:
            raise NotFoundException("skill not found")
        if skill.account_id != account.id:
            raise ForbiddenException("forbidden")

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

        return self.update(skill, **update_fields)

    def delete_skill(self, skill_id: UUID, account: Account) -> Skill:
        skill = self.get(Skill, skill_id)
        if not skill:
            raise NotFoundException("skill not found")
        if skill.account_id != account.id:
            raise ForbiddenException("forbidden")
        return self.delete(skill)
