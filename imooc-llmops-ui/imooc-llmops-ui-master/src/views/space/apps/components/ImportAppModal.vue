<script setup lang="ts">
import { ref } from 'vue'
import { useImportApp } from '@/hooks/use-app-export'

// 1.定义组件数据
const props = defineProps({
  visible: { type: Boolean, default: false, required: true },
  callback: { type: Function, default: () => {} },
})
const emits = defineEmits(['update:visible'])
const { loading, importResult, handleImportApp } = useImportApp()
const fileContent = ref<Record<string, any> | null>(null)
const fileName = ref('')

// 2.处理文件选择
const handleFileChange = (event: Event) => {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  fileName.value = file.name
  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      fileContent.value = JSON.parse(e.target?.result as string)
    } catch {
      fileContent.value = null
      fileName.value = ''
    }
  }
  reader.readAsText(file)
}

// 3.提交导入
const handleSubmit = async () => {
  if (!fileContent.value) return
  await handleImportApp(fileContent.value, () => {
    emits('update:visible', false)
    fileContent.value = null
    fileName.value = ''
    props.callback?.()
  })
}

// 4.取消
const handleCancel = () => {
  emits('update:visible', false)
  fileContent.value = null
  fileName.value = ''
}
</script>

<template>
  <a-modal
    :visible="props.visible"
    title="导入应用"
    :ok-loading="loading"
    :ok-button-props="{ disabled: !fileContent }"
    @ok="handleSubmit"
    @cancel="handleCancel"
  >
    <div class="flex flex-col gap-4">
      <div class="text-abyss-500 text-sm">
        选择一个从LLMOps导出的JSON文件来导入应用配置。
      </div>
      <div class="flex items-center gap-3">
        <label
          class="cursor-pointer px-4 py-2 bg-gold-50 border border-gold-dim rounded-lg text-abyss-600 hover:bg-gold-100 transition-all"
        >
          <input type="file" accept=".json" class="hidden" @change="handleFileChange" />
          选择文件
        </label>
        <span v-if="fileName" class="text-abyss-500 text-sm">{{ fileName }}</span>
        <span v-else class="text-abyss-300 text-sm">未选择文件</span>
      </div>
      <div v-if="fileContent" class="glass metal-border rounded-lg p-3">
        <div class="text-sm text-abyss-600">
          <span class="font-medium">应用名称：</span>{{ fileContent.name }}
        </div>
        <div v-if="fileContent.description" class="text-sm text-abyss-400 mt-1">
          {{ fileContent.description }}
        </div>
      </div>
      <!-- 导入警告 -->
      <div v-if="importResult?.warnings?.length > 0" class="flex flex-col gap-1">
        <div v-for="(warning, idx) in importResult.warnings" :key="idx" class="text-xs text-orange-500">
          {{ warning }}
        </div>
      </div>
    </div>
  </a-modal>
</template>
