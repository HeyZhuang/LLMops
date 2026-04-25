import { onMounted, ref } from 'vue'
import { Message } from '@arco-design/web-vue'
import {
  createImagingAnalysisTask,
  getImagingAuditLogs,
  getImagingFeedbackStats,
  getImagingMvpTasks,
  getImagingOverview,
  getImagingReviewLogs,
  getImagingStudyDetail,
  getImagingStudies,
  getImagingWorkflowTemplates,
  saveImagingReportDraft,
  submitImagingReview,
  uploadImagingDicom,
} from '@/services/imaging'
import type {
  ImagingAuditLog,
  ImagingFeedbackStats,
  ImagingMvpTask,
  ImagingPlanningOverview,
  ImagingReviewLog,
  ImagingStudy,
  ImagingStudyDetail,
  ImagingWorkflowTemplate,
  UploadImagingDicomRequest,
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

const createDefaultFeedbackStats = (): ImagingFeedbackStats => ({
  total_reviews: 0,
  approved: 0,
  needs_revision: 0,
  rejected: 0,
  approval_rate: 0,
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

export const useImagingAudit = () => {
  const loading = ref(false)
  const auditLogs = ref<ImagingAuditLog[]>([])
  const reviewLogs = ref<ImagingReviewLog[]>([])
  const feedbackStats = ref<ImagingFeedbackStats>(createDefaultFeedbackStats())

  const loadImagingAudit = async (studyId: string) => {
    try {
      loading.value = true
      const [auditResp, reviewResp, feedbackResp] = await Promise.all([
        getImagingAuditLogs(studyId),
        getImagingReviewLogs(studyId),
        getImagingFeedbackStats(studyId),
      ])
      auditLogs.value = auditResp.data
      reviewLogs.value = reviewResp.data
      feedbackStats.value = feedbackResp.data
    } finally {
      loading.value = false
    }
  }

  return {
    loading,
    auditLogs,
    reviewLogs,
    feedbackStats,
    loadImagingAudit,
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

export const useImagingStudyActions = () => {
  const submitting = ref(false)

  const handleUploadDicom = async (payload: UploadImagingDicomRequest) => {
    try {
      submitting.value = true
      const resp = await uploadImagingDicom(payload)
      Message.success('检查已上传并进入待处理队列')
      return resp.data
    } finally {
      submitting.value = false
    }
  }

  const handleCreateAnalysisTask = async (studyId: string) => {
    try {
      submitting.value = true
      const resp = await createImagingAnalysisTask(studyId)
      Message.success('分析任务已创建')
      return resp.data
    } finally {
      submitting.value = false
    }
  }

  return {
    submitting,
    handleUploadDicom,
    handleCreateAnalysisTask,
  }
}
