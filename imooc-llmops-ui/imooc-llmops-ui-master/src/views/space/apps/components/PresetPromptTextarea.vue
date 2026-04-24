<script setup lang="ts">
import { computed, ref, watch, type PropType } from 'vue'
import { Message } from '@arco-design/web-vue'
import { useUpdateDraftAppConfig } from '@/hooks/use-app'
import { useOptimizePrompt } from '@/hooks/use-ai'
import { useGetPromptTemplatesWithPage } from '@/hooks/use-prompt-template'
import { useGetSkillsWithPage } from '@/hooks/use-skill'
import type { Skill } from '@/models/skill'

const props = defineProps({
  app_id: { type: String, required: true },
  preset_prompt: { type: String, default: '', required: true },
  skills: {
    type: Array as PropType<Skill[]>,
    default: () => [],
  },
})
const emits = defineEmits(['update:preset_prompt', 'update:skills'])

const optimizeTriggerVisible = ref(false)
const templateTriggerVisible = ref(false)
const skillTriggerVisible = ref(false)
const origin_prompt = ref('')
const skillSearchWord = ref('')
const selectedSkillIds = ref<string[]>([])
const skillCache = ref<Record<string, Skill>>({})

const { handleUpdateDraftAppConfig } = useUpdateDraftAppConfig()
const { loading, optimize_prompt, handleOptimizePrompt } = useOptimizePrompt()
const { loading: templatesLoading, templates, loadTemplates } = useGetPromptTemplatesWithPage()
const { loading: skillsLoading, skills, loadSkills } = useGetSkillsWithPage()
const selectedSkillMap = computed(() => {
  return new Map([...Object.values(skillCache.value), ...props.skills].map((skill) => [skill.id, skill]))
})
const filteredSkills = computed(() => {
  const keyword = skillSearchWord.value.trim().toLowerCase()
  if (!keyword) {
    return skills.value
  }
  return skills.value.filter((skill) => {
    return [skill.name, skill.description, skill.category, skill.content]
      .filter(Boolean)
      .some((field) => field.toLowerCase().includes(keyword))
  })
})

watch(
  () => props.skills,
  (value) => {
    selectedSkillIds.value = value.map((skill) => skill.id)
  },
  { immediate: true, deep: true },
)

watch(
  () => skills.value,
  (value) => {
    value.forEach((skill) => {
      skillCache.value[skill.id] = skill
    })
  },
  { immediate: true, deep: true },
)

const handleReplacePresetPrompt = () => {
  if (optimize_prompt.value.trim() === '') {
    Message.warning('优化后的提示词为空，请重新生成。')
    return
  }
  emits('update:preset_prompt', optimize_prompt.value)
  handleUpdateDraftAppConfig(props.app_id, { preset_prompt: optimize_prompt.value })
  optimizeTriggerVisible.value = false
}

const handleSubmit = async () => {
  if (origin_prompt.value.trim() === '') {
    Message.warning('提示词不能为空。')
    return
  }
  await handleOptimizePrompt(origin_prompt.value)
}

const handleOpenTemplates = async () => {
  templateTriggerVisible.value = true
  await loadTemplates(true)
}

const handleSelectTemplate = (content: string) => {
  emits('update:preset_prompt', content)
  handleUpdateDraftAppConfig(props.app_id, { preset_prompt: content })
  templateTriggerVisible.value = false
  Message.success('模板已应用')
}

const handleOpenSkills = async () => {
  skillTriggerVisible.value = true
  skillSearchWord.value = ''
  selectedSkillIds.value = props.skills.map((skill) => skill.id)
  await loadSkills(true)
}

const handleSearchSkills = async (keyword: string) => {
  skillSearchWord.value = keyword
  await loadSkills(true, keyword)
}

const handleSaveSkills = async () => {
  const selectedSkills = selectedSkillIds.value
    .map((skill_id) => selectedSkillMap.value.get(skill_id))
    .filter(Boolean) as Skill[]

  await handleUpdateDraftAppConfig(props.app_id, { skills: selectedSkillIds.value })
  emits('update:skills', selectedSkills)
  skillTriggerVisible.value = false
  Message.success('技能已更新')
}

const handleCancelSkills = () => {
  selectedSkillIds.value = props.skills.map((skill) => skill.id)
  skillTriggerVisible.value = false
}
</script>

<template>
  <div class="flex flex-col h-[calc(100vh-173px)]">
    <div class="flex items-center justify-between px-4 mb-4">
      <div class="text-gray-700 font-bold">人设与回复逻辑</div>
      <div class="flex items-center gap-2">
        <a-trigger
          v-model:popup-visible="templateTriggerVisible"
          :trigger="['click']"
          position="bl"
          :popup-translate="[0, 8]"
        >
          <a-button size="mini" class="rounded-lg px-2" @click="handleOpenTemplates">
            <template #icon>
              <icon-book />
            </template>
            模板
          </a-button>
          <template #content>
            <a-card class="rounded-lg w-[340px]">
              <div class="flex flex-col">
                <div class="text-sm font-medium text-abyss-700 mb-3">选择一个提示词模板</div>
                <a-spin :loading="templatesLoading">
                  <div class="max-h-[300px] overflow-auto flex flex-col gap-2">
                    <div
                      v-for="tpl in templates"
                      :key="tpl.id"
                      class="p-3 border border-gold-dim rounded-lg cursor-pointer hover:bg-gold-50 transition-all"
                      @click="handleSelectTemplate(tpl.content)"
                    >
                      <div class="text-sm text-abyss-700 font-medium">{{ tpl.name }}</div>
                      <div class="text-xs text-abyss-400 line-clamp-2 mt-1">{{ tpl.content }}</div>
                    </div>
                    <div v-if="templates.length === 0" class="text-sm text-abyss-400 text-center py-4">
                      暂无模板
                    </div>
                  </div>
                </a-spin>
              </div>
            </a-card>
          </template>
        </a-trigger>

        <a-trigger
          v-model:popup-visible="skillTriggerVisible"
          :trigger="['click']"
          position="bl"
          :popup-translate="[0, 8]"
        >
          <a-button size="mini" class="rounded-lg px-2" @click="handleOpenSkills">
            <template #icon>
              <icon-bulb />
            </template>
            技能
          </a-button>
          <template #content>
            <a-card class="rounded-lg w-[400px]">
              <div class="flex flex-col">
                <div class="text-sm font-medium text-abyss-700 mb-3">为该应用绑定技能</div>
                <a-input-search
                  v-model="skillSearchWord"
                  allow-clear
                  placeholder="搜索技能"
                  class="mb-3"
                  @search="handleSearchSkills"
                />
                <a-spin :loading="skillsLoading">
                  <div class="max-h-[300px] overflow-auto flex flex-col gap-2">
                    <a-checkbox-group v-model="selectedSkillIds" class="flex flex-col gap-2">
                      <div
                        v-for="skill in filteredSkills"
                        :key="skill.id"
                        class="p-3 border border-gold-dim rounded-lg hover:bg-gold-50 transition-all"
                      >
                        <a-checkbox :value="skill.id" class="w-full">
                          <div class="flex flex-col gap-1 pl-1">
                            <div class="flex items-center justify-between gap-2">
                              <div class="text-sm text-abyss-700 font-medium line-clamp-1">
                                {{ skill.name }}
                              </div>
                              <a-tag v-if="skill.category" size="small" color="gold">
                                {{ skill.category }}
                              </a-tag>
                            </div>
                            <div class="text-xs text-abyss-400 line-clamp-2">
                              {{ skill.description || skill.content }}
                            </div>
                          </div>
                        </a-checkbox>
                      </div>
                    </a-checkbox-group>
                    <div v-if="filteredSkills.length === 0" class="text-sm text-abyss-400 text-center py-4">
                      暂无技能
                    </div>
                  </div>
                </a-spin>
                <div class="flex items-center justify-end gap-2 mt-4">
                  <a-button size="small" class="rounded-lg" @click="handleCancelSkills">
                    取消
                  </a-button>
                  <a-button size="small" type="primary" class="rounded-lg" @click="handleSaveSkills">
                    保存
                  </a-button>
                </div>
              </div>
            </a-card>
          </template>
        </a-trigger>

        <a-trigger
          v-model:popup-visible="optimizeTriggerVisible"
          :trigger="['click']"
          position="bl"
          :popup-translate="[0, 8]"
        >
          <a-button size="mini" class="rounded-lg px-2">
            <template #icon>
              <icon-sync />
            </template>
            优化
          </a-button>
          <template #content>
            <a-card class="rounded-lg w-[422px]">
              <div class="flex flex-col">
                <div v-if="optimize_prompt" class="mb-4 flex flex-col">
                  <div
                    class="max-h-[321px] overflow-scroll scrollbar-w-none mb-2 text-gray-700 whitespace-pre-line"
                  >
                    {{ optimize_prompt }}
                  </div>
                  <a-space v-if="!loading">
                    <a-button
                      size="small"
                      type="primary"
                      class="rounded-lg"
                      @click="handleReplacePresetPrompt"
                    >
                      替换
                    </a-button>
                    <a-button size="small" class="rounded-lg" @click="optimizeTriggerVisible = false">
                      关闭
                    </a-button>
                  </a-space>
                </div>
                <div>
                  <div
                    class="h-[50px] flex items-center gap-2 px-4 flex-1 border border-gray-200 rounded-full"
                  >
                    <input
                      v-model="origin_prompt"
                      type="text"
                      class="flex-1 outline-0"
                      placeholder="你希望如何撰写或优化提示词？"
                    />
                    <a-button :loading="loading" type="text" shape="circle" @click="handleSubmit">
                      <template #icon>
                        <icon-send :size="16" class="!text-blue-700" />
                      </template>
                    </a-button>
                  </div>
                </div>
              </div>
            </a-card>
          </template>
        </a-trigger>
      </div>
    </div>

    <div class="flex-1">
      <div v-if="props.skills.length" class="px-4 pb-3 flex flex-wrap gap-2">
        <a-tag v-for="skill in props.skills" :key="skill.id" color="arcoblue" class="rounded-full">
          {{ skill.name }}
        </a-tag>
      </div>
      <a-textarea
        class="h-full resize-none !bg-transparent !border-0 text-gray-700 px-1 preset-prompt-textarea"
        placeholder="在这里编写智能体人设与回复逻辑"
        :max-length="2000"
        show-word-limit
        :model-value="props.preset_prompt"
        @update:model-value="(value) => emits('update:preset_prompt', value)"
        @blur="
          async () => {
            await handleUpdateDraftAppConfig(props.app_id, {
              preset_prompt: props.preset_prompt,
            })
          }
        "
      />
    </div>
  </div>
</template>

<style>
.preset-prompt-textarea {
  textarea {
    scrollbar-width: none;
  }
}
</style>
