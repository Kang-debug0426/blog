import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('@/view/Home/index.vue'),
      meta: { title: 'FeiTwnd的简历' }
    },
    {
      path: '/403',
      name: 'forbidden',
      component: () => import('@/view/Forbidden/index.vue'),
      meta: { title: '无权访问' }
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'notFound',
      component: () => import('@/view/NotFound/index.vue'),
      meta: { title: '页面不存在' }
    }
  ]
})

router.beforeEach((to) => {
  document.title = to.meta.title || 'CV'
  return true
})

export default router
