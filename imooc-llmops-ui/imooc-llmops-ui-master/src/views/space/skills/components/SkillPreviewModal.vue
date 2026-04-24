<script setup lang="ts">
const props = defineProps({
  visible: { type: Boolean, default: false, required: true },
  skill: { type: Object, default: () => ({}), required: false },
})
const emits = defineEmits(['update:visible'])
</script>

<template>
  <a-modal
    :visible="props.visible"
    :title="props.skill?.name || '技能预览'"
    :footer="false"
    width="680px"
    @cancel="emits('update:visible', false)"
  >
    <div class="flex flex-col gap-3">
      <div v-if="props.skill?.category">
        <a-tag color="gold">{{ props.skill.category }}</a-tag>
        <a-tag v-if="props.skill.is_public" color="blue" class="ml-1">公开</a-tag>
      </div>
      <div v-if="props.skill?.description" class="text-sm text-abyss-500">
        {{ props.skill.description }}
      </div>
      <div class="divider-gold"></div>
      <div class="text-sm text-abyss-600 font-medium">技能内容</div>
      <div class="glass metal-border rounded-lg p-4 text-sm text-abyss-700 whitespace-pre-wrap max-h-[440px] overflow-auto">
        {{ props.skill?.content }}
      </div>
    </div>
  </a-modal>
</template>
