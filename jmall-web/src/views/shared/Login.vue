<template>
  <div class="auth-page">
    <el-card class="auth-card" shadow="hover">
      <h2>👋 欢迎回到 Jmall</h2>
      <p class="subtitle">AI 电商模拟经营平台</p>
      <el-form @submit.prevent="doLogin">
        <el-form-item>
          <el-input v-model="form.username" placeholder="用户名" prefix-icon="User" size="large" />
        </el-form-item>
        <el-form-item>
          <el-input v-model="form.password" type="password" placeholder="密码" prefix-icon="Lock" size="large" show-password @keyup.enter="doLogin" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" size="large" :loading="loading" @click="doLogin" style="width:100%">
            登录
          </el-button>
        </el-form-item>
      </el-form>
      <div class="auth-footer">
        还没有账号？<router-link to="/register">立即注册</router-link>
      </div>
      <el-divider />
      <div class="demo-hint">
        <p>🎮 演示账号: demo / demo123</p>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const loading = ref(false)

const form = reactive({ username: '', password: '' })

async function doLogin() {
  if (!form.username || !form.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    await authStore.login(form)
    ElMessage.success('登录成功!')
    const redirect = (route.query.redirect as string) || '/shop'
    router.push(redirect)
  } catch (e: any) {
    ElMessage.error(e.message || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-page {
  display: flex; align-items: center; justify-content: center;
  min-height: calc(100vh - 120px);
}
.auth-card {
  width: 420px; text-align: center; border-radius: 16px;
}
.auth-card h2 { margin: 0 0 8px; }
.subtitle { color: #999; margin: 0 0 24px; }
.auth-footer { font-size: 14px; color: #666; }
.demo-hint { font-size: 13px; color: #999; }
.demo-hint p { margin: 0; }
</style>
