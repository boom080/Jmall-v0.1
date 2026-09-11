<template>
  <section class="catch-game" aria-label="接住好物小游戏">
    <header class="game-header">
      <div>
        <span>AI 仍在后台工作</span>
        <h3>接住好物！</h3>
      </div>
      <div class="game-score">好物积分 <strong>{{ score }}</strong></div>
    </header>

    <div class="game-field" :class="{ 'is-playing': playing }">
      <div class="cloud cloud-one" aria-hidden="true"></div>
      <div class="cloud cloud-two" aria-hidden="true"></div>
      <div class="game-status" aria-live="polite">
        <strong>{{ playing ? `${secondsLeft} 秒` : statusText }}</strong>
        <span>{{ playing ? '左右移动接住金币和包裹' : '20 秒轻互动，不影响生成结果' }}</span>
      </div>
      <div
        v-if="playing"
        class="falling-item"
        :style="{ left: `${dropX}%`, top: `${dropY}px` }"
        aria-hidden="true"
      >
        {{ pickup.icon }}
      </div>
      <div class="player" :style="{ left: `calc(${playerX}% - 36px)` }">
        <img :src="logoMark" alt="Jmall 吉祥物" />
      </div>
    </div>

    <footer class="game-controls">
      <button type="button" aria-label="向左移动" @click="move(-12)">←</button>
      <button type="button" class="start-button" @click="startGame">
        {{ playing ? '重新开始' : score > 0 ? '再玩一次' : '开始游戏' }}
      </button>
      <button type="button" aria-label="向右移动" @click="move(12)">→</button>
    </footer>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import logoMark from '@/assets/v0.3/brand/jmall-logo-mark.svg'

const props = withDefaults(defineProps<{ active?: boolean }>(), { active: true })

const pickups = [
  { icon: '🪙', points: 10 },
  { icon: '📦', points: 20 },
  { icon: '⭐', points: 15 },
  { icon: '❔', points: -10 },
]

const score = ref(0)
const playing = ref(false)
const secondsLeft = ref(20)
const playerX = ref(50)
const dropX = ref(50)
const dropY = ref(58)
const pickupIndex = ref(0)
let timer: number | undefined
let ticker: number | undefined

const pickup = computed(() => pickups[pickupIndex.value])
const statusText = computed(() => score.value > 0 ? `本轮获得 ${score.value} 分` : '准备开始')

function move(delta: number) {
  playerX.value = Math.max(10, Math.min(90, playerX.value + delta))
}

function resetDrop() {
  dropY.value = 58
  dropX.value = 12 + Math.random() * 76
  pickupIndex.value = Math.floor(Math.random() * pickups.length)
}

function stopGame() {
  playing.value = false
  if (timer) window.clearInterval(timer)
  if (ticker) window.clearInterval(ticker)
  timer = undefined
  ticker = undefined
}

function startGame() {
  stopGame()
  score.value = 0
  secondsLeft.value = 20
  playing.value = true
  resetDrop()

  ticker = window.setInterval(() => {
    dropY.value += 8
    if (dropY.value < 188) return
    if (Math.abs(dropX.value - playerX.value) < 15) {
      score.value = Math.max(0, score.value + pickup.value.points)
    }
    resetDrop()
  }, 70)

  timer = window.setInterval(() => {
    secondsLeft.value -= 1
    if (secondsLeft.value <= 0) stopGame()
  }, 1000)
}

watch(() => props.active, (active) => {
  if (!active) stopGame()
})

onBeforeUnmount(stopGame)
</script>

<style scoped>
.catch-game {
  overflow: hidden;
  border: 1px solid var(--jm-line, #eedfd2);
  border-radius: 22px;
  color: var(--jm-text, #342b4a);
  background: var(--jm-surface, #fffefd);
}

.game-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 15px 16px;
}

.game-header > div:first-child { display: grid; gap: 2px; }
.game-header span { color: var(--jm-muted, #84798d); font-size: 11px; }
.game-header h3 { margin: 0; font-size: 18px; font-weight: 700; }
.game-score { padding: 7px 10px; border-radius: 12px; background: var(--jm-yellow-soft, #fff4cf); font-size: 11px; }
.game-score strong { color: #b57412; font-size: 16px; }

.game-field {
  position: relative;
  min-height: 260px;
  overflow: hidden;
  background: linear-gradient(#caf1f4 0 64%, #bfe0b2 64% 72%, #e8d4a5 72%);
}

.game-field::after {
  content: '';
  position: absolute;
  inset: auto 0 0;
  height: 24px;
  background: rgba(151, 105, 61, .12);
}

.cloud {
  position: absolute;
  width: 80px;
  height: 24px;
  border-radius: 99px;
  background: rgba(255,255,255,.62);
}
.cloud-one { left: 8%; top: 30%; }
.cloud-two { right: 10%; top: 42%; transform: scale(.72); }

.game-status {
  position: absolute;
  z-index: 3;
  left: 12px;
  right: 12px;
  top: 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 12px;
  background: rgba(255,255,255,.84);
  backdrop-filter: blur(8px);
}
.game-status strong { font-size: 12px; }
.game-status span { color: #6f6577; font-size: 10px; }

.falling-item {
  position: absolute;
  z-index: 3;
  transform: translateX(-50%);
  font-size: 30px;
}

.player {
  position: absolute;
  z-index: 4;
  bottom: 14px;
  width: 72px;
  height: 72px;
  transition: left .12s ease;
}
.player img { display: block; width: 100%; height: 100%; }

.game-controls {
  display: grid;
  grid-template-columns: 48px minmax(110px, 1fr) 48px;
  gap: 8px;
  padding: 12px;
}
.game-controls button {
  min-height: 42px;
  border: 1px solid var(--jm-line, #eedfd2);
  border-radius: 12px;
  color: var(--jm-text, #342b4a);
  background: var(--jm-soft, #fff1e2);
  cursor: pointer;
}
.game-controls .start-button { color: #fff; border-color: var(--jm-red, #ff4d63); background: var(--jm-red, #ff4d63); }

@media (prefers-reduced-motion: reduce) {
  .player { transition: none; }
}
</style>
