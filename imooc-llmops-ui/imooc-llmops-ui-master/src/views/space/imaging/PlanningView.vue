<script setup lang="ts">
import { computed } from 'vue'
import { useImagingPlanning } from '@/hooks/use-imaging'

const { loading, overview, workflowTemplates, mvpTasks } = useImagingPlanning()

const metricCards = computed(() => [
  { label: '应用数', value: overview.value.metrics.apps },
  { label: '知识库数', value: overview.value.metrics.datasets },
  { label: '文档数', value: overview.value.metrics.documents },
  { label: '工作流数', value: overview.value.metrics.workflows },
  { label: '影像模板数', value: overview.value.metrics.workflow_templates },
])
</script>

<template>
  <a-spin :loading="loading" class="block">
    <div class="min-h-full px-6 py-6">
      <div
        class="rounded-[28px] border border-[#d7e0dc] bg-[linear-gradient(135deg,#f7fbf8_0%,#eef5f1_45%,#f9f4ea_100%)] p-8 shadow-[0_20px_60px_rgba(15,23,42,0.08)]"
      >
        <div class="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
          <div class="max-w-3xl">
            <div
              class="inline-flex items-center rounded-full bg-white/80 px-4 py-1 text-xs font-semibold tracking-[0.24em] text-[#49635a]"
            >
              医院影像 AI
            </div>
            <h1 class="mt-4 text-4xl font-black tracking-tight text-[#123629]">
              {{ overview.title }}
            </h1>
            <p class="mt-4 max-w-2xl text-[15px] leading-7 text-[#49635a]">
              {{ overview.summary }}
            </p>
          </div>

          <div class="grid min-w-[280px] gap-3 md:grid-cols-3 lg:grid-cols-1">
            <div
              v-for="item in overview.positioning"
              :key="item"
              class="rounded-2xl border border-white/70 bg-white/85 px-4 py-3 text-sm font-medium text-[#123629] backdrop-blur"
            >
              {{ item }}
            </div>
            <router-link
              to="/space/imaging/studies"
              class="inline-flex items-center justify-center rounded-2xl bg-[#17382d] px-4 py-3 text-sm font-semibold text-white transition hover:bg-[#214637]"
            >
              打开影像工作台
            </router-link>
          </div>
        </div>

        <div class="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <div
            v-for="scene in overview.scenes"
            :key="scene.name"
            class="rounded-3xl border border-[#d3ddd7] bg-white/90 p-5 shadow-[0_8px_24px_rgba(26,71,54,0.06)]"
          >
            <div class="text-xs font-bold tracking-[0.24em] text-[#6c8a7f]">{{ scene.value }}</div>
            <div class="mt-3 text-xl font-bold text-[#17382d]">{{ scene.name }}</div>
            <div class="mt-2 text-sm leading-6 text-[#5d746b]">{{ scene.description }}</div>
          </div>
        </div>

        <div class="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-5">
          <div
            v-for="metric in metricCards"
            :key="metric.label"
            class="rounded-3xl border border-[#d3ddd7] bg-white/90 p-5"
          >
            <div class="text-xs font-bold tracking-[0.24em] text-[#6c8a7f]">{{ metric.label }}</div>
            <div class="mt-3 text-3xl font-black text-[#17382d]">{{ metric.value }}</div>
          </div>
        </div>

        <div class="mt-10 grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
          <div class="rounded-3xl border border-[#d3ddd7] bg-white/92 p-6">
            <div class="flex items-center justify-between">
              <div>
                <div class="text-xs font-bold tracking-[0.24em] text-[#6c8a7f]">执行路线</div>
                <h2 class="mt-2 text-2xl font-bold text-[#17382d]">分阶段落地</h2>
              </div>
              <div class="rounded-full bg-[#e9f2ed] px-3 py-1 text-xs font-semibold text-[#49635a]">
                先打基础，再闭环临床业务
              </div>
            </div>

            <div class="mt-5 grid gap-4">
              <div
                v-for="phase in overview.phases"
                :key="phase.key"
                class="rounded-2xl border border-[#e5ece8] bg-[#fbfcfb] p-5"
              >
                <div class="text-lg font-bold text-[#17382d]">{{ phase.title }}</div>
                <div class="mt-2 text-sm leading-6 text-[#5d746b]">{{ phase.goal }}</div>
                <div class="mt-3 flex flex-wrap gap-2">
                  <span
                    v-for="deliverable in phase.deliverables"
                    :key="deliverable"
                    class="rounded-full bg-[#edf4ef] px-3 py-1 text-xs font-medium text-[#355346]"
                  >
                    {{ deliverable }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div class="grid gap-6">
            <div class="rounded-3xl border border-[#d3ddd7] bg-white/92 p-6">
              <div class="text-xs font-bold tracking-[0.24em] text-[#6c8a7f]">临床边界</div>
              <h2 class="mt-2 text-2xl font-bold text-[#17382d]">合规与风控</h2>
              <div class="mt-4 grid gap-3">
                <div
                  v-for="guardrail in overview.guardrails"
                  :key="guardrail"
                  class="rounded-2xl bg-[#f4f8f5] px-4 py-3 text-sm leading-6 text-[#355346]"
                >
                  {{ guardrail }}
                </div>
              </div>
            </div>

            <div class="rounded-3xl border border-[#d3ddd7] bg-[#17382d] p-6 text-white">
              <div class="text-xs font-bold tracking-[0.24em] text-[#b5d0c3]">MVP 方案</div>
              <h2 class="mt-2 text-2xl font-bold">{{ overview.mvp.name }}</h2>
              <p class="mt-3 text-sm leading-6 text-[#d9e7e0]">
                {{ overview.mvp.value }}
              </p>
            </div>
          </div>
        </div>

        <div class="mt-10">
          <div class="text-xs font-bold tracking-[0.24em] text-[#6c8a7f]">工作流模板</div>
          <h2 class="mt-2 text-2xl font-bold text-[#17382d]">预置影像流程</h2>
          <div class="mt-5 grid gap-5 xl:grid-cols-2">
            <div
              v-for="workflow in workflowTemplates"
              :key="workflow.key"
              class="rounded-3xl border border-[#d3ddd7] bg-white/92 p-6"
            >
              <div class="flex items-center justify-between">
                <div class="text-xl font-bold text-[#17382d]">{{ workflow.name }}</div>
                <div class="rounded-full bg-[#edf4ef] px-3 py-1 text-xs font-semibold text-[#355346]">
                  模板
                </div>
              </div>
              <div class="mt-2 text-sm leading-6 text-[#5d746b]">{{ workflow.scene }}</div>
              <div class="mt-4 flex flex-wrap gap-2">
                <span
                  v-for="step in workflow.steps"
                  :key="step"
                  class="rounded-full border border-[#dce6e0] px-3 py-1 text-xs text-[#355346]"
                >
                  {{ step }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div class="mt-10">
          <div class="text-xs font-bold tracking-[0.24em] text-[#6c8a7f]">执行清单</div>
          <h2 class="mt-2 text-2xl font-bold text-[#17382d]">MVP 交付任务</h2>
          <div class="mt-5 grid gap-4 xl:grid-cols-2">
            <div
              v-for="task in mvpTasks"
              :key="task.key"
              class="rounded-3xl border border-[#d3ddd7] bg-white/92 p-6"
            >
              <div class="flex items-center justify-between gap-3">
                <div class="text-xl font-bold text-[#17382d]">{{ task.title }}</div>
                <div class="rounded-full bg-[#edf4ef] px-3 py-1 text-xs font-semibold text-[#355346]">
                  {{ task.owner }}
                </div>
              </div>
              <div class="mt-4 flex flex-wrap gap-2">
                <span
                  v-for="item in task.items"
                  :key="item"
                  class="rounded-full border border-[#dce6e0] px-3 py-1 text-xs text-[#355346]"
                >
                  {{ item }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </a-spin>
</template>
