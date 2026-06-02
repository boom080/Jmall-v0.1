import { createRouter, createWebHistory } from 'vue-router'

import UserLayout from '@/layouts/UserLayout.vue'
import AccountView from '@/views/account/AccountView.vue'
import AddressesView from '@/views/account/AddressesView.vue'
import LoginView from '@/views/auth/LoginView.vue'
import RegisterView from '@/views/auth/RegisterView.vue'
import CartView from '@/views/cart/CartView.vue'
import CheckoutView from '@/views/checkout/CheckoutView.vue'
import HomeView from '@/views/home/HomeView.vue'
import OrderDetailView from '@/views/orders/OrderDetailView.vue'
import OrdersView from '@/views/orders/OrdersView.vue'
import ProductDetailView from '@/views/products/ProductDetailView.vue'
import ProductsView from '@/views/products/ProductsView.vue'
import SeckillView from '@/views/seckill/SeckillView.vue'
import { useAuthStore } from '@/store/auth'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: UserLayout,
      children: [
        { path: '', name: 'home', component: HomeView },
        { path: 'products', name: 'products', component: ProductsView },
        { path: 'products/:productId', name: 'product-detail', component: ProductDetailView },
        { path: 'login', name: 'login', component: LoginView },
        { path: 'register', name: 'register', component: RegisterView },
        { path: 'cart', name: 'cart', component: CartView, meta: { requiresAuth: true } },
        { path: 'checkout', name: 'checkout', component: CheckoutView, meta: { requiresAuth: true } },
        { path: 'orders', name: 'orders', component: OrdersView, meta: { requiresAuth: true } },
        { path: 'orders/:orderRef', name: 'order-detail', component: OrderDetailView, meta: { requiresAuth: true } },
        { path: 'seckill', name: 'seckill', component: SeckillView, meta: { requiresAuth: true } },
        { path: 'account', name: 'account', component: AccountView, meta: { requiresAuth: true } },
        { path: 'account/addresses', name: 'addresses', component: AddressesView, meta: { requiresAuth: true } },
      ],
    },
  ],
})

router.beforeEach(async (to) => {
  const authStore = useAuthStore()

  await authStore.ensureSession()

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return {
      name: 'login',
      query: {
        redirect: to.fullPath,
      },
    }
  }

  if ((to.name === 'login' || to.name === 'register') && authStore.isAuthenticated) {
    return { name: 'account' }
  }

  return true
})


