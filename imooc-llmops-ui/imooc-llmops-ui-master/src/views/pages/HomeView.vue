<script setup lang="ts">
import { nextTick, onMounted, ref } from 'vue'
import {
  useAssistantAgentChat,
  useDeleteAssistantAgentConversation,
  useGetAssistantAgentMessagesWithPage,
  useStopAssistantAgentChat,
} from '@/hooks/use-assistant-agent'
import { useGenerateSuggestedQuestions } from '@/hooks/use-ai'
import { useConsultCenterOverview } from '@/hooks/use-consult-center'
import { useAccountStore } from '@/stores/account'
import { Message } from '@arco-design/web-vue'
import { QueueEvent } from '@/config'
import HumanMessage from '@/components/HumanMessage.vue'
import AiMessage from '@/components/AiMessage.vue'

const query = ref('')
const task_id = ref('')
const message_id = ref('')
const scroller = ref<HTMLElement | null>(null)
const scrollHeight = ref(0)
const accountStore = useAccountStore()
const { overview } = useConsultCenterOverview()

const heroTags = ['MDT', 'Graph RAG', '可追溯证据', '流程闭环']
const openingQuestions = [
  '胸痛合并心电图异常，如何组织跨科会诊',
  '如何把影像和检验整合成证据链',
  '设计一个多智能体会诊编排流程',
]
const orchestrationLayers = [
  { title: '临床接入', desc: '统一采集病史、影像、检验和主诉信息' },
  { title: '编排中枢', desc: '按专科、风险和复杂度路由会诊任务' },
  { title: 'Graph RAG', desc: '融合指南、病例与图谱，形成证据链' },
  { title: '审校闭环', desc: '复核结论并沉淀为可复用资产' },
]
const ragHighlights = [
  { label: '知识图谱', value: '结构化关系' },
  { label: '向量召回', value: '语义近邻' },
  { label: '证据回链', value: '原文可追踪' },
]
const quickScenarios = ['复杂病例会诊', '影像与检验联合解读', '指南证据快速检索', 'MDT 流程编排']

const { suggested_questions, handleGenerateSuggestedQuestions } = useGenerateSuggestedQuestions()
const { loading: assistantAgentChatLoading, handleAssistantAgentChat } = useAssistantAgentChat()
const { loading: stopAssistantAgentChatLoading, handleStopAssistantAgentChat } =
  useStopAssistantAgentChat()
const {
  loading: getAssistantAgentMessagesWithPageLoading,
  messages,
  loadAssistantAgentMessages,
} = useGetAssistantAgentMessagesWithPage()
const { loading: deleteAssistantAgentConversationLoading, handleDeleteAssistantAgentConversation } =
  useDeleteAssistantAgentConversation()

const saveScrollHeight = () => {
  if (!scroller.value) return
  scrollHeight.value = scroller.value.scrollHeight
}

const restoreScrollPosition = () => {
  if (!scroller.value) return
  scroller.value.scrollTop = scroller.value.scrollHeight - scrollHeight.value
}

const scrollToBottom = () => {
  if (!scroller.value) return
  scroller.value.scrollTop = scroller.value.scrollHeight
}

const handleScroll = async (event: Event) => {
  const { scrollTop } = event.target as HTMLElement
  if (scrollTop <= 0 && !getAssistantAgentMessagesWithPageLoading.value) {
    saveScrollHeight()
    await loadAssistantAgentMessages(false)
    restoreScrollPosition()
  }
}

const handleSubmit = async () => {
  if (query.value.trim() === '') {
    Message.warning('会诊输入不能为空')
    return
  }
  if (assistantAgentChatLoading.value) {
    Message.warning('上一轮会诊尚未结束，请稍候')
    return
  }

  suggested_questions.value = []
  message_id.value = ''
  task_id.value = ''
  messages.value.unshift({
    id: '',
    conversation_id: '',
    query: query.value,
    answer: '',
    total_token_count: 0,
    latency: 0,
    agent_thoughts: [],
    created_at: 0,
  })

  let position = 0
  const humanQuery = query.value
  query.value = ''

  await handleAssistantAgentChat(humanQuery, (event_response) => {
    const event = event_response?.event
    const data = event_response?.data
    const event_id = data?.id
    let agent_thoughts = messages.value[0].agent_thoughts

    if (message_id.value === '' && data?.message_id) {
      task_id.value = data?.task_id
      message_id.value = data?.message_id
      messages.value[0].id = data?.message_id
      messages.value[0].conversation_id = data?.conversation_id
    }

    if (event !== QueueEvent.ping) {
      if (event === QueueEvent.agentMessage) {
        const agent_thought_idx = agent_thoughts.findIndex((item) => item?.id === event_id)
        if (agent_thought_idx === -1) {
          position += 1
          agent_thoughts.push({
            id: event_id,
            position,
            event: data?.event,
            thought: data?.thought,
            observation: data?.observation,
            tool: data?.tool,
            tool_input: data?.tool_input,
            latency: data?.latency,
            created_at: 0,
          })
        } else {
          agent_thoughts[agent_thought_idx] = {
            ...agent_thoughts[agent_thought_idx],
            thought: agent_thoughts[agent_thought_idx]?.thought + data?.thought,
            latency: data?.latency,
          }
        }
        messages.value[0].answer += data?.thought
        messages.value[0].latency = data?.latency
        messages.value[0].total_token_count = data?.total_token_count
      } else if (event === QueueEvent.error) {
        messages.value[0].answer = data?.observation
      } else if (event === QueueEvent.timeout) {
        messages.value[0].answer = '会诊任务已超时，请稍后重试'
      } else {
        position += 1
        agent_thoughts.push({
          id: event_id,
          position,
          event: data?.event,
          thought: data?.thought,
          observation: data?.observation,
          tool: data?.tool,
          tool_input: data?.tool_input,
          latency: data?.latency,
          created_at: 0,
        })
      }

      messages.value[0].agent_thoughts = agent_thoughts
      messages.value[0] = { ...messages.value[0] }
      nextTick(() => scrollToBottom())
    }
  })

  await nextTick(() => {
    scrollToBottom()
  })

  setTimeout(() => loadAssistantAgentMessages(true), 1500)
  if (message_id.value) {
    try {
      await handleGenerateSuggestedQuestions(message_id.value)
    } catch {
      // 推荐问题生成失败不影响主会诊流程
    }
    setTimeout(() => scrollToBottom(), 100)
  }
}

const handleStop = async () => {
  if (task_id.value === '' || !assistantAgentChatLoading.value) return
  await handleStopAssistantAgentChat(task_id.value)
}

const handleSubmitQuestion = async (question: string) => {
  query.value = question
  await handleSubmit()
}

onMounted(async () => {
  await loadAssistantAgentMessages(true)
  await nextTick(() => {
    scrollToBottom()
  })
})
</script>

<template>
  <div class="home-page-scroll flex min-h-full w-full flex-col overflow-visible linen-bg px-4 py-6 lg:px-6">
    <div class="mx-auto flex w-full max-w-[1600px] min-w-0 flex-col gap-6">
      <section
        class="relative min-w-0 overflow-hidden rounded-[28px] glass metal-border shadow-glass px-6 py-6 md:px-8 md:py-8"
      >
        <div
          class="absolute -right-20 -top-20 h-64 w-64 rounded-full bg-[rgba(212,175,55,0.10)] blur-3xl"
        ></div>
        <div
          class="absolute -bottom-16 left-1/3 h-48 w-48 rounded-full bg-[rgba(15,65,85,0.08)] blur-3xl"
        ></div>
        <div class="relative flex flex-col gap-6 xl:flex-row xl:items-end xl:justify-between">
          <div class="max-w-3xl">
            <a-tag color="gold" size="small" class="!rounded-full !px-3 !py-1">
              会诊指挥中枢
            </a-tag>
            <h1 class="mt-4 text-4xl font-bold tracking-[0.18em] text-abyss-800 md:text-5xl">
              医脉天枢
            </h1>
            <p class="mt-4 max-w-3xl text-base leading-8 text-abyss-500 md:text-lg">
              融合多智能体编排与 Graph RAG 的跨学科全景会诊中枢，将病例摘要、影像、检验、
              指南与专家经验统一收束到同一个协同工作台。
            </p>
            <div class="mt-6 flex flex-wrap gap-3">
              <a-tag
                v-for="tag in heroTags"
                :key="tag"
                color="arcoblue"
                bordered
                class="!rounded-full"
              >
                {{ tag }}
              </a-tag>
            </div>
          </div>
          <div class="grid w-full min-w-0 gap-3 sm:grid-cols-3 xl:w-[560px]">
            <div class="rounded-2xl border border-gold-dim bg-white/60 px-4 py-4 shadow-sm">
              <div class="text-xs text-abyss-400">会诊资产</div>
              <div class="mt-2 text-3xl font-bold text-abyss-800">
                {{
                  (
                    overview.summary.total_apps +
                    overview.summary.total_datasets +
                    overview.summary.total_workflows
                  ).toLocaleString()
                }}
              </div>
              <div class="mt-1 text-sm text-abyss-500">当前工作区内的应用、知识库与工作流</div>
            </div>
            <div class="rounded-2xl border border-gold-dim bg-white/60 px-4 py-4 shadow-sm">
              <div class="text-xs text-abyss-400">已发布资源</div>
              <div class="mt-2 text-3xl font-bold text-abyss-800">
                {{
                  (
                    overview.summary.published_apps + overview.summary.published_workflows
                  ).toLocaleString()
                }}
              </div>
              <div class="mt-1 text-sm text-abyss-500">已发布的会诊应用和工作流</div>
            </div>
            <div class="rounded-2xl border border-gold-dim bg-white/60 px-4 py-4 shadow-sm">
              <div class="text-xs text-abyss-400">证据命中</div>
              <div class="mt-2 text-3xl font-bold text-abyss-800">
                {{ overview.summary.dataset_hit_count.toLocaleString() }}
              </div>
              <div class="mt-1 text-sm text-abyss-500">知识库中累计的证据命中次数</div>
            </div>
          </div>
        </div>
      </section>

      <section
        class="grid min-w-0 items-start gap-6 lg:grid-cols-[minmax(0,1.45fr)_minmax(340px,0.85fr)]"
      >
        <div class="flex min-h-0 min-w-0 flex-col gap-6 self-stretch">
          <div
            class="glass metal-border shadow-glass min-h-0 min-w-0 rounded-[28px] p-4 md:p-6 flex flex-col overflow-hidden"
          >
            <div
              class="flex flex-col gap-4 border-b border-gold-dim pb-4 md:flex-row md:items-center md:justify-between"
            >
              <div>
                <div class="text-xs uppercase tracking-[0.28em] text-abyss-400">会诊编排</div>
                <div class="mt-1 text-xl font-bold text-abyss-800">协同推理与响应</div>
              </div>
              <div class="flex flex-wrap items-center gap-2">
                <a-tag color="green" bordered>在线会诊</a-tag>
                <a-tag color="gold" bordered>Graph RAG</a-tag>
                <a-tag color="arcoblue" bordered>多智能体</a-tag>
              </div>
            </div>

            <div
              v-if="messages.length > 0"
              class="mt-4 flex min-h-[420px] flex-1 min-w-0 flex-col overflow-hidden"
            >
              <div
                ref="scroller"
                @scroll="handleScroll"
                class="consult-message-scroll min-h-0 flex-1 overflow-y-auto overflow-x-hidden pr-3"
              >
                <div
                  v-for="item in messages.slice().reverse()"
                  :key="item.id || item.created_at || item.query"
                  class="flex flex-col gap-6 py-6"
                >
                  <human-message :query="item.query" :account="accountStore.account" />
                  <ai-message
                    :agent_thoughts="item.agent_thoughts"
                    :answer="item.answer"
                    :app="{ name: '医脉天枢' }"
                    :suggested_questions="item.id === message_id ? suggested_questions : []"
                    :loading="item.id === message_id && assistantAgentChatLoading"
                    :latency="item.latency"
                    :total_token_count="item.total_token_count"
                    message_class="!bg-parchment-100"
                    @select-suggested-question="handleSubmitQuestion"
                  />
                </div>
              </div>

            </div>

            <div v-else class="mt-4 flex min-h-0 flex-1 min-w-0 flex-col gap-6 overflow-hidden">
              <div class="grid min-h-0 flex-1 min-w-0 gap-4 overflow-hidden lg:grid-cols-[minmax(0,1.1fr)_minmax(320px,0.9fr)]">
                <div class="rounded-[24px] border border-gold-dim bg-white/70 p-5">
                  <div class="text-sm font-medium text-abyss-400">今日会诊提示</div>
                  <div class="mt-2 text-2xl font-bold text-abyss-800">
                    输入病例摘要后，系统会自动组织专科智能体、检索证据，并生成可追溯建议。
                  </div>
                  <p class="mt-3 leading-7 text-abyss-500">
                    你可以直接描述主诉、检查结果、诊断目标或会诊诉求。系统会将上下文分发给
                    合适的智能体，并汇总成结构化会诊意见。
                  </p>
                </div>
                <div
                  class="rounded-[24px] border border-gold-dim bg-white/70 p-5 min-h-0 h-full overflow-y-auto pr-2"
                >
                  <div class="text-sm font-medium text-abyss-400">推荐起手场景</div>
                  <div class="mt-4 flex flex-col gap-2">
                    <button
                      v-for="question in overview.recommended_actions.length > 0
                        ? overview.recommended_actions
                        : openingQuestions"
                      :key="question"
                      class="rounded-xl border border-gold-dim bg-parchment-100 px-4 py-3 text-left text-sm leading-6 text-abyss-600 transition-all hover:border-gold-bright hover:bg-gold-50"
                      @click="handleSubmitQuestion(question)"
                    >
                      {{ question }}
                    </button>
                  </div>

                  <div class="mt-5 grid gap-4">
                    <div
                      v-for="item in orchestrationLayers"
                      :key="item.title"
                      class="rounded-2xl border border-gold-dim bg-white/70 p-4"
                    >
                      <div class="text-sm font-semibold text-abyss-800">{{ item.title }}</div>
                      <div class="mt-2 text-sm leading-6 text-abyss-500">{{ item.desc }}</div>
                    </div>
                  </div>

                  <div class="mt-5 rounded-[24px] border border-gold-dim bg-white/70 p-5">
                    <div class="text-sm font-medium text-abyss-400">Graph RAG 证据网</div>
                    <div class="mt-4 grid gap-3 md:grid-cols-3">
                      <div
                        v-for="item in ragHighlights"
                        :key="item.label"
                        class="rounded-2xl border border-gold-dim bg-parchment-100 px-4 py-4"
                      >
                        <div class="text-xs uppercase tracking-[0.2em] text-abyss-400">
                          {{ item.label }}
                        </div>
                        <div class="mt-2 text-lg font-semibold text-abyss-800">
                          {{ item.value }}
                        </div>
                      </div>
                    </div>
                  </div>

                  <div class="mt-5 rounded-[24px] border border-gold-dim bg-white/70 p-5">
                    <div class="text-sm font-medium text-abyss-400">快速启动</div>
                    <div class="mt-4 flex flex-wrap gap-2">
                      <a-tag
                        v-for="scenario in quickScenarios"
                        :key="scenario"
                        color="gold"
                        bordered
                        class="cursor-pointer !rounded-full"
                        @click="handleSubmitQuestion(scenario)"
                      >
                        {{ scenario }}
                      </a-tag>
                    </div>
                  </div>

                  <div class="mt-5 rounded-[24px] border border-gold-dim bg-white/70 p-5">
                    <div class="text-sm font-medium text-abyss-400">近期资产</div>
                    <div class="mt-4 flex flex-col gap-4">
                      <div>
                        <div class="text-sm font-semibold text-abyss-800">会诊应用</div>
                        <div class="mt-2 flex flex-col gap-2">
                          <div
                            v-for="item in overview.recent_items.apps.slice(0, 2)"
                            :key="item.id"
                            class="rounded-2xl border border-gold-dim bg-parchment-100 px-4 py-3"
                          >
                            <div class="text-sm font-medium text-abyss-800">{{ item.name }}</div>
                            <div class="mt-1 text-xs text-abyss-500">
                              {{ item.description || '暂无描述' }}
                            </div>
                          </div>
                        </div>
                      </div>
                      <div>
                        <div class="text-sm font-semibold text-abyss-800">知识库</div>
                        <div class="mt-2 flex flex-col gap-2">
                          <div
                            v-for="item in overview.recent_items.datasets.slice(0, 2)"
                            :key="item.id"
                            class="rounded-2xl border border-gold-dim bg-parchment-100 px-4 py-3"
                          >
                            <div class="text-sm font-medium text-abyss-800">{{ item.name }}</div>
                            <div class="mt-1 text-xs text-abyss-500">
                              {{ item.document_count }} 篇文档 · {{ item.hit_count }} 次命中
                            </div>
                          </div>
                        </div>
                      </div>
                      <div>
                        <div class="text-sm font-semibold text-abyss-800">工作流</div>
                        <div class="mt-2 flex flex-col gap-2">
                          <div
                            v-for="item in overview.recent_items.workflows.slice(0, 2)"
                            :key="item.id"
                            class="rounded-2xl border border-gold-dim bg-parchment-100 px-4 py-3"
                          >
                            <div class="text-sm font-medium text-abyss-800">{{ item.name }}</div>
                            <div class="mt-1 text-xs text-abyss-500">
                              {{ item.description || '暂无描述' }}
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

            </div>

            <div class="mt-4 flex w-full flex-col gap-4 border-t border-gold-dim pt-4">
              <div
                v-if="task_id && assistantAgentChatLoading"
                class="flex h-[50px] shrink-0 items-center justify-center"
              >
                <a-button
                  :loading="stopAssistantAgentChatLoading"
                  class="rounded-lg px-2 !border-gold-dim !text-abyss-600 hover:!border-gold-bright hover:!text-gold-500"
                  @click="handleStop"
                >
                  <template #icon>
                    <icon-poweroff />
                  </template>
                  停止会诊
                </a-button>
              </div>

              <div class="flex items-center gap-3">
                <a-button
                  :loading="deleteAssistantAgentConversationLoading"
                  class="flex-shrink-0 !text-abyss-400 hover:!text-gold-500"
                  type="text"
                  shape="circle"
                  @click="
                    async () => {
                      await handleStop()
                      await handleDeleteAssistantAgentConversation()
                      await loadAssistantAgentMessages(true)
                    }
                  "
                >
                  <template #icon>
                    <icon-empty :size="16" />
                  </template>
                </a-button>
                <div
                  class="glass h-[50px] flex items-center gap-2 px-4 flex-1 border border-gold-dim rounded-full shadow-gold-sm hover:shadow-gold-md transition-shadow"
                >
                  <input
                    v-model="query"
                    type="text"
                    class="flex-1 outline-0 bg-transparent text-abyss-700 placeholder:text-abyss-300"
                    placeholder="请输入病例摘要、检查结果或会诊目标"
                    @keyup.enter="handleSubmit"
                  />
                  <a-button
                    :loading="assistantAgentChatLoading"
                    type="text"
                    shape="circle"
                    class="!text-gold-500 hover:!text-gold-600"
                    @click="handleSubmit"
                  >
                    <template #icon>
                      <icon-send :size="16" />
                    </template>
                  </a-button>
                </div>
              </div>
              <div class="text-center text-abyss-300 text-xs">
                AI 生成的会诊建议仅供辅助决策，最终仍需由临床团队结合实际情况复核。
              </div>
            </div>
          </div>
        </div>

        <div class="flex min-w-0 flex-col gap-6 self-stretch">
          <div class="glass metal-border shadow-glass rounded-[28px] p-5 flex-none">
            <div class="text-xs uppercase tracking-[0.28em] text-abyss-400">编排蓝图</div>
            <div class="mt-2 text-xl font-bold text-abyss-800">会诊任务如何被拆解与路由</div>
            <div class="mt-5 flex flex-col gap-3">
              <div
                v-for="(item, index) in orchestrationLayers"
                :key="item.title"
                class="rounded-2xl border border-gold-dim bg-parchment-100 px-4 py-4"
              >
                <div class="flex items-center gap-3">
                  <div
                    class="flex h-8 w-8 items-center justify-center rounded-full bg-gold-50 text-sm font-bold text-gold-600"
                  >
                    0{{ index + 1 }}
                  </div>
                  <div>
                    <div class="font-semibold text-abyss-800">{{ item.title }}</div>
                    <div class="mt-1 text-sm leading-6 text-abyss-500">{{ item.desc }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="glass metal-border shadow-glass rounded-[28px] p-5 flex-none">
            <div class="text-xs uppercase tracking-[0.28em] text-abyss-400">Graph RAG</div>
            <div class="mt-2 text-xl font-bold text-abyss-800">证据网路与引用方式</div>
            <div class="mt-5 flex flex-col gap-3">
              <div class="rounded-2xl border border-gold-dim bg-white/70 p-4">
                <div class="text-sm font-semibold text-abyss-800">关系路径</div>
                <p class="mt-2 text-sm leading-6 text-abyss-500">
                  先梳理疾病、症状、检查与指南之间的关系，再叠加语义召回。
                </p>
              </div>
              <div class="rounded-2xl border border-gold-dim bg-white/70 p-4">
                <div class="text-sm font-semibold text-abyss-800">来源回链</div>
                <p class="mt-2 text-sm leading-6 text-abyss-500">
                  为每条建议保留来源路径、原文片段和命中节点，便于临床复核。
                </p>
              </div>
              <div class="rounded-2xl border border-gold-dim bg-white/70 p-4">
                <div class="text-sm font-semibold text-abyss-800">审校闸门</div>
                <p class="mt-2 text-sm leading-6 text-abyss-500">
                  高风险结论在最终输出前会进入人工复核队列。
                </p>
              </div>
            </div>
          </div>

          <div class="glass metal-border shadow-glass rounded-[28px] p-5 flex-none">
            <div class="text-xs uppercase tracking-[0.28em] text-abyss-400">启动场景</div>
            <div class="mt-2 text-xl font-bold text-abyss-800">最适合首批落地的场景</div>
            <div class="mt-5 flex flex-wrap gap-2">
              <a-tag
                v-for="scenario in quickScenarios"
                :key="scenario"
                color="arcoblue"
                bordered
                class="!rounded-full"
              >
                {{ scenario }}
              </a-tag>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
:deep(.home-page-scroll::-webkit-scrollbar) {
  display: block;
  width: 10px;
}

:deep(.home-page-scroll::-webkit-scrollbar-track) {
  background: rgba(212, 175, 55, 0.06);
  border-radius: 9999px;
}

:deep(.home-page-scroll::-webkit-scrollbar-thumb) {
  background: linear-gradient(180deg, rgba(212, 175, 55, 0.72), rgba(196, 155, 42, 0.92));
  border: 2px solid rgba(248, 245, 240, 0.85);
  border-radius: 9999px;
}

:deep(.home-page-scroll::-webkit-scrollbar-thumb:hover) {
  background: linear-gradient(180deg, rgba(230, 199, 110, 0.96), rgba(212, 175, 55, 0.96));
}

:deep(.consult-message-scroll) {
  min-height: 0;
  height: 100%;
  max-height: 560px;
  display: block;
  overflow-y: scroll !important;
  scrollbar-gutter: stable both-edges;
  overscroll-behavior: contain;
}

:deep(.consult-message-scroll::-webkit-scrollbar) {
  display: block;
  width: 10px;
}

:deep(.consult-message-scroll::-webkit-scrollbar-track) {
  background: rgba(212, 175, 55, 0.06);
  border-radius: 9999px;
}

:deep(.consult-message-scroll::-webkit-scrollbar-thumb) {
  background: linear-gradient(180deg, rgba(212, 175, 55, 0.72), rgba(196, 155, 42, 0.92));
  border: 2px solid rgba(248, 245, 240, 0.85);
  border-radius: 9999px;
}

:deep(.consult-message-scroll::-webkit-scrollbar-thumb:hover) {
  background: linear-gradient(180deg, rgba(230, 199, 110, 0.96), rgba(212, 175, 55, 0.96));
}
</style>
