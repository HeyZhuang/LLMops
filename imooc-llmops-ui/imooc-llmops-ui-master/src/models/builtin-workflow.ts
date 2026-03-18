import type { BaseResponse } from '@/models/base'

// 获取内置工作流模板分类响应结构体
export type GetBuiltinWorkflowCategoriesResponse = BaseResponse<
  {
    category: string
    name: string
  }[]
>

// 获取内置工作流模板列表响应结构体
export type GetBuiltinWorkflowsResponse = BaseResponse<
  {
    id: string
    category: string
    name: string
    tool_call_name: string
    icon: string
    description: string
    node_count: number
    author: string
    created_at: number
  }[]
>
