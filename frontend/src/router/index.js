import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue')
  },
  {
    path: '/',
    component: () => import('../components/layout/AppLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'UserDashboard',
        component: () => import('../views/user/UserDashboard.vue')
      },
      {
        path: 'configs',
        name: 'UserConfigs',
        component: () => import('../views/user/ConfigList.vue')
      },
      {
        path: 'clients',
        name: 'UserClients',
        component: () => import('../views/ClientsView.vue')
      }
    ]
  },
  {
    path: '/admin',
    component: () => import('../components/layout/AppLayout.vue'),
    meta: { requiresAuth: true, requireAdmin: true },
    children: [
      {
        path: '',
        name: 'AdminDashboard',
        component: () => import('../views/admin/AdminDashboard.vue')
      },
      {
        path: 'configs',
        name: 'AdminConfigs',
        component: () => import('../views/admin/ConfigManager.vue')
      },
      {
        path: 'configs/:id/edit',
        name: 'AdminConfigEditor',
        component: () => import('../views/admin/ConfigEditor.vue')
      },
      {
        path: 'clients',
        name: 'AdminClients',
        component: () => import('../views/ClientsView.vue')
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('../views/NotFoundView.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  
  if (to.meta.requiresAuth && !authStore.token) {
    return next({ path: '/login' })
  }
  
  if (to.meta.requireAdmin && !authStore.isAdmin) {
    return next({ path: '/' })
  }
  
  if (to.path === '/login' && authStore.token) {
    return next(authStore.isAdmin ? '/admin' : '/')
  }
  
  next()
})

export default router
