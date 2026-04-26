import { type BaseResponse } from '@/models/base'

export type AuthorizationData = {
  access_token: string
  expire_at: number
}

export type PasswordLoginResponse = BaseResponse<AuthorizationData>

export type RegisterResponse = BaseResponse<AuthorizationData>

export type SendRegisterCodeResponse = BaseResponse<Record<string, never>>
