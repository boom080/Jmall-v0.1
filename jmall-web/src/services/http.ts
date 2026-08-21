import axios from 'axios'

const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 10000,
})

// Request interceptor - attach token
http.interceptors.request.use((config) => {
  const token = localStorage.getItem('jmall-token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor - unwrap BackendResponse
http.interceptors.response.use(
  (response) => {
    const data = response.data
    // If it follows the R wrapper pattern {code, msg, data}, unwrap it
    if (data && typeof data.code === 'number' && 'data' in data) {
      if (data.code === 10000 || data.code === 0 || data.code === 200) {
        return data.data
      }
      return Promise.reject(new Error(data.msg || '请求失败'))
    }
    return data
  },
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('jmall-token')
      localStorage.removeItem('jmall-user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default http
