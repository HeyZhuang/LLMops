import { ref } from 'vue'
import { Message, Modal } from '@arco-design/web-vue'
import {
  getPromptTemplatesWithPage,
  createPromptTemplate,
  updatePromptTemplate,
  deletePromptTemplate,
} from '@/services/prompt-template'
import type { PromptTemplate, CreatePromptTemplateRequest } from '@/models/prompt-template'

const defaultPaginator = {
  current_page: 1,
  page_size: 20,
  total_page: 0,
  total_record: 0,
}

export const useGetPromptTemplatesWithPage = () => {
  const loading = ref(false)
  const templates = ref<PromptTemplate[]>([])
  const paginator = ref({ ...defaultPaginator })

  const loadTemplates = async (
    init: boolean = true,
    search_word: string = '',
    category: string = '',
  ) => {
    try {
      if (init) {
        paginator.value = { ...defaultPaginator }
      } else {
        if (paginator.value.current_page > paginator.value.total_page) return
      }

      loading.value = true
      const resp = await getPromptTemplatesWithPage({
        current_page: paginator.value.current_page,
        page_size: paginator.value.page_size,
        search_word,
        category,
      })

      if (init) {
        templates.value = resp.data.list
      } else {
        templates.value = [...templates.value, ...resp.data.list]
      }
      paginator.value = resp.data.paginator
      paginator.value.current_page += 1
    } finally {
      loading.value = false
    }
  }

  return { loading, templates, paginator, loadTemplates }
}

export const useCreatePromptTemplate = () => {
  const loading = ref(false)

  const handleCreatePromptTemplate = async (
    req: CreatePromptTemplateRequest,
    callback?: () => void,
  ) => {
    try {
      loading.value = true
      await createPromptTemplate(req)
      Message.success('模板创建成功')
      callback?.()
    } finally {
      loading.value = false
    }
  }

  return { loading, handleCreatePromptTemplate }
}

export const useUpdatePromptTemplate = () => {
  const loading = ref(false)

  const handleUpdatePromptTemplate = async (
    template_id: string,
    req: CreatePromptTemplateRequest,
    callback?: () => void,
  ) => {
    try {
      loading.value = true
      await updatePromptTemplate(template_id, req)
      Message.success('模板更新成功')
      callback?.()
    } finally {
      loading.value = false
    }
  }

  return { loading, handleUpdatePromptTemplate }
}

export const useDeletePromptTemplate = () => {
  const handleDeletePromptTemplate = (template_id: string, callback?: () => void) => {
    Modal.warning({
      title: '确认删除该模板？',
      content: '删除后将无法恢复，请谨慎操作。',
      hideCancel: false,
      onOk: async () => {
        await deletePromptTemplate(template_id)
        Message.success('模板删除成功')
        callback?.()
      },
    })
  }

  return { handleDeletePromptTemplate }
}
