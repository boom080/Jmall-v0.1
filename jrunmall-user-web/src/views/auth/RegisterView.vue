<template>
  <section class="commerce-panel commerce-card--summary">
    <header class="section-header">
      <div>
        <p class="eyebrow">用户注册</p>
        <h2>创建 Jrunmall 用户</h2>
        <p>当前使用最小真实登录态 MVP，注册后可直接登录并进入用户消费闭环。</p>
      </div>
    </header>

    <p v-if="errorMessage" class="inline-error">{{ errorMessage }}</p>
    <p v-if="successMessage" class="inline-success">{{ successMessage }}</p>

    <form class="stack-form" @submit.prevent="handleRegister">
      <label class="form-field">
        <span>用户名</span>
        <input v-model="form.userName" placeholder="请输入用户名" />
      </label>
      <label class="form-field">
        <span>手机号</span>
        <input v-model="form.phone" placeholder="请输入手机号" />
      </label>
      <label class="form-field">
        <span>密码</span>
        <input v-model="form.password" type="password" placeholder="至少 6 位" />
      </label>
      <button type="submit" class="primary-link button-reset" :disabled="authStore.loading">
        {{ authStore.loading ? '注册中...' : '注册' }}
      </button>
      <RouterLink to="/login" class="secondary-link">已有账号？去登录</RouterLink>
    </form>
  </section>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { useAuthStore } from '@/store/auth'

const router = useRouter()
const authStore = useAuthStore()
const errorMessage = ref('')
const successMessage = ref('')
const form = reactive({
  userName: '',
  phone: '',
  password: '',
})

async function handleRegister() {
  errorMessage.value = ''
  successMessage.value = ''
  try {
    await authStore.register(form)
    successMessage.value = '注册成功，请登录'
    await router.push('/login')
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '注册失败'
  }
}
</script>


