import { onMounted, ref } from 'vue'
import { Message } from '@arco-design/web-vue'
import {
  createImagingAnalysisTask,
  getImagingAnalysisResult,
  getImagingAuditLogs,
  getImagingFeedbackStats,
  getImagingMvpTasks,
  getImagingOverview,
  getImagingReviewLogs,
  getImagingStructuredFindings,
  getImagingStudySeries,
  getImagingSeriesInstances,
  getImagingInstancePreviewBlob,
  getImagingStudyDetail,
  getImagingStudies,
  getImagingWorkflowTemplates,
  saveImagingReportDraft,
  submitImagingReview,
  uploadImagingDicom,
} from '@/services/imaging'
import type {
  ImagingAnalysisResult,
  ImagingAuditLog,
  ImagingFeedbackStats,
  ImagingMvpTask,
  ImagingPlanningOverview,
  ImagingReviewLog,
  ImagingSeriesItem,
  ImagingInstanceItem,
  ImagingStructuredFindings,
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
  upload: {
    file_name: '',
    file_suffix: '',
    file_size: 0,
    stored_path: '',
    storage_mode: 'local',
    cos_key: '',
    cos_url: '',
    upload_file_id: '',
    upload_history: [],
  },
  dicom_metadata: {
    parser: '',
    parser_status: '',
    file_name: '',
    file_path: '',
    file_type: '',
    patient_id: '',
    study_instance_uid: '',
    series_instance_uid: '',
    study_date: '',
    study_time: '',
    study_description: '',
    series_description: '',
    modality: '',
    body_part_examined: '',
    slice_thickness: '',
    series_number: '',
    instance_number: '',
    rows: 0,
    columns: 0,
    window_center: '',
    window_width: '',
    manufacturer: '',
    extracted_files: 0,
    parsed_instances: 0,
  },
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

const createDefaultAnalysisResult = (): ImagingAnalysisResult => ({
  study_id: '',
  task_id: '',
  status: '',
  task_type: '',
  model_name: '',
  model_version: '',
  summary: '',
  findings: [],
  measurements: [],
  overlays: [],
  updated_at: 0,
})

const createDefaultStructuredFindings = (): ImagingStructuredFindings => ({
  study_id: '',
  status: '',
  summary: '',
  findings: [],
  measurements: [],
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

export const useImagingAnalysis = () => {
  const loading = ref(false)
  const analysisResult = ref<ImagingAnalysisResult>(createDefaultAnalysisResult())
  const structuredFindings = ref<ImagingStructuredFindings>(createDefaultStructuredFindings())

  const loadImagingAnalysis = async (studyId: string) => {
    try {
      loading.value = true
      const [resultResp, findingsResp] = await Promise.all([
        getImagingAnalysisResult(studyId),
        getImagingStructuredFindings(studyId),
      ])
      analysisResult.value = resultResp.data
      structuredFindings.value = findingsResp.data
    } finally {
      loading.value = false
    }
  }

  return {
    loading,
    analysisResult,
    structuredFindings,
    loadImagingAnalysis,
  }
}

export const useImagingSeries = () => {
  const loading = ref(false)
  const series = ref<ImagingSeriesItem[]>([])
  const instances = ref<Record<string, ImagingInstanceItem[]>>({})
  const previewUrls = ref<Record<string, string>>({})

  const loadImagingSeries = async (studyId: string) => {
    try {
      loading.value = true
      const resp = await getImagingStudySeries(studyId)
      series.value = resp.data
    } finally {
      loading.value = false
    }
  }

  const loadSeriesInstances = async (studyId: string, seriesId: string) => {
    try {
      loading.value = true
      const resp = await getImagingSeriesInstances(studyId, seriesId)
      instances.value = {
        ...instances.value,
        [seriesId]: resp.data,
      }
    } finally {
      loading.value = false
    }
  }

  const loadInstancePreview = async (studyId: string, seriesId: string, instanceId: string) => {
    const currentUrl = previewUrls.value[instanceId]
    if (currentUrl) {
      return currentUrl
    }

    try {
      loading.value = true
      const blob = await getImagingInstancePreviewBlob(studyId, seriesId, instanceId)
      const objectUrl = URL.createObjectURL(blob)
      previewUrls.value = {
        ...previewUrls.value,
        [instanceId]: objectUrl,
      }
      return objectUrl
    } finally {
      loading.value = false
    }
  }

  return {
    loading,
    series,
    instances,
    previewUrls,
    loadImagingSeries,
    loadSeriesInstances,
    loadInstancePreview,
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
