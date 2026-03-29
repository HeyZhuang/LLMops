import { ref } from 'vue'
import { Message } from '@arco-design/web-vue'
import { exportApp, importApp } from '@/services/app-export'

export const useExportApp = () => {
  const loading = ref(false)

  const handleExportApp = async (app_id: string) => {
    try {
      loading.value = true
      const resp = await exportApp(app_id)
      // 下载为JSON文件
      const blob = new Blob([JSON.stringify(resp.data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${resp.data.name || 'app'}.json`
      a.click()
      URL.revokeObjectURL(url)
      Message.success('应用导出成功')
    } finally {
      loading.value = false
    }
  }

  return { loading, handleExportApp }
}

export const useImportApp = () => {
  const loading = ref(false)
  const importResult = ref<Record<string, any>>({})

  const handleImportApp = async (data: Record<string, any>, callback?: () => void) => {
    try {
      loading.value = true
      const resp = await importApp(data)
      importResult.value = resp.data
      if (resp.data.warnings?.length > 0) {
        Message.warning(`导入成功，但有 ${resp.data.warnings.length} 个警告`)
      } else {
        Message.success('应用导入成功')
      }
      callback?.()
    } finally {
      loading.value = false
    }
  }

  return { loading, importResult, handleImportApp }
}
