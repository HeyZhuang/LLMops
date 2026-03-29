<script setup lang="ts">
import { computed, ref, type PropType } from 'vue'
import MarkdownIt from 'markdown-it'
import DotFlashing from '@/components/DotFlashing.vue'
import AgentThought from './AgentThought.vue'
import { useCreateFeedback } from '@/hooks/use-feedback'
import 'github-markdown-css'

// 1.定义自定义组件所需数据
const props = defineProps({
  app: {
    type: Object,
    default: () => {
      return {}
    },
    required: true,
  },
  answer: { type: String, default: '', required: true },
  loading: { type: Boolean, default: false, required: false },
  latency: { type: Number, default: 0, required: false },
  total_token_count: { type: Number, default: 0, required: false },
  agent_thoughts: {
    type: Array as PropType<Record<string, any>[]>,
    default: () => [],
    required: true,
  },
  suggested_questions: { type: Array as PropType<string[]>, default: () => [], required: false },
  message_class: { type: String, default: '!bg-parchment-200', required: false },
  message_id: { type: String, default: '', required: false },
  feedback: {
    type: Object as PropType<{ rating: string; content: string } | null>,
    default: null,
    required: false,
  },
})
const emits = defineEmits(['selectSuggestedQuestion'])
const md = MarkdownIt()
const compiledMarkdown = computed(() => {
  return md.render(props.answer)
})

// 反馈相关
const currentRating = ref<string>(props.feedback?.rating || '')
const { loading: feedbackLoading, handleCreateFeedback } = useCreateFeedback()

const handleFeedback = async (rating: 'like' | 'dislike') => {
  if (!props.message_id || feedbackLoading.value) return
  // 如果已经点过同一个，取消不做操作
  if (currentRating.value === rating) return
  currentRating.value = rating
  await handleCreateFeedback(props.message_id, rating)
}
</script>

<template>
  <div class="flex gap-2">
    <!-- 左侧图标 -->
    <a-avatar
      v-if="props.app?.icon"
      :size="30"
      shape="circle"
      class="flex-shrink-0 shadow-gold-sm"
      :image-url="props.app?.icon"
    />
    <a-avatar v-else :size="30" shape="circle" class="flex-shrink-0 !bg-abyss-800 !text-gold-400">
      <icon-apps />
    </a-avatar>
    <!-- 右侧名称与消息 -->
    <div class="flex-1 flex flex-col items-start gap-2">
      <!-- 应用名称 -->
      <div class="text-abyss-700 font-bold">{{ props.app?.name }}</div>
      <!-- 推理步骤 -->
      <agent-thought :agent_thoughts="props.agent_thoughts" :loading="props.loading" />
      <!-- AI消息 -->
      <div
        v-if="props.loading && props.answer.trim() === ''"
        :class="`${props.message_class} border border-gold-dim text-abyss-700 px-4 py-3 rounded-2xl break-all`"
      >
        <dot-flashing />
      </div>
      <div
        v-else
        :class="`${props.message_class} markdown-body border border-gold-dim text-abyss-700 px-4 py-3 rounded-2xl break-all`"
        v-html="compiledMarkdown"
      ></div>
      <!-- 消息展示与操作 -->
      <div class="flex items-center justify-between">
        <!-- 消息数据额外展示 -->
        <a-space class="text-xs">
          <template #split>
            <a-divider direction="vertical" class="m-0" />
          </template>
          <div class="flex items-center gap-1 text-abyss-400">
            <icon-check />
            {{ props.latency.toFixed(2) }}s
          </div>
          <div class="text-abyss-400">{{ props.total_token_count }} Tokens</div>
        </a-space>
        <!-- 反馈按钮 -->
        <div v-if="props.message_id && !props.loading" class="flex items-center gap-1 ml-3">
          <a-tooltip content="有帮助">
            <div
              :class="[
                'cursor-pointer p-1 rounded transition-all',
                currentRating === 'like' ? 'text-gold-500 bg-gold-50' : 'text-abyss-300 hover:text-gold-400'
              ]"
              @click="handleFeedback('like')"
            >
              <icon-thumb-up :size="14" />
            </div>
          </a-tooltip>
          <a-tooltip content="无帮助">
            <div
              :class="[
                'cursor-pointer p-1 rounded transition-all',
                currentRating === 'dislike' ? 'text-red-400 bg-red-50' : 'text-abyss-300 hover:text-red-400'
              ]"
              @click="handleFeedback('dislike')"
            >
              <icon-thumb-down :size="14" />
            </div>
          </a-tooltip>
        </div>
      </div>
      <!-- 建议问题列表 -->
      <div v-if="props.suggested_questions.length > 0" class="flex flex-col gap-2">
        <div
          v-for="(suggested_question, idx) in props.suggested_questions"
          :key="idx"
          class="px-4 py-1.5 border border-gold-dim rounded-lg text-abyss-600 cursor-pointer bg-parchment-100 hover:bg-gold-50 hover:border-gold-bright transition-all"
          @click="() => emits('selectSuggestedQuestion', suggested_question)"
        >
          {{ suggested_question }}
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped></style>
