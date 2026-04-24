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
  <div class="flex min-h-full flex-col px-6">
    <div class="linen-bg sticky top-0 z-20 pt-6">
      <div class="mb-6 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <a-avatar :size="32" class="!bg-abyss-800 !text-gold-400">
            <icon-user :size="18" />
          </a-avatar>
          <div class="text-lg font-semibold text-abyss-800">工作空间</div>
        </div>

        <a-button
          v-if="route.path.startsWith('/space/apps')"
          type="primary"
          class="rounded-lg"
          @click="createType = 'app'"
        >
          创建应用
        </a-button>
        <a-button
          v-if="route.path.startsWith('/space/tools')"
          type="primary"
          class="rounded-lg"
          @click="createType = 'tool'"
        >
          创建工具
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
        <router-link
          v-if="route.path.startsWith('/space/imaging')"
          to="/space/imaging"
          class="inline-flex items-center rounded-lg border border-[#d4ddda] bg-white px-4 py-2 text-sm font-medium text-[#355346] transition hover:border-[#b9cbc3] hover:text-[#17382d]"
        >
          影像规划
        </router-link>
      </div>

      <div class="mb-6 flex items-center justify-between">
        <div class="flex items-center gap-1 rounded-lg bg-parchment-300/50 p-1">
          <router-link
            to="/space/apps"
            class="h-8 rounded-md px-3 leading-8 text-abyss-500 transition-all hover:text-gold-500"
            active-class="!bg-white !text-gold-600 shadow-sm font-medium"
          >
            应用
          </router-link>
          <router-link
            to="/space/tools"
            class="h-8 rounded-md px-3 leading-8 text-abyss-500 transition-all hover:text-gold-500"
            active-class="!bg-white !text-gold-600 shadow-sm font-medium"
          >
            工具
          </router-link>
          <router-link
            to="/space/workflows"
            class="h-8 rounded-md px-3 leading-8 text-abyss-500 transition-all hover:text-gold-500"
            active-class="!bg-white !text-gold-600 shadow-sm font-medium"
          >
            工作流
          </router-link>
          <router-link
            to="/space/datasets"
            class="h-8 rounded-md px-3 leading-8 text-abyss-500 transition-all hover:text-gold-500"
            active-class="!bg-white !text-gold-600 shadow-sm font-medium"
          >
            知识库
          </router-link>
          <router-link
            to="/space/prompt-templates"
            class="h-8 rounded-md px-3 leading-8 text-abyss-500 transition-all hover:text-gold-500"
            active-class="!bg-white !text-gold-600 shadow-sm font-medium"
          >
            Prompt 模板
          </router-link>
          <router-link
            to="/space/skills"
            class="h-8 rounded-md px-3 leading-8 text-abyss-500 transition-all hover:text-gold-500"
            active-class="!bg-white !text-gold-600 shadow-sm font-medium"
          >
            技能
          </router-link>
          <router-link
            to="/space/imaging"
            class="h-8 rounded-md px-3 leading-8 text-abyss-500 transition-all hover:text-gold-500"
            active-class="!bg-white !text-gold-600 shadow-sm font-medium"
          >
            影像
          </router-link>
        </div>

        <a-input-search
          v-if="!route.path.startsWith('/space/imaging')"
          v-model="searchWord"
          placeholder="搜索工作空间资源"
          class="w-[240px] rounded-lg"
          @search="search"
        />
      </div>
    </div>

    <div class="min-h-0 flex-1">
      <router-view v-model:create-type="createType" />
    </div>
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
