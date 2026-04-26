import { ref } from 'vue'
import { Message } from '@arco-design/web-vue'

import { logout, passwordLogin, register, sendRegisterCode } from '@/services/auth'

export const useLogout = () => {
  const loading = ref(false)

  const handleLogout = async () => {
    try {
      loading.value = true
      const resp = await logout()
      Message.success(resp.message)
    } finally {
      loading.value = false
    }
  }

  return { loading, handleLogout }
}

export const usePasswordLogin = () => {
  const loading = ref(false)
  const authorization = ref<Record<string, any>>({})

  const handlePasswordLogin = async (email: string, password: string) => {
    try {
      loading.value = true
      const resp = await passwordLogin(email, password)
      authorization.value = resp.data
    } finally {
      loading.value = false
    }
  }

  return { loading, authorization, handlePasswordLogin }
}

export const useRegister = () => {
  const submitLoading = ref(false)
  const codeLoading = ref(false)
  const authorization = ref<Record<string, any>>({})

  const handleSendRegisterCode = async (email: string) => {
    try {
      codeLoading.value = true
      const resp = await sendRegisterCode(email)
      Message.success(resp.message || '验证码已发送')
    } finally {
      codeLoading.value = false
    }
  }

  const handleRegister = async (name: string, email: string, code: string, password: string) => {
    try {
      submitLoading.value = true
      const resp = await register(name, email, code, password)
      authorization.value = resp.data
    } finally {
      submitLoading.value = false
    }
  }

  return {
    submitLoading,
    codeLoading,
    authorization,
    handleSendRegisterCode,
    handleRegister,
  }
}
