<script setup lang="ts">
import { onMounted, ref } from 'vue'
import {
  useGetPromptTemplatesWithPage,
  useDeletePromptTemplate,
} from '@/hooks/use-prompt-template'
import moment from 'moment'
import CreateOrUpdateTemplateModal from './components/CreateOrUpdateTemplateModal.vue'
import TemplatePreviewModal from './components/TemplatePreviewModal.vue'

// 1.定义页面所需数据
const {
  loading: getTemplatesLoading,
  templates,
  paginator,
  loadTemplates,
} = useGetPromptTemplatesWithPage()
const { handleDeletePromptTemplate } = useDeletePromptTemplate()
const createOrUpdateModalVisible = ref(false)
const previewModalVisible = ref(false)
const editTemplateId = ref('')
const previewTemplate = ref<Record<string, any>>({})
const searchWord = ref('')

// 2.滚动分页
const handleScroll = async (event: UIEvent) => {
  const { scrollTop, scrollHeight, clientHeight } = event.target as HTMLElement
  if (scrollTop + clientHeight >= scrollHeight - 10) {
    if (getTemplatesLoading.value) return
    await loadTemplates(false, searchWord.value)
  }
}

// 3.搜索
const handleSearch = async () => {
  await loadTemplates(true, searchWord.value)
}

// 4.打开创建弹窗
const handleCreate = () => {
  editTemplateId.value = ''
  createOrUpdateModalVisible.value = true
}

// 5.打开编辑弹窗
const handleEdit = (id: string) => {
  editTemplateId.value = id
  createOrUpdateModalVisible.value = true
}

// 6.打开预览
const handlePreview = (template: Record<string, any>) => {
  previewTemplate.value = template
  previewModalVisible.value = true
}

onMounted(async () => {
  await loadTemplates(true)
})
</script>

<template>
  <div class="h-full flex flex-col p-5">
    <!-- 顶部操作栏 -->
    <div class="flex items-center justify-between mb-5">
      <div class="text-lg text-abyss-800 font-semibold">Prompt 模板库</div>
      <div class="flex items-center gap-3">
        <a-input-search
          v-model="searchWord"
          placeholder="搜索模板..."
          class="w-[240px]"
          @search="handleSearch"
          @press-enter="handleSearch"
        />
        <a-button type="primary" class="rounded-lg" @click="handleCreate">
          <template #icon><icon-plus /></template>
          创建模板
        </a-button>
      </div>
    </div>
    <!-- 模板列表 -->
    <a-spin
      :loading="getTemplatesLoading"
      class="block flex-1 overflow-scroll scrollbar-w-none"
      @scroll="handleScroll"
    >
      <a-row :gutter="[20, 20]">
        <a-col v-for="template in templates" :key="template.id" :span="6">
          <div class="glass metal-border rounded-xl p-5 cursor-pointer card-hover">
            <!-- 顶部信息 -->
            <div class="flex items-center justify-between mb-3">
              <div class="text-base text-abyss-800 font-bold line-clamp-1">{{ template.name }}</div>
              <a-dropdown position="br">
                <a-button type="text" size="small" class="rounded-lg !text-abyss-400 hover:!text-gold-400">
                  <template #icon><icon-more /></template>
                </a-button>
                <template #content>
                  <a-doption @click="handlePreview(template)">预览</a-doption>
                  <a-doption @click="handleEdit(template.id)">编辑</a-doption>
                  <a-doption
                    class="!text-red-400"
                    @click="handleDeletePromptTemplate(template.id, () => loadTemplates(true, searchWord))"
                  >
                    删除
                  </a-doption>
                </template>
              </a-dropdown>
            </div>
            <!-- 分类标签 -->
            <div v-if="template.category" class="mb-2">
              <a-tag size="small" color="gold">{{ template.category }}</a-tag>
              <a-tag v-if="template.is_public" size="small" color="blue" class="ml-1">公开</a-tag>
            </div>
            <!-- 描述 -->
            <div class="text-sm text-abyss-400 h-[54px] line-clamp-3 mb-3 break-all">
              {{ template.description || template.content }}
            </div>
            <!-- 金色分割线 -->
            <div class="divider-gold mb-3"></div>
            <!-- 底部信息 -->
            <div class="text-xs text-abyss-300">
              更新于 {{ moment(template.updated_at * 1000).format('MM-DD HH:mm') }}
            </div>
          </div>
        </a-col>
        <!-- 空状态 -->
        <a-col v-if="templates.length === 0 && !getTemplatesLoading" :span="24">
          <a-empty
            description="暂无模板，点击右上角创建"
            class="h-[400px] flex flex-col items-center justify-center"
          />
        </a-col>
      </a-row>
      <!-- 加载器 -->
      <a-row v-if="paginator.total_page >= 2">
        <a-col v-if="paginator.current_page <= paginator.total_page" :span="24" align="center">
          <a-space class="my-4">
            <a-spin />
            <div class="text-abyss-400">加载中</div>
          </a-space>
        </a-col>
        <a-col v-else :span="24" align="center">
          <div class="text-abyss-400 my-4">数据已加载完成</div>
        </a-col>
      </a-row>
    </a-spin>
    <!-- 创建/编辑弹窗 -->
    <create-or-update-template-modal
      v-model:visible="createOrUpdateModalVisible"
      v-model:template_id="editTemplateId"
      :callback="() => loadTemplates(true, searchWord)"
    />
    <!-- 预览弹窗 -->
    <template-preview-modal
      v-model:visible="previewModalVisible"
      :template="previewTemplate"
    />
  </div>
</template>

<style scoped>
.card-hover {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.card-hover:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(15,23,42,0.08), 0 0 0 1px rgba(212,175,55,0.15);
}
</style>
