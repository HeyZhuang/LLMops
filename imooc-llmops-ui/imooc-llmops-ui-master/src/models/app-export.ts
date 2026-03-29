import type { BaseResponse } from '@/models/base'

// 导出应用响应
export type ExportAppResponse = BaseResponse<{
  version: string
  type: string
  name: string
  description: string
  icon: string
  config: Record<string, any>
  exported_at: string
}>

// 导入应用响应
export type ImportAppResponse = BaseResponse<{
  app_id: string
  name: string
  warnings: string[]
}>
