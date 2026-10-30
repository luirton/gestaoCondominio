import { defineStore } from "pinia"
import apiClient from "@/api/client"
import axios from "axios"

export const useAuthStore = defineStore("auth", {
  state: () => ({
    user: JSON.parse(localStorage.getItem("user_data") || "null"),
    accessToken: localStorage.getItem("access_token") || null,
    refreshToken: localStorage.getItem("refresh_token") || null,
    activeProfile: localStorage.getItem("active_profile") || null,
    activeCondominioId: localStorage.getItem("active_condominio_id") || null,
    loading: false,
    error: null,
  }),

  getters: {
    isAuthenticated: (state) => !!state.accessToken,
    currentRole: (state) => state.activeProfile || state.user?.perfil_principal || "CONDOMINO",
    isSindico: (state) => state.user?.is_superuser || state.currentRole === "SINDICO",
    isSubSindico: (state) => state.currentRole === "SUBSINDICO",
    isConselheiro: (state) => state.currentRole === "CONSELHEIRO",
    isCondomino: (state) => state.currentRole === "CONDOMINO",
    isFuncionario: (state) => state.currentRole === "FUNCIONARIO",

    // Permissões granulares
    canEdit: (state) => {
      if (state.user?.is_superuser) return true
      return ["SINDICO", "SUBSINDICO"].includes(state.currentRole)
    },
    canDelete: (state) => {
      if (state.user?.is_superuser) return true
      return state.currentRole === "SINDICO"
    },
    isStaffManagement: (state) => {
      if (state.user?.is_superuser) return true
      return ["SINDICO", "SUBSINDICO"].includes(state.currentRole)
    },
  },

  actions: {
    async login(username, password) {
      this.loading = true
      this.error = null
      try {
        const response = await axios.post("http://127.0.0.1:8000/api/token/", {
          username,
          password,
        })

        const { access, refresh, user } = response.data
        this.accessToken = access
        this.refreshToken = refresh
        this.user = user

        localStorage.setItem("access_token", access)
        localStorage.setItem("refresh_token", refresh)
        localStorage.setItem("user_data", JSON.stringify(user))

        // Define perfil ativo inicial
        const perfilInicial = user.perfil_principal || (user.perfis?.length ? user.perfis[0] : "CONDOMINO")
        this.activeProfile = perfilInicial
        localStorage.setItem("active_profile", perfilInicial)

        // Define condomínio ativo inicial caso exista
        if (user.vinculos_condominios?.length > 0) {
          const condId = String(user.vinculos_condominios[0].condominio_id)
          this.activeCondominioId = condId
          localStorage.setItem("active_condominio_id", condId)
        }

        return true
      } catch (err) {
        this.error = err.response?.data?.detail || "Erro ao realizar login. Verifique seu usuário e senha."
        throw err
      } finally {
        this.loading = false
      }
    },

    async fetchCurrentUser() {
      if (!this.accessToken) return null
      try {
        const res = await apiClient.get("/auth/me/")
        this.user = res.data
        localStorage.setItem("user_data", JSON.stringify(res.data))
        if (!this.activeProfile) {
          this.activeProfile = res.data.perfil_principal
          localStorage.setItem("active_profile", res.data.perfil_principal)
        }
        return res.data
      } catch (err) {
        console.error("Erro ao buscar dados do usuário atual:", err)
        return null
      }
    },

    setActiveProfile(perfilCodigo) {
      this.activeProfile = perfilCodigo
      localStorage.setItem("active_profile", perfilCodigo)
    },

    setActiveCondominio(condominioId) {
      this.activeCondominioId = String(condominioId)
      localStorage.setItem("active_condominio_id", String(condominioId))
    },

    logout() {
      this.user = null
      this.accessToken = null
      this.refreshToken = null
      this.activeProfile = null
      this.activeCondominioId = null
      localStorage.removeItem("access_token")
      localStorage.removeItem("refresh_token")
      localStorage.removeItem("user_data")
      localStorage.removeItem("active_profile")
      localStorage.removeItem("active_condominio_id")
    },
  },
})
