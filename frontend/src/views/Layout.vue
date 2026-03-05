<template>
  <el-container class="layout-container">
    <el-aside width="200px" class="sidebar">
      <div class="logo">
        <h3>ASR质检</h3>
      </div>
      <el-menu
        :default-active="activeMenu"
        router
        class="sidebar-menu"
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409eff"
      >
        <el-menu-item index="/dashboard">
          <el-icon><DataAnalysis /></el-icon>
          <span>数据概览</span>
        </el-menu-item>
        <el-menu-item index="/recordings">
          <el-icon><Microphone /></el-icon>
          <span>录音管理</span>
        </el-menu-item>
        <el-menu-item index="/rules">
          <el-icon><Document /></el-icon>
          <span>规则管理</span>
        </el-menu-item>
        <el-menu-item index="/statistics">
          <el-icon><TrendCharts /></el-icon>
          <span>数据统计</span>
        </el-menu-item>
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <span>系统设置</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        <div class="header-left">
          <span class="page-title">{{ route.meta.title }}</span>
        </div>
        <div class="header-right">
          <el-dropdown @command="handleCommand">
            <span class="user-info">
              <el-icon><User /></el-icon>
              {{ userStore.username }}
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const activeMenu = computed(() => route.path)

async function handleCommand(command) {
  if (command === 'logout') {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      type: 'warning'
    })
    await userStore.logout()
    router.push('/login')
  }
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
}

.sidebar {
  background-color: #304156;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #2b3a4a;
}

.logo h3 {
  color: white;
  font-size: 18px;
  margin: 0;
}

.sidebar-menu {
  border-right: none;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
  border-bottom: 1px solid #e6e6e6;
  padding: 0 20px;
}

.header-left {
  display: flex;
  align-items: center;
}

.page-title {
  font-size: 16px;
  font-weight: 500;
  color: #333;
}

.header-right {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 5px;
  cursor: pointer;
  color: #666;
}

.user-info:hover {
  color: #409eff;
}

.main-content {
  background: #f0f2f5;
  padding: 20px;
}
</style>
