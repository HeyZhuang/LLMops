import type { BaseResponse } from '@/models/base'

export type ConsultCenterOverviewData = {
  summary: {
    total_apps: number
    published_apps: number
    total_datasets: number
    total_documents: number
    total_workflows: number
    published_workflows: number
    recent_messages: number
    recent_conversations: number
    total_token_count: number
    average_latency: number
    document_character_count: number
    dataset_hit_count: number
  }
  daily_activity: {
    date: string
    count: number
  }[]
  recent_items: {
    apps: {
      id: string
      name: string
      description: string
      status: string
      created_at: number
    }[]
    datasets: {
      id: string
      name: string
      description: string
      document_count: number
      hit_count: number
      created_at: number
    }[]
    workflows: {
      id: string
      name: string
      description: string
      status: string
      created_at: number
    }[]
  }
  recommended_actions: string[]
}

export type ConsultCenterOverviewResponse = BaseResponse<ConsultCenterOverviewData>
