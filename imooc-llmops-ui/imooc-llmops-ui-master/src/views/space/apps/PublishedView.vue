<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useGetPublishedConfig, useRegenerateWebAppToken } from '@/hooks/use-app'

// 1.定义页面所需数据
const route = useRoute()
const router = useRouter()
const {
  loading: getPublishedConfigLoading,
  published_config,
  loadPublishedConfig,
} = useGetPublishedConfig()
const {
  loading: regenerateWebAppTokenLoading,
  token,
  handleRegenerateWebAppToken,
} = useRegenerateWebAppToken()
const webAppUrl = computed(() => {
  if (published_config.value?.web_app?.status === 'published') {
    return getFullPath('web-apps-index', {
      token: published_config.value?.web_app?.token,
    })
  }
  return ''
})

// 2.定义获取完整路由路径函数
const getFullPath = (name: string, params = {}, query = {}) => {
  const { href } = router.resolve({ name, params, query })
  return window.location.origin + href
}

onMounted(() => {
  loadPublishedConfig(String(route.params?.app_id))
})
</script>

<template>
  <div class="linen-bg flex-1 w-full min-h-0 px-6 py-5">
    <!-- 顶部提示信息 -->
    <a-alert class="mb-5 !bg-gold-50 !border-gold-dim published-alert">
      如应用访问链接或二维码意外泄露，请及时重新生成或进行停止分发，避免资源出现异常消耗
    </a-alert>
    <!-- 发布渠道列表 -->
    <a-spin :loading="getPublishedConfigLoading" class="w-full">
      <div class="glass metal-border rounded-xl overflow-hidden">
        <table class="w-full">
          <thead>
            <tr class="h-10 bg-abyss-800">
              <th class="font-medium text-left px-5 text-gold-400 text-sm border-r border-abyss-700">发布渠道</th>
              <th class="font-medium text-left px-5 text-gold-400 text-sm border-r border-abyss-700">状态</th>
              <th class="font-medium text-left px-5 text-gold-400 text-sm">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr class="border-b border-gold-dim">
              <td class="py-4 px-5 w-2/3">
                <div class="flex items-center gap-3">
                  <a-avatar :size="36" shape="square" class="!bg-gold-50 rounded-lg">
                    <icon-compass :size="18" class="text-gold-500" />
                  </a-avatar>
                  <div class="flex flex-col">
                    <div class="text-abyss-800 font-semibold">网页版</div>
                    <div class="text-abyss-400 text-sm">可通过访问PC网页立即开始对话。</div>
                  </div>
                </div>
              </td>
              <td class="py-4 px-5 w-1/12">
                <a-tag v-if="published_config?.web_app?.status !== 'published'" class="!bg-abyss-100 !text-abyss-400 !border-abyss-200">
                  <template #icon>
                    <icon-minus-circle />
                  </template>
                  未发布
                </a-tag>
                <a-tag v-else class="!bg-gold-50 !text-gold-600 !border-gold-dim">
                  <template #icon>
                    <icon-check-circle-fill />
                  </template>
                  已发布
                </a-tag>
              </td>
              <td class="py-4 px-5">
                <div class="flex items-center gap-3">
                  <!-- 左侧URL链接 -->
                  <div class="flex items-center">
                    <div
                      class="bg-parchment-300/60 h-8 leading-8 px-3 rounded-tl-lg rounded-bl-lg text-abyss-600 w-[300px] max-w-[360px] line-clamp-1 break-all text-sm font-mono"
                    >
                      <template v-if="published_config?.web_app?.status === 'published'">
                        {{ webAppUrl }}
                      </template>
                      <template v-else>应用未发布，无可访问链接</template>
                    </div>
                    <a-button
                      :loading="regenerateWebAppTokenLoading"
                      :disabled="published_config?.web_app?.status !== 'published'"
                      type="primary"
                      class="rounded-tr-lg rounded-br-lg px-2"
                      @click="
                        async () => {
                          await handleRegenerateWebAppToken(String(route.params?.app_id))
                          published_config.web_app.token = token
                        }
                      "
                    >
                      重新生成
                    </a-button>
                  </div>
                  <!-- 右侧访问按钮 -->
                  <a-button class="rounded-lg px-2 !border-gold-dim !text-abyss-600 hover:!border-gold-bright hover:!text-gold-500">
                    <template v-if="published_config?.web_app?.status !== 'published'">
                      立即访问
                    </template>
                    <template v-else>
                      <a :href="webAppUrl" target="_blank" class="text-inherit">立即访问</a>
                    </template>
                  </a-button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </a-spin>
  </div>
</template>

<style scoped>
.published-alert :deep(.arco-alert-body) {
  color: #8a6319;
}
</style>
