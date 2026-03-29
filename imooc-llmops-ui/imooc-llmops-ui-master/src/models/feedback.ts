import type { BaseResponse } from '@/models/base'

// 反馈评价类型
export type FeedbackRating = 'like' | 'dislike'

// 创建/更新反馈请求
export type CreateFeedbackRequest = {
  rating: FeedbackRating
  content?: string
}

// 反馈响应
export type GetFeedbackResponse = BaseResponse<{
  id: string
  message_id: string
  rating: FeedbackRating
  content: string
  created_at: number
} | null>

// 反馈统计响应
export type GetFeedbackStatsResponse = BaseResponse<{
  like_count: number
  dislike_count: number
  total_count: number
  satisfaction_rate: number
}>
