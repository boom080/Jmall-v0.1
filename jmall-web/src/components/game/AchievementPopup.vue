<template>
  <Teleport to="body">
    <div class="achievement-popup" :class="{ visible: !!achievement }">
      <button class="achievement-card" type="button" aria-label="关闭成就提示" @click="$emit('close')">
        <JmallMascot variant="reward" :size="102" label="Jmall 吉祥物庆祝获得奖励" />
        <div class="achievement-copy">
          <div class="unlock-label">任务完成 · 成就解锁</div>
          <div class="achievement-name"><span>{{ achievement?.icon || '🏆' }}</span>{{ achievement?.name }}</div>
          <div class="achievement-desc">{{ achievement?.description }}</div>
          <small>点击收下奖励</small>
        </div>
      </button>
      </div>
  </Teleport>
</template>

<script setup lang="ts">
import type { Achievement } from '@/types'
import JmallMascot from '@/components/brand/JmallMascot.vue'

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
  top: 88px;
  right: -410px;
  z-index: 9998;
  transition: right .6s cubic-bezier(.68, -.55, .27, 1.55);
}
.achievement-popup.visible { right: 20px; }
.achievement-card {
  display: flex;
  align-items: center;
  width: 374px;
  padding: 8px 18px 8px 8px;
  border: 2px solid #ffe09a;
  border-radius: 24px;
  color: var(--jm-text, #342b4a);
  text-align: left;
  background: linear-gradient(135deg, #fff9e7, #fff0f2);
  box-shadow: 0 18px 50px rgba(129, 75, 79, .20);
  cursor: pointer;
}
.achievement-copy { display: grid; min-width: 0; gap: 4px; }
.unlock-label { color: #bd7b14; font-size: 10px; font-weight: 800; letter-spacing: .08em; }
.achievement-name { display: flex; align-items: center; gap: 6px; font-size: 17px; font-weight: 800; }
.achievement-name span { font-size: 20px; }
.achievement-desc { overflow: hidden; color: var(--jm-muted, #84798d); font-size: 12px; text-overflow: ellipsis; white-space: nowrap; }
.achievement-copy small { margin-top: 2px; color: var(--jm-red, #ff4d63); font-size: 10px; font-weight: 700; }

@media (max-width: 440px) {
  .achievement-popup { top: 70px; right: -100%; left: auto; }
  .achievement-popup.visible { right: 10px; }
  .achievement-card { width: calc(100vw - 20px); }
}
</style>
