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

export type SaveImagingReportDraftRequest = {
  content: string
}

export type SubmitImagingReviewRequest = {
  label: string
  comment: string
}
