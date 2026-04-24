import { get, post } from '@/utils/request'
import type {
  ImagingPlanningOverviewResponse,
  ImagingWorkflowTemplatesResponse,
  ImagingMvpTasksResponse,
  ImagingStudyResponse,
  ImagingStudyDetailResponse,
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

export const getImagingStudyDetail = (studyId: string) => {
  return get<ImagingStudyDetailResponse>(`/imaging/studies/${studyId}`)
}

export const saveImagingReportDraft = (studyId: string, body: SaveImagingReportDraftRequest) => {
  return post(`/imaging/studies/${studyId}/report-draft`, { body })
}

export const submitImagingReview = (studyId: string, body: SubmitImagingReviewRequest) => {
  return post(`/imaging/studies/${studyId}/review`, { body })
}
