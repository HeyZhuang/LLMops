<script setup lang="ts">
import { ref, watch } from 'vue'
import { type Form, type ValidatedError } from '@arco-design/web-vue'
import { useCreateApp, useGetApp, useUpdateApp } from '@/hooks/use-app'
import { useUploadImage } from '@/hooks/use-upload-file'

// 1.定义自定义组件所需数据
const props = defineProps({
  app_id: { type: String, default: '', required: false },
  visible: { type: Boolean, required: true },
  callback: { type: Function, required: false },
})
const emits = defineEmits(['update:visible', 'update:app_id'])
const { loading: createAppLoading, handleCreateApp } = useCreateApp()
const { loading: updateAppLoading, handleUpdateApp } = useUpdateApp()
const { app, loadApp } = useGetApp()
const { image_url, handleUploadImage } = useUploadImage()
const defaultForm = {
  fileList: [] as any,
  icon: '',
  name: '',
  description: '',
}
const form = ref({ ...defaultForm })
const formRef = ref<InstanceType<typeof Form>>()

// 2.定义隐藏模态窗函数
const hideModal = () => emits('update:visible', false)

// 3.定义表单提交函数
const saveApp = async ({ errors }: { errors: Record<string, ValidatedError> | undefined }) => {
  if (errors) return
  if (props.app_id) {
    await handleUpdateApp(props.app_id, form.value)
  } else {
    await handleCreateApp(form.value)
  }
  emits('update:visible', false)
  props.callback && props.callback()
}

// 4.监听模态窗显示状态变化
watch(
  () => props.visible,
  async (newValue) => {
    formRef.value?.resetFields()
    if (newValue) {
      if (props.app_id) {
        await loadApp(props.app_id)
        form.value = {
          fileList: [{ uid: '1', name: '应用图标', url: app.value.icon }],
          icon: app.value.icon,
          name: app.value.name,
          description: app.value.description,
        }
      }
    } else {
      form.value = defaultForm
      formRef.value?.resetFields()
      emits('update:app_id', '')
    }
  },
)
</script>

<template>
  <a-modal
    :width="520"
    :visible="props.visible"
    hide-title
    :footer="false"
    modal-class="rounded-xl"
    :modal-style="{
      background: 'rgba(248,245,240,0.95)',
      backdropFilter: 'blur(24px)',
      border: '1px solid rgba(212,175,55,0.15)',
      borderRadius: '16px',
      boxShadow: '0 24px 64px rgba(15,23,42,0.15), 0 0 0 1px rgba(212,175,55,0.08)',
    }"
    @cancel="hideModal"
  >
    <!-- 顶部标题 -->
    <div class="flex items-center justify-between">
      <div class="text-lg font-bold text-gold-shine">
        {{ props.app_id === '' ? '创建 AI 应用' : '编辑 AI 应用' }}
      </div>
      <a-button type="text" class="!text-abyss-400 hover:!text-gold-400" size="small" @click="hideModal">
        <template #icon>
          <icon-close />
        </template>
      </a-button>
    </div>
    <div class="divider-gold my-4"></div>
    <!-- 中间表单 -->
    <div>
      <a-form ref="formRef" :model="form" layout="vertical" @submit="saveApp" class="app-form">
        <a-form-item
          field="fileList"
          hide-label
          :rules="[{ required: true, message: '应用图标不能为空' }]"
        >
          <a-upload
            :limit="1"
            list-type="picture-card"
            accept="image/png, image/jpeg"
            class="!w-auto mx-auto"
            v-model:file-list="form.fileList"
            image-preview
            :custom-request="
              (option) => {
                const { fileItem, onSuccess, onError } = option
                const uploadTask = async () => {
                  try {
                    await handleUploadImage(fileItem.file as File)
                    form.icon = image_url
                    onSuccess(image_url)
                  } catch (error) {
                    onError(error)
                  }
                }
                uploadTask()
                return { abort: () => {} }
              }
            "
            :on-before-remove="
              async () => {
                form.icon = ''
                return true
              }
            "
          />
        </a-form-item>
        <a-form-item
          field="name"
          asterisk-position="end"
          :rules="[{ required: true, message: '应用名称不能为空' }]"
        >
          <template #label>
            <span class="text-abyss-700">应用名称</span>
          </template>
          <a-input v-model:model-value="form.name" placeholder="请输入应用名称" />
        </a-form-item>
        <a-form-item field="description">
          <template #label>
            <span class="text-abyss-700">应用描述</span>
          </template>
          <a-textarea
            v-model:model-value="form.description"
            :auto-size="{ minRows: 8, maxRows: 8 }"
            :max-length="800"
            show-word-limit
            placeholder="请输入关于该应用的描述信息"
          />
        </a-form-item>
        <!-- 底部按钮 -->
        <div class="flex items-center justify-end gap-3">
          <a-button class="rounded-lg !border-gold-dim !text-abyss-500 hover:!border-gold-bright" @click="hideModal">取消</a-button>
          <a-button
            :loading="createAppLoading || updateAppLoading"
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
.app-form :deep(.arco-upload-list-picture) {
  border: 2px solid rgba(212,175,55,0.2) !important;
  border-radius: 12px !important;
}
.app-form :deep(.arco-upload-picture-card) {
  border: 2px dashed rgba(212,175,55,0.2) !important;
  border-radius: 12px !important;
  background: rgba(212,175,55,0.03) !important;
}
.app-form :deep(.arco-upload-picture-card:hover) {
  border-color: rgba(212,175,55,0.4) !important;
}
</style>
