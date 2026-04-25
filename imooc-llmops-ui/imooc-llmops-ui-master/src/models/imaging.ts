import type { BaseResponse } from '@/models/base'

export type ImagingPhase = {
  key: string
  title: string
  goal: string
  deliverables: string[]
}

export type ImagingScene = {
  name: string
  value: string
  description: string
}

export type ImagingPlanningOverview = {
  title: string
  summary: string
  positioning: string[]
  scenes: ImagingScene[]
  phases: ImagingPhase[]
  guardrails: string[]
  metrics: {
    apps: number
    datasets: number
    documents: number
    workflows: number
    workflow_templates: number
  }
  mvp: {
    name: string
    value: string
  }
}

export type ImagingPlanningOverviewResponse = BaseResponse<ImagingPlanningOverview>

export type ImagingWorkflowTemplate = {
  key: string
  name: string
  scene: string
  steps: string[]
  outputs?: string[]
}

export type ImagingWorkflowTemplatesResponse = BaseResponse<ImagingWorkflowTemplate[]>

export type ImagingMvpTask = {
  key: string
  title: string
  owner: string
  items: string[]
}

export type ImagingMvpTasksResponse = BaseResponse<ImagingMvpTask[]>

export type ImagingStudy = {
  id: string
  patient_code: string
  patient_name_masked: string
  modality: string
  body_part: string
  study_description: string
  study_time: number
  status: string
  quality_status: string
  ai_summary: string
  findings_count: number
  report_status: string
  priority: string
}

export type ImagingStudyResponse = BaseResponse<ImagingStudy[]>

export type ImagingStudyDetail = ImagingStudy & {
  series: {
    name: string
    images: number
    slice_thickness: string
  }[]
  findings: {
    title: string
    confidence: number
    description: string
  }[]
  report_draft: {
    status: string
    content: string
    template_name: string
    template_version: string
  }
  timeline: {
    label: string
    value: string
  }[]
  review: {
    label: string
    comment: string
    updated_at: number
  }
}

export type ImagingStudyDetailResponse = BaseResponse<ImagingStudyDetail>

export type ImagingAuditLog = {
  id: string
  action: string
  target_type: string
  target_id: string
  success: boolean
  details: Record<string, unknown>
  created_at: number
}

export type ImagingAuditLogsResponse = BaseResponse<ImagingAuditLog[]>

export type ImagingReviewLog = {
  id: string
  label: string
  comment: string
  review_type: string
  reviewer_id: string
  status: string
  created_at: number
}

export type ImagingReviewLogsResponse = BaseResponse<ImagingReviewLog[]>

export type ImagingFeedbackStats = {
  total_reviews: number
  approved: number
  needs_revision: number
  rejected: number
  approval_rate: number
}

export type ImagingFeedbackStatsResponse = BaseResponse<ImagingFeedbackStats>

export type UploadImagingDicomRequest = {
  accession_number?: string
  patient_code?: string
  patient_name_masked?: string
  modality?: string
  body_part?: string
  study_description?: string
  priority?: string
  source_type?: string
}

export type UploadImagingDicomResult = {
  study_id: string
  status: string
  message: string
}

export type UploadImagingDicomResponse = BaseResponse<UploadImagingDicomResult>

export type CreateImagingAnalysisTaskResult = {
  study_id: string
  task_id: string
  status: string
  task_type: string
}

export type CreateImagingAnalysisTaskResponse = BaseResponse<CreateImagingAnalysisTaskResult>

export type ImagingAnalysisResult = {
  study_id: string
  task_id: string
  status: string
  task_type: string
  model_name: string
  model_version: string
  summary: string
  findings: Record<string, unknown>[]
  measurements: Record<string, unknown>[]
  overlays: Record<string, unknown>[]
  updated_at: number
}

export type ImagingAnalysisResultResponse = BaseResponse<ImagingAnalysisResult>

export type ImagingStructuredFindings = {
  study_id: string
  status: string
  summary: string
  findings: Record<string, unknown>[]
  measurements: Record<string, unknown>[]
}

export type ImagingStructuredFindingsResponse = BaseResponse<ImagingStructuredFindings>

export type SaveImagingReportDraftRequest = {
  content: string
}

export type SubmitImagingReviewRequest = {
  label: string
  comment: string
}
