<template>
  <div class="auth-page">
    <el-card class="auth-card" shadow="hover">
      <h2>🚀 加入 Jmall</h2>
      <p class="subtitle">开始你的电商模拟之旅</p>
      <el-form @submit.prevent="doRegister">
        <el-form-item>
          <el-input v-model="form.username" placeholder="用户名" size="large" />
        </el-form-item>
        <el-form-item>
          <el-input v-model="form.nickname" placeholder="昵称" size="large" />
        </el-form-item>
        <el-form-item>
          <el-input v-model="form.password" type="password" placeholder="密码" size="large" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" size="large" :loading="loading" @click="doRegister" style="width:100%">
            注册
          </el-button>
        </el-form-item>
      </el-form>
      <div class="auth-footer">
        已有账号？<router-link to="/login">去登录</router-link>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()
const loading = ref(false)

const form = reactive({ username: '', nickname: '', password: '' })

async function doRegister() {
  loading.value = true
  try {
    await authStore.register(form)
    ElMessage.success('注册成功! 请登录')
    router.push('/login')
  } catch (e: any) {
    ElMessage.error(e.message || '注册失败')
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
.auth-card { width: 420px; text-align: center; border-radius: 16px; }
.auth-card h2 { margin: 0 0 8px; }
.subtitle { color: #999; margin: 0 0 24px; }
.auth-footer { font-size: 14px; color: #666; }
</style>
