<script setup lang="ts">
import { ref, watch } from 'vue'
import {
  useCreatePromptTemplate,
  useUpdatePromptTemplate,
} from '@/hooks/use-prompt-template'
import { getPromptTemplate } from '@/services/prompt-template'

// 1.定义组件数据
const props = defineProps({
  visible: { type: Boolean, default: false, required: true },
  template_id: { type: String, default: '', required: false },
  callback: { type: Function, default: () => {} },
})
const emits = defineEmits(['update:visible', 'update:template_id'])

const form = ref({
  name: '',
  description: '',
  content: '',
  category: '',
  is_public: false,
})

const { loading: createLoading, handleCreatePromptTemplate } = useCreatePromptTemplate()
const { loading: updateLoading, handleUpdatePromptTemplate } = useUpdatePromptTemplate()

// 2.监听template_id变化，加载编辑数据
watch(
  () => props.template_id,
  async (newVal) => {
    if (newVal) {
      const resp = await getPromptTemplate(newVal)
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
)

// 3.提交
const handleSubmit = async () => {
  if (props.template_id) {
    await handleUpdatePromptTemplate(props.template_id, form.value, () => {
      emits('update:visible', false)
      emits('update:template_id', '')
      props.callback?.()
    })
  } else {
    await handleCreatePromptTemplate(form.value, () => {
      emits('update:visible', false)
      props.callback?.()
    })
  }
}

// 4.取消
const handleCancel = () => {
  emits('update:visible', false)
  emits('update:template_id', '')
  form.value = { name: '', description: '', content: '', category: '', is_public: false }
}
</script>

<template>
  <a-modal
    :visible="props.visible"
    :title="props.template_id ? '编辑模板' : '创建模板'"
    :ok-loading="createLoading || updateLoading"
    width="600px"
    @ok="handleSubmit"
    @cancel="handleCancel"
  >
    <div class="flex flex-col gap-4">
      <div>
        <div class="text-sm text-abyss-600 mb-1">模板名称 <span class="text-red-400">*</span></div>
        <a-input v-model="form.name" placeholder="请输入模板名称" :max-length="255" />
      </div>
      <div>
        <div class="text-sm text-abyss-600 mb-1">分类</div>
        <a-input v-model="form.category" placeholder="如：客服、写作、编程" :max-length="100" />
      </div>
      <div>
        <div class="text-sm text-abyss-600 mb-1">描述</div>
        <a-textarea v-model="form.description" placeholder="描述模板用途" :max-length="500" :auto-size="{ minRows: 2 }" />
      </div>
      <div>
        <div class="text-sm text-abyss-600 mb-1">
          Prompt内容 <span class="text-red-400">*</span>
          <span class="text-abyss-300 text-xs ml-2">支持 {{变量名}} 语法</span>
        </div>
        <a-textarea
          v-model="form.content"
          placeholder="请输入Prompt内容..."
          :max-length="5000"
          show-word-limit
          :auto-size="{ minRows: 6, maxRows: 15 }"
        />
      </div>
      <div>
        <a-checkbox v-model="form.is_public">公开模板（其他用户可以查看）</a-checkbox>
      </div>
    </div>
  </a-modal>
</template>
