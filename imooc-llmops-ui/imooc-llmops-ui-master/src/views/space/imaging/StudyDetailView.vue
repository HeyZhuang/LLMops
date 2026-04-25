<script setup lang="ts">
import moment from 'moment'
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import {
  useImagingAnalysis,
  useImagingAudit,
  useImagingReviewActions,
  useImagingSeries,
  useImagingStudyDetail,
} from '@/hooks/use-imaging'

const route = useRoute()
const { loading, study, loadImagingStudyDetail } = useImagingStudyDetail()
const { saving, handleSaveDraft, handleSubmitReview } = useImagingReviewActions()
const { loading: auditLoading, auditLogs, reviewLogs, feedbackStats, loadImagingAudit } = useImagingAudit()
const { loading: analysisLoading, analysisResult, structuredFindings, loadImagingAnalysis } = useImagingAnalysis()
const { loading: seriesLoading, series, instances, previewUrls, loadImagingSeries, loadSeriesInstances, loadInstancePreview } = useImagingSeries()

const studyId = computed(() => String(route.params.study_id ?? ''))
const draftContent = ref('')
const reviewComment = ref('')
const expandedSeriesId = ref('')
const activeSeriesId = ref('')
const activeInstanceId = ref('')
const activePreviewUrl = ref('')

const statusMap: Record<string, string> = {
  waiting: '待处理',
  awaiting_ai: '等待 AI 处理',
  ai_completed: 'AI 已完成',
  doctor_review: '待医生审核',
  doctor_reviewed: '医生已审核',
  doctor_revision_needed: '待医生修订',
  doctor_rejected: '医生已驳回',
  completed: '已完成',
}

const reportStatusMap: Record<string, string> = {
  pending: '待生成',
  pending_draft: '待起草',
  draft_ready: '草稿待审',
  doctor_editing: '医生修订中',
  signed: '已签发',
  not_started: '未开始',
}

const reviewLabelMap: Record<string, string> = {
  approved: '审核通过',
  needs_revision: '需要修改',
  rejected: '驳回',
}

const auditActionMap: Record<string, string> = {
  dicom_uploaded: '上传 DICOM',
  study_detail_viewed: '查看检查详情',
  analysis_task_created: '创建分析任务',
  report_draft_saved: '保存报告草稿',
  study_review_submitted: '提交医生审核',
}

const refreshStudy = async () => {
  if (!studyId.value) return
  await Promise.all([
    loadImagingStudyDetail(studyId.value),
    loadImagingAudit(studyId.value),
    loadImagingAnalysis(studyId.value),
    loadImagingSeries(studyId.value),
  ])
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

const formatFindingMeta = (finding: Record<string, unknown>) => {
  const parts: string[] = []
  if (finding.location) parts.push(`位置: ${String(finding.location)}`)
  if (finding.size) parts.push(`大小: ${String(finding.size)}`)
  if (finding.risk_level) parts.push(`风险: ${String(finding.risk_level)}`)
  return parts.join(' / ')
}

const dicomMetadataItems = computed(() => [
  { label: '解析状态', value: study.value.dicom_metadata?.parser_status || '未解析' },
  { label: '解析器', value: study.value.dicom_metadata?.parser || '-' },
  { label: '文件名', value: study.value.upload?.file_name || study.value.dicom_metadata?.file_name || '-' },
  {
    label: '文件大小',
    value: study.value.upload?.file_size ? `${study.value.upload.file_size} bytes` : '-',
  },
  { label: 'Patient ID', value: study.value.dicom_metadata?.patient_id || '-' },
  { label: 'Study UID', value: study.value.dicom_metadata?.study_instance_uid || '-' },
  { label: 'Series UID', value: study.value.dicom_metadata?.series_instance_uid || '-' },
  { label: 'Study Date', value: study.value.dicom_metadata?.study_date || '-' },
  { label: 'Study Time', value: study.value.dicom_metadata?.study_time || '-' },
  { label: '检查描述', value: study.value.dicom_metadata?.study_description || '-' },
  { label: '序列描述', value: study.value.dicom_metadata?.series_description || '-' },
  { label: '设备厂商', value: study.value.dicom_metadata?.manufacturer || '-' },
  {
    label: '解压文件数',
    value: String(study.value.dicom_metadata?.extracted_files || 0),
  },
  {
    label: '识别实例数',
    value: String(study.value.dicom_metadata?.parsed_instances || 0),
  },
  {
    label: '图像尺寸',
    value: study.value.dicom_metadata?.rows && study.value.dicom_metadata?.columns
      ? `${study.value.dicom_metadata.rows} x ${study.value.dicom_metadata.columns}`
      : '-',
  },
  {
    label: '窗宽 / 窗位',
    value: `${study.value.dicom_metadata?.window_width || '-'} / ${study.value.dicom_metadata?.window_center || '-'}`,
  },
])

const storageModeLabel = computed(() => {
  const value = study.value.upload?.storage_mode || 'local'
  if (value === 'hybrid') return '本地 + COS'
  if (value === 'cos') return '仅 COS'
  return '仅本地'
})

const storageStatusItems = computed(() => [
  { label: '存储模式', value: storageModeLabel.value },
  { label: '本地路径', value: study.value.upload?.stored_path || '-' },
  { label: '主上传记录 ID', value: study.value.upload?.upload_file_id || '-' },
  { label: 'COS Key', value: study.value.upload?.cos_key || '-' },
  { label: 'COS URL', value: study.value.upload?.cos_url || '-' },
])

const toggleSeries = async (seriesId: string) => {
  if (!studyId.value) return
  expandedSeriesId.value = expandedSeriesId.value === seriesId ? '' : seriesId
  if (expandedSeriesId.value === seriesId && !instances.value[seriesId]) {
    await loadSeriesInstances(studyId.value, seriesId)
  }
}

const selectInstance = async (seriesId: string, instanceId: string) => {
  if (!studyId.value) return
  activeSeriesId.value = seriesId
  activeInstanceId.value = instanceId
  activePreviewUrl.value = await loadInstancePreview(studyId.value, seriesId, instanceId)
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

watch(
  () => series.value,
  async (value) => {
    if (!studyId.value || !value.length || activeSeriesId.value) return
    const firstSeries = value[0]
    expandedSeriesId.value = firstSeries.id
    await loadSeriesInstances(studyId.value, firstSeries.id)
  },
  { deep: true },
)

watch(
  () => instances.value,
  async (value) => {
    if (!studyId.value || activeInstanceId.value) return
    const sourceSeriesId = activeSeriesId.value || expandedSeriesId.value
    const sourceInstances = value[sourceSeriesId] || []
    if (sourceSeriesId && sourceInstances.length) {
      await selectInstance(sourceSeriesId, sourceInstances[0].id)
    }
  },
  { deep: true },
)
</script>

<template>
  <a-spin :loading="loading || auditLoading || analysisLoading || seriesLoading" class="block h-full">
    <div class="min-h-full overflow-auto px-6 py-6">
      <div class="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <div
          class="rounded-[28px] border border-[#d7e0dc] bg-[linear-gradient(135deg,#f8fbf9_0%,#edf4f0_42%,#f7f1e6_100%)] p-8 shadow-[0_20px_60px_rgba(15,23,42,0.08)]"
        >
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

          <div class="mt-6 rounded-3xl border border-[#d3ddd7] bg-white/92 p-6">
            <div class="flex items-center justify-between gap-3">
              <div>
                <div class="text-xs font-bold tracking-[0.2em] text-[#6c8a7f]">分析结果</div>
                <h2 class="mt-2 text-2xl font-bold text-[#17382d]">{{ analysisResult.model_name || '影像分析结果' }}</h2>
              </div>
              <div class="rounded-full bg-[#edf4ef] px-3 py-1 text-xs font-semibold text-[#355346]">
                {{ statusMap[analysisResult.status] || analysisResult.status || '待分析' }}
              </div>
            </div>

            <div class="mt-3 text-sm text-[#5d746b]">
              {{ analysisResult.model_version || 'v0.1' }} / {{ analysisResult.task_type || 'detection' }}
            </div>
            <div class="mt-4 rounded-2xl bg-[#f5f8f6] px-4 py-4 text-sm leading-6 text-[#355346]">
              {{ analysisResult.summary || '当前暂无分析摘要。' }}
            </div>

            <div class="mt-4 grid gap-3">
              <div
                v-for="(finding, index) in analysisResult.findings"
                :key="`${index}-${String(finding.title || index)}`"
                class="rounded-2xl border border-[#e4ebe7] bg-[#fbfcfb] px-4 py-4"
              >
                <div class="flex items-center justify-between gap-3">
                  <div class="text-sm font-semibold text-[#17382d]">{{ String(finding.title || '结构化发现') }}</div>
                  <div class="text-xs text-[#5d746b]">
                    {{ Math.round(Number(finding.confidence || 0) * 100) }}%
                  </div>
                </div>
                <div class="mt-2 text-sm leading-6 text-[#5d746b]">{{ String(finding.description || '') }}</div>
                <div v-if="formatFindingMeta(finding)" class="mt-2 text-xs text-[#6c8a7f]">
                  {{ formatFindingMeta(finding) }}
                </div>
              </div>
              <div
                v-if="!analysisResult.findings.length"
                class="rounded-2xl bg-[#f5f8f6] px-4 py-4 text-sm text-[#5d746b]"
              >
                暂无分析结果，等待任务执行或手动触发分析。
              </div>
            </div>
          </div>

          <div class="mt-6 rounded-3xl border border-[#d3ddd7] bg-white/92 p-6">
            <div class="text-xs font-bold tracking-[0.2em] text-[#6c8a7f]">DICOM 元数据</div>
            <div class="mt-4 grid gap-3 md:grid-cols-2">
              <div
                v-for="item in dicomMetadataItems"
                :key="item.label"
                class="rounded-2xl bg-[#f5f8f6] px-4 py-3"
              >
                <div class="text-xs font-bold tracking-[0.14em] text-[#6c8a7f]">{{ item.label }}</div>
                <div class="mt-2 break-all text-sm text-[#17382d]">{{ item.value }}</div>
              </div>
            </div>
          </div>

          <div class="mt-6 rounded-3xl border border-[#d3ddd7] bg-white/92 p-6">
            <div class="flex items-center justify-between gap-3">
              <div class="text-xs font-bold tracking-[0.2em] text-[#6c8a7f]">存储状态</div>
              <span class="rounded-full bg-[#edf4ef] px-3 py-1 text-xs font-semibold text-[#355346]">
                {{ storageModeLabel }}
              </span>
            </div>
            <div class="mt-4 grid gap-3">
              <div
                v-for="item in storageStatusItems"
                :key="item.label"
                class="rounded-2xl bg-[#f5f8f6] px-4 py-3"
              >
                <div class="text-xs font-bold tracking-[0.14em] text-[#6c8a7f]">{{ item.label }}</div>
                <div class="mt-2 break-all text-sm text-[#17382d]">{{ item.value }}</div>
              </div>
            </div>
            <a
              v-if="study.upload?.cos_url"
              :href="study.upload.cos_url"
              target="_blank"
              rel="noreferrer"
              class="mt-4 inline-flex text-sm font-semibold text-[#2d4fb8]"
            >
              查看 COS 对象地址
            </a>
          </div>

          <div class="mt-6 rounded-3xl border border-[#d3ddd7] bg-white/92 p-6">
            <div class="text-xs font-bold tracking-[0.2em] text-[#6c8a7f]">上传历史 / 对象引用</div>
            <div class="mt-4 grid gap-3">
              <div
                v-for="item in study.upload?.upload_history || []"
                :key="`${item.storage}-${item.id}`"
                class="rounded-2xl bg-[#f5f8f6] px-4 py-4"
              >
                <div class="flex items-center justify-between gap-3">
                  <div class="text-sm font-semibold text-[#17382d]">{{ item.name }}</div>
                  <span class="rounded-full bg-white px-3 py-1 text-xs font-semibold text-[#355346]">
                    {{ item.storage === 'cos' ? 'COS' : '本地' }}
                  </span>
                </div>
                <div class="mt-2 text-xs text-[#6c8a7f]">记录 ID：{{ item.id }}</div>
                <div class="mt-2 break-all text-sm text-[#355346]">{{ item.key }}</div>
                <div class="mt-2 text-xs text-[#6c8a7f]">
                  {{ item.mime_type || 'application/octet-stream' }} / {{ item.size || 0 }} bytes
                </div>
                <a
                  v-if="item.url"
                  :href="item.url"
                  target="_blank"
                  rel="noreferrer"
                  class="mt-3 inline-flex text-sm font-semibold text-[#2d4fb8]"
                >
                  打开对象地址
                </a>
              </div>
              <div
                v-if="!(study.upload?.upload_history || []).length"
                class="rounded-2xl border border-dashed border-[#dce6e0] px-4 py-4 text-sm text-[#5d746b]"
              >
                当前检查还没有可展示的上传历史记录。
              </div>
            </div>
          </div>
        </div>

        <div class="grid gap-6">
          <div class="rounded-3xl border border-[#d3ddd7] bg-white/92 p-6 shadow-[0_12px_30px_rgba(15,23,42,0.05)]">
            <div class="text-xs font-bold tracking-[0.2em] text-[#6c8a7f]">报告草稿</div>
            <h2 class="mt-2 text-2xl font-bold text-[#17382d]">{{ study.report_draft.template_name }}</h2>
            <div class="mt-2 text-sm text-[#5d746b]">
              {{ study.report_draft.template_version }} /
              {{ reportStatusMap[study.report_draft.status] || study.report_draft.status }}
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
            <div class="text-xs font-bold tracking-[0.2em] text-[#6c8a7f]">影像浏览器</div>
            <div class="mt-4 overflow-hidden rounded-3xl border border-[#d9e4de] bg-[#0f1720]">
              <div class="flex min-h-[360px] items-center justify-center bg-[radial-gradient(circle_at_top,#2e3645_0%,#111827_58%,#0b1220_100%)] p-4">
                <img
                  v-if="activePreviewUrl"
                  :src="activePreviewUrl"
                  alt="DICOM preview"
                  class="max-h-[520px] w-full rounded-2xl object-contain"
                />
                <div v-else class="text-sm text-[#c9d6df]">选择一个实例后，这里会显示影像切片预览。</div>
              </div>
              <div class="border-t border-[#263244] bg-[#111927] px-4 py-3 text-xs text-[#c9d6df]">
                当前序列：{{ activeSeriesId || '未选择' }} / 当前实例：{{ activeInstanceId || '未选择' }}
              </div>
            </div>
          </div>

          <div class="rounded-3xl border border-[#d3ddd7] bg-white/92 p-6 shadow-[0_12px_30px_rgba(15,23,42,0.05)]">
            <div class="text-xs font-bold tracking-[0.2em] text-[#6c8a7f]">序列概览</div>
            <div class="mt-4 grid gap-3">
              <div
                v-for="seriesItem in series.length ? series : study.series"
                :key="seriesItem.id || seriesItem.name"
                class="rounded-2xl bg-[#f5f8f6] px-4 py-3"
              >
                <div class="flex items-center justify-between gap-3">
                  <div>
                    <div class="text-sm font-semibold text-[#17382d]">{{ seriesItem.name }}</div>
                    <div class="mt-1 text-xs text-[#5d746b]">
                      {{ seriesItem.images }} 张图像 / {{ seriesItem.slice_thickness }}
                    </div>
                  </div>
                  <a-button
                    v-if="seriesItem.id"
                    size="mini"
                    class="rounded-xl"
                    @click="toggleSeries(seriesItem.id)"
                  >
                    {{ expandedSeriesId === seriesItem.id ? '收起实例' : '查看实例' }}
                  </a-button>
                </div>
                <div v-if="seriesItem.orientation" class="mt-2 text-xs text-[#6c8a7f]">
                  方向信息：{{ seriesItem.orientation }}
                </div>
                <div v-if="expandedSeriesId === seriesItem.id" class="mt-3 grid gap-2">
                  <div
                    v-for="instance in instances[seriesItem.id] || []"
                    :key="instance.id"
                    class="cursor-pointer rounded-2xl border px-3 py-3 transition"
                    :class="activeInstanceId === instance.id ? 'border-[#17382d] bg-[#edf4ef]' : 'border-[#dce6e0] bg-white hover:border-[#bfd0c6]'"
                    @click="selectInstance(seriesItem.id, instance.id)"
                  >
                    <div class="flex items-center justify-between gap-3">
                      <div class="text-sm font-medium text-[#17382d]">实例 {{ instance.instance_number || 1 }}</div>
                      <div class="text-[11px] text-[#5d746b]">
                        {{ previewUrls[instance.id] ? '已加载预览' : '点击查看' }}
                      </div>
                    </div>
                    <div class="mt-1 break-all text-xs text-[#5d746b]">
                      {{ instance.file_path || '暂无文件路径' }}
                    </div>
                    <div class="mt-1 text-xs text-[#6c8a7f]">
                      {{ instance.rows || 0 }} x {{ instance.columns || 0 }} / 窗宽 {{ instance.window_width || '-' }} / 窗位 {{ instance.window_center || '-' }}
                    </div>
                  </div>
                  <div
                    v-if="!(instances[seriesItem.id] || []).length"
                    class="rounded-2xl border border-dashed border-[#dce6e0] px-3 py-3 text-xs text-[#5d746b]"
                  >
                    当前序列暂无实例详情。
                  </div>
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
            <div class="text-xs font-bold tracking-[0.2em] text-[#6c8a7f]">结构化发现</div>
            <div class="mt-2 text-sm text-[#5d746b]">
              {{ structuredFindings.summary || '暂无结构化发现摘要。' }}
            </div>
            <pre
              class="mt-4 overflow-auto rounded-2xl bg-[#17382d] p-4 text-xs leading-6 text-[#d9e7e0]"
            >{{ JSON.stringify(structuredFindings.findings, null, 2) }}</pre>
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

          <div class="rounded-3xl border border-[#d3ddd7] bg-white/92 p-6 shadow-[0_12px_30px_rgba(15,23,42,0.05)]">
            <div class="text-xs font-bold tracking-[0.2em] text-[#6c8a7f]">审核统计</div>
            <div class="mt-4 grid grid-cols-2 gap-3">
              <div class="rounded-2xl bg-[#f5f8f6] px-4 py-3">
                <div class="text-xs text-[#6c8a7f]">总审核数</div>
                <div class="mt-2 text-xl font-bold text-[#17382d]">{{ feedbackStats.total_reviews }}</div>
              </div>
              <div class="rounded-2xl bg-[#f5f8f6] px-4 py-3">
                <div class="text-xs text-[#6c8a7f]">通过率</div>
                <div class="mt-2 text-xl font-bold text-[#17382d]">{{ feedbackStats.approval_rate }}%</div>
              </div>
              <div class="rounded-2xl bg-[#f5f8f6] px-4 py-3">
                <div class="text-xs text-[#6c8a7f]">通过</div>
                <div class="mt-2 text-xl font-bold text-[#17382d]">{{ feedbackStats.approved }}</div>
              </div>
              <div class="rounded-2xl bg-[#f5f8f6] px-4 py-3">
                <div class="text-xs text-[#6c8a7f]">需修改 / 驳回</div>
                <div class="mt-2 text-xl font-bold text-[#17382d]">
                  {{ feedbackStats.needs_revision + feedbackStats.rejected }}
                </div>
              </div>
            </div>
          </div>

          <div class="rounded-3xl border border-[#d3ddd7] bg-white/92 p-6 shadow-[0_12px_30px_rgba(15,23,42,0.05)]">
            <div class="text-xs font-bold tracking-[0.2em] text-[#6c8a7f]">审核日志</div>
            <div class="mt-4 grid gap-3">
              <div
                v-for="item in reviewLogs"
                :key="item.id"
                class="rounded-2xl bg-[#f5f8f6] px-4 py-3"
              >
                <div class="flex items-center justify-between gap-3">
                  <div class="text-sm font-semibold text-[#17382d]">
                    {{ reviewLabelMap[item.label] || item.label }}
                  </div>
                  <div class="text-xs text-[#5d746b]">
                    {{ moment(item.created_at * 1000).format('MM-DD HH:mm') }}
                  </div>
                </div>
                <div class="mt-1 text-xs text-[#5d746b]">状态：{{ statusMap[item.status] || item.status }}</div>
                <div v-if="item.comment" class="mt-2 text-sm text-[#355346]">{{ item.comment }}</div>
              </div>
              <div v-if="!reviewLogs.length" class="rounded-2xl bg-[#f5f8f6] px-4 py-3 text-sm text-[#5d746b]">
                暂无审核日志
              </div>
            </div>
          </div>

          <div class="rounded-3xl border border-[#d3ddd7] bg-white/92 p-6 shadow-[0_12px_30px_rgba(15,23,42,0.05)]">
            <div class="text-xs font-bold tracking-[0.2em] text-[#6c8a7f]">访问日志</div>
            <div class="mt-4 grid gap-3">
              <div
                v-for="item in auditLogs"
                :key="item.id"
                class="rounded-2xl bg-[#f5f8f6] px-4 py-3"
              >
                <div class="flex items-center justify-between gap-3">
                  <div class="text-sm font-semibold text-[#17382d]">
                    {{ auditActionMap[item.action] || item.action }}
                  </div>
                  <div class="text-xs text-[#5d746b]">
                    {{ moment(item.created_at * 1000).format('MM-DD HH:mm:ss') }}
                  </div>
                </div>
                <div class="mt-1 text-xs text-[#5d746b]">
                  目标：{{ item.target_type }} / {{ item.success ? '成功' : '失败' }}
                </div>
              </div>
              <div v-if="!auditLogs.length" class="rounded-2xl bg-[#f5f8f6] px-4 py-3 text-sm text-[#5d746b]">
                暂无访问日志
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </a-spin>
</template>
