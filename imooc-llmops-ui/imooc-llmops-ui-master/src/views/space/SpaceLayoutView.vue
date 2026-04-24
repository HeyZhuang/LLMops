<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const createType = ref<string>('')
const searchWord = ref(route.query?.search_word || '')

const search = (value: string) => {
  router.push({
    path: route.path,
    query: {
      search_word: value,
    },
  })
}

watch(
  () => route.query?.search_word,
  () => {
    searchWord.value = route.query?.search_word || ''
  },
)
</script>

<template>
  <div class="px-6 flex flex-col overflow-hidden h-full">
    <div class="pt-6 sticky top-0 z-20 linen-bg">
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center gap-3">
          <a-avatar :size="32" class="!bg-abyss-800 !text-gold-400">
            <icon-user :size="18" />
          </a-avatar>
          <div class="text-lg font-semibold text-abyss-800">个人空间</div>
        </div>

        <a-button
          v-if="route.path.startsWith('/space/apps')"
          type="primary"
          class="rounded-lg"
          @click="createType = 'app'"
        >
          创建 AI 应用
        </a-button>
        <a-button
          v-if="route.path.startsWith('/space/tools')"
          type="primary"
          class="rounded-lg"
          @click="createType = 'tool'"
        >
          创建自定义插件
        </a-button>
        <a-button
          v-if="route.path.startsWith('/space/workflows')"
          type="primary"
          class="rounded-lg"
          @click="createType = 'workflow'"
        >
          创建工作流
        </a-button>
        <a-button
          v-if="route.path.startsWith('/space/datasets')"
          type="primary"
          class="rounded-lg"
          @click="createType = 'dataset'"
        >
          创建知识库
        </a-button>
        <a-button
          v-if="route.path.startsWith('/space/skills')"
          type="primary"
          class="rounded-lg"
          @click="createType = 'skill'"
        >
          创建技能
        </a-button>
      </div>

      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center gap-1 p-1 rounded-lg bg-parchment-300/50">
          <router-link
            to="/space/apps"
            class="rounded-md text-abyss-500 px-3 h-8 leading-8 hover:text-gold-500 transition-all"
            active-class="!bg-white !text-gold-600 shadow-sm font-medium"
          >
            AI应用
          </router-link>
          <router-link
            to="/space/tools"
            class="rounded-md text-abyss-500 px-3 h-8 leading-8 hover:text-gold-500 transition-all"
            active-class="!bg-white !text-gold-600 shadow-sm font-medium"
          >
            插件
          </router-link>
          <router-link
            to="/space/workflows"
            class="rounded-md text-abyss-500 px-3 h-8 leading-8 hover:text-gold-500 transition-all"
            active-class="!bg-white !text-gold-600 shadow-sm font-medium"
          >
            工作流
          </router-link>
          <router-link
            to="/space/datasets"
            class="rounded-md text-abyss-500 px-3 h-8 leading-8 hover:text-gold-500 transition-all"
            active-class="!bg-white !text-gold-600 shadow-sm font-medium"
          >
            知识库
          </router-link>
          <router-link
            to="/space/prompt-templates"
            class="rounded-md text-abyss-500 px-3 h-8 leading-8 hover:text-gold-500 transition-all"
            active-class="!bg-white !text-gold-600 shadow-sm font-medium"
          >
            Prompt 模板
          </router-link>
          <router-link
            to="/space/skills"
            class="rounded-md text-abyss-500 px-3 h-8 leading-8 hover:text-gold-500 transition-all"
            active-class="!bg-white !text-gold-600 shadow-sm font-medium"
          >
            Skills
          </router-link>
        </div>

        <a-input-search
          v-model="searchWord"
          placeholder="输入关键词进行搜索"
          class="w-[240px] rounded-lg"
          @search="search"
        />
      </div>
    </div>

    <router-view v-model:create-type="createType" />
  </div>
</template>

<style scoped>
:deep(.arco-input-wrapper) {
  background: rgba(248, 245, 240, 0.8) !important;
  border: 1px solid rgba(212, 175, 55, 0.12) !important;
}
:deep(.arco-input-wrapper:hover) {
  border-color: rgba(212, 175, 55, 0.3) !important;
}
:deep(.arco-input-wrapper.arco-input-focus) {
  border-color: #d4af37 !important;
  box-shadow: 0 0 0 3px rgba(212, 175, 55, 0.08) !important;
}
</style>
