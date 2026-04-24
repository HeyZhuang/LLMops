import type { BaseResponse, BasePaginatorResponse } from '@/models/base'

export type Skill = {
  id: string
  name: string
  description: string
  content: string
  category: string
  is_public: boolean
  updated_at: number
  created_at: number
}

export type CreateSkillRequest = {
  name: string
  description?: string
  content: string
  category?: string
  is_public?: boolean
}

export type UpdateSkillRequest = CreateSkillRequest

export type GetSkillsWithPageResponse = BasePaginatorResponse<Skill>

export type GetSkillResponse = BaseResponse<Skill>
