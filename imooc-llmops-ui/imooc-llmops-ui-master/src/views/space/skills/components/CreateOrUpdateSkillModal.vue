<script setup lang="ts">
import { ref, watch } from 'vue'
import { getSkill } from '@/services/skill'
import { useCreateSkill, useUpdateSkill } from '@/hooks/use-skill'

const props = defineProps({
  visible: { type: Boolean, default: false, required: true },
  skill_id: { type: String, default: '', required: false },
  callback: { type: Function, default: () => {} },
})
const emits = defineEmits(['update:visible', 'update:skill_id'])

const form = ref({
  name: '',
  description: '',
  content: '',
  category: '',
  is_public: false,
})

const { loading: createLoading, handleCreateSkill } = useCreateSkill()
const { loading: updateLoading, handleUpdateSkill } = useUpdateSkill()

watch(
  () => props.skill_id,
  async (newVal) => {
    if (newVal) {
      const resp = await getSkill(newVal)
      form.value = {
        name: resp.data.name,
        description: resp.data.description,
        content: resp.data.content,
        category: resp.data.category,
        is_public: resp.data.is_public,
      }
    } else {
      form.value = { name: '', description: '', content: '', category: '', is_public: false }
    }
  },
  { immediate: true },
)

const handleSubmit = async () => {
  if (props.skill_id) {
    await handleUpdateSkill(props.skill_id, form.value, () => {
      emits('update:visible', false)
      emits('update:skill_id', '')
      props.callback?.()
    })
    return
  }

  await handleCreateSkill(form.value, () => {
    emits('update:visible', false)
    props.callback?.()
  })
}

const handleCancel = () => {
  emits('update:visible', false)
  emits('update:skill_id', '')
  form.value = { name: '', description: '', content: '', category: '', is_public: false }
}
</script>

<template>
  <a-modal
    :visible="props.visible"
    :title="props.skill_id ? '编辑技能' : '新建技能'"
    :ok-loading="createLoading || updateLoading"
    width="680px"
    @ok="handleSubmit"
    @cancel="handleCancel"
  >
    <div class="flex flex-col gap-4">
      <div>
        <div class="text-sm text-abyss-600 mb-1">技能名称 <span class="text-red-400">*</span></div>
        <a-input v-model="form.name" placeholder="例如：资深财务分析师" :max-length="255" />
      </div>
      <div>
        <div class="text-sm text-abyss-600 mb-1">分类</div>
        <a-input v-model="form.category" placeholder="例如：金融 / 医疗 / 法律 / 编程" :max-length="100" />
      </div>
      <div>
        <div class="text-sm text-abyss-600 mb-1">技能简介</div>
        <a-textarea
          v-model="form.description"
          placeholder="简要描述这个技能擅长什么"
          :max-length="500"
          :auto-size="{ minRows: 2 }"
        />
      </div>
      <div>
        <div class="text-sm text-abyss-600 mb-1">
          技能内容 <span class="text-red-400">*</span>
        </div>
        <a-textarea
          v-model="form.content"
          placeholder="填写行为特征、回复风格、边界约束、示例等内容"
          :max-length="8000"
          show-word-limit
          :auto-size="{ minRows: 8, maxRows: 16 }"
        />
      </div>
      <div>
        <a-checkbox v-model="form.is_public">公开技能</a-checkbox>
      </div>
    </div>
  </a-modal>
</template>
