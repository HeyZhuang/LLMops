import { Message } from '@arco-design/web-vue'
import { apiPrefix, httpCode } from '@/config'
import { useCredentialStore } from '@/stores/credential'
import router from '@/router'

const TIME_OUT = 100000

const baseFetchOptions = {
  method: 'GET',
  mode: 'cors' as RequestMode,
  credentials: 'include' as RequestCredentials,
  redirect: 'follow' as RequestRedirect,
}

type FetchOptionType = Omit<RequestInit, 'body'> & {
  params?: Record<string, any>
  body?: BodyInit | Record<string, any> | null
}

const createHeaders = (headers?: HeadersInit) => {
  const nextHeaders = new Headers(headers)
  if (!nextHeaders.has('Content-Type')) {
    nextHeaders.set('Content-Type', 'application/json')
  }
  return nextHeaders
}

const createFetchOptions = (fetchOptions: FetchOptionType) => ({
  ...baseFetchOptions,
  ...fetchOptions,
  headers: createHeaders(fetchOptions.headers),
})

const normalizeBody = (body?: FetchOptionType['body']) => {
  if (!body) return undefined

  if (
    body instanceof FormData ||
    body instanceof URLSearchParams ||
    body instanceof Blob ||
    typeof body === 'string'
  ) {
    return body
  }

  return JSON.stringify(body)
}

const resolveErrorMessage = (error: unknown) => {
  const rawMessage = String((error as Error)?.message || error || '')

  if (rawMessage.includes('The requested URL was not found on the server')) {
    return '接口地址不存在，请确认后端已重启并加载最新路由'
  }

  if (rawMessage.includes('Failed to fetch')) {
    return '无法连接后端服务，请确认 http://localhost:5000 已启动'
  }

  return rawMessage || '请求失败，请稍后重试'
}

const navigateSafely = async (to: { name?: string; path?: string }) => {
  const target = to.name ? router.resolve({ name: to.name }) : router.resolve({ path: to.path || '/' })

  if (router.currentRoute.value.fullPath !== target.fullPath) {
    await router.replace(target)
  }
}

const baseFetch = <T>(url: string, fetchOptions: FetchOptionType): Promise<T> => {
  const options = createFetchOptions(fetchOptions)
  const { credential, clear: clearCredential } = useCredentialStore()
  const access_token = credential.access_token
  if (access_token) options.headers.set('Authorization', `Bearer ${access_token}`)

  let urlWithPrefix = `${apiPrefix}${url.startsWith('/') ? url : `/${url}`}`
  const { method, params, body } = options

  if (method === 'GET' && params) {
    const paramsArray: string[] = []
    Object.keys(params).forEach((key) => {
      paramsArray.push(`${key}=${encodeURIComponent(params[key])}`)
    })
    if (urlWithPrefix.search(/\?/) === -1) {
      urlWithPrefix += `?${paramsArray.join('&')}`
    } else {
      urlWithPrefix += `&${paramsArray.join('&')}`
    }

    delete options.params
  }

  const normalizedBody = normalizeBody(body)
  if (normalizedBody !== undefined) {
    options.body = normalizedBody
  }

  return Promise.race([
    new Promise((_, reject) => {
      setTimeout(() => {
        reject(new Error('接口已超时'))
      }, TIME_OUT)
    }),
    new Promise((resolve, reject) => {
      globalThis
        .fetch(urlWithPrefix, options as RequestInit)
        .then(async (res) => {
          const contentType = res.headers.get('Content-Type') || ''
          const json = contentType.includes('application/json') ? await res.json() : null

          if (!json) {
            const message = res.ok
              ? '接口返回格式异常，请检查后端响应'
              : '接口请求失败，请确认后端服务是否已启动'
            Message.error(message)
            reject(new Error(message))
            return
          }

          if (json.code === httpCode.success) {
            resolve(json)
            return
          }

          if (json.code === httpCode.unauthorized) {
            clearCredential()
            await navigateSafely({ name: 'auth-login' })
            reject(new Error(json.message || '登录状态已失效，请重新登录'))
            return
          }

          if (json.code === httpCode.notFound) {
            await navigateSafely({ name: 'errors-not-found' })
            reject(new Error(json.message || '请求的资源不存在'))
            return
          }

          if (json.code === httpCode.forbidden) {
            await navigateSafely({ name: 'errors-forbidden' })
            reject(new Error(json.message || '暂无权限访问该资源'))
            return
          }

          const message = json.message || '请求失败，请稍后重试'
          Message.error(message)
          reject(new Error(message))
        })
        .catch((err) => {
          const message = resolveErrorMessage(err)
          Message.error(message)
          reject(new Error(message))
        })
    }),
  ]) as Promise<T>
}

export const ssePost = async (
  url: string,
  fetchOptions: FetchOptionType,
  onData: (data: { [key: string]: any }) => void,
) => {
  const options = createFetchOptions({ ...fetchOptions, method: 'POST' })
  const { credential } = useCredentialStore()
  const access_token = credential.access_token
  if (access_token) options.headers.set('Authorization', `Bearer ${access_token}`)

  const urlWithPrefix = `${apiPrefix}${url.startsWith('/') ? url : `/${url}`}`
  const normalizedBody = normalizeBody(fetchOptions.body)
  if (normalizedBody !== undefined) {
    options.body = normalizedBody
  }

  const response = await globalThis.fetch(urlWithPrefix, options as RequestInit)
  const contentType = response.headers.get('Content-Type')
  if (contentType?.includes('application/json')) {
    return await response.json()
  }

  return await handleStream(response, onData)
}

const handleStream = (
  response: Response,
  onData: (data: Record<string, any>) => void,
): Promise<void> => {
  return new Promise((resolve, reject) => {
    if (!response.ok) {
      reject(new Error('网络请求失败'))
      return
    }

    const reader = response.body?.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''
    let event = ''
    let data = ''

    const read = () => {
      reader?.read().then((result: any) => {
        if (result.done) {
          resolve()
          return
        }

        buffer += decoder.decode(result.value, { stream: true })
        const lines = buffer.split('\n')

        try {
          lines.forEach((line) => {
            line = line.trim()
            if (line.startsWith('event:')) {
              event = line.slice(6).trim()
            } else if (line.startsWith('data:')) {
              data = line.slice(5).trim()
            }

            if (line === '') {
              if (event !== '' && data !== '') {
                onData({
                  event: event,
                  data: JSON.parse(data),
                })
                event = ''
                data = ''
              }
            }
          })
          buffer = lines.pop() || ''
        } catch (e) {
          reject(e)
          return
        }

        read()
      }).catch(reject)
    }

    read()
  })
}

export const upload = <T>(url: string, options: any = {}): Promise<T> => {
  const urlWithPrefix = `${apiPrefix}${url.startsWith('/') ? url : `/${url}`}`

  const defaultOptions = {
    method: 'POST',
    url: urlWithPrefix,
    headers: {} as Record<string, string>,
    data: {},
  }
  options = {
    ...defaultOptions,
    ...options,
    headers: { ...defaultOptions.headers, ...options.headers },
  }
  const { credential, clear: clearCredential } = useCredentialStore()
  const access_token = credential.access_token
  if (access_token) options.headers.Authorization = `Bearer ${access_token}`

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest()

    xhr.open(options.method, options.url)
    for (const key in options.headers) {
      xhr.setRequestHeader(key, options.headers[key])
    }

    xhr.withCredentials = true
    xhr.responseType = 'json'

    xhr.onreadystatechange = async () => {
      if (xhr.readyState !== 4) return

      if (xhr.status === 200) {
        const response = xhr.response
        if (response.code === httpCode.success) {
          resolve(response)
        } else if (response.code === httpCode.unauthorized) {
          clearCredential()
          await navigateSafely({ path: '/auth/login' })
          reject(new Error(response.message || '登录状态已失效，请重新登录'))
        } else {
          reject(new Error(response.message || '上传失败，请稍后重试'))
        }
        return
      }

      reject(new Error(`上传失败，HTTP ${xhr.status}`))
    }

    xhr.upload.onprogress = options.onprogress
    xhr.send(options.data)
  })
}

export const request = <T>(url: string, options = {}) => {
  return baseFetch<T>(url, options)
}

export const requestBlob = async (url: string, options: FetchOptionType = {}) => {
  const fetchOptions = createFetchOptions({ ...options, method: options.method || 'GET' })
  const { credential, clear: clearCredential } = useCredentialStore()
  const access_token = credential.access_token
  if (access_token) fetchOptions.headers.set('Authorization', `Bearer ${access_token}`)

  const urlWithPrefix = `${apiPrefix}${url.startsWith('/') ? url : `/${url}`}`
  const response = await globalThis.fetch(urlWithPrefix, fetchOptions as RequestInit)

  if (response.status === 401) {
    clearCredential()
    await navigateSafely({ name: 'auth-login' })
    throw new Error('登录状态已失效，请重新登录')
  }

  if (!response.ok) {
    throw new Error(`请求失败，HTTP ${response.status}`)
  }

  return await response.blob()
}

export const get = <T>(url: string, options = {}) => {
  return request<T>(url, Object.assign({}, options, { method: 'GET' }))
}

export const post = <T>(url: string, options = {}) => {
  return request<T>(url, Object.assign({}, options, { method: 'POST' }))
}
