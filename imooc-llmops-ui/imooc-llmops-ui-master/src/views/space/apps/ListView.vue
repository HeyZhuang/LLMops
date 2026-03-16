<script setup lang="ts">
import moment from 'moment/moment'
import { useCopyApp, useDeleteApp, useGetAppsWithPage } from '@/hooks/use-app'
import { onMounted, ref, watch } from 'vue'
import { useAccountStore } from '@/stores/account'
import CreateOrUpdateAppModal from './components/CreateOrUpdateAppModal.vue'
import { useRoute } from 'vue-router'

// 1.定义页面所需数据
const route = useRoute()
const props = defineProps({
  createType: { type: String, default: '', required: true },
})
const emits = defineEmits(['update:create-type'])
const createOrUpdateAppModalVisible = ref(false)
const updateAppId = ref('')
const accountStore = useAccountStore()
const { handleCopyApp } = useCopyApp()
const { loading: getAppsWithPageLoading, apps, paginator, loadApps } = useGetAppsWithPage()
const { handleDeleteApp } = useDeleteApp()

// 2.定义滚动数据分页处理器
const handleScroll = async (event: UIEvent) => {
  const { scrollTop, scrollHeight, clientHeight } = event.target as HTMLElement
  if (scrollTop + clientHeight >= scrollHeight - 10) {
    if (getAppsWithPageLoading.value) return
    await loadApps(false, String(route.query?.search_word ?? ''))
  }
}

// 页面DOM加载完毕后执行
onMounted(async () => {
  await loadApps(true, String(route.query?.search_word ?? ''))
})

watch(
  () => props.createType,
  (newValue) => {
    if (newValue === 'app') {
      updateAppId.value = ''
      createOrUpdateAppModalVisible.value = true
      emits('update:create-type', '')
    }
  },
)

watch(
  () => route.query?.search_word,
  (newValue) => loadApps(true, String(newValue)),
)

watch(
  () => route.query?.create_type,
  (newValue) => {
    if (newValue === 'app') {
      updateAppId.value = ''
      createOrUpdateAppModalVisible.value = true
    }
  },
  { immediate: true },
)
</script>

<template>
  <a-spin
    :loading="getAppsWithPageLoading"
    class="block h-full w-full scrollbar-w-none overflow-scroll"
    @scroll="handleScroll"
  >
    <!-- 底部应用列表 -->
    <a-row :gutter="[20, 20]" class="flex-1">
      <!-- 有数据的UI状态 -->
      <a-col v-for="app in apps" :key="app.id" :span="6">
        <div class="app-card glass metal-border rounded-xl p-5 cursor-pointer card-hover">
          <!-- 顶部应用名称 -->
          <div class="flex items-center gap-3 mb-3">
            <!-- 左侧图标 -->
            <a-avatar :size="40" shape="square" :image-url="app.icon" class="rounded-lg shadow-gold-sm" />
            <!-- 右侧App信息 -->
            <div class="flex flex-1 justify-between">
              <div class="flex flex-col">
                <router-link
                  :to="{
                    name: 'space-apps-detail',
                    params: { app_id: app.id },
                  }"
                  class="text-base text-abyss-800 font-bold hover:text-gold-500 transition-colors"
                >
                  {{ app.name }}
                  <icon-check-circle-fill
                    v-if="app.status === 'published'"
                    class="text-gold-400"
                  />
                </router-link>
                <div class="text-xs text-abyss-400 line-clamp-1">
                  {{ app.model_config.provider }} · {{ app.model_config.model }}
                </div>
              </div>
              <!-- 操作按钮 -->
              <a-dropdown position="br">
                <a-button type="text" size="small" class="rounded-lg !text-abyss-400 hover:!text-gold-400">
                  <template #icon>
                    <icon-more />
                  </template>
                </a-button>
                <template #content>
                  <router-link :to="{ name: 'space-apps-analysis', params: { app_id: app.id } }">
                    <a-doption>分析</a-doption>
                  </router-link>
                  <a-doption
                    @click="
                      () => {
                        updateAppId = app.id
                        createOrUpdateAppModalVisible = true
                      }
                    "
                  >
                    编辑应用
                  </a-doption>
                  <a-doption @click="async () => await handleCopyApp(app.id)">创建副本</a-doption>
                  <a-doption
                    class="!text-red-400"
                    @click="
                      () =>
                        handleDeleteApp(
                          app.id,
                          async () => await loadApps(true, String(route.query?.search_word ?? '')),
                        )
                    "
                  >
                    删除
                  </a-doption>
                </template>
              </a-dropdown>
            </div>
          </div>
          <!-- App的描述信息 -->
          <div class="leading-[18px] text-abyss-400 h-[72px] line-clamp-4 mb-3 break-all text-sm">
            {{ app.description.trim() === '' ? app.preset_prompt : app.description }}
          </div>
          <!-- 金色分割线 -->
          <div class="divider-gold mb-3"></div>
          <!-- 应用的归属者信息 -->
          <div class="flex items-center gap-1.5">
            <a-avatar :size="18" class="!bg-abyss-800 !text-gold-400 text-[10px]">
              <icon-user />
            </a-avatar>
            <div class="text-xs text-abyss-300">
              {{ accountStore.account.name }} · 最近编辑
              {{ moment(app.created_at * 1000).format('MM-DD HH:mm') }}
            </div>
          </div>
        </div>
      </a-col>
      <!-- 没数据的UI状态 -->
      <a-col v-if="apps.length === 0" :span="24">
        <a-empty
          description="没有可用的Agent智能体"
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
    <!-- 新建/修改模态窗 -->
    <create-or-update-app-modal
      v-model:visible="createOrUpdateAppModalVisible"
      v-model:app_id="updateAppId"
      :callback="() => loadApps(true, String(route.query?.search_word ?? ''))"
    />
  </a-spin>
</template>

<style scoped>
.app-card {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.app-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(15,23,42,0.08), 0 0 0 1px rgba(212,175,55,0.15);
}
</style>
