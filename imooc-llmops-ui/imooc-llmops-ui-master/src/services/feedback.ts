import { get, post } from '@/utils/request'
import type {
  CreateFeedbackRequest,
  GetFeedbackResponse,
  GetFeedbackStatsResponse,
} from '@/models/feedback'

// 创建/更新消息反馈
export const createFeedback = (message_id: string, req: CreateFeedbackRequest) => {
  return post<GetFeedbackResponse>(`/messages/${message_id}/feedback`, { body: req })
}

// 获取消息反馈
export const getFeedback = (message_id: string) => {
  return get<GetFeedbackResponse>(`/messages/${message_id}/feedback`)
}

// 获取应用反馈统计
export const getFeedbackStats = (app_id: string) => {
  return get<GetFeedbackStatsResponse>(`/apps/${app_id}/feedback-stats`)
}
