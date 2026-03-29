import { get, post } from '@/utils/request'
import type { ExportAppResponse, ImportAppResponse } from '@/models/app-export'

// 导出应用
export const exportApp = (app_id: string) => {
  return get<ExportAppResponse>(`/apps/${app_id}/export`)
}

// 导入应用
export const importApp = (data: Record<string, any>) => {
  return post<ImportAppResponse>('/apps/import', { body: data })
}
