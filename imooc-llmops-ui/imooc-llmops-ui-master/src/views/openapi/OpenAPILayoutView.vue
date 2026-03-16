<script setup lang="ts">
import { useRoute } from 'vue-router'
import { ref } from 'vue'

const route = useRoute()
const create_api_key = ref(false)
</script>

<template>
  <!-- 调整边距+隐藏 -->
  <div class="px-6 flex flex-col overflow-hidden h-full">
    <div class="pt-6 sticky top-0 z-20 linen-bg">
      <!-- 顶层标题+创建按钮 -->
      <div class="flex items-center justify-between mb-6">
        <!-- 左侧标题 -->
        <div class="flex items-center gap-3">
          <a-avatar :size="32" class="!bg-abyss-800 !text-gold-400">
            <icon-user :size="18" />
          </a-avatar>
          <div class="flex items-center gap-2">
            <span class="text-lg font-semibold text-abyss-800">开放API</span>
            <span class="text-xs text-abyss-400">利用开放 API 快速与企业现有业务对接</span>
          </div>
        </div>
      </div>
      <!-- 导航按钮 -->
      <div class="flex items-center justify-between mb-6">
        <!-- 左侧导航 -->
        <div class="flex items-center gap-1 p-1 rounded-lg bg-parchment-300/50">
          <router-link
            to="/openapi"
            class="rounded-md text-abyss-500 px-3 h-8 leading-8 hover:text-gold-500 transition-all"
            exact-active-class="!bg-white !text-gold-600 shadow-sm font-medium"
          >
            快速开始
          </router-link>
          <router-link
            to="/openapi/api-keys"
            class="rounded-md text-abyss-500 px-3 h-8 leading-8 hover:text-gold-500 transition-all"
            active-class="!bg-white !text-gold-600 shadow-sm font-medium"
          >
            秘钥
          </router-link>
        </div>
        <!-- 右侧按钮 -->
        <a-button
          v-if="route.path.startsWith('/openapi/api-keys')"
          type="primary"
          class="rounded-lg"
          @click="create_api_key = true"
        >
          新增秘钥
        </a-button>
      </div>
    </div>
    <!-- 中间内容 -->
    <router-view v-model:create_api_key="create_api_key" />
  </div>
</template>

<style scoped></style>
