import axios from 'axios'
import { ElMessage } from 'element-plus'

const request = axios.create({
  baseURL: '/api/v1',
  timeout: 30000
})

// 请求拦截器
request.interceptors.request.use(
  config => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  response => {
    return response.data
  },
  async error => {
    const { response } = error

    if (response?.status === 401) {
      // 尝试刷新token
      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken) {
        try {
          const res = await axios.post('/api/v1/auth/refresh', {
            refresh_token: refreshToken
          })
          localStorage.setItem('access_token', res.data.access_token)
          localStorage.setItem('refresh_token', res.data.refresh_token)
          // 重新请求
          error.config.headers.Authorization = `Bearer ${res.data.access_token}`
          return request(error.config)
        } catch (e) {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          window.location.href = '/login'
        }
      } else {
        window.location.href = '/login'
      }
    }

    const message = response?.data?.detail || response?.data?.message || '请求失败'
    ElMessage.error(message)
    return Promise.reject(error)
  }
)

export default {
  // 认证
  auth: {
    login: (username, password) => request.post('/auth/login', { username, password }),
    logout: () => request.post('/auth/logout'),
    refresh: (refresh_token) => request.post('/auth/refresh', { refresh_token })
  },

  // 用户
  user: {
    getCurrentUser: () => request.get('/users/me'),
    getUser: (id) => request.get(`/users/${id}`),
    createUser: (data) => request.post('/users', data),
    updateUser: (id, data) => request.put(`/users/${id}`, data)
  },

  // 组织
  organization: {
    list: () => request.get('/organizations'),
    get: (id) => request.get(`/organizations/${id}`),
    create: (data) => request.post('/organizations', data),
    update: (id, data) => request.put(`/organizations/${id}`, data)
  },

  // 应用组
  appGroup: {
    list: (params) => request.get('/app-groups', { params }),
    get: (id) => request.get(`/app-groups/${id}`),
    create: (params) => request.post('/app-groups', null, { params }),
    update: (id, data) => request.put(`/app-groups/${id}`, data)
  },

  // 录音
  recording: {
    list: (params) => request.get('/recordings', { params }),
    get: (id) => request.get(`/recordings/${id}`),
    initUpload: (data) => request.post('/recordings/init-upload', data),
    upload: (id, file) => {
      const formData = new FormData()
      formData.append('file', file)
      return request.post(`/recordings/${id}/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
    },
    triggerTranscribe: (id) => request.post(`/recordings/${id}/transcribe`),
    triggerScore: (id, ruleId) => request.post(`/recordings/${id}/score`, { rule_id: ruleId }),
    getScore: (id) => request.get(`/recordings/${id}/score`),
    getPlayUrl: (id) => request.get(`/recordings/${id}/play`)
  },

  // 规则
  rule: {
    list: (params) => request.get('/rules', { params }),
    get: (id) => request.get(`/rules/${id}`),
    create: (data) => request.post('/rules', data),
    update: (id, data) => request.put(`/rules/${id}`, data),
    delete: (id) => request.delete(`/rules/${id}`),
    publish: (id, remark) => request.post(`/rules/${id}/publish`, { remark }),
    test: (id, data) => request.post(`/rules/${id}/test`, data),
    copy: (id, newVersion) => request.post(`/rules/${id}/copy`, { new_version: newVersion }),
    createItem: (ruleId, data) => request.post(`/rules/items?rule_id=${ruleId}`, data),
    updateItem: (id, data) => request.put(`/rules/items/${id}`, data),
    deleteItem: (id) => request.delete(`/rules/items/${id}`)
  },

  // 统计
  statistics: {
    overview: (params) => request.get('/statistics/overview', { params }),
    scoreDistribution: (params) => request.get('/statistics/score-distribution', { params }),
    agentRankings: (params) => request.get('/statistics/agent-rankings', { params })
  },

  // 导出
  export: {
    recordings: (params) => request.post('/export/recordings', null, { params })
  }
}
