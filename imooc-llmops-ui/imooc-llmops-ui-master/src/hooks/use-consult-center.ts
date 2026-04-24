import { onMounted, ref } from 'vue'
import { getConsultCenterOverview } from '@/services/consult-center'
import type { ConsultCenterOverviewData } from '@/models/consult-center'

const createDefaultOverview = (): ConsultCenterOverviewData => ({
  summary: {
    total_apps: 0,
    published_apps: 0,
    total_datasets: 0,
    total_documents: 0,
    total_workflows: 0,
    published_workflows: 0,
    recent_messages: 0,
    recent_conversations: 0,
    total_token_count: 0,
    average_latency: 0,
    document_character_count: 0,
    dataset_hit_count: 0,
  },
  daily_activity: [],
  recent_items: {
    apps: [],
    datasets: [],
    workflows: [],
  },
  recommended_actions: [],
})

export const useConsultCenterOverview = () => {
  const loading = ref(false)
  const overview = ref<ConsultCenterOverviewData>(createDefaultOverview())

  const loadConsultCenterOverview = async () => {
    try {
      loading.value = true
      const resp = await getConsultCenterOverview()
      overview.value = resp.data
    } finally {
      loading.value = false
    }
  }

  onMounted(() => {
    loadConsultCenterOverview()
  })

  return {
    loading,
    overview,
    loadConsultCenterOverview,
  }
}
