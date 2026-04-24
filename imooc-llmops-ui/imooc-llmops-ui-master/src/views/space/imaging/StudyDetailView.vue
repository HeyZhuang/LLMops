<script setup lang="ts">
import moment from 'moment'
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useImagingReviewActions, useImagingStudyDetail } from '@/hooks/use-imaging'

const route = useRoute()
const { loading, study, loadImagingStudyDetail } = useImagingStudyDetail()
const { saving, handleSaveDraft, handleSubmitReview } = useImagingReviewActions()

const studyId = computed(() => String(route.params.study_id ?? ''))
const draftContent = ref('')
const reviewComment = ref('')

const statusMap: Record<string, string> = {
  ready: '已完成 AI 处理',
  processing: '处理中',
}

const reportStatusMap: Record<string, string> = {
  pending: '待生成',
  draft_ready: '草稿待审',
  signed: '已签发',
}

const reviewLabelMap: Record<string, string> = {
  approved: '审核通过',
  needs_revision: '需要修改',
  rejected: '驳回',
}

const refreshStudy = async () => {
  if (studyId.value) {
    await loadImagingStudyDetail(studyId.value)
  }
}

const saveDraft = async () => {
  if (!studyId.value) return
  await handleSaveDraft(studyId.value, draftContent.value)
  await refreshStudy()
}

const submitReview = async (label: string) => {
  if (!studyId.value) return
  await handleSubmitReview(studyId.value, label, reviewComment.value)
  await refreshStudy()
}

onMounted(async () => {
  await refreshStudy()
})

watch(
  () => study.value.report_draft.content,
  (value) => {
    draftContent.value = value
  },
  { immediate: true },
)

watch(
  () => study.value.review.comment,
  (value) => {
    reviewComment.value = value
  },
  { immediate: true },
)
</script>

<template>
  <a-spin :loading="loading" class="block h-full">
    <div class="min-h-full overflow-auto px-6 py-6">
      <div class="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <div class="rounded-[28px] border border-[#d7e0dc] bg-[linear-gradient(135deg,#f8fbf9_0%,#edf4f0_42%,#f7f1e6_100%)] p-8 shadow-[0_20px_60px_rgba(15,23,42,0.08)]">
          <div class="flex flex-wrap items-center gap-2">
            <router-link
              to="/space/imaging/studies"
              class="rounded-full border border-[#d3ddd7] bg-white/90 px-4 py-1 text-xs font-semibold text-[#355346]"
            >
              返回检查列表
            </router-link>
            <span class="rounded-full bg-[#edf4ef] px-3 py-1 text-xs font-semibold text-[#355346]">
              {{ study.modality }}
            </span>
            <span class="rounded-full border border-[#dce6e0] px-3 py-1 text-xs text-[#355346]">
              {{ study.body_part }}
            </span>
          </div>

          <h1 class="mt-5 text-4xl font-black tracking-tight text-[#17382d]">
            {{ study.patient_code }} / {{ study.patient_name_masked }}
          </h1>
          <p class="mt-3 max-w-3xl text-sm leading-7 text-[#5d746b]">
            {{ study.study_description }}
          </p>

          <div class="mt-6 grid gap-4 md:grid-cols-3">
            <div class="rounded-2xl bg-white/88 px-5 py-4">
              <div class="text-xs font-bold tracking-[0.16em] text-[#6c8a7f]">检查时间</div>
              <div class="mt-2 text-sm font-medium text-[#17382d]">
                {{ moment(study.study_time * 1000).format('YYYY-MM-DD HH:mm') }}
              </div>
            </div>
            <div class="rounded-2xl bg-white/88 px-5 py-4">
              <div class="text-xs font-bold tracking-[0.16em] text-[#6c8a7f]">AI 状态</div>
              <div class="mt-2 text-sm font-medium text-[#17382d]">
                {{ statusMap[study.status] || study.status }}
              </div>
            </div>
            <div class="rounded-2xl bg-white/88 px-5 py-4">
              <div class="text-xs font-bold tracking-[0.16em] text-[#6c8a7f]">报告状态</div>
              <div class="mt-2 text-sm font-medium text-[#17382d]">
                {{ reportStatusMap[study.report_status] || study.report_status }}
              </div>
            </div>
          </div>

          <div class="mt-8 rounded-3xl border border-[#d3ddd7] bg-white/92 p-6">
            <div class="text-xs font-bold tracking-[0.2em] text-[#6c8a7f]">AI 发现</div>
            <div class="mt-4 grid gap-4">
              <div
                v-for="finding in study.findings"
                :key="finding.title"
                class="rounded-2xl border border-[#e4ebe7] bg-[#fbfcfb] p-5"
              >
                <div class="flex items-center justify-between gap-3">
                  <div class="text-lg font-bold text-[#17382d]">{{ finding.title }}</div>
                  <div class="rounded-full bg-[#edf4ef] px-3 py-1 text-xs font-semibold text-[#355346]">
                    {{ Math.round(finding.confidence * 100) }}%
                  </div>
                </div>
                <div class="mt-2 text-sm leading-6 text-[#5d746b]">{{ finding.description }}</div>
              </div>
            </div>
          </div>
        </div>

        <div class="grid gap-6">
          <div class="rounded-3xl border border-[#d3ddd7] bg-white/92 p-6 shadow-[0_12px_30px_rgba(15,23,42,0.05)]">
            <div class="text-xs font-bold tracking-[0.2em] text-[#6c8a7f]">报告草稿</div>
            <h2 class="mt-2 text-2xl font-bold text-[#17382d]">{{ study.report_draft.template_name }}</h2>
            <div class="mt-2 text-sm text-[#5d746b]">
              {{ study.report_draft.template_version }} / {{ reportStatusMap[study.report_draft.status] || study.report_draft.status }}
            </div>
            <a-textarea
              v-model="draftContent"
              class="mt-4"
              :auto-size="{ minRows: 8, maxRows: 14 }"
            />
            <div class="mt-4 flex gap-3">
              <a-button type="primary" :loading="saving" @click="saveDraft">保存草稿</a-button>
              <a-button :loading="saving" @click="refreshStudy">重新加载</a-button>
            </div>
          </div>

          <div class="rounded-3xl border border-[#d3ddd7] bg-white/92 p-6 shadow-[0_12px_30px_rgba(15,23,42,0.05)]">
            <div class="text-xs font-bold tracking-[0.2em] text-[#6c8a7f]">序列概览</div>
            <div class="mt-4 grid gap-3">
              <div
                v-for="series in study.series"
                :key="series.name"
                class="rounded-2xl bg-[#f5f8f6] px-4 py-3"
              >
                <div class="text-sm font-semibold text-[#17382d]">{{ series.name }}</div>
                <div class="mt-1 text-xs text-[#5d746b]">
                  {{ series.images }} 张图像 / {{ series.slice_thickness }}
                </div>
              </div>
            </div>
          </div>

          <div class="rounded-3xl border border-[#d3ddd7] bg-white/92 p-6 shadow-[0_12px_30px_rgba(15,23,42,0.05)]">
            <div class="text-xs font-bold tracking-[0.2em] text-[#6c8a7f]">流程时间线</div>
            <div class="mt-4 grid gap-3">
              <div
                v-for="item in study.timeline"
                :key="item.label"
                class="flex items-center justify-between rounded-2xl bg-[#f5f8f6] px-4 py-3"
              >
                <div class="text-sm font-medium text-[#17382d]">{{ item.label }}</div>
                <div class="text-xs font-semibold text-[#355346]">{{ item.value }}</div>
              </div>
            </div>
          </div>

          <div class="rounded-3xl border border-[#d3ddd7] bg-white/92 p-6 shadow-[0_12px_30px_rgba(15,23,42,0.05)]">
            <div class="text-xs font-bold tracking-[0.2em] text-[#6c8a7f]">医生审核</div>
            <div class="mt-2 text-sm text-[#5d746b]">
              当前审核结论：{{ reviewLabelMap[study.review.label] || '待处理' }}
            </div>
            <a-textarea
              v-model="reviewComment"
              class="mt-4"
              placeholder="请输入医生审核意见"
              :auto-size="{ minRows: 4, maxRows: 8 }"
            />
            <div class="mt-4 flex flex-wrap gap-3">
              <a-button type="primary" status="success" :loading="saving" @click="submitReview('approved')">
                审核通过
              </a-button>
              <a-button type="primary" status="warning" :loading="saving" @click="submitReview('needs_revision')">
                需要修改
              </a-button>
              <a-button type="primary" status="danger" :loading="saving" @click="submitReview('rejected')">
                驳回草稿
              </a-button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </a-spin>
</template>
