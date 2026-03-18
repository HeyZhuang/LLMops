import { get, post } from '@/utils/request'
import type {
  GetBuiltinWorkflowCategoriesResponse,
  GetBuiltinWorkflowsResponse,
} from '@/models/builtin-workflow'
import type { BaseResponse } from '@/models/base'

// 获取内置工作流模板分类列表
export const getBuiltinWorkflowCategories = () => {
  return get<GetBuiltinWorkflowCategoriesResponse>(`/builtin-workflows/categories`)
}

// 获取内置工作流模板列表信息
export const getBuiltinWorkflows = () => {
  return get<GetBuiltinWorkflowsResponse>(`/builtin-workflows`)
}

// 将指定工作流模板添加到工作区
export const addBuiltinWorkflowToSpace = (builtin_workflow_id: string) => {
  return post<BaseResponse<{ id: string }>>(`/builtin-workflows/add-builtin-workflow-to-space`, {
    body: { builtin_workflow_id },
  })
}
