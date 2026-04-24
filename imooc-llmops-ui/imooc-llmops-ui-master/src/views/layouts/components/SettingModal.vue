<script setup lang="ts">
import { ref, watch } from 'vue'
import { useAccountStore } from '@/stores/account'
import {
  useGetCurrentUser,
  useUpdateAvatar,
  useUpdateName,
  useUpdatePassword,
} from '@/hooks/use-account'
import { useUploadImage } from '@/hooks/use-upload-file'

// 1.定义自定义组件所需数据
const props = defineProps({
  visible: { type: Boolean, required: true },
})
const emits = defineEmits(['update:visible'])
const updateName = ref(false)
const updatePassword = ref(false)
const accountStore = useAccountStore()
const { current_user, loadCurrentUser } = useGetCurrentUser()
const { handleUpdateAvatar } = useUpdateAvatar()
const { handleUpdateName } = useUpdateName()
const { handleUpdatePassword } = useUpdatePassword()
const { image_url, handleUploadImage } = useUploadImage()
const accountForm = ref({
  fileList: [{ uid: '1', name: '账号头像', url: accountStore.account.avatar }],
  name: accountStore.account.name,
  avatar: accountStore.account.avatar,
  password: '',
  email: accountStore.account.email,
})

// 2.更新当前账号信息
const updateAccount = async () => {
  await loadCurrentUser()
  accountStore.update(current_user.value)
}

// 3.关闭模态窗处理器
const handleCancel = () => emits('update:visible', false)

// 4.监听模态窗关闭事件
watch(
  () => props.visible,
  (newValue) => {
    if (!newValue) {
      // 如果为关闭模态窗则重置表单，并关闭所有输入框
      updatePassword.value = false
      updateName.value = false
    }

    // 无论是开启还是关闭模态窗，均赋初始值，可以确保首次加载的时候数据正确展示
    accountForm.value = {
      fileList: [{ uid: '1', name: '账号头像', url: accountStore.account.avatar }],
      name: accountStore.account.name,
      avatar: accountStore.account.avatar,
      password: '',
      email: accountStore.account.email,
    }
  },
)
</script>

<template>
  <a-modal
    :visible="visible"
    hide-title
    :footer="false"
    :width="1000"
    @cancel="handleCancel"
    class="setting-modal"
    :modal-style="{
      background: 'rgba(248,245,240,0.95)',
      backdropFilter: 'blur(24px) saturate(180%)',
      border: '1px solid rgba(212,175,55,0.15)',
      borderRadius: '16px',
      boxShadow: '0 24px 64px rgba(15,23,42,0.15), 0 0 0 1px rgba(212,175,55,0.08)',
      overflow: 'hidden',
    }"
  >
    <!-- 关闭按钮 -->
    <a-button
      type="text"
      class="!text-abyss-400 hover:!text-gold-400 absolute right-5 top-5 z-10"
      size="small"
      @click="handleCancel"
    >
      <template #icon>
        <icon-close />
      </template>
    </a-button>
    <!-- 内容容器 -->
    <div class="flex min-h-[500px]">
      <!-- 左侧导航 -->
      <div class="w-[200px] border-r border-gold-dim pr-5">
        <!-- 导航版标题 -->
        <div class="text-xl font-bold text-gold-shine mb-5">设置</div>
        <!-- 导航列表 -->
        <div class="flex flex-col gap-1">
          <div
            class="nav-active cursor-pointer rounded-lg h-9 leading-9 text-gold-600 px-4 text-sm font-medium"
          >
            账号设置
          </div>
        </div>
      </div>
      <!-- 右侧内容 -->
      <div class="flex-1 px-8">
        <!-- 右侧标题 -->
        <div class="text-xl font-bold text-abyss-800 mb-2">账号设置</div>
        <div class="divider-gold mb-5"></div>
        <!-- 账号表单 -->
        <a-form :model="{}" layout="vertical" class="setting-form">
          <a-form-item field="avatar">
            <template #label>
              <div class="flex items-center gap-1">
                <span class="text-abyss-700">账号头像</span>
                <span class="text-gold-400">*</span>
              </div>
            </template>
            <a-upload
              v-model:file-list="accountForm.fileList"
              list-type="picture-card"
              :limit="1"
              image-preview
              :custom-request="
                (option: any) => {
                  const uploadTask = async () => {
                    // 1.提取数据并发起请求获取响应内容
                    const { fileItem, onSuccess } = option
                    await handleUploadImage(fileItem.file as File)
                    accountForm.avatar = image_url
                    onSuccess(image_url)

                    // 2.更新账号头像
                    await handleUpdateAvatar(String(accountForm.avatar))

                    // 3.更新账号信息
                    await updateAccount()
                  }

                  uploadTask()

                  return {}
                }
              "
            />
          </a-form-item>
          <a-form-item field="name">
            <template #label>
              <div class="flex items-center gap-1">
                <span class="text-abyss-700">账号昵称</span>
                <span class="text-gold-400">*</span>
              </div>
            </template>
            <div v-if="updateName" class="flex items-center gap-2 w-full">
              <!-- 左侧输入框 -->
              <a-input
                v-model="accountForm.name"
                placeholder="请输入账号名称"
                :default-value="accountStore.account.name"
              />
              <!-- 取消&保存 -->
              <div class="flex items-center gap-1">
                <a-button
                  class="rounded-lg !border-gold-dim !text-abyss-500 hover:!border-gold-bright hover:!text-abyss-800"
                  @click="
                    () => {
                      updateName = false
                      accountForm.name = accountStore.account.name
                    }
                  "
                >
                  取消
                </a-button>
                <a-button
                  type="primary"
                  class="rounded-lg"
                  @click="
                    async () => {
                      // 发起请求更新账号名称
                      await handleUpdateName(accountForm.name)

                      // 成功更新则重新获取账号数据并隐藏输入框
                      await updateAccount()
                      updateName = false
                    }
                  "
                >
                  保存
                </a-button>
              </div>
            </div>
            <div v-else class="flex items-center gap-1">
              <div class="text-abyss-700">{{ accountStore.account.name }}</div>
              <a-button
                size="mini"
                type="text"
                class="!text-gold-400 hover:!text-gold-600"
                @click="updateName = true"
              >
                <template #icon>
                  <icon-edit />
                </template>
              </a-button>
            </div>
          </a-form-item>
          <a-form-item field="password">
            <template #label>
              <div class="flex items-center gap-1">
                <span class="text-abyss-700">账号密码</span>
                <span class="text-gold-400">*</span>
              </div>
            </template>
            <div v-if="updatePassword" class="flex items-center gap-2 w-full">
              <!-- 左侧输入框 -->
              <a-input-password v-model="accountForm.password" placeholder="请输入账号密码" />
              <!-- 取消&保存 -->
              <div class="flex items-center gap-1">
                <a-button
                  class="rounded-lg !border-gold-dim !text-abyss-500 hover:!border-gold-bright hover:!text-abyss-800"
                  @click="
                    () => {
                      updatePassword = false
                      accountForm.password = ''
                    }
                  "
                >
                  取消
                </a-button>
                <a-button
                  type="primary"
                  class="rounded-lg"
                  @click="
                    async () => {
                      // 发起请求更新账号密码
                      await handleUpdatePassword(accountForm.password)

                      // 隐藏输入框并将输入框值清空
                      accountForm.password = ''
                      updatePassword = false
                    }
                  "
                >
                  保存
                </a-button>
              </div>
            </div>
            <div v-else class="flex items-center gap-1">
              <div class="text-abyss-700">******</div>
              <a-button
                size="mini"
                type="text"
                class="!text-gold-400 hover:!text-gold-600"
                @click="updatePassword = true"
              >
                <template #icon>
                  <icon-edit />
                </template>
              </a-button>
            </div>
          </a-form-item>
          <a-form-item field="email">
            <template #label>
              <span class="text-abyss-700">绑定邮箱</span>
            </template>
            <a-input readonly v-model="accountForm.email" />
          </a-form-item>
        </a-form>
      </div>
    </div>
  </a-modal>
</template>

<style scoped>
/* 上传组件主题适配 */
.setting-form :deep(.arco-upload-list-picture) {
  border: 2px solid rgba(212, 175, 55, 0.2) !important;
  border-radius: 12px !important;
  overflow: hidden;
}
.setting-form :deep(.arco-upload-picture-card) {
  border: 2px dashed rgba(212, 175, 55, 0.2) !important;
  border-radius: 12px !important;
  background: rgba(212, 175, 55, 0.03) !important;
  transition: all 0.3s ease;
}
.setting-form :deep(.arco-upload-picture-card:hover) {
  border-color: rgba(212, 175, 55, 0.4) !important;
  background: rgba(212, 175, 55, 0.06) !important;
}
.setting-form :deep(.arco-upload-picture-card .arco-icon) {
  color: #d4af37;
}
/* 表单标签 */
.setting-form :deep(.arco-form-item-label) {
  color: #2a3a5c;
}
/* 只读输入框 */
.setting-form :deep(.arco-input[readonly]) {
  color: #505f83;
  cursor: default;
}
</style>
