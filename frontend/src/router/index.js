import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: () => import('@/views/Layout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        redirect: '/dashboard'
      },
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '数据概览' }
      },
      {
        path: 'recordings',
        name: 'Recordings',
        component: () => import('@/views/Recordings.vue'),
        meta: { title: '录音管理' }
      },
      {
        path: 'recordings/:id',
        name: 'RecordingDetail',
        component: () => import('@/views/RecordingDetail.vue'),
        meta: { title: '录音详情' }
      },
      {
        path: 'rules',
        name: 'Rules',
        component: () => import('@/views/Rules.vue'),
        meta: { title: '规则管理' }
      },
      {
        path: 'rules/:id',
        name: 'RuleDetail',
        component: () => import('@/views/RuleDetail.vue'),
        meta: { title: '规则详情' }
      },
      {
        path: 'statistics',
        name: 'Statistics',
        component: () => import('@/views/Statistics.vue'),
        meta: { title: '数据统计' }
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/Settings.vue'),
        meta: { title: '系统设置' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  const token = localStorage.getItem('access_token')

  if (to.meta.requiresAuth !== false && !token) {
    next('/login')
  } else if (to.path === '/login' && token) {
    next('/')
  } else {
    next()
  }
})

export default router
