<script setup lang="ts">
import CodeHighLight from '@/components/CodeHighLight.vue'
import {
  blockApiOutput,
  blockApiShell,
  streamApiOutput,
  streamApiShell,
} from '@/views/openapi/quick-start'
</script>

<template>
  <div class="pb-6">
    <div class="glass metal-border p-6 rounded-xl h-[calc(100vh-160px)] overflow-scroll scrollbar-w-none">
      <h2 class="text-base text-abyss-800 font-bold mb-4">概览</h2>
      <p class="text-abyss-500 mb-4">
        LLMOps API 是LLMOps-Platform LLMOps 平台面向开发者提供的专业技术交互能力，致力于通过 API
        实现开发者更高效更全面的述求，不仅如此，扣子 API
        将提供更加灵活的和高精度的模型、工作流、知识库和扩展插件等能力的扩展，让定制化 Agent
        更加的精确、高效和智能。
      </p>
      <h2 class="text-base text-abyss-800 font-bold mb-4">准备工作</h2>
      <p class="text-abyss-500 mb-4">
        在开始之前，您需要创建个人访问令牌，其次需要在 LLMOps 上完成 Agent 的创建与发布。
      </p>
      <h2 class="text-base text-abyss-800 font-bold mb-4">基础使用</h2>
      <a-tabs type="text" class="api-tabs">
        <a-tab-pane key="block" title="非流式Chat">
          <p class="text-abyss-500 mb-4">请求CURL</p>
          <code-high-light language="shell">{{ blockApiShell }}</code-high-light>
          <p class="text-abyss-500 mb-4">返回结果示例</p>
          <code-high-light language="json">{{ blockApiOutput }}</code-high-light>
        </a-tab-pane>
        <a-tab-pane key="stream" title="流式Chat">
          <p class="text-abyss-500 mb-4">请求CURL</p>
          <code-high-light language="shell">{{ streamApiShell }}</code-high-light>
          <p class="text-abyss-500 mb-4">返回结果示例</p>
          <code-high-light language="json">{{ streamApiOutput }}</code-high-light>
        </a-tab-pane>
      </a-tabs>
    </div>
  </div>
</template>

<style scoped>
.api-tabs :deep(.arco-tabs-tab) {
  color: #505f83;
}
.api-tabs :deep(.arco-tabs-tab-active) {
  color: #D4AF37;
}
.api-tabs :deep(.arco-tabs-tab:hover) {
  color: #D4AF37;
}
.api-tabs :deep(.arco-tabs-nav-ink) {
  background: #D4AF37;
}
</style>
