import { get } from '@/utils/request'
import type { GetAppAnalysisResponse, GetTokenCostAnalysisResponse } from '@/models/analysis'

// 获取应用统计分析服务
export const getAppAnalysis = (app_id: string) => {
  return get<GetAppAnalysisResponse>(`/analysis/${app_id}`)
}

// 获取Token成本分析
export const getTokenCostAnalysis = (app_id: string) => {
  return get<GetTokenCostAnalysisResponse>(`/analysis/${app_id}/token-cost`)
}
