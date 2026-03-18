<script setup lang="ts">
import { type PropType, ref } from 'vue'
import type { MultiAgentConfig, SubAgentConfig } from '@/models/app'
import { useUpdateDraftAppConfig } from '@/hooks/use-app'
import { Message } from '@arco-design/web-vue'

// 1.定义自定义组件所需数据
const props = defineProps({
  app_id: { type: String, default: '', required: true },
  multi_agent_config: {
    type: Object as PropType<MultiAgentConfig>,
    default: () => ({ enable: false, sub_agents: [] }),
    required: true,
  },
})
const emits = defineEmits(['update:multi_agent_config'])
const { loading: updateDraftAppConfigLoading, handleUpdateDraftAppConfig } =
  useUpdateDraftAppConfig()

// 2.子Agent编辑模态窗数据
const subAgentModalVisible = ref(false)
const editingIdx = ref(-1) // -1 代表新增
const subAgentForm = ref<Record<string, any>>({
  name: '',
  description: '',
  model_config: { provider: 'tongyi', model: 'qwen-plus', parameters: {} },
  preset_prompt: '',
  tools: [],
  workflows: [],
  datasets: [],
  max_iteration_count: 5,
})

// 3.开关多Agent模式
const handleToggleEnable = async (enable: boolean) => {
  const newConfig = { ...props.multi_agent_config, enable }
  // 启用时至少需要2个子Agent
  if (enable && newConfig.sub_agents.length < 2) {
    Message.warning('启用多智能体模式至少需要配置2个子Agent')
    return
  }
  await handleUpdateDraftAppConfig(props.app_id, { multi_agent_config: newConfig })
  emits('update:multi_agent_config', newConfig)
}

// 4.显示新增/编辑子Agent模态窗
const handleShowSubAgentModal = (idx: number = -1) => {
  editingIdx.value = idx
  if (idx >= 0) {
    const sa = props.multi_agent_config.sub_agents[idx]
    subAgentForm.value = {
      name: sa.name,
      description: sa.description,
      model_config: { ...sa.model_config },
      preset_prompt: sa.preset_prompt || '',
      tools: sa.tools || [],
      workflows: sa.workflows || [],
      datasets: sa.datasets || [],
      max_iteration_count: sa.max_iteration_count || 5,
    }
  } else {
    subAgentForm.value = {
      name: '',
      description: '',
      model_config: { provider: 'tongyi', model: 'qwen-plus', parameters: {} },
      preset_prompt: '',
      tools: [],
      workflows: [],
      datasets: [],
      max_iteration_count: 5,
    }
  }
  subAgentModalVisible.value = true
}

// 5.保存子Agent
const handleSaveSubAgent = async () => {
  // 校验必填字段
  if (!subAgentForm.value.name.trim()) {
    Message.warning('子Agent名称不能为空')
    return
  }
  if (!subAgentForm.value.description.trim()) {
    Message.warning('子Agent描述不能为空')
    return
  }
  // 校验名称唯一性
  const existingNames = props.multi_agent_config.sub_agents
    .filter((_: any, i: number) => i !== editingIdx.value)
    .map((sa: SubAgentConfig) => sa.name)
  if (existingNames.includes(subAgentForm.value.name.trim())) {
    Message.warning('子Agent名称已存在，请使用唯一名称')
    return
  }

  const newSubAgents = [...props.multi_agent_config.sub_agents]
  const subAgent: SubAgentConfig = {
    name: subAgentForm.value.name.trim(),
    description: subAgentForm.value.description.trim(),
    model_config: subAgentForm.value.model_config,
    preset_prompt: subAgentForm.value.preset_prompt,
    tools: subAgentForm.value.tools,
    workflows: subAgentForm.value.workflows,
    datasets: subAgentForm.value.datasets,
    max_iteration_count: subAgentForm.value.max_iteration_count,
  }

  if (editingIdx.value >= 0) {
    newSubAgents[editingIdx.value] = subAgent
  } else {
    if (newSubAgents.length >= 5) {
      Message.warning('子Agent数量不能超过5个')
      return
    }
    newSubAgents.push(subAgent)
  }

  const newConfig = { ...props.multi_agent_config, sub_agents: newSubAgents }
  await handleUpdateDraftAppConfig(props.app_id, { multi_agent_config: newConfig })
  emits('update:multi_agent_config', newConfig)
  subAgentModalVisible.value = false
}

// 6.删除子Agent
const handleDeleteSubAgent = async (idx: number) => {
  const newSubAgents = [...props.multi_agent_config.sub_agents]
  newSubAgents.splice(idx, 1)

  // 如果删除后少于2个且已开启，自动关闭
  const enable = newSubAgents.length >= 2 ? props.multi_agent_config.enable : false

  const newConfig = { enable, sub_agents: newSubAgents }
  await handleUpdateDraftAppConfig(props.app_id, { multi_agent_config: newConfig })
  emits('update:multi_agent_config', newConfig)
}
</script>

<template>
  <div class="">
    <!-- 折叠面板 -->
    <a-collapse-item key="multi_agent" class="app-ability-item">
      <template #header>
        <div class="text-gray-700 font-bold">多智能体协作</div>
      </template>
      <template #extra>
        <a-switch
          :model-value="props.multi_agent_config.enable"
          size="small"
          @click.stop
          @change="(val: any) => handleToggleEnable(val as boolean)"
        />
      </template>
      <!-- 子Agent列表 -->
      <div class="flex flex-col gap-2">
        <div class="text-xs text-gray-500 leading-[22px] mb-1">
          配置多个专业子Agent，由Supervisor智能调度器自动分析用户意图并分配给最合适的子Agent执行。
        </div>
        <!-- 已配置的子Agent -->
        <div
          v-for="(sa, idx) in props.multi_agent_config.sub_agents"
          :key="sa.name"
          class="flex items-center justify-between bg-white p-3 rounded-lg cursor-pointer hover:shadow-sm group"
        >
          <div class="flex items-center gap-2">
            <div
              class="w-9 h-9 rounded flex items-center justify-center bg-blue-50 text-blue-700 flex-shrink-0 font-bold text-sm"
            >
              {{ sa.name.charAt(0).toUpperCase() }}
            </div>
            <div class="flex flex-col gap-1 h-9">
              <div class="text-gray-700 font-bold leading-[18px] line-clamp-1 break-all">
                {{ sa.name }}
              </div>
              <div class="text-gray-500 text-xs line-clamp-1 break-all">
                {{ sa.description }}
              </div>
            </div>
          </div>
          <div class="hidden group-hover:flex items-center gap-1 flex-shrink-0 ml-2">
            <a-button
              size="mini"
              type="text"
              class="!text-gray-700 rounded"
              @click="handleShowSubAgentModal(idx)"
            >
              <template #icon>
                <icon-settings />
              </template>
            </a-button>
            <a-button
              :loading="updateDraftAppConfigLoading"
              size="mini"
              type="text"
              class="!text-red-700 rounded"
              @click="handleDeleteSubAgent(idx)"
            >
              <template #icon>
                <icon-delete />
              </template>
            </a-button>
          </div>
        </div>
        <!-- 添加子Agent按钮 -->
        <a-button
          long
          type="dashed"
          class="rounded-lg"
          :disabled="props.multi_agent_config.sub_agents.length >= 5"
          @click="handleShowSubAgentModal(-1)"
        >
          <template #icon>
            <icon-plus />
          </template>
          添加子Agent
        </a-button>
      </div>
    </a-collapse-item>
    <!-- 子Agent设置模态窗 -->
    <a-modal
      v-model:visible="subAgentModalVisible"
      :title="editingIdx >= 0 ? '编辑子Agent' : '添加子Agent'"
      :ok-loading="updateDraftAppConfigLoading"
      @ok="handleSaveSubAgent"
      @cancel="subAgentModalVisible = false"
    >
      <a-form :model="subAgentForm" layout="vertical">
        <a-form-item field="name" label="名称" required>
          <a-input
            v-model="subAgentForm.name"
            placeholder="唯一标识，如 code_expert"
            :max-length="30"
          />
        </a-form-item>
        <a-form-item field="description" label="能力描述" required>
          <a-textarea
            v-model="subAgentForm.description"
            placeholder="描述该子Agent擅长处理什么类型的问题（Supervisor据此选择）"
            :max-length="500"
            :auto-size="{ minRows: 2, maxRows: 4 }"
          />
        </a-form-item>
        <a-form-item field="model_config.provider" label="模型提供商">
          <a-input
            v-model="subAgentForm.model_config.provider"
            placeholder="如 openai"
          />
        </a-form-item>
        <a-form-item field="model_config.model" label="模型名称">
          <a-input
            v-model="subAgentForm.model_config.model"
            placeholder="如 qwen-plus"
          />
        </a-form-item>
        <a-form-item field="preset_prompt" label="预设提示词">
          <a-textarea
            v-model="subAgentForm.preset_prompt"
            placeholder="该子Agent的角色定义和行为规范"
            :max-length="2000"
            :auto-size="{ minRows: 2, maxRows: 6 }"
          />
        </a-form-item>
        <a-form-item field="max_iteration_count" label="最大迭代次数">
          <a-slider
            v-model="subAgentForm.max_iteration_count"
            :min="1"
            :max="20"
            :step="1"
            show-input
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>
