import { ref } from 'vue'
import { Message, Modal } from '@arco-design/web-vue'
import {
  createSkill,
  deleteSkill,
  getSkill,
  getSkillsWithPage,
  updateSkill,
} from '@/services/skill'
import type { CreateSkillRequest, Skill, UpdateSkillRequest } from '@/models/skill'

const defaultPaginator = {
  current_page: 1,
  page_size: 20,
  total_page: 0,
  total_record: 0,
}

export const useGetSkillsWithPage = () => {
  const loading = ref(false)
  const skills = ref<Skill[]>([])
  const paginator = ref({ ...defaultPaginator })

  const loadSkills = async (init: boolean = true, search_word: string = '', category: string = '') => {
    try {
      if (init) {
        paginator.value = { ...defaultPaginator }
      } else if (paginator.value.current_page > paginator.value.total_page) {
        return
      }

      loading.value = true
      const resp = await getSkillsWithPage({
        current_page: paginator.value.current_page,
        page_size: paginator.value.page_size,
        search_word,
        category,
      })

      if (init) {
        skills.value = resp.data.list
      } else {
        skills.value = [...skills.value, ...resp.data.list]
      }
      paginator.value = resp.data.paginator
      paginator.value.current_page += 1
    } finally {
      loading.value = false
    }
  }

  return { loading, skills, paginator, loadSkills }
}

export const useCreateSkill = () => {
  const loading = ref(false)

  const handleCreateSkill = async (req: CreateSkillRequest, callback?: () => void) => {
    try {
      loading.value = true
      await createSkill(req)
      Message.success('技能创建成功')
      callback?.()
    } finally {
      loading.value = false
    }
  }

  return { loading, handleCreateSkill }
}

export const useUpdateSkill = () => {
  const loading = ref(false)

  const handleUpdateSkill = async (skill_id: string, req: UpdateSkillRequest, callback?: () => void) => {
    try {
      loading.value = true
      await updateSkill(skill_id, req)
      Message.success('技能更新成功')
      callback?.()
    } finally {
      loading.value = false
    }
  }

  return { loading, handleUpdateSkill }
}

export const useDeleteSkill = () => {
  const handleDeleteSkill = (skill_id: string, callback?: () => void) => {
    Modal.warning({
      title: '删除该技能？',
      content: '此操作不可恢复。',
      hideCancel: false,
      onOk: async () => {
        await deleteSkill(skill_id)
        Message.success('技能删除成功')
        callback?.()
      },
    })
  }

  return { handleDeleteSkill }
}

export const useGetSkill = () => {
  const loading = ref(false)
  const skill = ref<Skill | null>(null)

  const loadSkill = async (skill_id: string) => {
    try {
      loading.value = true
      const resp = await getSkill(skill_id)
      skill.value = resp.data
    } finally {
      loading.value = false
    }
  }

  return { loading, skill, loadSkill }
}
