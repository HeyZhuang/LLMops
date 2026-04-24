import { get, post } from '@/utils/request'
import type {
  CreateSkillRequest,
  GetSkillResponse,
  GetSkillsWithPageResponse,
  UpdateSkillRequest,
} from '@/models/skill'
import type { BaseResponse } from '@/models/base'

export const getSkillsWithPage = (params: Record<string, any> = {}) => {
  return get<GetSkillsWithPageResponse>('/skills', { params })
}

export const createSkill = (req: CreateSkillRequest) => {
  return post<GetSkillResponse>('/skills', { body: req })
}

export const getSkill = (skill_id: string) => {
  return get<GetSkillResponse>(`/skills/${skill_id}`)
}

export const updateSkill = (skill_id: string, req: UpdateSkillRequest) => {
  return post<GetSkillResponse>(`/skills/${skill_id}`, { body: req })
}

export const deleteSkill = (skill_id: string) => {
  return post<BaseResponse<Record<string, any>>>(`/skills/${skill_id}/delete`)
}
