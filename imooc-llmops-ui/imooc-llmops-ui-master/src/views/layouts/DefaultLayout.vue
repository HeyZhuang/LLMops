<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useLogout } from '@/hooks/use-auth'
import LayoutSidebar from './components/LayoutSidebar.vue'
import { useGetCurrentUser } from '@/hooks/use-account'
import { useCredentialStore } from '@/stores/credential'
import { useAccountStore } from '@/stores/account'
import SettingModal from '@/views/layouts/components/SettingModal.vue'

const settingModalVisible = ref(false)
const router = useRouter()
const credentialStore = useCredentialStore()
const accountStore = useAccountStore()
const { handleLogout: handleLogoutHook } = useLogout()
const { current_user, loadCurrentUser } = useGetCurrentUser()

const handleLogout = async () => {
  await handleLogoutHook()
  credentialStore.clear()
  accountStore.clear()
  await router.replace({ name: 'auth-login' })
}

onMounted(async () => {
  await loadCurrentUser()
  accountStore.update(current_user.value)
})
</script>

<template>
  <a-layout has-sider class="h-screen overflow-hidden linen-bg">
    <a-layout-sider :width="240" class="h-screen shrink-0 p-2 !bg-transparent">
      <div
        class="glass metal-border shimmer h-full rounded-xl px-3 py-4 flex flex-col justify-between shadow-glass"
      >
        <div>
          <router-link
            to="/home"
            class="flex items-center gap-2 mb-4 hover:opacity-80 transition-opacity decoration-transparent"
          >
            <img
              src="@/assets/images/logo2_transparent.png"
              alt="医脉天枢"
              class="h-10 w-auto object-contain flex-shrink-0"
            />
            <span
              class="text-xl font-bold bg-gradient-to-r from-gold-500 to-amber-600 bg-clip-text text-transparent tracking-widest whitespace-nowrap"
            >
              医脉天枢
            </span>
          </router-link>
          <div class="divider-gold mb-4"></div>
          <router-link :to="{ name: 'space-apps-list', query: { create_type: 'app' } }">
            <a-button type="primary" long class="rounded-lg mb-4 !h-9">
              <template #icon>
                <icon-plus />
              </template>
              新建会诊应用
            </a-button>
          </router-link>
          <layout-sidebar />
        </div>
        <div>
          <div class="divider-gold mb-3"></div>
          <a-dropdown position="tl">
            <div
              class="flex items-center p-2 gap-2 transition-all cursor-pointer rounded-lg hover:bg-gold-50"
            >
              <a-avatar
                :size="32"
                class="text-sm !bg-abyss-800 !text-gold-400"
                :image-url="accountStore.account.avatar"
              >
                {{ accountStore.account.name[0] }}
              </a-avatar>
              <div class="flex flex-col">
                <div class="text-sm text-abyss-800 font-medium">
                  {{ accountStore.account.name }}
                </div>
                <div class="text-xs text-abyss-400">{{ accountStore.account.email }}</div>
              </div>
            </div>
            <template #content>
              <a-doption @click="settingModalVisible = true">
                <template #icon>
                  <icon-settings />
                </template>
                账户设置
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
    <a-layout-content class="h-screen min-w-0 overflow-y-auto overflow-x-hidden !bg-transparent">
      <router-view />
    </a-layout-content>
    <setting-modal v-model:visible="settingModalVisible" />
  </a-layout>
</template>

<style scoped>
:deep(.arco-layout-sider) {
  background: transparent !important;
}
</style>
