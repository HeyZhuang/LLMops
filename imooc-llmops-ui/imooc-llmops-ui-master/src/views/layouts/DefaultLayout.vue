<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useLogout } from '@/hooks/use-auth'
import LayoutSidebar from './components/LayoutSidebar.vue'
import { useGetCurrentUser } from '@/hooks/use-account'
import { useCredentialStore } from '@/stores/credential'
import { useAccountStore } from '@/stores/account'
import SettingModal from '@/views/layouts/components/SettingModal.vue'

// 1.定义页面所需数据
const settingModalVisible = ref(false)
const router = useRouter()
const credentialStore = useCredentialStore()
const accountStore = useAccountStore()
const { handleLogout: handleLogoutHook } = useLogout()
const { current_user, loadCurrentUser } = useGetCurrentUser()

// 2.退出登录按钮
const handleLogout = async () => {
  // 2.1 发起请求退出登录
  await handleLogoutHook()

  // 2.2 清空授权凭证+账号信息
  credentialStore.clear()
  accountStore.clear()

  // 2.3 跳转到授权认证页面
  await router.replace({ name: 'auth-login' })
}

// 3.页面DOM加载完成时获取当前登录账号信息
onMounted(async () => {
  await loadCurrentUser()
  accountStore.update(current_user.value)
})
</script>

<template>
  <a-layout has-sider class="h-full linen-bg">
    <!-- 侧边栏 -->
    <a-layout-sider :width="240" class="min-h-screen p-2 !bg-transparent">
      <div class="glass metal-border shimmer h-full rounded-xl px-3 py-4 flex flex-col justify-between shadow-glass">
        <!-- 上半部分 -->
        <div>
          <!-- 顶部Logo -->
          <router-link to="/home" class="block mb-4">
            <img
              src="@/assets/images/logo.png"
              alt="LLMOps"
              class="h-9 w-[110px] object-contain"
            />
          </router-link>
          <!-- 金色分割线 -->
          <div class="divider-gold mb-4"></div>
          <!-- 创建AI应用按钮 -->
          <router-link :to="{ name: 'space-apps-list', query: { create_type: 'app' } }">
            <a-button type="primary" long class="rounded-lg mb-4 !h-9">
              <template #icon>
                <icon-plus />
              </template>
              创建 AI 应用
            </a-button>
          </router-link>
          <!-- 侧边栏导航 -->
          <layout-sidebar />
        </div>
        <!-- 账号设置 -->
        <div>
          <!-- 金色分割线 -->
          <div class="divider-gold mb-3"></div>
          <a-dropdown position="tl">
            <div
              class="flex items-center p-2 gap-2 transition-all cursor-pointer rounded-lg hover:bg-gold-50"
            >
              <!-- 头像 -->
              <a-avatar
                :size="32"
                class="text-sm !bg-abyss-800 !text-gold-400"
                :image-url="accountStore.account.avatar"
              >
                {{ accountStore.account.name[0] }}
              </a-avatar>
              <!-- 个人信息 -->
              <div class="flex flex-col">
                <div class="text-sm text-abyss-800 font-medium">{{ accountStore.account.name }}</div>
                <div class="text-xs text-abyss-400">{{ accountStore.account.email }}</div>
              </div>
            </div>
            <template #content>
              <a-doption @click="settingModalVisible = true">
                <template #icon>
                  <icon-settings />
                </template>
                账号设置
              </a-doption>
              <a-doption @click="handleLogout">
                <template #icon>
                  <icon-poweroff />
                </template>
                退出登录
              </a-doption>
            </template>
          </a-dropdown>
        </div>
      </div>
    </a-layout-sider>
    <!-- 右侧内容 -->
    <a-layout-content class="!bg-transparent">
      <router-view />
    </a-layout-content>
    <!-- 设置模态窗 -->
    <setting-modal v-model:visible="settingModalVisible" />
  </a-layout>
</template>

<style scoped>
:deep(.arco-layout-sider) {
  background: transparent !important;
}
</style>
