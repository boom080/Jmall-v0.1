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
  position: relative;
  min-height: calc(100vh - 72px);
  padding: 0;
  isolation: isolate;
}

.shopper-layout::before {
  position: fixed;
  z-index: -1;
  top: 120px;
  right: -80px;
  width: 240px;
  height: 240px;
  border-radius: 50%;
  background: rgba(139, 124, 246, .06);
  filter: blur(2px);
  content: '';
  pointer-events: none;
}

@media (max-width: 760px) {
  .shopper-layout { min-height: calc(100vh - 62px); }
}
</style>
