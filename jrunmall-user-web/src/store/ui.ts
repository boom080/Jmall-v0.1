import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

export const useUserUiStore = defineStore('user-ui', () => {
  const cartCount = ref(0)
  const appTitle = ref('Jrunmall User')

  const cartLabel = computed(() => `购物车(${cartCount.value})`)

  function setCartCount(nextCount: number) {
    cartCount.value = Math.max(0, nextCount)
  }

  return {
    appTitle,
    cartCount,
    cartLabel,
    setCartCount,
  }
})


