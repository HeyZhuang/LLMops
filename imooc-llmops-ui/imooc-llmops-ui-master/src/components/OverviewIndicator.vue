<script setup lang="ts">
// 1.定义自定义组件所需数据
const props = defineProps({
  title: { type: String, default: '' },
  help: { type: String, default: '' },
  data: { type: Number, default: 0 },
  unit: { type: String, default: '次' },
  pop: { type: Number, default: 0 },
})
</script>

<template>
  <div class="flex flex-col flex-1 gap-3 glass metal-border rounded-xl px-5 py-4">
    <!-- 指标卡标题 -->
    <div class="flex items-center gap-2 text-abyss-600">
      <a-avatar shape="circle" :size="32" class="!bg-gold-50">
        <!-- 创建命名插槽 -->
        <slot name="icon" />
      </a-avatar>
      <div class="text-sm">{{ props.title }}</div>
      <a-tooltip :content="props.help">
        <icon-question-circle class="text-gold-300" />
      </a-tooltip>
    </div>
    <!-- 指标卡数据 -->
    <div class="flex items-baseline gap-4">
      <!-- 数据 -->
      <div class="flex items-baseline gap-1 text-abyss-800 font-semibold">
        <div class="text-2xl">
          {{ props.data % 1 !== 0 ? props.data.toFixed(2) : props.data.toString() }}
        </div>
        <div class="text-sm text-abyss-500">{{ props.unit }}</div>
      </div>
      <!-- 环比 -->
      <div class="flex items-center gap-1 text-abyss-400 text-xs">
        <div class="">环比</div>
        <a-avatar shape="circle" :size="14" class="!bg-gold-50">
          <icon-sync class="text-[14px] text-gold-500" />
        </a-avatar>
        <div class="text-gold-600 font-medium">{{ (props.pop * 100).toFixed(2) }}%</div>
      </div>
    </div>
  </div>
</template>

<style scoped></style>
