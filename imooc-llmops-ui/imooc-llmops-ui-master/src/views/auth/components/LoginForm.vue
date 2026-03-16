<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useCredentialStore } from '@/stores/credential'
import { Message, type ValidatedError } from '@arco-design/web-vue'
import { usePasswordLogin } from '@/hooks/use-auth'
import { useProvider } from '@/hooks/use-oauth'

// 接收父组件传入的鼠标坐标
const props = defineProps({
  mouseX: { type: Number, default: 0 },
  mouseY: { type: Number, default: 0 },
})

// 1.定义自定义组件所需数据
const errorMessage = ref('')
const loginForm = ref({ email: '', password: '' })
const credentialStore = useCredentialStore()
const router = useRouter()
const { loading: passwordLoginLoading, authorization, handlePasswordLogin } = usePasswordLogin()
const { loading: providerLoading, redirect_url, handleProvider } = useProvider()

// 卡片局部鼠标追踪（精细3D倾斜）
const cardRef = ref<HTMLElement | null>(null)
const localX = ref(0)
const localY = ref(0)
const isHovering = ref(false)

const onCardMouseMove = (e: MouseEvent) => {
  if (!cardRef.value) return
  const rect = cardRef.value.getBoundingClientRect()
  localX.value = ((e.clientX - rect.left) / rect.width - 0.5) * 2
  localY.value = ((e.clientY - rect.top) / rect.height - 0.5) * 2
}
const onCardEnter = () => { isHovering.value = true }
const onCardLeave = () => {
  isHovering.value = false
  localX.value = 0
  localY.value = 0
}

// 3D 变换计算
const cardTransform = computed(() => {
  if (isHovering.value) {
    return `perspective(800px) rotateY(${localX.value * 8}deg) rotateX(${localY.value * -8}deg) scale(1.02)`
  }
  return `perspective(800px) rotateY(${props.mouseX * 3}deg) rotateX(${props.mouseY * -2}deg)`
})

// 光泽位置
const glareStyle = computed(() => {
  if (!isHovering.value) return { opacity: 0 }
  const x = (localX.value + 1) * 50
  const y = (localY.value + 1) * 50
  return {
    opacity: 0.12,
    background: `radial-gradient(circle at ${x}% ${y}%, rgba(212,175,55,0.4) 0%, transparent 60%)`,
  }
})

// 2.定义忘记密码点击事件
const forgetPassword = () => Message.error('忘记密码请联系管理员')

// 3.定义github第三方授权认证登录
const githubLogin = async () => {
  await handleProvider('github')
  window.location.href = redirect_url.value
}

// 4.账号密码登录
const handleSubmit = async ({ errors }: { errors: Record<string, ValidatedError> | undefined }) => {
  if (errors) return
  try {
    await handlePasswordLogin(loginForm.value.email, loginForm.value.password)
    Message.success('登录成功，正在跳转')
    credentialStore.update(authorization.value)
    await router.replace({ path: '/home' })
  } catch (error: any) {
    errorMessage.value = error.message
    loginForm.value.password = ''
  }
}
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
    <!-- 光泽追踪层 -->
    <div class="card-glare" :style="glareStyle"></div>

    <!-- 金属边框光效 -->
    <div class="card-border-glow"></div>

    <!-- 内容 -->
    <div class="card-content">
      <!-- 顶部装饰 -->
      <div class="flex items-center gap-3 mb-2">
        <div class="h-[2px] w-8 bg-gradient-to-r from-gold-400 to-transparent"></div>
        <span class="text-gold-400 text-xs tracking-[4px] uppercase">Secure Login</span>
      </div>

      <!-- 标题 -->
      <h2 class="card-title">欢迎回来</h2>
      <p class="card-subtitle">登录 LLMOps 开始构建 AI 应用</p>

      <!-- 分割线 -->
      <div class="divider-gold my-5"></div>

      <!-- 错误提示 -->
      <div class="h-6 text-red-400 leading-6 line-clamp-1 text-sm">{{ errorMessage }}</div>

      <!-- 登录表单 -->
      <a-form
        :model="loginForm"
        @submit="handleSubmit"
        layout="vertical"
        size="large"
        class="login-form"
      >
        <a-form-item
          field="email"
          :rules="[{ type: 'email', required: true, message: '登录账号必须是合法的邮箱' }]"
          :validate-trigger="['change', 'blur']"
          hide-label
        >
          <a-input v-model="loginForm.email" size="large" placeholder="登录账号">
            <template #prefix>
              <icon-user />
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
            <a-link @click="forgetPassword">忘记密码?</a-link>
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
          <a-divider>第三方授权</a-divider>
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
            Github
          </a-button>
        </a-space>
      </a-form>
    </div>
  </div>
</template>

<style scoped>
/* ===== 3D卡片容器 ===== */
.login-card {
  position: relative;
  width: 420px;
  border-radius: 20px;
  transition: transform 0.15s ease-out, box-shadow 0.3s ease;
  transform-style: preserve-3d;
  will-change: transform;
}
.login-card:hover {
  box-shadow:
    0 30px 60px rgba(0,0,0,0.3),
    0 0 40px rgba(212,175,55,0.08);
}

/* ===== 光泽追踪 ===== */
.card-glare {
  position: absolute;
  inset: 0;
  border-radius: 20px;
  pointer-events: none;
  z-index: 2;
  transition: opacity 0.3s ease;
}

/* ===== 金属边框光效 ===== */
.card-border-glow {
  position: absolute;
  inset: -1px;
  border-radius: 21px;
  padding: 1px;
  background: linear-gradient(
    135deg,
    rgba(212,175,55,0.5) 0%,
    rgba(212,175,55,0.1) 25%,
    rgba(212,175,55,0.05) 50%,
    rgba(212,175,55,0.1) 75%,
    rgba(212,175,55,0.4) 100%
  );
  mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  mask-composite: exclude;
  -webkit-mask-composite: xor;
  pointer-events: none;
  animation: border-shimmer 4s linear infinite;
}
@keyframes border-shimmer {
  0% {
    background: linear-gradient(135deg, rgba(212,175,55,0.5) 0%, rgba(212,175,55,0.05) 50%, rgba(212,175,55,0.4) 100%);
  }
  50% {
    background: linear-gradient(315deg, rgba(212,175,55,0.4) 0%, rgba(212,175,55,0.05) 50%, rgba(212,175,55,0.5) 100%);
  }
  100% {
    background: linear-gradient(135deg, rgba(212,175,55,0.5) 0%, rgba(212,175,55,0.05) 50%, rgba(212,175,55,0.4) 100%);
  }
}

/* ===== 内容区域 ===== */
.card-content {
  position: relative;
  z-index: 1;
  padding: 40px 36px;
  border-radius: 20px;
  background: rgba(15,23,42,0.75);
  backdrop-filter: blur(40px) saturate(150%);
  -webkit-backdrop-filter: blur(40px) saturate(150%);
}

.card-title {
  font-size: 28px;
  font-weight: 700;
  background: linear-gradient(135deg, #D4AF37 0%, #f0dda6 50%, #D4AF37 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1.3;
}
.card-subtitle {
  font-size: 14px;
  color: rgba(168,175,193,0.6);
  margin-top: 4px;
}

/* ===== 登录按钮加强 ===== */
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
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.15), transparent);
  animation: btn-shine 3s ease-in-out infinite;
}
@keyframes btn-shine {
  0% { left: -100%; }
  100% { left: 200%; }
}

/* ===== GitHub 按钮 ===== */
.github-btn {
  border: 1px solid rgba(212,175,55,0.15) !important;
  color: rgba(248,245,240,0.5) !important;
  background: transparent !important;
  transition: all 0.3s ease;
}
.github-btn:hover {
  border-color: rgba(212,175,55,0.4) !important;
  color: #D4AF37 !important;
  box-shadow: 0 0 20px rgba(212,175,55,0.08);
}

/* ===== 表单深色适配 ===== */
.login-form :deep(.arco-input-wrapper) {
  background: rgba(255,255,255,0.04) !important;
  border: 1px solid rgba(212,175,55,0.12) !important;
  border-radius: 12px !important;
  transition: all 0.3s ease;
}
.login-form :deep(.arco-input-wrapper:hover) {
  border-color: rgba(212,175,55,0.3) !important;
  background: rgba(255,255,255,0.06) !important;
}
.login-form :deep(.arco-input-wrapper.arco-input-focus) {
  border-color: #D4AF37 !important;
  box-shadow: 0 0 0 3px rgba(212,175,55,0.08), 0 0 20px rgba(212,175,55,0.06) !important;
  background: rgba(255,255,255,0.06) !important;
}
.login-form :deep(.arco-input) {
  color: rgba(255,255,255,0.9);
}
.login-form :deep(.arco-input::placeholder) {
  color: rgba(255,255,255,0.3);
}
.login-form :deep(.arco-input-prefix) {
  color: rgba(212,175,55,0.4);
}
.login-form :deep(.arco-checkbox-label) {
  color: rgba(255,255,255,0.4);
}
.login-form :deep(.arco-checkbox:not(.arco-checkbox-checked) .arco-checkbox-icon) {
  border-color: rgba(212,175,55,0.2);
  background: transparent;
}
.login-form :deep(.arco-divider-text) {
  color: rgba(255,255,255,0.2);
  background: transparent;
}
.login-form :deep(.arco-divider-horizontal::before),
.login-form :deep(.arco-divider-horizontal::after) {
  border-color: rgba(212,175,55,0.1) !important;
}
.login-form :deep(.arco-form-item-message) {
  color: #cf6679;
}
.login-form :deep(.arco-link) {
  color: rgba(212,175,55,0.6) !important;
}
.login-form :deep(.arco-link:hover) {
  color: #D4AF37 !important;
}
</style>
