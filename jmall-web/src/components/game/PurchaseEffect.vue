<template>
  <Teleport to="body">
    <transition name="purchase-overlay">
      <div v-if="active" class="purchase-overlay" @click="dismiss">
        <div class="purchase-card">
          <div class="multiplier-badge" :class="multiplierClass">
            ✨ ×{{ multiplier }} 暴击! ✨
          </div>
          <div class="product-name">{{ productName }}</div>
          <div class="gold-earned">
            <span class="gold-icon">🪙</span>
            <span class="gold-amount">+{{ formatNumber(goldEarned) }}</span>
          </div>
          <div class="tap-hint">点击任意处继续</div>
        </div>
        <!-- Confetti particles -->
        <div class="particles">
          <span v-for="i in 20" :key="i" class="particle" :style="particleStyle(i)" />
        </div>
      </div>
    </transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, nextTick } from 'vue'
import confetti from 'canvas-confetti'

const active = ref(false)
const productName = ref('')
const multiplier = ref(1)
const goldEarned = ref(0)
const goldDisplay = ref(0)

let counting = false

const multiplierClass = computed(() => {
  if (multiplier.value >= 8) return 'legendary'
  if (multiplier.value >= 5) return 'epic'
  if (multiplier.value >= 3) return 'rare'
  return 'normal'
})

async function play(product: { title: string }, mult: number, gold: number) {
  productName.value = product.title
  multiplier.value = mult
  goldEarned.value = gold
  goldDisplay.value = 0
  active.value = true

  await nextTick()

  // Fire confetti burst
  fireConfetti(mult)

  // Animate gold counter
  countUp(gold, mult)
}

function fireConfetti(mult: number) {
  const isEpic = mult >= 5

  // Main burst from center
  confetti({
    particleCount: isEpic ? 150 : 80,
    spread: 100,
    origin: { x: 0.5, y: 0.5 },
    colors: ['#ffd700', '#ff6b6b', '#48dbfb', '#ff9ff3', '#feca57'],
    startVelocity: isEpic ? 45 : 30,
    decay: 0.9,
  })

  // Side bursts for epic/legendary
  if (isEpic) {
    setTimeout(() => {
      confetti({
        particleCount: 60,
        spread: 60,
        origin: { x: 0.2, y: 0.5 },
        colors: ['#ffd700', '#feca57'],
        startVelocity: 40,
      })
      confetti({
        particleCount: 60,
        spread: 60,
        origin: { x: 0.8, y: 0.5 },
        colors: ['#ffd700', '#feca57'],
        startVelocity: 40,
      })
    }, 150)
  }

  // Legendary: sustained celebration
  if (mult >= 8) {
    setTimeout(() => {
      confetti({
        particleCount: 100,
        spread: 360,
        origin: { x: 0.5, y: 0.3 },
        colors: ['#ffd700', '#ff6b6b', '#a29bfe', '#48dbfb', '#ff9ff3'],
        startVelocity: 50,
        decay: 0.85,
      })
    }, 400)
  }
}

function countUp(target: number, mult: number) {
  counting = true
  const duration = mult >= 8 ? 2000 : mult >= 5 ? 1500 : 1000
  const start = performance.now()

  function tick(now: number) {
    if (!counting) return
    const elapsed = now - start
    const progress = Math.min(elapsed / duration, 1)
    // Ease-out cubic for dramatic slowdown at end
    const eased = 1 - Math.pow(1 - progress, 3)
    goldDisplay.value = Math.floor(eased * target)
    if (progress < 1) {
      requestAnimationFrame(tick)
    } else {
      goldDisplay.value = target
    }
  }

  requestAnimationFrame(tick)
}

function dismiss() {
  counting = false
  active.value = false
}

function particleStyle(i: number) {
  const colors = ['#ffd700', '#ff6b6b', '#48dbfb', '#ff9ff3', '#feca57', '#54a0ff']
  return {
    '--x': `${Math.random() * 100}%`,
    '--delay': `${Math.random() * 0.5}s`,
    '--color': colors[i % colors.length],
    '--size': `${8 + Math.random() * 12}px`,
  }
}

function formatNumber(n: number): string {
  return n.toLocaleString()
}

defineExpose({ play })
</script>

<style scoped>
.purchase-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  backdrop-filter: blur(4px);
}
.purchase-card {
  background: linear-gradient(135deg, #1a1a2e, #16213e);
  border: 2px solid #ffd700;
  border-radius: 20px;
  padding: 48px;
  text-align: center;
  color: white;
  animation: card-pop 0.5s cubic-bezier(0.68, -0.55, 0.27, 1.55);
}
@keyframes card-pop {
  0% { transform: scale(0.3); opacity: 0; }
  100% { transform: scale(1); opacity: 1; }
}
.multiplier-badge {
  font-size: 28px;
  font-weight: bold;
  margin-bottom: 16px;
  padding: 8px 24px;
  border-radius: 16px;
  display: inline-block;
}
.multiplier-badge.normal { background: #636e72; }
.multiplier-badge.rare { background: linear-gradient(135deg, #a29bfe, #6c5ce7); }
.multiplier-badge.epic { background: linear-gradient(135deg, #fdcb6e, #e17055); }
.multiplier-badge.legendary { background: linear-gradient(135deg, #ffd700, #ff6b6b); animation: glow 0.5s infinite alternate; }
@keyframes glow {
  from { box-shadow: 0 0 20px #ffd700; }
  to { box-shadow: 0 0 40px #ff6b6b; }
}
.product-name {
  font-size: 20px;
  color: #ddd;
  margin-bottom: 16px;
}
.gold-earned {
  font-size: 36px;
  font-weight: bold;
  color: #ffd700;
}
.tap-hint {
  margin-top: 24px;
  font-size: 14px;
  color: #888;
}
.particles { position: absolute; inset: 0; pointer-events: none; overflow: hidden; }
.particle {
  position: absolute;
  left: var(--x);
  top: -20px;
  width: var(--size);
  height: var(--size);
  background: var(--color);
  border-radius: 50%;
  animation: fall 1.5s var(--delay) linear forwards;
}
@keyframes fall {
  to { top: 110%; opacity: 0; }
}
.purchase-overlay-enter-active { transition: all 0.3s ease; }
.purchase-overlay-leave-active { transition: all 0.3s ease; }
.purchase-overlay-enter-from, .purchase-overlay-leave-to { opacity: 0; }
</style>
