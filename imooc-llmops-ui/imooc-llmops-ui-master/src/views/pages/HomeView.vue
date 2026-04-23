<script setup lang="ts">
// @ts-ignore
import { DynamicScroller, DynamicScrollerItem } from 'vue-virtual-scroller'
import 'vue-virtual-scroller/dist/vue-virtual-scroller.css'
import { nextTick, onMounted, ref } from 'vue'
import {
  useAssistantAgentChat,
  useDeleteAssistantAgentConversation,
  useGetAssistantAgentMessagesWithPage,
  useStopAssistantAgentChat,
} from '@/hooks/use-assistant-agent'
import { useGenerateSuggestedQuestions } from '@/hooks/use-ai'
import { useAccountStore } from '@/stores/account'
import { Message } from '@arco-design/web-vue'
import { QueueEvent } from '@/config'
import HumanMessage from '@/components/HumanMessage.vue'
import AiMessage from '@/components/AiMessage.vue'

// 1.定义页面所需数据
const query = ref('')
const task_id = ref('')
const message_id = ref('')
const scroller = ref<any>(null)
const scrollHeight = ref(0)
const accountStore = useAccountStore()
const opening_questions = ['什么是LLMOps-Platform LLMOps?', '我想创建一个应用', '能介绍下什么是RAG吗?']
const { suggested_questions, handleGenerateSuggestedQuestions } = useGenerateSuggestedQuestions()
const { loading: assistantAgentChatLoading, handleAssistantAgentChat } = useAssistantAgentChat()
const {
  loading: stopAssistantAgentChatLoading,
  handleStopAssistantAgentChat,
} = useStopAssistantAgentChat()
const {
  loading: getAssistantAgentMessagesWithPageLoading,
  messages,
  loadAssistantAgentMessages,
} = useGetAssistantAgentMessagesWithPage()
const {
  loading: deleteAssistantAgentConversationLoading,
  handleDeleteAssistantAgentConversation,
} = useDeleteAssistantAgentConversation()

// 2.定义保存滚动高度函数
const saveScrollHeight = () => {
  scrollHeight.value = scroller.value.$el.scrollHeight
}

// 3.定义还原滚动高度函数
const restoreScrollPosition = () => {
  scroller.value.$el.scrollTop = scroller.value.$el.scrollHeight - scrollHeight.value
}

// 4.定义滚动函数
const handleScroll = async (event: UIEvent) => {
  const { scrollTop } = event.target as HTMLElement
  if (scrollTop <= 0 && !getAssistantAgentMessagesWithPageLoading.value) {
    saveScrollHeight()
    await loadAssistantAgentMessages(false)
    restoreScrollPosition()
  }
}

// 5.定义输入框提交函数
const handleSubmit = async () => {
  if (query.value.trim() === '') {
    Message.warning('用户提问不能为空')
    return
  }
  if (assistantAgentChatLoading.value) {
    Message.warning('上一次提问还未结束，请稍等')
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
            position: position,
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
        messages.value[0].answer = '当前Agent执行已超时，无法得到答案，请重试'
      } else {
        position += 1
        agent_thoughts.push({
          id: event_id,
          position: position,
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
      // 替换对象引用，触发 DynamicScroller 检测到 item 变化并重新渲染
      messages.value[0] = { ...messages.value[0] }
      nextTick(() => scroller.value?.scrollToBottom())
    }
  })
  await nextTick(() => {
    if (scroller.value) {
      scroller.value.scrollToBottom()
    }
  })
  // 延迟刷新消息列表，等待后端save线程完成数据库写入
  setTimeout(() => loadAssistantAgentMessages(true), 1500)
  if (message_id.value) {
    try {
      await handleGenerateSuggestedQuestions(message_id.value)
    } catch {
      // 建议问题生成失败不影响主流程
    }
    setTimeout(() => scroller.value && scroller.value.scrollToBottom(), 100)
  }
}

// 6.定义停止调试会话函数
const handleStop = async () => {
  if (task_id.value === '' || !assistantAgentChatLoading.value) return
  await handleStopAssistantAgentChat(task_id.value)
}

// 7.定义问题提交函数
const handleSubmitQuestion = async (question: string) => {
  query.value = question
  await handleSubmit()
}

// 8.页面DOM加载完毕时初始化数据
onMounted(async () => {
  await loadAssistantAgentMessages(true)
  await nextTick(() => {
    if (scroller.value) {
      scroller.value.scrollToBottom()
    }
  })
})
</script>

<template>
  <div class="w-full h-full min-h-screen linen-bg">
    <!-- 中间页面信息 -->
    <div class="w-[600px] h-full min-h-screen mx-auto">
      <!-- 历史对话列表 -->
      <div
        v-if="messages.length > 0"
        class="flex flex-col px-6 h-[calc(100%-100px)] min-h-[calc(100vh-100px)]"
      >
        <dynamic-scroller
          ref="scroller"
          :items="messages.slice().reverse()"
          :min-item-size="1"
          @scroll="handleScroll"
          class="h-full scrollbar-w-none"
        >
          <template v-slot="{ item, active }">
            <dynamic-scroller-item :item="item" :active="active" :data-index="item.id">
              <div class="flex flex-col gap-6 py-6">
                <human-message :query="item.query" :account="accountStore.account" />
                <ai-message
                  :agent_thoughts="item.agent_thoughts"
                  :answer="item.answer"
                  :app="{ name: '辅助Agent' }"
                  :suggested_questions="item.id === message_id ? suggested_questions : []"
                  :loading="item.id === message_id && assistantAgentChatLoading"
                  :latency="item.latency"
                  :total_token_count="item.total_token_count"
                  message_class="!bg-parchment-100"
                  @select-suggested-question="handleSubmitQuestion"
                />
              </div>
            </dynamic-scroller-item>
          </template>
        </dynamic-scroller>
        <!-- 停止调试会话 -->
        <div
          v-if="task_id && assistantAgentChatLoading"
          class="h-[50px] flex items-center justify-center"
        >
          <a-button
            :loading="stopAssistantAgentChatLoading"
            class="rounded-lg px-2 !border-gold-dim !text-abyss-600 hover:!border-gold-bright hover:!text-gold-500"
            @click="handleStop"
          >
            <template #icon>
              <icon-poweroff />
            </template>
            停止响应
          </a-button>
        </div>
      </div>
      <!-- 对话列表为空时展示的对话开场白 -->
      <div
        v-else
        class="flex flex-col p-6 gap-2 items-center justify-center overflow-scroll scrollbar-w-none h-[calc(100%-100px)] min-h-[calc(100vh-100px)]"
      >
        <div class="mb-9">
          <div class="text-[40px] font-bold text-abyss-800 mt-[52px] mb-4">
            Hi，我是LLMOps AI 应用构建器
          </div>
          <div class="text-[30px] font-bold text-abyss-700 mb-2">
            你的专属
            <span class="text-gold-shine">AI 原生应用</span>
            开发平台
          </div>
          <div class="text-base text-abyss-500">
            说出你的创意，我可以快速帮你创建专属应用，一键轻松分享给朋友，也可以一键发布到
            LLMOps 平台、微信等多个渠道。
          </div>
        </div>
        <!-- 开场AI对话消息 -->
        <div class="flex gap-2">
          <!-- 左侧图标 -->
          <a-avatar :size="30" shape="circle" class="flex-shrink-0 !bg-abyss-800 !text-gold-400">
            <icon-apps />
          </a-avatar>
          <!-- 右侧名称与消息 -->
          <div class="flex flex-col items-start gap-2">
            <!-- 应用名称 -->
            <div class="text-abyss-700 font-bold">辅助Agent</div>
            <!-- AI消息 -->
            <div
              class="glass metal-border text-abyss-700 px-4 py-3 rounded-2xl break-all leading-7"
            >
              <div class="font-bold">你好，欢迎来到 LLMOps</div>
              <div class="">
                LLMOps 是新一代大模型 AI 应用开发平台。无论你是否有编程基础，都可以快速搭建出各种
                AI 应用，并一键发布到各大社交平台，或者轻松部署到自己的网站。
              </div>
              <ul class="list-disc pl-6 mt-2">
                <li>
                  随时来
                  <router-link :to="{ name: 'store-apps-list' }" class="text-gold-500 hover:text-gold-600 font-medium"
                    >应用广场
                  </router-link>
                  逛逛，这里内置了许多超有趣的应用。
                </li>
                <li>你也可以直接发送"我想做一个应用"，我可以帮你快速创建应用。</li>
                <li>你也可以向我提问有关课程的问题，我可以快速替你解答。</li>
              </ul>
              <div class="mt-2">如果你还有其他 LLMOps 使用问题，也欢迎随时问我！</div>
            </div>
            <!-- 开场白建议问题 -->
            <div class="flex flex-col gap-2">
              <div
                v-for="(opening_question, idx) in opening_questions"
                :key="idx"
                class="px-4 py-1.5 border border-gold-dim rounded-lg text-abyss-600 cursor-pointer bg-parchment-100 hover:bg-gold-50 hover:border-gold-bright transition-all"
                @click="async () => await handleSubmitQuestion(opening_question)"
              >
                {{ opening_question }}
              </div>
            </div>
          </div>
        </div>
      </div>
      <!-- 对话输入框 -->
      <div class="w-full flex flex-col flex-shrink-0">
        <!-- 顶部输入框 -->
        <div class="px-6 flex items-center gap-4">
          <!-- 清除按钮 -->
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
          <!-- 输入框组件 -->
          <div
            class="glass h-[50px] flex items-center gap-2 px-4 flex-1 border border-gold-dim rounded-full shadow-gold-sm hover:shadow-gold-md transition-shadow"
          >
            <input
              v-model="query"
              type="text"
              class="flex-1 outline-0 bg-transparent text-abyss-700 placeholder:text-abyss-300"
              placeholder="发送消息或创建AI医疗应用..."
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
        <!-- 底部提示信息 -->
        <div class="text-center text-abyss-300 text-xs py-4">
          内容由AI生成，无法确保真实准确，仅供参考。
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped></style>
