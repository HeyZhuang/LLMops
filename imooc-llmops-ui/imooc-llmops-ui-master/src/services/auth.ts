import { post } from '@/utils/request'
import { type BaseResponse } from '@/models/base'
import {
  type PasswordLoginResponse,
  type RegisterResponse,
  type SendRegisterCodeResponse,
} from '@/models/auth'

export const passwordLogin = (email: string, password: string) => {
  return post<PasswordLoginResponse>('/auth/password-login', {
    body: { email, password },
  })
}

export const sendRegisterCode = (email: string) => {
  return post<SendRegisterCodeResponse>('/auth/send-register-code', {
    body: { email },
  })
}

export const register = (name: string, email: string, code: string, password: string) => {
  return post<RegisterResponse>('/auth/register', {
    body: { name, email, code, password },
  })
}

export const logout = () => {
  return post<BaseResponse<any>>('/auth/logout')
}
