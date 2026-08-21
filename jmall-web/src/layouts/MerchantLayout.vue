<template>
  <div class="merchant-layout">
    <el-container>
      <!-- Sidebar -->
      <el-aside width="220px" class="merchant-sidebar">
        <el-menu :default-active="activeMenu" router>
          <el-menu-item index="/merchant">
            <el-icon><DataAnalysis /></el-icon>
            <span>工作台</span>
          </el-menu-item>
          <el-menu-item index="/merchant/products">
            <el-icon><Goods /></el-icon>
            <span>商品管理</span>
          </el-menu-item>
          <el-menu-item index="/merchant/store">
            <el-icon><Shop /></el-icon>
            <span>店铺装修</span>
          </el-menu-item>
          <el-menu-item index="/merchant/knowledge">
            <el-icon><Document /></el-icon>
            <span>知识库</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <!-- Main Content -->
      <el-main>
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const activeMenu = computed(() => {
  const path = route.path
  if (path.startsWith('/merchant/products')) return '/merchant/products'
  if (path.startsWith('/merchant/store')) return '/merchant/store'
  if (path.startsWith('/merchant/knowledge')) return '/merchant/knowledge'
  return '/merchant'
})
</script>

<style scoped>
.merchant-layout {
  height: calc(100vh - 64px);
}
.merchant-sidebar {
  background: var(--bg-secondary, #fafafa);
  border-right: 1px solid var(--border-color, #e8e8e8);
  display: flex;
  flex-direction: column;
}
</style>
