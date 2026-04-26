<script setup lang="ts">
import moment from 'moment/moment'
import { onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useAccountStore } from '@/stores/account'
import { useDeleteWorkflow, useGetWorkflowsWithPage } from '@/hooks/use-workflow'
import CreateOrUpdateWorkflowModal from '@/views/space/workflows/components/CreateOrUpdateWorkflowModal.vue'
// import {
//   useAddBuiltinWorkflowToSpace,
//   useGetBuiltinWorkflows,
// } from '@/hooks/use-builtin-workflow'

const route = useRoute()
const props = defineProps({
  createType: { type: String, default: '', required: true },
})
const emits = defineEmits(['update:create-type'])

const createOrUpdateWorkflowModalVisible = ref(false)
const updateWorkflowId = ref('')
const accountStore = useAccountStore()

const {
  loading: getWorkflowsWithPageLoading,
  workflows,
  paginator,
  loadWorkflows,
} = useGetWorkflowsWithPage()

const { handleDeleteWorkflow } = useDeleteWorkflow()
// const { workflows: builtinWorkflows, loadBuiltinWorkflows } = useGetBuiltinWorkflows()
// const { handleAddBuiltinWorkflowToSpace } = useAddBuiltinWorkflowToSpace()
// const recommendedWorkflows = ref<typeof builtinWorkflows.value>([])

const handleScroll = async (event: UIEvent) => {
  const { scrollTop, scrollHeight, clientHeight } = event.target as HTMLElement

  if (scrollTop + clientHeight >= scrollHeight - 10) {
    if (getWorkflowsWithPageLoading.value) return
    await loadWorkflows(String(route.query?.search_word ?? ''), '')
  }
}

onMounted(async () => {
  await loadWorkflows(String(route.query?.search_word ?? ''), '', true)
  // 暂时省略“推荐模板”
  // await loadBuiltinWorkflows()
  // recommendedWorkflows.value = builtinWorkflows.value.slice(0, 6)
})

watch(
  () => props.createType,
  (newValue) => {
    if (newValue === 'workflow') {
      updateWorkflowId.value = ''
      createOrUpdateWorkflowModalVisible.value = true
      emits('update:create-type', '')
    }
  },
)

watch(
  () => route.query?.search_word,
  async () => await loadWorkflows(String(route.query?.search_word ?? ''), '', true),
)
</script>

<template>
  <a-spin
    :loading="getWorkflowsWithPageLoading"
    class="block h-full w-full scrollbar-w-none overflow-scroll"
    @scroll="handleScroll"
  >
    <!-- 暂时省略“推荐模板”区域
    <div v-if="recommendedWorkflows.length > 0" class="mb-6">
      <div class="flex items-center justify-between mb-3">
        <div class="text-base font-medium text-gray-900">推荐模板</div>
        <router-link to="/store/workflows" class="text-sm text-blue-600 hover:text-blue-700">
          查看更多 &rarr;
        </router-link>
      </div>
      <div class="flex gap-4 overflow-x-auto pb-2 scrollbar-w-none">
        <a-card
          v-for="tmpl in recommendedWorkflows"
          :key="tmpl.id"
          hoverable
          class="cursor-pointer rounded-lg flex-shrink-0 w-[240px]"
          @click="async () => await handleAddBuiltinWorkflowToSpace(tmpl.id)"
        >
          <div class="flex items-center gap-2 mb-2">
            <a-avatar :size="32" shape="square" class="bg-blue-100">
              <icon-mind-mapping class="text-blue-700" />
            </a-avatar>
            <div class="flex flex-col flex-1 min-w-0">
              <div class="text-sm font-bold text-gray-900 truncate">{{ tmpl.name }}</div>
              <div class="text-xs text-gray-400">{{ tmpl.node_count }} 节点</div>
            </div>
          </div>
          <div class="text-xs text-gray-500 line-clamp-2 h-[32px]">
            {{ tmpl.description }}
          </div>
        </a-card>
      </div>
    </div>
    -->

    <a-row :gutter="[20, 20]" class="flex-1">
      <a-col v-for="workflow in workflows" :key="workflow.id" :span="6">
        <a-card hoverable class="cursor-pointer rounded-lg">
          <div class="flex items-center gap-3 mb-3">
            <a-avatar :size="40" shape="square" :image-url="workflow.icon" />
            <div class="flex flex-1 justify-between">
              <div class="flex flex-col">
                <router-link
                  :to="{
                    name: 'space-workflows-detail',
                    params: { workflow_id: workflow.id },
                  }"
                  class="text-base text-gray-900 font-bold"
                >
                  {{ workflow.name }}
                  <icon-check-circle-fill
                    v-if="workflow.status === 'published'"
                    class="text-green-700"
                  />
                </router-link>
                <div class="text-xs text-gray-500 line-clamp-1">
                  {{ workflow.tool_call_name }} · {{ workflow.node_count }} 节点
                </div>
              </div>

              <a-dropdown position="br">
                <a-button type="text" size="small" class="rounded-lg !text-gray-700">
                  <template #icon>
                    <icon-more />
                  </template>
                </a-button>
                <template #content>
                  <a-doption
                    @click="
                      () => {
                        updateWorkflowId = workflow.id
                        createOrUpdateWorkflowModalVisible = true
                      }
                    "
                  >
                    编辑工作流
                  </a-doption>
                  <a-doption
                    class="text-red-700"
                    @click="
                      async () =>
                        await handleDeleteWorkflow(workflow.id, async () => {
                          await loadWorkflows(String(route.query?.search_word ?? ''), '', true)
                        })
                    "
                  >
                    删除
                  </a-doption>
                </template>
              </a-dropdown>
            </div>
          </div>

          <div class="leading-[18px] text-gray-500 h-[72px] line-clamp-4 mb-2 break-all">
            {{ workflow.description }}
          </div>

          <div class="flex items-center gap-1.5">
            <a-avatar :size="18" class="bg-blue-700">
              <icon-user />
            </a-avatar>
            <div class="text-xs text-gray-400">
              {{ accountStore.account.name }} · 最近编辑
              {{ moment(workflow.created_at * 1000).format('MM-DD HH:mm') }}
            </div>
          </div>
        </a-card>
      </a-col>

      <a-col v-if="workflows.length === 0" :span="24">
        <a-empty
          description="没有可用的工作流"
          class="h-[400px] flex flex-col items-center justify-center"
        />
      </a-col>
    </a-row>

    <a-row v-if="paginator.total_page >= 2">
      <a-col v-if="paginator.current_page <= paginator.total_page" :span="24" align="center">
        <a-space class="my-4">
          <a-spin />
          <div class="text-gray-400">加载中</div>
        </a-space>
      </a-col>
      <a-col v-else :span="24" align="center">
        <div class="text-gray-400 my-4">数据已加载完成</div>
      </a-col>
    </a-row>

    <create-or-update-workflow-modal
      v-model:visible="createOrUpdateWorkflowModalVisible"
      v-model:workflow_id="updateWorkflowId"
      :callback="async () => await loadWorkflows(String(route.query?.search_word ?? ''), '', true)"
    />
  </a-spin>
</template>

<style scoped></style>
