<script setup lang="ts">
import moment from 'moment'
import { computed, reactive, ref } from 'vue'
import { Message } from '@arco-design/web-vue'
import { useRouter } from 'vue-router'
import { useImagingStudies, useImagingStudyActions } from '@/hooks/use-imaging'

const router = useRouter()
const { loading, studies, loadImagingStudies } = useImagingStudies()
const { submitting, handleUploadDicom, handleCreateAnalysisTask } = useImagingStudyActions()

const uploadModalVisible = ref(false)
const selectedFile = ref<File | null>(null)
const uploadForm = reactive({
  patient_name_masked: '',
  patient_code: '',
  modality: 'CT',
  body_part: 'Chest',
  study_description: '',
  priority: 'normal',
})

const urgentCount = computed(() => studies.value.filter((study) => study.priority === 'urgent').length)

const reportReadyCount = computed(() =>
  studies.value.filter((study) => study.report_status === 'draft_ready').length,
)

const priorityMap: Record<string, string> = {
  urgent: '急诊优先',
  normal: '常规',
  routine: '常规',
}

const reportStatusMap: Record<string, string> = {
  pending: '待生成',
  pending_draft: '待起草',
  draft_ready: '草稿待审',
  doctor_editing: '医生修订中',
  signed: '已签发',
  not_started: '未开始',
}

const statusMap: Record<string, string> = {
  waiting: '待处理',
  awaiting_ai: '等待 AI',
  ai_completed: 'AI 已完成',
  failed: '分析失败',
  doctor_review: '待审核',
  doctor_reviewed: '已审核',
  doctor_revision_needed: '待修订',
  doctor_rejected: '已驳回',
}

const resetUploadForm = () => {
  uploadForm.patient_name_masked = ''
  uploadForm.patient_code = ''
  uploadForm.modality = 'CT'
  uploadForm.body_part = 'Chest'
  uploadForm.study_description = ''
  uploadForm.priority = 'normal'
  selectedFile.value = null
}

const openUploadModal = () => {
  resetUploadForm()
  uploadModalVisible.value = true
}

const submitUpload = async () => {
  if (!selectedFile.value) {
    Message.warning('请先选择 DICOM 文件')
    return
  }

  const result = await handleUploadDicom({
    file: selectedFile.value,
    patient_name_masked: uploadForm.patient_name_masked || '匿名患者',
    patient_code: uploadForm.patient_code,
    modality: uploadForm.modality,
    body_part: uploadForm.body_part,
    study_description:
      uploadForm.study_description || `${uploadForm.body_part} ${uploadForm.modality} DICOM 上传`,
    priority: uploadForm.priority,
    source_type: 'manual_upload',
  })

  uploadModalVisible.value = false
  await loadImagingStudies()

  if (result?.study_id) {
    await router.push({ name: 'space-imaging-study-detail', params: { study_id: result.study_id } })
  }
}

const createAnalysis = async (studyId: string) => {
  await handleCreateAnalysisTask(studyId)
  await loadImagingStudies()
}

const handleFileChange = (event: Event) => {
  const input = event.target as HTMLInputElement
  selectedFile.value = input.files?.[0] || null
}
</script>

<template>
  <a-spin :loading="loading" class="block h-full">
    <div class="min-h-full overflow-auto px-6 py-6">
      <div
        class="rounded-[28px] border border-[#d7e0dc] bg-[linear-gradient(135deg,#f8fbf9_0%,#edf4f0_42%,#f7f1e6_100%)] p-8 shadow-[0_20px_60px_rgba(15,23,42,0.08)]"
      >
        <div class="flex flex-col gap-6 xl:flex-row xl:items-end xl:justify-between">
          <div>
            <div class="text-xs font-bold tracking-[0.24em] text-[#6c8a7f]">影像工作台</div>
            <h1 class="mt-2 text-4xl font-black tracking-tight text-[#17382d]">影像检查列表</h1>
            <p class="mt-3 max-w-2xl text-sm leading-7 text-[#5d746b]">
              聚焦影像科真实业务链路，把检查、AI 发现、报告草稿和审核状态放在同一个工作台里。
            </p>
          </div>

          <div class="flex flex-wrap gap-3">
            <a-button class="rounded-2xl" :loading="loading" @click="loadImagingStudies">刷新列表</a-button>
            <a-button type="primary" class="rounded-2xl" :loading="submitting" @click="openUploadModal">
              上传 DICOM
            </a-button>
          </div>
        </div>

        <div class="mt-8 grid gap-3 md:grid-cols-3">
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

        <div class="mt-8 grid gap-5">
          <div
            v-for="study in studies"
            :key="study.id"
            class="rounded-3xl border border-[#d3ddd7] bg-white/92 p-6 transition hover:shadow-[0_14px_34px_rgba(15,23,42,0.08)]"
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
                  <span class="rounded-full border border-[#dce6e0] px-3 py-1 text-xs text-[#355346]">
                    {{ statusMap[study.status] || study.status }}
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

              <div class="grid gap-3 sm:grid-cols-3 xl:min-w-[400px]">
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

            <div class="mt-5 flex flex-wrap gap-3">
              <a-button
                type="primary"
                class="rounded-2xl"
                :loading="submitting"
                @click="createAnalysis(study.id)"
              >
                触发分析
              </a-button>
              <a-button
                class="rounded-2xl"
                @click="router.push({ name: 'space-imaging-study-detail', params: { study_id: study.id } })"
              >
                查看详情
              </a-button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <a-modal
      :visible="uploadModalVisible"
      title="上传 DICOM 检查"
      :ok-loading="submitting"
      @ok="submitUpload"
      @cancel="uploadModalVisible = false"
    >
      <div class="grid gap-4 py-2">
        <div class="rounded-2xl border border-dashed border-[#cfdad4] bg-[#f7faf8] px-4 py-4">
          <div class="text-sm font-semibold text-[#17382d]">选择 DICOM 文件</div>
          <div class="mt-2 text-xs leading-6 text-[#5d746b]">
            支持 `.dcm`、`.dicom` 和压缩包 `.zip`，用于当前 MVP 演示链路。
          </div>
          <input
            class="mt-3 block w-full text-sm text-[#355346] file:mr-4 file:rounded-xl file:border-0 file:bg-[#17382d] file:px-4 file:py-2 file:text-sm file:font-semibold file:text-white"
            type="file"
            accept=".dcm,.dicom,.zip"
            @change="handleFileChange"
          />
          <div v-if="selectedFile" class="mt-3 text-xs text-[#5d746b]">
            已选择：{{ selectedFile.name }}
          </div>
        </div>
        <a-input v-model="uploadForm.patient_name_masked" placeholder="脱敏患者姓名，例如 Zhang**" />
        <a-input v-model="uploadForm.patient_code" placeholder="患者编号或检查号" />
        <a-select v-model="uploadForm.modality" placeholder="检查模态">
          <a-option value="CT">CT</a-option>
          <a-option value="MR">MR</a-option>
          <a-option value="DR">DR</a-option>
        </a-select>
        <a-select v-model="uploadForm.body_part" placeholder="检查部位">
          <a-option value="Chest">Chest</a-option>
          <a-option value="Brain">Brain</a-option>
          <a-option value="Abdomen">Abdomen</a-option>
        </a-select>
        <a-select v-model="uploadForm.priority" placeholder="优先级">
          <a-option value="normal">常规</a-option>
          <a-option value="urgent">急诊优先</a-option>
        </a-select>
        <a-textarea
          v-model="uploadForm.study_description"
          :auto-size="{ minRows: 3, maxRows: 5 }"
          placeholder="检查描述，例如 Chest CT plain scan for follow-up"
        />
      </div>
    </a-modal>
  </a-spin>
</template>
