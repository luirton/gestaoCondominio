import axios from "axios"

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api",
  headers: {
    "Content-Type": "application/json",
  },
})

// Intercepta requisições para anexar o token JWT e condomínio ativo
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("access_token")
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    const condId = localStorage.getItem("active_condominio_id")
    if (condId) {
      config.headers["X-Condominio-Id"] = condId
    }
    const activeRole = localStorage.getItem("active_profile")
    if (activeRole) {
      config.headers["X-Active-Role"] = activeRole
      if (!config.params) {
        config.params = {}
      }
      if (!config.params.active_role) {
        config.params.active_role = activeRole
      }
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Intercepta respostas para renovar token se receber 401
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      const refresh = localStorage.getItem("refresh_token")

      if (refresh) {
        try {
          const res = await axios.post("http://127.0.0.1:8000/api/token/refresh/", {
            refresh,
          })
          const newAccess = res.data.access
          localStorage.setItem("access_token", newAccess)
          apiClient.defaults.headers.common["Authorization"] = `Bearer ${newAccess}`
          originalRequest.headers["Authorization"] = `Bearer ${newAccess}`
          return apiClient(originalRequest)
        } catch (refreshErr) {
          // Token de refresh expirado
          localStorage.removeItem("access_token")
          localStorage.removeItem("refresh_token")
          localStorage.removeItem("user_data")
          window.location.href = "/login"
        }
      } else {
        localStorage.removeItem("access_token")
        localStorage.removeItem("user_data")
        window.location.href = "/login"
      }
    }

    return Promise.reject(error)
  }
)

export default apiClient
