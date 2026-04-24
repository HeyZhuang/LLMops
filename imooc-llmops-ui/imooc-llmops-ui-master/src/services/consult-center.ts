import { get } from '@/utils/request'
import type { ConsultCenterOverviewResponse } from '@/models/consult-center'

export const getConsultCenterOverview = () => {
  return get<ConsultCenterOverviewResponse>(`/consult-center/overview`)
}
