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
    <div
      class="glass metal-border p-6 rounded-xl h-[calc(100vh-160px)] overflow-scroll scrollbar-w-none"
    >
      <h2 class="text-base text-abyss-800 font-bold mb-4">概览</h2>
      <p class="text-abyss-500 mb-4">
        医脉天枢开放接口为开发者提供标准化接入能力，可通过 API
        读取会诊应用、工作流、知识库和扩展插件能力， 方便在外部系统中构建更灵活的医疗智能体方案。
      </p>
      <h2 class="text-base text-abyss-800 font-bold mb-4">准备工作</h2>
      <p class="text-abyss-500 mb-4">
        开始之前，请先创建个人访问令牌，并在医脉天枢中完成会诊应用或开放能力的发布。
      </p>
      <h2 class="text-base text-abyss-800 font-bold mb-4">基础使用</h2>
      <a-tabs type="text" class="api-tabs">
        <a-tab-pane key="block" title="非流式会话">
          <p class="text-abyss-500 mb-4">请求示例</p>
          <code-high-light language="shell">{{ blockApiShell }}</code-high-light>
          <p class="text-abyss-500 mb-4">返回结果示例</p>
          <code-high-light language="json">{{ blockApiOutput }}</code-high-light>
        </a-tab-pane>
        <a-tab-pane key="stream" title="流式会话">
          <p class="text-abyss-500 mb-4">请求示例</p>
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
  color: #d4af37;
}

.api-tabs :deep(.arco-tabs-tab:hover) {
  color: #d4af37;
}

.api-tabs :deep(.arco-tabs-nav-ink) {
  background: #d4af37;
}
</style>
