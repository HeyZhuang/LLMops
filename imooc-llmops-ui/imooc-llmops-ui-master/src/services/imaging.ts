import { get, post, requestBlob, upload } from '@/utils/request'
import type {
  ImagingPlanningOverviewResponse,
  ImagingWorkflowTemplatesResponse,
  ImagingMvpTasksResponse,
  ImagingSeriesResponse,
  ImagingInstanceResponse,
  ImagingStudyResponse,
  ImagingStudyDetailResponse,
  ImagingAuditLogsResponse,
  ImagingReviewLogsResponse,
  ImagingFeedbackStatsResponse,
  UploadImagingDicomRequest,
  UploadImagingDicomResponse,
  CreateImagingAnalysisTaskResponse,
  ImagingAnalysisResultResponse,
  ImagingStructuredFindingsResponse,
  SaveImagingReportDraftRequest,
  SubmitImagingReviewRequest,
} from '@/models/imaging'

export const getImagingOverview = () => {
  return get<ImagingPlanningOverviewResponse>('/imaging/overview')
}

export const getImagingWorkflowTemplates = () => {
  return get<ImagingWorkflowTemplatesResponse>('/imaging/workflow-templates')
}

export const getImagingMvpTasks = () => {
  return get<ImagingMvpTasksResponse>('/imaging/mvp-tasks')
}

export const getImagingStudies = () => {
  return get<ImagingStudyResponse>('/imaging/studies')
}

export const uploadImagingDicom = (body: UploadImagingDicomRequest) => {
  const formData = new FormData()

  if (body.file) {
    formData.append('file', body.file)
  }

  Object.entries(body).forEach(([key, value]) => {
    if (key === 'file' || value === undefined || value === null || value === '') return
    formData.append(key, String(value))
  })

  return upload<UploadImagingDicomResponse>('/imaging/upload-dicom', { data: formData })
}

export const getImagingStudyDetail = (studyId: string) => {
  return get<ImagingStudyDetailResponse>(`/imaging/studies/${studyId}`)
}

export const getImagingStudySeries = (studyId: string) => {
  return get<ImagingSeriesResponse>(`/imaging/studies/${studyId}/series`)
}

export const getImagingSeriesInstances = (studyId: string, seriesId: string) => {
  return get<ImagingInstanceResponse>(`/imaging/studies/${studyId}/series/${seriesId}/instances`)
}

export const getImagingInstancePreviewBlob = (studyId: string, seriesId: string, instanceId: string) => {
  return requestBlob(`/imaging/studies/${studyId}/series/${seriesId}/instances/${instanceId}/preview`)
}

export const createImagingAnalysisTask = (studyId: string) => {
  return post<CreateImagingAnalysisTaskResponse>(`/imaging/studies/${studyId}/analysis-tasks`)
}

export const getImagingAnalysisResult = (studyId: string) => {
  return get<ImagingAnalysisResultResponse>(`/imaging/studies/${studyId}/analysis-result`)
}

export const getImagingStructuredFindings = (studyId: string) => {
  return get<ImagingStructuredFindingsResponse>(`/imaging/studies/${studyId}/structured-findings`)
}

export const getImagingAuditLogs = (studyId: string) => {
  return get<ImagingAuditLogsResponse>(`/imaging/studies/${studyId}/audit-logs`)
}

export const getImagingReviewLogs = (studyId: string) => {
  return get<ImagingReviewLogsResponse>(`/imaging/studies/${studyId}/review-logs`)
}

export const getImagingFeedbackStats = (studyId: string) => {
  return get<ImagingFeedbackStatsResponse>(`/imaging/studies/${studyId}/feedback-stats`)
}

export const saveImagingReportDraft = (studyId: string, body: SaveImagingReportDraftRequest) => {
  return post(`/imaging/studies/${studyId}/report-draft`, { body })
}

export const submitImagingReview = (studyId: string, body: SubmitImagingReviewRequest) => {
  return post(`/imaging/studies/${studyId}/review`, { body })
}
