import { onMounted, ref } from 'vue'
import { Message } from '@arco-design/web-vue'
import {
  getImagingMvpTasks,
  getImagingOverview,
  getImagingStudyDetail,
  getImagingStudies,
  getImagingWorkflowTemplates,
  saveImagingReportDraft,
  submitImagingReview,
} from '@/services/imaging'
import type {
  ImagingMvpTask,
  ImagingPlanningOverview,
  ImagingStudy,
  ImagingStudyDetail,
  ImagingWorkflowTemplate,
} from '@/models/imaging'

const createDefaultOverview = (): ImagingPlanningOverview => ({
  title: '',
  summary: '',
  positioning: [],
  scenes: [],
  phases: [],
  guardrails: [],
  metrics: {
    apps: 0,
    datasets: 0,
    documents: 0,
    workflows: 0,
    workflow_templates: 0,
  },
  mvp: {
    name: '',
    value: '',
  },
})

const createDefaultStudyDetail = (): ImagingStudyDetail => ({
  id: '',
  patient_code: '',
  patient_name_masked: '',
  modality: '',
  body_part: '',
  study_description: '',
  study_time: 0,
  status: '',
  quality_status: '',
  ai_summary: '',
  findings_count: 0,
  report_status: '',
  priority: '',
  series: [],
  findings: [],
  report_draft: {
    status: '',
    content: '',
    template_name: '',
    template_version: '',
  },
  timeline: [],
  review: {
    label: '',
    comment: '',
    updated_at: 0,
  },
})

export const useImagingPlanning = () => {
  const loading = ref(false)
  const overview = ref<ImagingPlanningOverview>(createDefaultOverview())
  const workflowTemplates = ref<ImagingWorkflowTemplate[]>([])
  const mvpTasks = ref<ImagingMvpTask[]>([])

  const loadImagingPlanning = async () => {
    try {
      loading.value = true
      const [overviewResp, templatesResp, tasksResp] = await Promise.all([
        getImagingOverview(),
        getImagingWorkflowTemplates(),
        getImagingMvpTasks(),
      ])
      overview.value = overviewResp.data
      workflowTemplates.value = templatesResp.data
      mvpTasks.value = tasksResp.data
    } finally {
      loading.value = false
    }
  }

  onMounted(() => {
    loadImagingPlanning()
  })

  return {
    loading,
    overview,
    workflowTemplates,
    mvpTasks,
    loadImagingPlanning,
  }
}

export const useImagingStudies = () => {
  const loading = ref(false)
  const studies = ref<ImagingStudy[]>([])

  const loadImagingStudies = async () => {
    try {
      loading.value = true
      const resp = await getImagingStudies()
      studies.value = resp.data
    } finally {
      loading.value = false
    }
  }

  onMounted(() => {
    loadImagingStudies()
  })

  return {
    loading,
    studies,
    loadImagingStudies,
  }
}

export const useImagingStudyDetail = () => {
  const loading = ref(false)
  const study = ref<ImagingStudyDetail>(createDefaultStudyDetail())

  const loadImagingStudyDetail = async (studyId: string) => {
    try {
      loading.value = true
      const resp = await getImagingStudyDetail(studyId)
      study.value = resp.data
    } finally {
      loading.value = false
    }
  }

  return {
    loading,
    study,
    loadImagingStudyDetail,
  }
}

export const useImagingReviewActions = () => {
  const saving = ref(false)

  const handleSaveDraft = async (studyId: string, content: string) => {
    try {
      saving.value = true
      await saveImagingReportDraft(studyId, { content })
      Message.success('报告草稿已保存')
    } finally {
      saving.value = false
    }
  }

  const handleSubmitReview = async (studyId: string, label: string, comment: string) => {
    try {
      saving.value = true
      await submitImagingReview(studyId, { label, comment })
      Message.success('审核结果已提交')
    } finally {
      saving.value = false
    }
  }

  return {
    saving,
    handleSaveDraft,
    handleSubmitReview,
  }
}
