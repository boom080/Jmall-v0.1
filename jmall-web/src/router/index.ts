import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    // === Shopper routes ===
    {
      path: '/shop',
      component: () => import('@/layouts/ShopperLayout.vue'),
      children: [
        { path: '', name: 'shop-home', component: () => import('@/views/shopper/ProductFeed.vue') },
        { path: 'product/:id', name: 'product-detail', component: () => import('@/views/shopper/ProductDetail.vue') },
        { path: 'leaderboard', name: 'leaderboard', component: () => import('@/views/game/Leaderboard.vue') },
        { path: 'cart', name: 'cart', component: () => import('@/views/shopper/Cart.vue'), meta: { requiresAuth: true } },
        { path: 'checkout', name: 'checkout', component: () => import('@/views/shopper/Checkout.vue'), meta: { requiresAuth: true } },
        { path: 'orders', name: 'orders', component: () => import('@/views/shopper/Orders.vue'), meta: { requiresAuth: true } },
      ],
    },
    // === Merchant routes ===
    {
      path: '/merchant',
      component: () => import('@/layouts/MerchantLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        { path: '', name: 'merchant-dashboard', component: () => import('@/views/merchant/Dashboard.vue') },
        { path: 'products', name: 'merchant-products', component: () => import('@/views/merchant/ProductEditor.vue') },
        { path: 'products/:id', name: 'merchant-product-edit', component: () => import('@/views/merchant/ProductEditor.vue') },
        { path: 'store', name: 'merchant-store', component: () => import('@/views/merchant/StoreManager.vue') },
        { path: 'knowledge', name: 'merchant-knowledge', component: () => import('@/views/merchant/KnowledgeBase.vue') },
      ],
    },
    // === Store front page ===
    {
      path: '/store/:storeId', name: 'store-front', component: () => import('@/views/shopper/StorePage.vue'),
    },
    // === Shared routes ===
    {
      path: '/login', name: 'login', component: () => import('@/views/shared/Login.vue'),
    },
    {
      path: '/register', name: 'register', component: () => import('@/views/shared/Register.vue'),
    },
    {
      path: '/profile', name: 'profile', component: () => import('@/views/shared/Profile.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/collections', name: 'collections', component: () => import('@/views/game/Collection.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/achievements', name: 'achievements', component: () => import('@/views/game/Achievements.vue'),
      meta: { requiresAuth: true },
    },
    // === Redirects ===
    { path: '/', redirect: '/shop' },
    { path: '/leaderboard', redirect: '/shop/leaderboard' },
  ],
})

router.beforeEach(async (to, _from, next) => {
  const authStore = useAuthStore()

  // Try to restore session
  if (!authStore.sessionChecked) {
    await authStore.ensureSession()
  }

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'login', query: { redirect: to.fullPath } })
  } else {
    next()
  }
})

export default router
