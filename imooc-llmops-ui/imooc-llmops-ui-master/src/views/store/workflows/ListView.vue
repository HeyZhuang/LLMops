<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  useAddBuiltinWorkflowToSpace,
  useGetBuiltinWorkflowCategories,
  useGetBuiltinWorkflows,
} from '@/hooks/use-builtin-workflow'
import moment from 'moment/moment'

// 1.定义页面所需数据
const category = ref('all')
const search_word = ref('')
const { categories, loadBuiltinWorkflowCategories } = useGetBuiltinWorkflowCategories()
const {
  loading: getBuiltinWorkflowsLoading,
  workflows,
  loadBuiltinWorkflows,
} = useGetBuiltinWorkflows()
const { handleAddBuiltinWorkflowToSpace } = useAddBuiltinWorkflowToSpace()
const filterWorkflows = computed(() => {
  return workflows.value.filter((item) => {
    const matchCategory = category.value === 'all' || item.category === category.value
    const matchSearchWord =
      search_word.value === '' || item.name.toLowerCase().includes(search_word.value.toLowerCase())

    return matchCategory && matchSearchWord
  })
})

onMounted(() => {
  loadBuiltinWorkflowCategories()
  loadBuiltinWorkflows()
})
</script>

<template>
  <a-spin :loading="getBuiltinWorkflowsLoading" class="block h-full w-full">
    <div class="p-6 flex flex-col">
      <!-- 顶层标题 -->
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center gap-2">
          <a-avatar :size="32" class="bg-blue-700">
            <icon-mind-mapping :size="18" />
          </a-avatar>
          <div class="text-lg font-medium text-gray-900">编排工坊</div>
        </div>
      </div>
      <!-- 会诊编排分类+搜索框 -->
      <div class="flex items-center justify-between mb-6">
        <!-- 左侧分类 -->
        <div class="flex items-center gap-2">
          <a-button
            :type="category === 'all' ? 'secondary' : 'text'"
            class="rounded-lg !text-gray-700 px-3"
            @click="category = 'all'"
          >
            全部
          </a-button>
          <a-button
            v-for="item in categories"
            :key="item.category"
            :type="category === item.category ? 'secondary' : 'text'"
            class="rounded-lg !text-gray-700 px-3"
            @click="category = item.category"
          >
            {{ item.name }}
          </a-button>
        </div>
        <!-- 右侧搜索 -->
        <a-input-search
          v-model="search_word"
          placeholder="搜索编排模板"
          class="w-[240px] bg-white rounded-lg border-gray-300"
        />
      </div>
      <!-- 底部工作流模板列表 -->
      <a-row :gutter="[20, 20]" class="flex-1">
        <!-- 有数据的UI状态 -->
        <a-col v-for="workflow in filterWorkflows" :key="workflow.id" :span="6">
          <a-card hoverable class="cursor-pointer rounded-lg">
            <!-- 顶部工作流名称 -->
            <div class="flex items-center gap-3 mb-3">
              <!-- 左侧图标 -->
              <a-avatar :size="40" shape="square" class="bg-blue-100">
                <icon-mind-mapping class="text-blue-700" />
              </a-avatar>
              <!-- 右侧信息 -->
              <div class="flex flex-1 justify-between">
                <div class="flex flex-col">
                  <div class="text-base text-gray-900 font-bold">{{ workflow.name }}</div>
                  <div class="text-xs text-gray-500 line-clamp-1">
                    {{ workflow.tool_call_name }} · {{ workflow.node_count }} 节点数
                  </div>
                </div>
                <!-- 操作按钮 -->
                <a-dropdown position="br">
                  <a-button type="text" size="small" class="rounded-lg !text-gray-700">
                    <template #icon>
                      <icon-more />
                    </template>
                  </a-button>
                  <template #content>
                    <a-doption
                      @click="async () => await handleAddBuiltinWorkflowToSpace(workflow.id)"
                    >
                      加入会诊工作区
                    </a-doption>
                  </template>
                </a-dropdown>
              </div>
            </div>
            <!-- 描述信息 -->
            <div class="leading-[18px] text-gray-500 h-[72px] line-clamp-4 mb-2 break-all">
              {{ workflow.description }}
            </div>
            <!-- 归属者信息 -->
            <div class="flex items-center gap-1.5">
              <a-avatar :size="18" class="bg-blue-700">
                <icon-user />
              </a-avatar>
              <div class="text-xs text-gray-400">
                {{ workflow.author }} · 发布时间
                {{ moment(workflow.created_at * 1000).format('MM-DD HH:mm') }}
              </div>
            </div>
          </a-card>
        </a-col>
        <!-- 没数据的UI状态 -->
        <a-col v-if="filterWorkflows.length === 0" :span="24">
          <a-empty
            description="暂无可用的编排模板"
            class="h-[400px] flex flex-col items-center justify-center"
          />
        </a-col>
      </a-row>
    </div>
  </a-spin>
</template>

<style scoped></style>
