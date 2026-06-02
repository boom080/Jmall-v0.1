<template>
  <section class="commerce-panel commerce-card--summary">
    <header class="section-header">
      <div>
        <p class="eyebrow">用户登录</p>
        <h2>登录 Jrunmall 用户端</h2>
        <p>登录后才能访问购物车、下单、订单、秒杀和地址管理。</p>
      </div>
    </header>

    <p v-if="errorMessage" class="inline-error">{{ errorMessage }}</p>

    <form class="stack-form" @submit.prevent="handleLogin">
      <label class="form-field">
        <span>账号</span>
        <input v-model="form.loginacct" placeholder="用户名或手机号" />
      </label>
      <label class="form-field">
        <span>密码</span>
        <input v-model="form.password" type="password" placeholder="请输入密码" />
      </label>
      <button type="submit" class="primary-link button-reset" :disabled="authStore.loading">
        {{ authStore.loading ? '登录中...' : '登录' }}
      </button>
      <RouterLink to="/register" class="secondary-link">没有账号？去注册</RouterLink>
    </form>
  </section>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useAuthStore } from '@/store/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const errorMessage = ref('')
const form = reactive({
  loginacct: '',
  password: '',
})

async function handleLogin() {
  errorMessage.value = ''
  try {
    await authStore.login(form)
    await router.push(String(route.query.redirect || '/account'))
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '登录失败'
  }
}
</script>


