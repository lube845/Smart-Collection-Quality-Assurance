<template>
  <div id="app" class="app-container">
    <router-view />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()

onMounted(async () => {
  // 检查登录状态
  const token = localStorage.getItem('access_token')
  if (token) {
    try {
      await userStore.fetchCurrentUser()
    } catch (e) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
    }
  }
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #app {
  height: 100%;
  width: 100%;
}

.app-container {
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
</style>
