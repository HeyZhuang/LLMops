<script setup lang="ts">
import { onMounted, ref } from 'vue'
import moment from 'moment'
import { useDeleteSkill, useGetSkillsWithPage } from '@/hooks/use-skill'
import CreateOrUpdateSkillModal from './components/CreateOrUpdateSkillModal.vue'
import SkillPreviewModal from './components/SkillPreviewModal.vue'

const { loading: getSkillsLoading, skills, paginator, loadSkills } = useGetSkillsWithPage()
const { handleDeleteSkill } = useDeleteSkill()
const createOrUpdateModalVisible = ref(false)
const previewModalVisible = ref(false)
const editSkillId = ref('')
const previewSkill = ref<Record<string, any>>({})
const searchWord = ref('')

const handleScroll = async (event: UIEvent) => {
  const { scrollTop, scrollHeight, clientHeight } = event.target as HTMLElement
  if (scrollTop + clientHeight >= scrollHeight - 10) {
    if (getSkillsLoading.value) return
    await loadSkills(false, searchWord.value)
  }
}

const handleSearch = async () => {
  await loadSkills(true, searchWord.value)
}

const handleCreate = () => {
  editSkillId.value = ''
  createOrUpdateModalVisible.value = true
}

const handleEdit = (id: string) => {
  editSkillId.value = id
  createOrUpdateModalVisible.value = true
}

const handlePreview = (skill: Record<string, any>) => {
  previewSkill.value = skill
  previewModalVisible.value = true
}

onMounted(async () => {
  await loadSkills(true)
})
</script>

<template>
  <div class="h-full flex flex-col p-5">
    <div class="flex items-center justify-between mb-5">
      <div class="text-lg text-abyss-800 font-semibold">技能库</div>
      <div class="flex items-center gap-3">
        <a-input-search
          v-model="searchWord"
          placeholder="搜索技能..."
          class="w-[240px]"
          @search="handleSearch"
          @press-enter="handleSearch"
        />
        <a-button type="primary" class="rounded-lg" @click="handleCreate">
          <template #icon><icon-plus /></template>
          新建技能
        </a-button>
      </div>
    </div>

    <a-spin
      :loading="getSkillsLoading"
      class="block flex-1 overflow-scroll scrollbar-w-none"
      @scroll="handleScroll"
    >
      <a-row :gutter="[20, 20]">
        <a-col v-for="skill in skills" :key="skill.id" :span="6">
          <div class="glass metal-border rounded-xl p-5 cursor-pointer card-hover">
            <div class="flex items-center justify-between mb-3">
              <div class="text-base text-abyss-800 font-bold line-clamp-1">{{ skill.name }}</div>
              <a-dropdown position="br">
                <a-button type="text" size="small" class="rounded-lg !text-abyss-400 hover:!text-gold-400">
                  <template #icon><icon-more /></template>
                </a-button>
                <template #content>
                  <a-doption @click="handlePreview(skill)">预览</a-doption>
                  <a-doption @click="handleEdit(skill.id)">编辑</a-doption>
                  <a-doption
                    class="!text-red-400"
                    @click="handleDeleteSkill(skill.id, () => loadSkills(true, searchWord))"
                  >
                    删除
                  </a-doption>
                </template>
              </a-dropdown>
            </div>
            <div v-if="skill.category" class="mb-2">
              <a-tag size="small" color="gold">{{ skill.category }}</a-tag>
              <a-tag v-if="skill.is_public" size="small" color="blue" class="ml-1">公开</a-tag>
            </div>
            <div class="text-sm text-abyss-400 h-[54px] line-clamp-3 mb-3 break-all">
              {{ skill.description || skill.content }}
            </div>
            <div class="divider-gold mb-3"></div>
            <div class="text-xs text-abyss-300">
              更新于 {{ moment(skill.updated_at * 1000).format('MM-DD HH:mm') }}
            </div>
          </div>
        </a-col>
        <a-col v-if="skills.length === 0 && !getSkillsLoading" :span="24">
          <a-empty
            description="暂无技能，点击新建技能开始添加"
            class="h-[400px] flex flex-col items-center justify-center"
          />
        </a-col>
      </a-row>
      <a-row v-if="paginator.total_page >= 2">
        <a-col v-if="paginator.current_page <= paginator.total_page" :span="24" align="center">
          <a-space class="my-4">
            <a-spin />
            <div class="text-abyss-400">加载中</div>
          </a-space>
        </a-col>
        <a-col v-else :span="24" align="center">
          <div class="text-abyss-400 my-4">已加载全部数据</div>
        </a-col>
      </a-row>
    </a-spin>

    <create-or-update-skill-modal
      v-model:visible="createOrUpdateModalVisible"
      v-model:skill_id="editSkillId"
      :callback="() => loadSkills(true, searchWord)"
    />
    <skill-preview-modal
      v-model:visible="previewModalVisible"
      :skill="previewSkill"
    />
  </div>
</template>

<style scoped>
.card-hover {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.card-hover:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(15, 23, 42, 0.08), 0 0 0 1px rgba(212, 175, 55, 0.15);
}
</style>
