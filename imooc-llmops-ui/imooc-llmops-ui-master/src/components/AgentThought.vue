<script setup lang="ts">
import { type PropType, ref } from 'vue'
import { QueueEvent } from '@/config'

// 1.定义自定义组件所需数据
const props = defineProps({
  loading: { type: Boolean, default: false, required: true },
  agent_thoughts: {
    type: Array as PropType<Record<string, any>[]>,
    default: () => [],
    required: true,
  },
})
const visible = ref(false)
</script>

<template>
  <!-- 智能体推理步骤 -->
  <div :class="`flex flex-col rounded-2xl border border-gold-dim ${visible ? 'w-[360px]' : 'w-[180px]'}`">
    <div
      :class="`flex items-center justify-between h-10 rounded-2xl bg-gold-50 px-4 text-abyss-600 cursor-pointer w-auto transition-all ${visible ? 'rounded-bl-none rounded-br-none' : ''}`"
      @click="visible = !visible"
    >
      <!-- 左侧图标与标题 -->
      <div class="flex items-center gap-2">
        <icon-list class="text-gold-500" />
        {{ visible ? '隐藏' : '显示' }}运行流程
      </div>
      <!-- 右侧图标 -->
      <div class="text-gold-500">
        <template v-if="props.loading">
          <icon-loading />
        </template>
        <template v-else>
          <icon-up v-if="visible" />
          <icon-down v-else />
        </template>
      </div>
    </div>
    <!-- 底部内容 -->
    <a-collapse class="agent-thought" v-if="visible" destroy-on-hide :bordered="false">
      <a-collapse-item
        v-for="agent_thought in props.agent_thoughts.filter((item: any) =>
          [
            QueueEvent.longTermMemoryRecall,
            QueueEvent.agentThought,
            QueueEvent.datasetRetrieval,
            QueueEvent.agentAction,
            QueueEvent.agentMessage,
            QueueEvent.agentDelegation,
            QueueEvent.subAgentEnd,
          ].includes(item.event),
        )"
        :key="agent_thought.id"
      >
        <template #expand-icon>
          <icon-file v-if="agent_thought.event === QueueEvent.longTermMemoryRecall" class="text-gold-500" />
          <icon-language v-else-if="agent_thought.event === QueueEvent.agentThought" class="text-gold-500" />
          <icon-storage v-else-if="agent_thought.event === QueueEvent.datasetRetrieval" class="text-gold-500" />
          <icon-tool v-else-if="agent_thought.event === QueueEvent.agentAction" class="text-gold-500" />
          <icon-message v-else-if="agent_thought.event === QueueEvent.agentMessage" class="text-gold-500" />
          <icon-swap v-else-if="agent_thought.event === QueueEvent.agentDelegation" class="text-gold-500" />
          <icon-check-circle v-else-if="agent_thought.event === QueueEvent.subAgentEnd" class="text-gold-500" />
        </template>
        <template #header>
          <div class="text-abyss-600" v-if="agent_thought.event === QueueEvent.longTermMemoryRecall">
            {{ agent_thought.sub_agent_name ? `[${agent_thought.sub_agent_name}] ` : '' }}长期记忆召回
          </div>
          <div class="text-abyss-600" v-if="agent_thought.event === QueueEvent.agentThought">
            {{ agent_thought.sub_agent_name ? `[${agent_thought.sub_agent_name}] ` : '' }}智能体推理
          </div>
          <div class="text-abyss-600" v-if="agent_thought.event === QueueEvent.datasetRetrieval">
            {{ agent_thought.sub_agent_name ? `[${agent_thought.sub_agent_name}] ` : '' }}搜索知识库
          </div>
          <div class="text-abyss-600" v-if="agent_thought.event === QueueEvent.agentAction">
            {{ agent_thought.sub_agent_name ? `[${agent_thought.sub_agent_name}] ` : '' }}调用工具
          </div>
          <div class="text-abyss-600" v-if="agent_thought.event === QueueEvent.agentMessage">
            {{ agent_thought.sub_agent_name ? `[${agent_thought.sub_agent_name}] ` : '' }}智能体消息
          </div>
          <div class="text-abyss-600" v-if="agent_thought.event === QueueEvent.agentDelegation">
            调度子Agent: {{ agent_thought.sub_agent_name || agent_thought.tool }}
          </div>
          <div class="text-abyss-600" v-if="agent_thought.event === QueueEvent.subAgentEnd">
            {{ agent_thought.sub_agent_name }} 完成
          </div>
        </template>
        <template #extra>
          <div class="text-gold-600 text-xs">{{ agent_thought.latency.toFixed(2) }}s</div>
        </template>
        <div
          v-if="['agent_thought', 'agent_message', 'agent_delegation', 'sub_agent_end'].includes(agent_thought.event)"
          class="text-xs text-abyss-400 line-clamp-4 break-all"
        >
          {{ agent_thought.thought || '-' }}
        </div>
        <div v-else class="text-xs text-abyss-400 line-clamp-4 break-all">
          {{ agent_thought.observation || '-' }}
        </div>
      </a-collapse-item>
    </a-collapse>
  </div>
</template>

<style>
.agent-thought {
  .arco-collapse-item-content {
    padding: 0 16px;
  }
}
</style>
