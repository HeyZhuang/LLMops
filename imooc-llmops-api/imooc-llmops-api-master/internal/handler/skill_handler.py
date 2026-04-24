#!/usr/bin/env python
# -*- coding: utf-8 -*-
from dataclasses import dataclass
from uuid import UUID

from flask_login import current_user, login_required
from injector import inject

from internal.schema.skill_schema import (
    CreateSkillReq,
    UpdateSkillReq,
    GetSkillsWithPageReq,
    GetSkillResp,
)
from internal.service.skill_service import SkillService
from pkg.response import success_json, validate_error_json, success_message


@inject
@dataclass
class SkillHandler:
    skill_service: SkillService

    @login_required
    def get_skills_with_page(self):
        req = GetSkillsWithPageReq()
        if not req.validate():
            return validate_error_json(req.errors)

        page_model = self.skill_service.get_skills_with_page(req, current_user)
        resp = GetSkillResp()
        return success_json(
            {
                "list": resp.dump(page_model.list, many=True),
                "paginator": {
                    "total_page": page_model.paginator.total_page,
                    "total_record": page_model.paginator.total_record,
                    "current_page": page_model.paginator.current_page,
                    "page_size": page_model.paginator.page_size,
                },
            }
        )

    @login_required
    def create_skill(self):
        req = CreateSkillReq()
        if not req.validate():
            return validate_error_json(req.errors)

        skill = self.skill_service.create_skill(
            name=req.name.data,
            content=req.content.data,
            account=current_user,
            description=req.description.data or "",
            category=req.category.data or "",
            is_public=req.is_public.data or False,
        )
        resp = GetSkillResp()
        return success_json(resp.dump(skill))

    @login_required
    def get_skill(self, skill_id: UUID):
        skill = self.skill_service.get_skill(skill_id, current_user)
        resp = GetSkillResp()
        return success_json(resp.dump(skill))

    @login_required
    def update_skill(self, skill_id: UUID):
        req = UpdateSkillReq()
        if not req.validate():
            return validate_error_json(req.errors)

        skill = self.skill_service.update_skill(
            skill_id=skill_id,
            account=current_user,
            name=req.name.data,
            content=req.content.data,
            description=req.description.data or "",
            category=req.category.data or "",
            is_public=req.is_public.data or False,
        )
        resp = GetSkillResp()
        return success_json(resp.dump(skill))

    @login_required
    def delete_skill(self, skill_id: UUID):
        self.skill_service.delete_skill(skill_id, current_user)
        return success_message("skill deleted successfully")
