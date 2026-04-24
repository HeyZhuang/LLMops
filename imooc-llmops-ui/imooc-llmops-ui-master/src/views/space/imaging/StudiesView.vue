<script setup lang="ts">
import moment from 'moment'
import { computed } from 'vue'
import { useImagingStudies } from '@/hooks/use-imaging'

const { loading, studies } = useImagingStudies()

const urgentCount = computed(() => studies.value.filter((study) => study.priority === 'urgent').length)

const reportReadyCount = computed(() =>
  studies.value.filter((study) => study.report_status === 'draft_ready').length,
)

const priorityMap: Record<string, string> = {
  urgent: '急诊优先',
  routine: '常规',
}

const reportStatusMap: Record<string, string> = {
  pending: '待生成',
  draft_ready: '草稿待审',
  signed: '已签发',
}
</script>

<template>
  <a-spin :loading="loading" class="block h-full">
    <div class="min-h-full overflow-auto px-6 py-6">
      <div class="rounded-[28px] border border-[#d7e0dc] bg-[linear-gradient(135deg,#f8fbf9_0%,#edf4f0_42%,#f7f1e6_100%)] p-8 shadow-[0_20px_60px_rgba(15,23,42,0.08)]">
        <div class="flex flex-col gap-6 xl:flex-row xl:items-end xl:justify-between">
          <div>
            <div class="text-xs font-bold tracking-[0.24em] text-[#6c8a7f]">影像工作台</div>
            <h1 class="mt-2 text-4xl font-black tracking-tight text-[#17382d]">影像检查列表</h1>
            <p class="mt-3 max-w-2xl text-sm leading-7 text-[#5d746b]">
              聚焦影像科真实业务链路，把检查、AI 发现、报告草稿和审核状态放在同一个工作台里。
            </p>
          </div>

          <div class="grid gap-3 md:grid-cols-3">
            <div class="rounded-2xl border border-[#d3ddd7] bg-white/90 px-5 py-4">
              <div class="text-xs font-bold tracking-[0.2em] text-[#6c8a7f]">检查总数</div>
              <div class="mt-2 text-3xl font-black text-[#17382d]">{{ studies.length }}</div>
            </div>
            <div class="rounded-2xl border border-[#d3ddd7] bg-white/90 px-5 py-4">
              <div class="text-xs font-bold tracking-[0.2em] text-[#6c8a7f]">急诊优先</div>
              <div class="mt-2 text-3xl font-black text-[#17382d]">{{ urgentCount }}</div>
            </div>
            <div class="rounded-2xl border border-[#d3ddd7] bg-white/90 px-5 py-4">
              <div class="text-xs font-bold tracking-[0.2em] text-[#6c8a7f]">草稿待审</div>
              <div class="mt-2 text-3xl font-black text-[#17382d]">{{ reportReadyCount }}</div>
            </div>
          </div>
        </div>

        <div class="mt-8 grid gap-5">
          <router-link
            v-for="study in studies"
            :key="study.id"
            :to="{ name: 'space-imaging-study-detail', params: { study_id: study.id } }"
            class="block rounded-3xl border border-[#d3ddd7] bg-white/92 p-6 transition hover:-translate-y-0.5 hover:shadow-[0_14px_34px_rgba(15,23,42,0.08)]"
          >
            <div class="flex flex-col gap-5 xl:flex-row xl:items-start xl:justify-between">
              <div class="max-w-3xl">
                <div class="flex flex-wrap items-center gap-2">
                  <span class="rounded-full bg-[#edf4ef] px-3 py-1 text-xs font-semibold text-[#355346]">
                    {{ study.modality }}
                  </span>
                  <span class="rounded-full border border-[#dce6e0] px-3 py-1 text-xs text-[#355346]">
                    {{ study.body_part }}
                  </span>
                  <span
                    class="rounded-full px-3 py-1 text-xs font-semibold"
                    :class="study.priority === 'urgent' ? 'bg-[#fff0e6] text-[#b75700]' : 'bg-[#eef3ff] text-[#2d4fb8]'"
                  >
                    {{ priorityMap[study.priority] || study.priority }}
                  </span>
                </div>

                <div class="mt-4 text-2xl font-bold text-[#17382d]">
                  {{ study.patient_code }} / {{ study.patient_name_masked }}
                </div>
                <div class="mt-2 text-sm leading-7 text-[#5d746b]">
                  {{ study.study_description }}
                </div>
                <div class="mt-4 text-sm text-[#5d746b]">
                  {{ study.ai_summary }}
                </div>
              </div>

              <div class="grid gap-3 sm:grid-cols-3 xl:min-w-[360px]">
                <div class="rounded-2xl bg-[#f5f8f6] px-4 py-3">
                  <div class="text-xs font-bold tracking-[0.16em] text-[#6c8a7f]">检查时间</div>
                  <div class="mt-2 text-sm font-medium text-[#17382d]">
                    {{ moment(study.study_time * 1000).format('MM-DD HH:mm') }}
                  </div>
                </div>
                <div class="rounded-2xl bg-[#f5f8f6] px-4 py-3">
                  <div class="text-xs font-bold tracking-[0.16em] text-[#6c8a7f]">发现数量</div>
                  <div class="mt-2 text-sm font-medium text-[#17382d]">{{ study.findings_count }}</div>
                </div>
                <div class="rounded-2xl bg-[#f5f8f6] px-4 py-3">
                  <div class="text-xs font-bold tracking-[0.16em] text-[#6c8a7f]">报告状态</div>
                  <div class="mt-2 text-sm font-medium text-[#17382d]">
                    {{ reportStatusMap[study.report_status] || study.report_status }}
                  </div>
                </div>
              </div>
            </div>
          </router-link>
        </div>
      </div>
    </div>
  </a-spin>
</template>
