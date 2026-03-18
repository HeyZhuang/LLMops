import { ref } from 'vue'
import type {
  GetBuiltinWorkflowCategoriesResponse,
  GetBuiltinWorkflowsResponse,
} from '@/models/builtin-workflow'
import {
  addBuiltinWorkflowToSpace,
  getBuiltinWorkflowCategories,
  getBuiltinWorkflows,
} from '@/services/builtin-workflow'
import { useRouter } from 'vue-router'
import { Message } from '@arco-design/web-vue'

export const useGetBuiltinWorkflowCategories = () => {
  const loading = ref(false)
  const categories = ref<GetBuiltinWorkflowCategoriesResponse['data']>([])

  const loadBuiltinWorkflowCategories = async () => {
    try {
      loading.value = true
      const resp = await getBuiltinWorkflowCategories()
      categories.value = resp.data
    } finally {
      loading.value = false
    }
  }

  return { loading, categories, loadBuiltinWorkflowCategories }
}

export const useGetBuiltinWorkflows = () => {
  const loading = ref(false)
  const workflows = ref<GetBuiltinWorkflowsResponse['data']>([])

  const loadBuiltinWorkflows = async () => {
    try {
      loading.value = true
      const resp = await getBuiltinWorkflows()
      workflows.value = resp.data
    } finally {
      loading.value = false
    }
  }

  return { loading, workflows, loadBuiltinWorkflows }
}

export const useAddBuiltinWorkflowToSpace = () => {
  const router = useRouter()
  const loading = ref(false)

  const handleAddBuiltinWorkflowToSpace = async (builtin_workflow_id: string) => {
    try {
      loading.value = true
      const resp = await addBuiltinWorkflowToSpace(builtin_workflow_id)
      Message.success('将工作流模板添加到工作区成功')
      await router.push({
        name: 'space-workflows-detail',
        params: { workflow_id: resp.data.id },
      })
    } finally {
      loading.value = false
    }
  }

  return { loading, handleAddBuiltinWorkflowToSpace }
}
