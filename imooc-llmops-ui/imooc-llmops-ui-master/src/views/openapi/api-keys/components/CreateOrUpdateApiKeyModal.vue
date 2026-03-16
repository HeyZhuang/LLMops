<script setup lang="ts">
import { ref, watch } from 'vue'
import { type ValidatedError } from '@arco-design/web-vue'
import { useCreateApiKey, useUpdateApiKey } from '@/hooks/use-api-key'

// 1.定义自定义组件所需数据
const props = defineProps({
  visible: { type: Boolean, default: false, required: true },
  api_key_id: { type: String, default: '', required: true },
  is_active: { type: Boolean, default: false, required: true },
  remark: { type: String, default: '', required: true },
  callback: { type: Function, required: false },
})
const emits = defineEmits([
  'update:visible',
  'update:api_key_id',
  'update:is_active',
  'update:remark',
])
const form = ref<Record<string, any>>({})
const formRef = ref(null)
const { loading: updateApiKeyLoading, handleUpdateApiKey } = useUpdateApiKey()
const { loading: createApiKeyLoading, handleCreateApiKey } = useCreateApiKey()

// 2.定义隐藏模态窗函数
const hideModal = () => {
  emits('update:visible', false)
}

// 3.定义表单提交函数
const saveApiKey = async ({ errors }: { errors: Record<string, ValidatedError> | undefined }) => {
  if (errors) return
  if (props.api_key_id) {
    await handleUpdateApiKey(props.api_key_id, {
      is_active: Boolean(form.value?.is_active),
      remark: String(form.value?.remark),
    })
  } else {
    await handleCreateApiKey({
      is_active: Boolean(form.value?.is_active),
      remark: String(form.value?.remark),
    })
  }
  hideModal()
  props.callback && props.callback()
}

// 4.监听模态窗的显示or隐藏状态
watch(
  () => props.visible,
  (newValue) => {
    if (newValue) {
      form.value = {
        is_active: props.is_active,
        remark: props.remark,
      }
    } else {
      emits('update:api_key_id', '')
      emits('update:is_active', false)
      emits('update:remark', '')
    }
  },
)
</script>

<template>
  <a-modal
    :visible="props.visible"
    @update:visible="(value) => emits('update:visible', value)"
    hide-title
    :footer="false"
    :modal-style="{
      background: 'rgba(248,245,240,0.95)',
      backdropFilter: 'blur(24px)',
      border: '1px solid rgba(212,175,55,0.15)',
      borderRadius: '16px',
      boxShadow: '0 24px 64px rgba(15,23,42,0.15), 0 0 0 1px rgba(212,175,55,0.08)',
    }"
  >
    <!-- 顶部标题 -->
    <div class="flex items-center justify-between">
      <div class="text-lg font-bold text-gold-shine">{{ api_key_id ? '更新' : '新增' }}秘钥</div>
      <a-button
        type="text"
        class="!text-abyss-400 hover:!text-gold-400"
        size="small"
        @click="() => emits('update:visible', false)"
      >
        <template #icon>
          <icon-close />
        </template>
      </a-button>
    </div>
    <div class="divider-gold my-4"></div>
    <!-- 中间表单 -->
    <div>
      <a-form ref="formRef" :model="form" layout="vertical" @submit="saveApiKey" class="key-form">
        <a-form-item field="is_active">
          <template #label>
            <span class="text-abyss-700">秘钥状态</span>
          </template>
          <a-switch v-model:model-value="form.is_active" />
        </a-form-item>
        <a-form-item field="remark">
          <template #label>
            <span class="text-abyss-700">秘钥备注</span>
          </template>
          <a-textarea
            v-model:model-value="form.remark"
            :max-length="100"
            show-word-limit
            placeholder="请输入秘钥备注，用于描述秘钥基础信息"
          />
        </a-form-item>
        <!-- 底部按钮 -->
        <div class="flex items-center justify-end gap-3">
          <a-button class="rounded-lg !border-gold-dim !text-abyss-500 hover:!border-gold-bright" @click="() => emits('update:visible', false)">
            取消
          </a-button>
          <a-button
            :loading="updateApiKeyLoading || createApiKeyLoading"
            type="primary"
            html-type="submit"
            class="rounded-lg"
          >
            保存
          </a-button>
        </div>
      </a-form>
    </div>
  </a-modal>
</template>

<style scoped>
.key-form :deep(.arco-switch-checked) {
  background: #D4AF37 !important;
}
</style>
