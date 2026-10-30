import { createRouter, createWebHistory } from "vue-router"
import { useAuthStore } from "@/stores/auth"

import AppLayout from "@/layouts/AppLayout.vue"
import LoginView from "@/views/LoginView.vue"
import DashboardView from "@/views/DashboardView.vue"
import CondominiosView from "@/views/CondominiosView.vue"
import UnidadesView from "@/views/UnidadesView.vue"
import PessoasView from "@/views/PessoasView.vue"
import VinculosView from "@/views/VinculosView.vue"
import FuncionariosView from "@/views/FuncionariosView.vue"
import CargosView from "@/views/CargosView.vue"
import UsuariosView from "@/views/UsuariosView.vue"
import MeuEspacoView from "@/views/MeuEspacoView.vue"

const routes = [
  {
    path: "/login",
    name: "Login",
    component: LoginView,
    meta: { guestOnly: true },
  },
  {
    path: "/",
    component: AppLayout,
    meta: { requiresAuth: true },
    children: [
      {
        path: "",
        name: "Dashboard",
        component: DashboardView,
      },
      {
        path: "condominios",
        name: "Condominios",
        component: CondominiosView,
        meta: { allowedRoles: ["SINDICO", "SUBSINDICO", "CONSELHEIRO"] },
      },
      {
        path: "unidades",
        name: "Unidades",
        component: UnidadesView,
        meta: { allowedRoles: ["SINDICO", "SUBSINDICO", "CONSELHEIRO"] },
      },
      {
        path: "pessoas",
        name: "Pessoas",
        component: PessoasView,
        meta: { allowedRoles: ["SINDICO", "SUBSINDICO", "CONSELHEIRO"] },
      },
      {
        path: "vinculos",
        name: "Vinculos",
        component: VinculosView,
        meta: { allowedRoles: ["SINDICO", "SUBSINDICO", "CONSELHEIRO"] },
      },
      {
        path: "funcionarios",
        name: "Funcionarios",
        component: FuncionariosView,
        meta: { allowedRoles: ["SINDICO", "SUBSINDICO", "CONSELHEIRO"] },
      },
      {
        path: "cargos",
        name: "Cargos",
        component: CargosView,
        meta: { allowedRoles: ["SINDICO", "SUBSINDICO", "CONSELHEIRO"] },
      },
      {
        path: "usuarios",
        name: "Usuarios",
        component: UsuariosView,
        meta: { allowedRoles: ["SINDICO", "SUBSINDICO"] },
      },
      {
        path: "meu-espaco",
        name: "MeuEspaco",
        component: MeuEspacoView,
        meta: { allowedRoles: ["CONDOMINO", "SINDICO", "SUBSINDICO"] },
      },
    ],
  },
  {
    path: "/:pathMatch(.*)*",
    redirect: "/",
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Route Guards
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  const token = localStorage.getItem("access_token")
  const isAuthenticated = !!token

  if (to.meta.guestOnly && isAuthenticated) {
    return next({ path: "/" })
  }

  if (to.meta.requiresAuth && !isAuthenticated) {
    return next({ path: "/login" })
  }

  // Verifica permissão por perfil (Role-Based Access Control)
  if (to.meta.allowedRoles && isAuthenticated) {
    const isSuperUser = authStore.user?.is_superuser
    if (isSuperUser) {
      return next()
    }

    const currentRole = authStore.currentRole
    if (!to.meta.allowedRoles.includes(currentRole)) {
      // Se for condômino e tentar rota administrativa, redireciona para seu espaço
      if (currentRole === "CONDOMINO") {
        return next({ path: "/meu-espaco" })
      }
      return next({ path: "/" })
    }
  }

  next()
})

export default router
