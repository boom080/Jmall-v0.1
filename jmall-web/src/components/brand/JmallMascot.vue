<template>
  <span
    class="jmall-mascot"
    :class="[`is-${variant}`, { 'is-animated': animated }]"
    :style="{ '--mascot-size': `${size}px` }"
    role="img"
    :aria-label="label"
  >
    <img :src="assetUrl" alt="" aria-hidden="true" />
    <i class="sparkle sparkle-one" aria-hidden="true">✦</i>
    <i class="sparkle sparkle-two" aria-hidden="true">✦</i>
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import logoMark from '@/assets/v0.3/brand/jmall-logo-mark.svg'
import idlePose from '@/assets/v0.3/mascot/pose-idle.webp'
import wavePose from '@/assets/v0.3/mascot/pose-wave.webp'
import celebratePose from '@/assets/v0.3/mascot/pose-celebrate.webp'

type MascotVariant = 'mark' | 'idle' | 'wave' | 'celebrate' | 'loading' | 'publishing' | 'reward'

const props = withDefaults(defineProps<{
  variant?: MascotVariant
  size?: number
  animated?: boolean
  label?: string
}>(), {
  variant: 'mark',
  size: 88,
  animated: true,
  label: 'Jmall 粉色购物袋吉祥物',
})

const assets: Record<MascotVariant, string> = {
  mark: logoMark,
  idle: idlePose,
  wave: wavePose,
  celebrate: celebratePose,
  // The preview GIF sheets contain multiple stacked frames and can expose a
  // black canvas in browsers. Runtime states use the transparent poses and
  // CSS motion so the mascot always blends into the surrounding card.
  loading: wavePose,
  publishing: celebratePose,
  reward: celebratePose,
}

const assetUrl = computed(() => assets[props.variant])
</script>

<style scoped>
.jmall-mascot {
  --mascot-size: 88px;
  position: relative;
  display: inline-grid;
  width: var(--mascot-size);
  height: var(--mascot-size);
  place-items: center;
  flex: 0 0 auto;
}

.jmall-mascot img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.jmall-mascot.is-mark img { filter: drop-shadow(0 8px 14px rgba(255, 77, 99, 0.18)); }
.jmall-mascot.is-idle img,
.jmall-mascot.is-wave img,
.jmall-mascot.is-celebrate img,
.jmall-mascot.is-loading img,
.jmall-mascot.is-publishing img,
.jmall-mascot.is-reward img { transform: scale(1.08); }

.sparkle {
  position: absolute;
  display: none;
  color: var(--jm-yellow, #ffd75e);
  font-style: normal;
  pointer-events: none;
}

.is-celebrate .sparkle,
.is-reward .sparkle { display: block; }
.sparkle-one { right: 0; top: 4%; font-size: calc(var(--mascot-size) * 0.2); }
.sparkle-two { left: 3%; bottom: 10%; color: var(--jm-mint, #6dd2af); font-size: calc(var(--mascot-size) * 0.13); }

.is-animated.is-mark,
.is-animated.is-idle,
.is-animated.is-wave,
.is-animated.is-loading,
.is-animated.is-publishing,
.is-animated.is-reward { animation: mascot-float 3.2s ease-in-out infinite; }
.is-animated .sparkle-one { animation: mascot-sparkle 1.8s ease-in-out infinite; }
.is-animated .sparkle-two { animation: mascot-sparkle 1.8s .5s ease-in-out infinite; }

@keyframes mascot-float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-4px); }
}

@keyframes mascot-sparkle {
  0%, 100% { opacity: .35; transform: scale(.78) rotate(0); }
  50% { opacity: 1; transform: scale(1.08) rotate(18deg); }
}

@media (prefers-reduced-motion: reduce) {
  .is-animated.is-mark,
  .is-animated.is-idle,
  .is-animated.is-wave,
  .is-animated .sparkle { animation: none; }
}
</style>
