<script setup lang="ts">
import { useUpdateDraftAppConfig } from '@/hooks/use-app'
import { useOptimizePrompt } from '@/hooks/use-ai'
import { ref } from 'vue'
import { Message } from '@arco-design/web-vue'
import { useGetPromptTemplatesWithPage } from '@/hooks/use-prompt-template'

// 1.定义自定义组件所需数据
const props = defineProps({
  app_id: { type: String, required: true },
  preset_prompt: { type: String, default: '', required: true },
})
const emits = defineEmits(['update:preset_prompt'])
const optimizeTriggerVisible = ref(false)
const templateTriggerVisible = ref(false)
const origin_prompt = ref('')
const { handleUpdateDraftAppConfig } = useUpdateDraftAppConfig()
const { loading, optimize_prompt, handleOptimizePrompt } = useOptimizePrompt()
const { loading: templatesLoading, templates, loadTemplates } = useGetPromptTemplatesWithPage()

// 2.定义替换预设prompt处理器
const handleReplacePresetPrompt = () => {
  if (optimize_prompt.value.trim() === '') {
    Message.warning('优化prompt为空，请重新生成')
    return
  }
  emits('update:preset_prompt', optimize_prompt.value)
  handleUpdateDraftAppConfig(props.app_id, { preset_prompt: optimize_prompt.value })
  optimizeTriggerVisible.value = false
}

// 3.提交优化prompt处理器
const handleSubmit = async () => {
  if (origin_prompt.value.trim() === '') {
    Message.warning('原始prompt不能为空')
    return
  }
  await handleOptimizePrompt(origin_prompt.value)
}

// 4.从模板选择
const handleOpenTemplates = async () => {
  templateTriggerVisible.value = true
  await loadTemplates(true)
}

const handleSelectTemplate = (content: string) => {
  emits('update:preset_prompt', content)
  handleUpdateDraftAppConfig(props.app_id, { preset_prompt: content })
  templateTriggerVisible.value = false
  Message.success('已应用模板')
}
</script>

<template>
  <div class="flex flex-col h-[calc(100vh-173px)]">
    <!-- 提示标题 -->
    <div class="flex items-center justify-between px-4 mb-4">
      <div class="text-gray-700 font-bold">人设与回复逻辑</div>
      <div class="flex items-center gap-2">
        <a-trigger
          v-model:popup-visible="templateTriggerVisible"
          :trigger="['click']"
          position="bl"
          :popup-translate="[0, 8]"
        >
          <a-button size="mini" class="rounded-lg px-2" @click="handleOpenTemplates">
            <template #icon>
              <icon-book />
            </template>
            模板
          </a-button>
          <template #content>
            <a-card class="rounded-lg w-[320px]">
              <div class="flex flex-col">
                <div class="text-sm font-medium text-abyss-700 mb-3">选择Prompt模板</div>
                <a-spin :loading="templatesLoading">
                  <div class="max-h-[300px] overflow-auto flex flex-col gap-2">
                    <div
                      v-for="tpl in templates"
                      :key="tpl.id"
                      class="p-3 border border-gold-dim rounded-lg cursor-pointer hover:bg-gold-50 transition-all"
                      @click="handleSelectTemplate(tpl.content)"
                    >
                      <div class="text-sm text-abyss-700 font-medium">{{ tpl.name }}</div>
                      <div class="text-xs text-abyss-400 line-clamp-2 mt-1">{{ tpl.content }}</div>
                    </div>
                    <div v-if="templates.length === 0" class="text-sm text-abyss-400 text-center py-4">
                      暂无模板
                    </div>
                  </div>
                </a-spin>
              </div>
            </a-card>
          </template>
        </a-trigger>
        <a-trigger
          v-model:popup-visible="optimizeTriggerVisible"
          :trigger="['click']"
          position="bl"
          :popup-translate="[0, 8]"
        >
        <a-button size="mini" class="rounded-lg px-2">
          <template #icon>
            <icon-sync />
          </template>
          优化
        </a-button>
        <template #content>
          <a-card class="rounded-lg w-[422px]">
            <div class="flex flex-col">
              <!-- 优化prompt -->
              <div v-if="optimize_prompt" class="mb-4 flex flex-col">
                <div
                  class="max-h-[321px] overflow-scroll scrollbar-w-none mb-2 text-gray-700 whitespace-pre-line"
                >
                  {{ optimize_prompt }}
                </div>
                <a-space v-if="!loading">
                  <a-button
                    size="small"
                    type="primary"
                    class="rounded-lg"
                    @click="handleReplacePresetPrompt"
                  >
                    替换
                  </a-button>
                  <a-button size="small" class="rounded-lg" @click="optimizeTriggerVisible = false">
                    退出
                  </a-button>
                </a-space>
              </div>
              <!-- 底部输入框 -->
              <div class="">
                <div
                  class="h-[50px] flex items-center gap-2 px-4 flex-1 border border-gray-200 rounded-full"
                >
                  <input
                    v-model="origin_prompt"
                    type="text"
                    class="flex-1 outline-0"
                    placeholder="你希望如何编写或优化提示词"
                  />
                  <a-button :loading="loading" type="text" shape="circle" @click="handleSubmit">
                    <template #icon>
                      <icon-send :size="16" class="!text-blue-700" />
                    </template>
                  </a-button>
                </div>
              </div>
            </div>
          </a-card>
        </template>
      </a-trigger>
      </div>
    </div>
    <!-- 输入框容器 -->
    <div class="flex-1">
      <a-textarea
        class="h-full resize-none !bg-transparent !border-0 text-gray-700 px-1 preset-prompt-textarea"
        placeholder="请在这里输入Agent的人设与回复逻辑(预设prompt)"
        :max-length="2000"
        show-word-limit
        :model-value="props.preset_prompt"
        @update:model-value="(value) => emits('update:preset_prompt', value)"
        @blur="
          async () => {
            await handleUpdateDraftAppConfig(props.app_id, {
              preset_prompt: props.preset_prompt,
            })
          }
        "
      />
    </div>
  </div>
</template>

<style>
.preset-prompt-textarea {
  textarea {
    scrollbar-width: none;
  }
}
</style>
