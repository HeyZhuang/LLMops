<script setup lang="ts">
import { useRoute } from 'vue-router'
import IconHomeFull from '@/components/icons/IconHomeFull.vue'
import IconAppFull from '@/components/icons/IconAppFull.vue'
import IconOpenApi from '@/components/icons/IconOpenApi.vue'
import IconHome from '@/components/icons/IconHome.vue'
import IconSpaceFull from '@/components/icons/IconSpaceFull.vue'
import IconSpace from '@/components/icons/IconSpace.vue'
import IconToolFull from '@/components/icons/IconToolFull.vue'
import IconTool from '@/components/icons/IconTool.vue'
import IconApp from '@/components/icons/IconApp.vue'
import IconOpenApiFull from '@/components/icons/IconOpenApiFull.vue'

// 1.定义自定义组件所需数据
const route = useRoute()
</script>

<template>
  <div class="flex flex-col gap-1">
    <router-link
      to="/home"
      :class="[
        'flex items-center gap-2 h-9 leading-9 rounded-lg transition-all px-3 text-abyss-500',
        'hover:text-gold-400 hover:bg-gold-50',
        route.path.startsWith('/home') ? 'nav-active !text-gold-600 font-medium' : ''
      ]"
    >
      <icon-home-full v-if="route.path.startsWith('/home')" />
      <icon-home v-else />
      主页
    </router-link>
    <router-link
      to="/space/apps"
      :class="[
        'flex items-center gap-2 h-9 leading-9 rounded-lg transition-all px-3 text-abyss-500',
        'hover:text-gold-400 hover:bg-gold-50',
        route.path.startsWith('/space') ? 'nav-active !text-gold-600 font-medium' : ''
      ]"
    >
      <icon-space-full v-if="route.path.startsWith('/space')" />
      <icon-space v-else />
      个人空间
    </router-link>
    <!-- 分区标题 -->
    <div class="text-abyss-300 text-xs px-3 mt-2 mb-1 uppercase tracking-wider">探索</div>
    <router-link
      to="/store/apps"
      :class="[
        'flex items-center gap-2 h-9 leading-9 rounded-lg transition-all px-3 text-abyss-500',
        'hover:text-gold-400 hover:bg-gold-50',
        route.path.startsWith('/store/apps') ? 'nav-active !text-gold-600 font-medium' : ''
      ]"
    >
      <icon-app-full v-if="route.path.startsWith('/store/apps')" />
      <icon-app v-else />
      应用广场
    </router-link>
    <router-link
      to="/store/tools"
      :class="[
        'flex items-center gap-2 h-9 leading-9 rounded-lg transition-all px-3 text-abyss-500',
        'hover:text-gold-400 hover:bg-gold-50',
        route.path.startsWith('/store/tools') ? 'nav-active !text-gold-600 font-medium' : ''
      ]"
    >
      <icon-tool-full v-if="route.path.startsWith('/store/tools')" />
      <icon-tool v-else />
      插件广场
    </router-link>
    <router-link
      to="/openapi"
      :class="[
        'flex items-center gap-2 h-9 leading-9 rounded-lg transition-all px-3 text-abyss-500',
        'hover:text-gold-400 hover:bg-gold-50',
        route.path.startsWith('/openapi') ? 'nav-active !text-gold-600 font-medium' : ''
      ]"
    >
      <icon-open-api-full v-if="route.path.startsWith('/openapi')" />
      <icon-open-api v-else />
      开放 API
    </router-link>
  </div>
</template>

<style scoped></style>
