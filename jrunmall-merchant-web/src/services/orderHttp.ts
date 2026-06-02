import axios from 'axios'

export const orderHttp = axios.create({
  baseURL: import.meta.env.VITE_ORDER_API_BASE_URL || import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 6000,
})


