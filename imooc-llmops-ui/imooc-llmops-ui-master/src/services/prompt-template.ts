import { get, post } from '@/utils/request'
import type {
  CreatePromptTemplateRequest,
  UpdatePromptTemplateRequest,
  GetPromptTemplatesWithPageResponse,
  GetPromptTemplateResponse,
} from '@/models/prompt-template'
import type { BaseResponse } from '@/models/base'

// 获取模板分页列表
export const getPromptTemplatesWithPage = (params: Record<string, any> = {}) => {
  return get<GetPromptTemplatesWithPageResponse>('/prompt-templates', { params })
}

// 创建模板
export const createPromptTemplate = (req: CreatePromptTemplateRequest) => {
  return post<GetPromptTemplateResponse>('/prompt-templates', { body: req })
}

// 获取模板详情
export const getPromptTemplate = (template_id: string) => {
  return get<GetPromptTemplateResponse>(`/prompt-templates/${template_id}`)
}

// 更新模板
export const updatePromptTemplate = (template_id: string, req: UpdatePromptTemplateRequest) => {
  return post<GetPromptTemplateResponse>(`/prompt-templates/${template_id}`, { body: req })
}

// 删除模板
export const deletePromptTemplate = (template_id: string) => {
  return post<BaseResponse<Record<string, any>>>(`/prompt-templates/${template_id}/delete`)
}
