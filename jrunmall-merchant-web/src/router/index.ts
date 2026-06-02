import { createRouter, createWebHistory } from 'vue-router'

import MerchantLayout from '@/layouts/MerchantLayout.vue'
import KnowledgeBaseView from '@/views/knowledge-base/KnowledgeBaseView.vue'
import MerchantOrdersView from '@/views/orders/MerchantOrdersView.vue'
import ProductManagementView from '@/views/products/ProductManagementView.vue'
import MerchantSeckillOrdersView from '@/views/seckill-orders/MerchantSeckillOrdersView.vue'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: MerchantLayout,
      redirect: '/products',
      children: [
        { path: '/products', name: 'products', component: ProductManagementView, meta: { title: '商品管理' } },
        { path: '/orders', name: 'orders', component: MerchantOrdersView, meta: { title: '普通订单' } },
        { path: '/seckill-orders', name: 'seckill-orders', component: MerchantSeckillOrdersView, meta: { title: '秒杀订单' } },
        { path: '/knowledge-bases', name: 'knowledge-bases', component: KnowledgeBaseView, meta: { title: '知识库管理' } },
      ],
    },
  ],
})
