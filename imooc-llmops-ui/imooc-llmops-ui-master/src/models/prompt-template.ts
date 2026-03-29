import type { BaseResponse, BasePaginatorResponse } from '@/models/base'

// Prompt模板
export type PromptTemplate = {
  id: string
  name: string
  description: string
  content: string
  category: string
  is_public: boolean
  updated_at: number
  created_at: number
}

// 创建Prompt模板请求
export type CreatePromptTemplateRequest = {
  name: string
  description?: string
  content: string
  category?: string
  is_public?: boolean
}

// 更新Prompt模板请求
export type UpdatePromptTemplateRequest = CreatePromptTemplateRequest

// 获取Prompt模板分页响应
export type GetPromptTemplatesWithPageResponse = BasePaginatorResponse<PromptTemplate>

// 获取Prompt模板详情响应
export type GetPromptTemplateResponse = BaseResponse<PromptTemplate>
