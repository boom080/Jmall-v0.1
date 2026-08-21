<template>
  <Teleport to="body">
    <div class="achievement-popup" :class="{ visible: !!achievement }">
      <div class="achievement-card">
        <div class="achievement-icon">{{ achievement?.icon || '🏆' }}</div>
        <div class="achievement-name">{{ achievement?.name }}</div>
        <div class="achievement-desc">{{ achievement?.description }}</div>
        <div class="unlock-label">🎉 成就解锁!</div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import type { Achievement } from '@/types'

defineProps<{
  achievement: Achievement | null
}>()

defineEmits<{
  close: []
}>()
</script>

<style scoped>
.achievement-popup {
  position: fixed;
  top: 80px;
  right: -320px;
  z-index: 9998;
  transition: right 0.6s cubic-bezier(0.68, -0.55, 0.27, 1.55);
}
.achievement-popup.visible {
  right: 20px;
}
.achievement-card {
  background: linear-gradient(135deg, #1a1a2e, #2d3436);
  border: 2px solid #ffd700;
  border-radius: 16px;
  padding: 24px 32px;
  color: white;
  text-align: center;
  width: 280px;
  box-shadow: 0 8px 32px rgba(255, 215, 0, 0.3);
}
.achievement-icon { font-size: 48px; margin-bottom: 8px; }
.achievement-name { font-size: 18px; font-weight: bold; margin-bottom: 4px; }
.achievement-desc { font-size: 14px; color: #aaa; margin-bottom: 12px; }
.unlock-label { font-size: 16px; color: #ffd700; font-weight: bold; }
</style>
