import { ref } from 'vue'
import { defineStore } from 'pinia'

export const useMerchantUiStore = defineStore('merchant-ui', () => {
  const appTitle = ref('Jrunmall Merchant')
  const sidebarCollapsed = ref(false)

  return {
    appTitle,
    sidebarCollapsed,
  }
})


