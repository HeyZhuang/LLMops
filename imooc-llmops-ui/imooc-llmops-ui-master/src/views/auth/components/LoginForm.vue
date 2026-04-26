<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Message, type ValidatedError } from '@arco-design/web-vue'

import { usePasswordLogin, useRegister } from '@/hooks/use-auth'
import { useProvider } from '@/hooks/use-oauth'
import { useCredentialStore } from '@/stores/credential'

const props = defineProps({
  mouseX: { type: Number, default: 0 },
  mouseY: { type: Number, default: 0 },
})

const credentialStore = useCredentialStore()
const router = useRouter()

const mode = ref<'login' | 'register'>('login')
const errorMessage = ref('')
const loginForm = ref({ email: '', password: '' })
const registerForm = ref({
  name: '',
  email: '',
  code: '',
  password: '',
  confirmPassword: '',
})

const { loading: passwordLoginLoading, authorization, handlePasswordLogin } = usePasswordLogin()
const {
  submitLoading: registerLoading,
  codeLoading,
  authorization: registerAuthorization,
  handleSendRegisterCode,
  handleRegister,
} = useRegister()
const { loading: providerLoading, redirect_url, handleProvider } = useProvider()

const cardRef = ref<HTMLElement | null>(null)
const localX = ref(0)
const localY = ref(0)
const isHovering = ref(false)
const countdown = ref(0)
let countdownTimer: number | null = null

const onCardMouseMove = (e: MouseEvent) => {
  if (!cardRef.value) return
  const rect = cardRef.value.getBoundingClientRect()
  localX.value = ((e.clientX - rect.left) / rect.width - 0.5) * 2
  localY.value = ((e.clientY - rect.top) / rect.height - 0.5) * 2
}

const onCardEnter = () => {
  isHovering.value = true
}

const onCardLeave = () => {
  isHovering.value = false
  localX.value = 0
  localY.value = 0
}

const cardTransform = computed(() => {
  if (isHovering.value) {
    return `perspective(800px) rotateY(${localX.value * 8}deg) rotateX(${localY.value * -8}deg) scale(1.02)`
  }
  return `perspective(800px) rotateY(${props.mouseX * 3}deg) rotateX(${props.mouseY * -2}deg)`
})

const glareStyle = computed(() => {
  if (!isHovering.value) return { opacity: 0 }
  const x = (localX.value + 1) * 50
  const y = (localY.value + 1) * 50
  return {
    opacity: 0.12,
    background: `radial-gradient(circle at ${x}% ${y}%, rgba(212,175,55,0.4) 0%, transparent 60%)`,
  }
})

const registerCodeText = computed(() => {
  if (countdown.value > 0) return `${countdown.value}s 后重发`
  return '发送验证码'
})

const switchMode = (nextMode: 'login' | 'register') => {
  mode.value = nextMode
  errorMessage.value = ''
  loginForm.value.password = ''
  registerForm.value.password = ''
  registerForm.value.confirmPassword = ''
}

const forgetPassword = () => Message.error('忘记密码请联系管理员')

const githubLogin = async () => {
  await handleProvider('github')
  window.location.href = redirect_url.value
}

const startCountdown = () => {
  if (countdownTimer) window.clearInterval(countdownTimer)
  countdown.value = 60
  countdownTimer = window.setInterval(() => {
    if (countdown.value <= 1) {
      if (countdownTimer) window.clearInterval(countdownTimer)
      countdownTimer = null
      countdown.value = 0
      return
    }
    countdown.value -= 1
  }, 1000)
}

const handleSendCodeClick = async () => {
  const email = registerForm.value.email.trim()
  if (!email) {
    Message.error('请先输入注册邮箱')
    return
  }

  try {
    errorMessage.value = ''
    await handleSendRegisterCode(email)
    startCountdown()
  } catch (error: any) {
    errorMessage.value = error.message
  }
}

const handleLoginSubmit = async ({
  errors,
}: {
  errors: Record<string, ValidatedError> | undefined
}) => {
  if (errors) return

  try {
    errorMessage.value = ''
    await handlePasswordLogin(loginForm.value.email, loginForm.value.password)
    Message.success('登录成功，正在跳转')
    credentialStore.update(authorization.value)
    await router.replace({ path: '/home' })
  } catch (error: any) {
    errorMessage.value = error.message
    loginForm.value.password = ''
  }
}

const handleRegisterSubmit = async ({
  errors,
}: {
  errors: Record<string, ValidatedError> | undefined
}) => {
  if (errors) return

  if (registerForm.value.password !== registerForm.value.confirmPassword) {
    errorMessage.value = '两次输入的密码不一致'
    return
  }

  try {
    errorMessage.value = ''
    await handleRegister(
      registerForm.value.name,
      registerForm.value.email,
      registerForm.value.code,
      registerForm.value.password,
    )
    Message.success('注册成功，正在跳转')
    credentialStore.update(registerAuthorization.value)
    await router.replace({ path: '/home' })
  } catch (error: any) {
    errorMessage.value = error.message
    registerForm.value.code = ''
  }
}

onBeforeUnmount(() => {
  if (countdownTimer) window.clearInterval(countdownTimer)
})
</script>

<template>
  <div
    ref="cardRef"
    class="login-card"
    :style="{ transform: cardTransform }"
    @mousemove="onCardMouseMove"
    @mouseenter="onCardEnter"
    @mouseleave="onCardLeave"
  >
    <div class="card-glare" :style="glareStyle"></div>
    <div class="card-border-glow"></div>

    <div class="card-content">
      <div class="flex items-center gap-3 mb-2">
        <div class="h-[2px] w-8 bg-gradient-to-r from-gold-400 to-transparent"></div>
        <span class="text-gold-400 text-xs tracking-[4px] uppercase">
          {{ mode === 'login' ? '安全登录' : '邮箱注册' }}
        </span>
      </div>

      <div class="mode-switch">
        <button
          class="mode-switch-item"
          :class="{ active: mode === 'login' }"
          type="button"
          @click="switchMode('login')"
        >
          登录
        </button>
        <button
          class="mode-switch-item"
          :class="{ active: mode === 'register' }"
          type="button"
          @click="switchMode('register')"
        >
          注册
        </button>
      </div>

      <h2 class="card-title">
        {{ mode === 'login' ? '欢迎回到医脉天枢' : '创建你的 LLMOps 账号' }}
      </h2>
      <p class="card-subtitle">
        {{
          mode === 'login'
            ? '登录后即可继续构建智能会话、知识编排与专科协作能力'
            : '使用邮箱验证码完成注册，注册成功后将自动登录进入平台'
        }}
      </p>

      <div class="divider-gold my-5"></div>

      <div class="h-6 text-red-400 leading-6 line-clamp-1 text-sm">{{ errorMessage }}</div>

      <a-form
        v-if="mode === 'login'"
        :model="loginForm"
        @submit="handleLoginSubmit"
        layout="vertical"
        size="large"
        class="login-form"
      >
        <a-form-item
          field="email"
          :rules="[{ type: 'email', required: true, message: '请输入合法的登录邮箱' }]"
          :validate-trigger="['change', 'blur']"
          hide-label
        >
          <a-input v-model="loginForm.email" size="large" placeholder="登录邮箱">
            <template #prefix>
              <icon-email />
            </template>
          </a-input>
        </a-form-item>
        <a-form-item
          field="password"
          :rules="[{ required: true, message: '账号密码不能为空' }]"
          :validate-trigger="['change', 'blur']"
          hide-label
        >
          <a-input-password v-model="loginForm.password" size="large" placeholder="账号密码">
            <template #prefix>
              <icon-lock />
            </template>
          </a-input-password>
        </a-form-item>

        <a-space :size="16" direction="vertical" class="w-full">
          <div class="flex justify-between">
            <a-checkbox>记住密码</a-checkbox>
            <a-link @click="forgetPassword">忘记密码？</a-link>
          </div>

          <a-button
            :loading="passwordLoginLoading"
            size="large"
            type="primary"
            html-type="submit"
            long
            class="login-btn"
          >
            登录
          </a-button>

          <button type="button" class="switch-link" @click="switchMode('register')">
            还没有账号？立即注册
          </button>

          <div class="flex items-center gap-3 my-1 w-full opacity-80">
            <div class="h-px flex-1 bg-gradient-to-r from-transparent to-gold-dim"></div>
            <span class="text-xs text-abyss-300 font-medium tracking-[2px]">第三方登录</span>
            <div class="h-px flex-1 bg-gradient-to-l from-transparent to-gold-dim"></div>
          </div>

          <a-button
            :loading="providerLoading"
            size="large"
            type="dashed"
            long
            @click="githubLogin"
            class="github-btn"
          >
            <template #icon>
              <icon-github />
            </template>
            通过 GitHub 登录
          </a-button>
        </a-space>
      </a-form>

      <a-form
        v-else
        :model="registerForm"
        @submit="handleRegisterSubmit"
        layout="vertical"
        size="large"
        class="login-form"
      >
        <a-form-item
          field="name"
          :rules="[{ required: true, message: '请输入账号名称' }]"
          :validate-trigger="['change', 'blur']"
          hide-label
        >
          <a-input v-model="registerForm.name" size="large" placeholder="账号名称">
            <template #prefix>
              <icon-user />
            </template>
          </a-input>
        </a-form-item>

        <a-form-item
          field="email"
          :rules="[{ type: 'email', required: true, message: '请输入合法的注册邮箱' }]"
          :validate-trigger="['change', 'blur']"
          hide-label
        >
          <a-input v-model="registerForm.email" size="large" placeholder="注册邮箱">
            <template #prefix>
              <icon-email />
            </template>
          </a-input>
        </a-form-item>

        <div class="code-row">
          <a-form-item
            field="code"
            :rules="[{ required: true, message: '请输入邮箱验证码' }]"
            :validate-trigger="['change', 'blur']"
            hide-label
            class="code-field"
          >
            <a-input v-model="registerForm.code" size="large" placeholder="6 位验证码">
              <template #prefix>
                <icon-safe />
              </template>
            </a-input>
          </a-form-item>

          <a-button
            type="outline"
            size="large"
            class="code-btn"
            :loading="codeLoading"
            :disabled="countdown > 0"
            @click="handleSendCodeClick"
          >
            {{ registerCodeText }}
          </a-button>
        </div>

        <a-form-item
          field="password"
          :rules="[{ required: true, message: '请输入注册密码' }]"
          :validate-trigger="['change', 'blur']"
          hide-label
        >
          <a-input-password v-model="registerForm.password" size="large" placeholder="设置密码">
            <template #prefix>
              <icon-lock />
            </template>
          </a-input-password>
        </a-form-item>

        <a-form-item
          field="confirmPassword"
          :rules="[{ required: true, message: '请再次输入密码' }]"
          :validate-trigger="['change', 'blur']"
          hide-label
        >
          <a-input-password
            v-model="registerForm.confirmPassword"
            size="large"
            placeholder="确认密码"
          >
            <template #prefix>
              <icon-lock />
            </template>
          </a-input-password>
        </a-form-item>

        <a-space :size="16" direction="vertical" class="w-full">
          <a-button
            :loading="registerLoading"
            size="large"
            type="primary"
            html-type="submit"
            long
            class="login-btn"
          >
            注册并登录
          </a-button>

          <button type="button" class="switch-link" @click="switchMode('login')">
            已有账号？返回登录
          </button>
        </a-space>
      </a-form>
    </div>
  </div>
</template>

<style scoped>
.login-card {
  position: relative;
  width: 440px;
  border-radius: 20px;
  transition:
    transform 0.15s ease-out,
    box-shadow 0.3s ease;
  transform-style: preserve-3d;
  will-change: transform;
}

.login-card:hover {
  box-shadow:
    0 30px 60px rgba(0, 0, 0, 0.3),
    0 0 40px rgba(212, 175, 55, 0.08);
}

.card-glare {
  position: absolute;
  inset: 0;
  border-radius: 20px;
  pointer-events: none;
  z-index: 2;
  transition: opacity 0.3s ease;
}

.card-border-glow {
  position: absolute;
  inset: -1px;
  border-radius: 21px;
  padding: 1px;
  background: linear-gradient(
    135deg,
    rgba(212, 175, 55, 0.5) 0%,
    rgba(212, 175, 55, 0.1) 25%,
    rgba(212, 175, 55, 0.05) 50%,
    rgba(212, 175, 55, 0.1) 75%,
    rgba(212, 175, 55, 0.4) 100%
  );
  mask:
    linear-gradient(#fff 0 0) content-box,
    linear-gradient(#fff 0 0);
  -webkit-mask:
    linear-gradient(#fff 0 0) content-box,
    linear-gradient(#fff 0 0);
  mask-composite: exclude;
  -webkit-mask-composite: xor;
  pointer-events: none;
  animation: border-shimmer 4s linear infinite;
}

@keyframes border-shimmer {
  0% {
    background: linear-gradient(
      135deg,
      rgba(212, 175, 55, 0.5) 0%,
      rgba(212, 175, 55, 0.05) 50%,
      rgba(212, 175, 55, 0.4) 100%
    );
  }

  50% {
    background: linear-gradient(
      315deg,
      rgba(212, 175, 55, 0.4) 0%,
      rgba(212, 175, 55, 0.05) 50%,
      rgba(212, 175, 55, 0.5) 100%
    );
  }

  100% {
    background: linear-gradient(
      135deg,
      rgba(212, 175, 55, 0.5) 0%,
      rgba(212, 175, 55, 0.05) 50%,
      rgba(212, 175, 55, 0.4) 100%
    );
  }
}

.card-content {
  position: relative;
  z-index: 1;
  padding: 40px 36px;
  border-radius: 20px;
  background: rgba(8, 24, 32, 0.75);
  backdrop-filter: blur(40px) saturate(150%);
  -webkit-backdrop-filter: blur(40px) saturate(150%);
}

.mode-switch {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 20px;
}

.mode-switch-item {
  border: 1px solid rgba(212, 175, 55, 0.14);
  border-radius: 12px;
  background: rgba(10, 28, 36, 0.6);
  color: rgba(248, 245, 240, 0.58);
  font-size: 14px;
  font-weight: 600;
  letter-spacing: 0.08em;
  padding: 11px 14px;
  transition: all 0.25s ease;
}

.mode-switch-item.active {
  border-color: rgba(212, 175, 55, 0.55);
  color: #f0dda6;
  background: linear-gradient(135deg, rgba(212, 175, 55, 0.18), rgba(212, 175, 55, 0.06));
  box-shadow: 0 10px 24px rgba(212, 175, 55, 0.08);
}

.card-title {
  font-size: 28px;
  font-weight: 700;
  background: linear-gradient(135deg, #d4af37 0%, #f0dda6 50%, #d4af37 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1.3;
}

.card-subtitle {
  font-size: 14px;
  color: rgba(168, 175, 193, 0.6);
  margin-top: 4px;
}

.code-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 132px;
  gap: 12px;
}

.code-field {
  margin-bottom: 20px;
}

.code-btn {
  border-color: rgba(212, 175, 55, 0.24) !important;
  color: #d4af37 !important;
  background: rgba(212, 175, 55, 0.06) !important;
}

.switch-link {
  background: transparent;
  border: none;
  color: rgba(212, 175, 55, 0.72);
  font-size: 14px;
  text-align: center;
  cursor: pointer;
}

.switch-link:hover {
  color: #f0dda6;
}

.login-btn {
  position: relative;
  overflow: hidden;
}

.login-btn::after {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 60%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.15), transparent);
  animation: btn-shine 3s ease-in-out infinite;
}

@keyframes btn-shine {
  0% {
    left: -100%;
  }

  100% {
    left: 200%;
  }
}

.github-btn {
  border: 1px solid rgba(212, 175, 55, 0.15) !important;
  color: rgba(248, 245, 240, 0.5) !important;
  background: transparent !important;
  transition: all 0.3s ease;
}

.github-btn:hover {
  border-color: rgba(212, 175, 55, 0.4) !important;
  color: #d4af37 !important;
  box-shadow: 0 0 20px rgba(212, 175, 55, 0.08);
}

.login-form :deep(.arco-input-wrapper) {
  background: transparent !important;
  border: 1px solid rgba(212, 175, 55, 0.12) !important;
  border-radius: 12px !important;
  transition: all 0.3s ease;
}

.login-form :deep(.arco-input-wrapper:hover) {
  border-color: rgba(212, 175, 55, 0.3) !important;
  background: transparent !important;
}

.login-form :deep(.arco-input-wrapper.arco-input-focus) {
  border-color: #d4af37 !important;
  box-shadow:
    0 0 0 3px rgba(212, 175, 55, 0.08),
    0 0 20px rgba(212, 175, 55, 0.06) !important;
  background: transparent !important;
}

.login-form :deep(.arco-input) {
  color: #ffffff !important;
}

.login-form :deep(.arco-input::placeholder) {
  color: rgba(255, 255, 255, 0.5);
}

.login-form :deep(.arco-input-prefix) {
  color: rgba(212, 175, 55, 0.4);
}

.login-form :deep(.arco-checkbox-label) {
  color: rgba(255, 255, 255, 0.4);
}

.login-form :deep(.arco-checkbox:not(.arco-checkbox-checked) .arco-checkbox-icon) {
  border-color: rgba(212, 175, 55, 0.2);
  background: transparent;
}

.login-form :deep(.arco-form-item-message) {
  color: #cf6679;
}

.login-form :deep(.arco-link) {
  color: rgba(212, 175, 55, 0.6) !important;
}

.login-form :deep(.arco-link:hover) {
  color: #d4af37 !important;
}

@media (max-width: 768px) {
  .login-card {
    width: min(440px, calc(100vw - 32px));
  }

  .card-content {
    padding: 32px 24px;
  }

  .code-row {
    grid-template-columns: 1fr;
  }
}
</style>
