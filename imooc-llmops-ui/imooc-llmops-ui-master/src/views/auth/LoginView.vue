<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import LoginForm from './components/LoginForm.vue'

// 鼠标位置追踪（用于全局视差）
const mouseX = ref(0)
const mouseY = ref(0)
const onMouseMove = (e: MouseEvent) => {
  mouseX.value = (e.clientX / window.innerWidth - 0.5) * 2
  mouseY.value = (e.clientY / window.innerHeight - 0.5) * 2
}

// 粒子系统
const particles = Array.from({ length: 50 }, (_, i) => ({
  id: i,
  x: Math.random() * 100,
  y: Math.random() * 100,
  size: Math.random() * 3 + 1,
  duration: Math.random() * 15 + 10,
  delay: Math.random() * -20,
  opacity: Math.random() * 0.5 + 0.1,
}))

// 浮动3D几何体参数
const shapes = [
  { type: 'cube', x: 12, y: 20, size: 60, duration: 20, delay: 0, rotateAxis: 'Y' },
  { type: 'cube', x: 85, y: 70, size: 40, duration: 25, delay: -5, rotateAxis: 'X' },
  { type: 'octahedron', x: 75, y: 15, size: 50, duration: 18, delay: -3, rotateAxis: 'Y' },
  { type: 'octahedron', x: 20, y: 80, size: 35, duration: 22, delay: -8, rotateAxis: 'X' },
  { type: 'ring', x: 90, y: 40, size: 70, duration: 30, delay: -2, rotateAxis: 'Z' },
  { type: 'ring', x: 8, y: 55, size: 45, duration: 28, delay: -10, rotateAxis: 'Y' },
]

// 特性列表（替代原轮播）
const features = [
  { icon: '⬡', title: '智能问诊', desc: '基于医疗大模型的精准辅助诊断' },
  { icon: '◈', title: '医学图谱增强', desc: '向量检索 + 专业医学知识库' },
  { icon: '⎔', title: '多模态医疗融合', desc: '支持影像/报告/病历多源数据引擎' },
]
const activeFeature = ref(0)
let featureTimer: number

onMounted(() => {
  window.addEventListener('mousemove', onMouseMove)
  featureTimer = window.setInterval(() => {
    activeFeature.value = (activeFeature.value + 1) % features.length
  }, 3000)
})
onUnmounted(() => {
  window.removeEventListener('mousemove', onMouseMove)
  clearInterval(featureTimer)
})
</script>

<template>
  <div class="login-scene" @mousemove="onMouseMove">
    <!-- ===== 层1: 深空背景 + 渐变 ===== -->
    <div class="scene-bg"></div>

    <!-- ===== 层2: 金色粒子星空 ===== -->
    <div class="particles-layer">
      <div
        v-for="p in particles"
        :key="p.id"
        class="particle"
        :style="{
          left: p.x + '%',
          top: p.y + '%',
          width: p.size + 'px',
          height: p.size + 'px',
          opacity: p.opacity,
          animationDuration: p.duration + 's',
          animationDelay: p.delay + 's',
        }"
      ></div>
    </div>

    <!-- ===== 层3: 浮动3D几何体（视差层） ===== -->
    <div
      class="shapes-layer"
      :style="{
        transform: `translate(${mouseX * -15}px, ${mouseY * -15}px)`,
      }"
    >
      <div
        v-for="(shape, i) in shapes"
        :key="i"
        class="floating-shape"
        :style="{
          left: shape.x + '%',
          top: shape.y + '%',
          animationDuration: shape.duration + 's',
          animationDelay: shape.delay + 's',
        }"
      >
        <!-- 立方体 -->
        <div v-if="shape.type === 'cube'" class="cube-wrapper" :style="{ width: shape.size + 'px', height: shape.size + 'px', animationDuration: shape.duration + 's' }">
          <div class="cube" :class="'rotate-' + shape.rotateAxis">
            <div class="cube-face front"></div>
            <div class="cube-face back"></div>
            <div class="cube-face left"></div>
            <div class="cube-face right"></div>
            <div class="cube-face top"></div>
            <div class="cube-face bottom"></div>
          </div>
        </div>
        <!-- 八面体 -->
        <div v-if="shape.type === 'octahedron'" class="octa-wrapper" :style="{ width: shape.size + 'px', height: shape.size + 'px', animationDuration: shape.duration + 's' }">
          <div class="octahedron" :class="'rotate-' + shape.rotateAxis">
            <div class="octa-face f1"></div>
            <div class="octa-face f2"></div>
            <div class="octa-face f3"></div>
            <div class="octa-face f4"></div>
          </div>
        </div>
        <!-- 环 -->
        <div v-if="shape.type === 'ring'" class="ring-wrapper" :style="{ width: shape.size + 'px', height: shape.size + 'px', animationDuration: shape.duration + 's' }">
          <div class="golden-ring" :class="'rotate-' + shape.rotateAxis"></div>
        </div>
      </div>
    </div>

    <!-- ===== 层4: 金色光线扫射 ===== -->
    <div class="light-rays">
      <div class="ray ray-1"></div>
      <div class="ray ray-2"></div>
      <div class="ray ray-3"></div>
    </div>

    <!-- ===== 层5: 主内容区 ===== -->
    <div class="content-layer">
      <!-- 左侧品牌区 -->
      <div
        class="brand-section"
        :style="{
          transform: `perspective(1000px) rotateY(${mouseX * 2}deg) rotateX(${mouseY * -1}deg)`,
        }"
      >
        <!-- 大标题 -->
        <div class="brand-title">
          <span class="title-line-1">医脉</span>
          <span class="title-line-2">天枢</span>
        </div>
        <p class="brand-subtitle">新一代智慧医疗大语言模型平台</p>

        <!-- 金色分割线 -->
        <div class="divider-gold w-20 my-8"></div>

        <!-- 3D特性卡片 -->
        <div class="features-3d">
          <div
            v-for="(feat, i) in features"
            :key="i"
            class="feature-card"
            :class="{ 'feature-active': activeFeature === i }"
            @mouseenter="activeFeature = i"
          >
            <span class="feature-icon">{{ feat.icon }}</span>
            <div>
              <div class="feature-title">{{ feat.title }}</div>
              <div class="feature-desc">{{ feat.desc }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧表单区 -->
      <div class="form-section">
        <login-form :mouse-x="mouseX" :mouse-y="mouseY" />
      </div>
    </div>

    <!-- ===== 顶部Logo ===== -->
    <div class="fixed top-6 left-8 z-50 flex items-center gap-4">
      <img src="@/assets/images/logo2_transparent.png" alt="医脉天枢" class="h-12 w-auto flex-shrink-0" />
      <span class="text-gold-shine text-3xl font-bold tracking-widest leading-none pt-1">医脉天枢</span>
    </div>

    <!-- ===== 底部信息 ===== -->
    <footer class="fixed bottom-4 left-0 w-full text-center text-abyss-400 text-xs tracking-wider z-50">
      医脉天枢 (Yimai Tianshu) &middot; Enterprise Medical AI Platform
    </footer>
  </div>
</template>

<style scoped>
/* ===== 场景容器 ===== */
.login-scene {
  position: relative;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  cursor: default;
}

/* ===== 深空背景 ===== */
.scene-bg {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse at 30% 20%, rgba(15, 65, 85, 0.8) 0%, transparent 60%),
    radial-gradient(ellipse at 70% 80%, rgba(212,175,55,0.06) 0%, transparent 50%),
    linear-gradient(180deg, #05141e 0%, #0c202f 40%, #061219 100%);
}

/* ===== 金色粒子 ===== */
.particles-layer {
  position: absolute;
  inset: 0;
  pointer-events: none;
}
.particle {
  position: absolute;
  border-radius: 50%;
  background: radial-gradient(circle, #D4AF37 0%, transparent 70%);
  animation: float-particle linear infinite;
}
@keyframes float-particle {
  0%, 100% { transform: translateY(0) translateX(0); opacity: 0; }
  10% { opacity: var(--tw-opacity, 0.3); }
  90% { opacity: var(--tw-opacity, 0.3); }
  50% { transform: translateY(-80px) translateX(30px); }
}

/* ===== 3D几何体层 ===== */
.shapes-layer {
  position: absolute;
  inset: 0;
  pointer-events: none;
  transition: transform 0.3s ease-out;
}
.floating-shape {
  position: absolute;
  animation: float-updown ease-in-out infinite;
}
@keyframes float-updown {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-25px); }
}

/* ===== CSS 3D 立方体 ===== */
.cube-wrapper {
  perspective: 200px;
}
.cube {
  width: 100%;
  height: 100%;
  position: relative;
  transform-style: preserve-3d;
  animation: spin linear infinite;
}
.cube-face {
  position: absolute;
  width: 100%;
  height: 100%;
  border: 1px solid rgba(212,175,55,0.15);
  background: rgba(212,175,55,0.03);
  backdrop-filter: blur(2px);
}
.cube-face.front  { transform: translateZ(calc(var(--s, 30px))); }
.cube-face.back   { transform: translateZ(calc(var(--s, 30px) * -1)) rotateY(180deg); }
.cube-face.left   { transform: translateX(calc(var(--s, 30px) * -1)) rotateY(-90deg); }
.cube-face.right  { transform: translateX(var(--s, 30px)) rotateY(90deg); }
.cube-face.top    { transform: translateY(calc(var(--s, 30px) * -1)) rotateX(90deg); }
.cube-face.bottom { transform: translateY(var(--s, 30px)) rotateX(-90deg); }
.cube-wrapper:nth-child(1) .cube-face { --s: 30px; }
.cube-wrapper:nth-child(2) .cube-face { --s: 20px; }

/* ===== CSS 3D 八面体 ===== */
.octa-wrapper {
  perspective: 200px;
}
.octahedron {
  width: 100%;
  height: 100%;
  position: relative;
  transform-style: preserve-3d;
  animation: spin linear infinite;
}
.octa-face {
  position: absolute;
  width: 0; height: 0;
  left: 50%; top: 50%;
  border-left: 20px solid transparent;
  border-right: 20px solid transparent;
  border-bottom: 35px solid rgba(212,175,55,0.08);
  filter: drop-shadow(0 0 4px rgba(212,175,55,0.15));
}
.octa-face.f1 { transform: translate(-50%, -50%) rotateX(0deg); }
.octa-face.f2 { transform: translate(-50%, -50%) rotateX(90deg); }
.octa-face.f3 { transform: translate(-50%, -50%) rotateY(90deg); }
.octa-face.f4 { transform: translate(-50%, -50%) rotateX(180deg); }

/* ===== CSS 3D 环 ===== */
.ring-wrapper {
  perspective: 300px;
}
.golden-ring {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  border: 2px solid rgba(212,175,55,0.12);
  box-shadow: 0 0 15px rgba(212,175,55,0.05), inset 0 0 15px rgba(212,175,55,0.03);
  animation: spin linear infinite;
}

/* ===== 旋转方向 ===== */
.rotate-X { animation-name: spin-x; }
.rotate-Y { animation-name: spin-y; }
.rotate-Z { animation-name: spin-z; }
@keyframes spin-x { from { transform: rotateX(0deg); } to { transform: rotateX(360deg); } }
@keyframes spin-y { from { transform: rotateY(0deg); } to { transform: rotateY(360deg); } }
@keyframes spin-z { from { transform: rotateZ(0deg); } to { transform: rotateZ(360deg); } }
@keyframes spin   { from { transform: rotateX(0deg) rotateY(0deg); } to { transform: rotateX(360deg) rotateY(360deg); } }

/* ===== 金色光线 ===== */
.light-rays {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}
.ray {
  position: absolute;
  width: 2px;
  height: 150%;
  background: linear-gradient(180deg, transparent 0%, rgba(212,175,55,0.06) 50%, transparent 100%);
  animation: ray-sweep linear infinite;
}
.ray-1 { left: 20%; animation-duration: 12s; animation-delay: 0s; transform: rotate(15deg); }
.ray-2 { left: 55%; animation-duration: 16s; animation-delay: -4s; transform: rotate(-10deg); }
.ray-3 { left: 80%; animation-duration: 14s; animation-delay: -8s; transform: rotate(5deg); }
@keyframes ray-sweep {
  0%   { opacity: 0; transform: translateX(-200px) rotate(15deg); }
  20%  { opacity: 1; }
  80%  { opacity: 1; }
  100% { opacity: 0; transform: translateX(200px) rotate(15deg); }
}

/* ===== 主内容层 ===== */
.content-layer {
  position: relative;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 80px;
  padding: 0 60px;
}

/* ===== 品牌区 ===== */
.brand-section {
  flex: 0 0 480px;
  transition: transform 0.2s ease-out;
  transform-style: preserve-3d;
}
.brand-title {
  line-height: 1;
  margin-bottom: 16px;
}
.title-line-1 {
  display: block;
  font-size: 72px;
  font-weight: 800;
  letter-spacing: 8px;
  background: linear-gradient(135deg, #D4AF37 0%, #f0dda6 40%, #D4AF37 80%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  filter: drop-shadow(0 0 30px rgba(212,175,55,0.2));
  animation: title-enter 1s ease-out both;
}
.title-line-2 {
  display: block;
  font-size: 72px;
  font-weight: 300;
  letter-spacing: 12px;
  color: rgba(248,245,240,0.15);
  text-shadow: 0 0 40px rgba(212,175,55,0.08);
  animation: title-enter 1s ease-out 0.2s both;
}
.brand-subtitle {
  font-size: 16px;
  color: rgba(168,175,193,0.6);
  letter-spacing: 4px;
  animation: fade-up 1s ease-out 0.4s both;
}

/* ===== 特性卡片 ===== */
.features-3d {
  display: flex;
  flex-direction: column;
  gap: 12px;
  animation: fade-up 1s ease-out 0.6s both;
}
.feature-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 14px 20px;
  border-radius: 12px;
  border: 1px solid rgba(212,175,55,0.06);
  background: rgba(255,255,255,0.02);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: default;
  transform: perspective(600px) rotateY(0deg);
}
.feature-card:hover,
.feature-active {
  background: rgba(212,175,55,0.06);
  border-color: rgba(212,175,55,0.2);
  transform: perspective(600px) rotateY(-3deg) translateX(8px);
  box-shadow: -8px 4px 24px rgba(212,175,55,0.06);
}
.feature-icon {
  font-size: 24px;
  color: #D4AF37;
  text-shadow: 0 0 12px rgba(212,175,55,0.3);
  flex-shrink: 0;
  width: 40px;
  text-align: center;
}
.feature-title {
  font-size: 15px;
  font-weight: 600;
  color: rgba(248,245,240,0.85);
  margin-bottom: 2px;
}
.feature-desc {
  font-size: 13px;
  color: rgba(168,175,193,0.5);
}

/* ===== Logo钻石 ===== */
.logo-diamond {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(212,175,55,0.3);
  border-radius: 8px;
  transform: rotate(0deg);
  background: rgba(212,175,55,0.06);
  animation: diamond-pulse 3s ease-in-out infinite;
}
.diamond-inner {
  color: #D4AF37;
  font-size: 18px;
  text-shadow: 0 0 8px rgba(212,175,55,0.4);
}
@keyframes diamond-pulse {
  0%, 100% { box-shadow: 0 0 8px rgba(212,175,55,0.1); }
  50% { box-shadow: 0 0 20px rgba(212,175,55,0.2); }
}

/* ===== 表单区 ===== */
.form-section {
  flex: 0 0 auto;
  animation: form-enter 1s ease-out 0.3s both;
}

/* ===== 入场动画 ===== */
@keyframes title-enter {
  from { opacity: 0; transform: translateY(30px) rotateX(10deg); }
  to { opacity: 1; transform: translateY(0) rotateX(0); }
}
@keyframes fade-up {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes form-enter {
  from { opacity: 0; transform: translateX(60px) scale(0.95); }
  to { opacity: 1; transform: translateX(0) scale(1); }
}
</style>
