import { ref } from 'vue'
import { Message } from '@arco-design/web-vue'
import { createFeedback, getFeedbackStats } from '@/services/feedback'
import type { FeedbackRating } from '@/models/feedback'

export const useCreateFeedback = () => {
  const loading = ref(false)

  const handleCreateFeedback = async (
    message_id: string,
    rating: FeedbackRating,
    content: string = '',
  ) => {
    try {
      loading.value = true
      const resp = await createFeedback(message_id, { rating, content })
      return resp.data
    } finally {
      loading.value = false
    }
  }

  return { loading, handleCreateFeedback }
}

export const useGetFeedbackStats = () => {
  const loading = ref(false)
  const feedback_stats = ref<Record<string, any>>({})

  const loadFeedbackStats = async (app_id: string) => {
    try {
      loading.value = true
      const resp = await getFeedbackStats(app_id)
      feedback_stats.value = resp.data
    } finally {
      loading.value = false
    }
  }

  return { loading, feedback_stats, loadFeedbackStats }
}
