<script setup lang="ts">
// 1.定义组件数据
const props = defineProps({
  visible: { type: Boolean, default: false, required: true },
  template: { type: Object, default: () => ({}), required: false },
})
const emits = defineEmits(['update:visible'])
</script>

<template>
  <a-modal
    :visible="props.visible"
    :title="props.template?.name || '模板预览'"
    :footer="false"
    width="600px"
    @cancel="emits('update:visible', false)"
  >
    <div class="flex flex-col gap-3">
      <div v-if="props.template?.category">
        <a-tag color="gold">{{ props.template.category }}</a-tag>
        <a-tag v-if="props.template.is_public" color="blue" class="ml-1">公开</a-tag>
      </div>
      <div v-if="props.template?.description" class="text-sm text-abyss-500">
        {{ props.template.description }}
      </div>
      <div class="divider-gold"></div>
      <div class="text-sm text-abyss-600 font-medium">Prompt内容</div>
      <div class="glass metal-border rounded-lg p-4 text-sm text-abyss-700 whitespace-pre-wrap max-h-[400px] overflow-auto">
        {{ props.template?.content }}
      </div>
    </div>
  </a-modal>
</template>
