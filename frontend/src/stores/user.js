import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'

export const useUserStore = defineStore('user', () => {
  const user = ref(null)
  const token = ref(localStorage.getItem('access_token') || '')
  const refreshToken = ref(localStorage.getItem('refresh_token') || '')

  const isLoggedIn = computed(() => !!token.value)
  const username = computed(() => user.value?.username || '')
  const role = computed(() => user.value?.role || '')

  async function login(username, password) {
    const response = await api.auth.login(username, password)
    token.value = response.access_token
    refreshToken.value = response.refresh_token
    localStorage.setItem('access_token', response.access_token)
    localStorage.setItem('refresh_token', response.refresh_token)
    await fetchCurrentUser()
    return response
  }

  async function logout() {
    try {
      await api.auth.logout()
    } finally {
      token.value = ''
      refreshToken.value = ''
      user.value = null
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
    }
  }

  async function fetchCurrentUser() {
    const response = await api.user.getCurrentUser()
    user.value = response
    return response
  }

  return {
    user,
    token,
    refreshToken,
    isLoggedIn,
    username,
    role,
    login,
    logout,
    fetchCurrentUser
  }
})
