<template>
  <div class="shopper-layout">
    <router-view v-slot="{ Component }">
      <transition name="fade" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>
  </div>
</template>

<style scoped>
.shopper-layout {
  padding: 0;
}
</style>
