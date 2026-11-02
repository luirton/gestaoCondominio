<template>
  <div class="flex h-screen bg-slate-50 overflow-hidden">
    <!-- Sidebar -->
    <aside class="w-64 bg-slate-900 text-slate-200 flex flex-col shadow-xl z-20">
      <div class="p-5 border-b border-slate-800 flex items-center justify-between">
        <div class="flex items-center space-x-3">
          <div class="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center font-bold text-white shadow-lg shadow-blue-500/30">
            CG
          </div>
          <div>
            <h1 class="font-bold text-base tracking-tight text-white">CondoGestão</h1>
            <p class="text-xs text-slate-400">Administração v1.0</p>
          </div>
        </div>
      </div>

      <!-- Card Usuário & Condomínio no Menu Lateral -->
      <div class="p-3.5 mx-3 my-2.5 bg-slate-800/90 rounded-2xl border border-slate-700/70 shadow-sm space-y-3">
        <!-- Usuário & Papel -->
        <div class="flex items-center space-x-3">
          <div class="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center font-bold text-white text-base shadow-md shrink-0">
            {{ (authStore.user?.first_name || authStore.user?.username || 'U').charAt(0).toUpperCase() }}
          </div>
          <div class="min-w-0 flex-1">
            <p class="text-xs font-bold text-white truncate">
              {{ authStore.user?.first_name ? `${authStore.user.first_name} ${authStore.user.last_name || ''}` : authStore.user?.username }}
            </p>
            <div class="flex items-center gap-1.5 mt-0.5">
              <span class="inline-block text-[10px] px-2 py-0.5 rounded-full font-semibold" :class="roleBadgeClass">
                {{ roleDisplayName }}
              </span>
            </div>
          </div>
        </div>

        <!-- Condomínio Ativo -->
        <div class="pt-2 border-t border-slate-700/60">
          <label class="block text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1 flex items-center gap-1">
            <span>🏢</span> Condomínio Ativo
          </label>
          <div v-if="meusCondominios.length > 1 || authStore.user?.is_superuser">
            <select
              :value="authStore.activeCondominioId"
              @change="handleCondominioChange($event.target.value)"
              class="w-full text-xs font-semibold bg-slate-950 border border-slate-700 rounded-lg px-2.5 py-1.5 text-white focus:outline-none focus:border-blue-500 shadow-inner"
            >
              <option v-for="c in meusCondominios" :key="c.id" :value="String(c.id)">
                {{ c.nome }}
              </option>
            </select>
          </div>
          <div v-else class="text-xs font-semibold text-slate-200 bg-slate-900/80 px-2.5 py-1.5 rounded-lg border border-slate-700/60 truncate">
            {{ meusCondominios[0]?.nome || 'Condomínio Vinculado' }}
          </div>
        </div>

        <!-- Seletor rápido de Perfil (caso o usuário tenha múltiplos perfis) -->
        <div v-if="authStore.user?.perfis?.length > 1 || authStore.user?.is_superuser" class="pt-2 border-t border-slate-700/60">
          <label class="block text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">Alternar Visão:</label>
          <select 
            :value="authStore.currentRole" 
            @change="handleProfileChange($event.target.value)"
            class="w-full text-xs bg-slate-950 border border-slate-700 rounded-lg px-2 py-1 text-slate-200 focus:outline-none focus:border-blue-500"
          >
            <option value="SINDICO">Síndico (Total)</option>
            <option value="SUBSINDICO">Subsíndico</option>
            <option value="CONSELHEIRO">Conselheiro</option>
            <option value="CONDOMINO">Condômino</option>
            <option value="FUNCIONARIO">Funcionário</option>
          </select>
        </div>
      </div>

      <!-- Navigation Links -->
      <nav class="flex-1 overflow-y-auto px-3 space-y-1 py-2">
        <router-link
          to="/"
          class="flex items-center px-3 py-2.5 rounded-lg text-sm font-medium transition-colors"
          :class="$route.name === 'Dashboard' ? 'bg-blue-600 text-white shadow' : 'text-slate-300 hover:bg-slate-800 hover:text-white'"
        >
          <svg class="w-5 h-5 mr-3 text-slate-400 group-hover:text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>
          </svg>
          Dashboard
        </router-link>

        <div v-if="canViewManagement" class="pt-3 pb-1 px-3 text-xs font-semibold uppercase tracking-wider text-slate-400">
          Prestação de Contas
        </div>

        <router-link
          v-if="canViewManagement"
          to="/prestacao"
          class="flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors"
          :class="$route.path === '/prestacao' ? 'bg-blue-600 text-white shadow' : 'text-slate-300 hover:bg-slate-800 hover:text-white'"
        >
          <svg class="w-5 h-5 mr-3 text-slate-400 group-hover:text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          Dashboard Financeiro
        </router-link>

        <router-link
          v-if="canViewManagement"
          to="/prestacao/periodos"
          class="flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors"
          :class="$route.path.startsWith('/prestacao/periodos') ? 'bg-blue-600 text-white shadow' : 'text-slate-300 hover:bg-slate-800 hover:text-white'"
        >
          <svg class="w-5 h-5 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          Períodos & Parâmetros
        </router-link>

        <router-link
          v-if="canViewManagement"
          to="/prestacao/pagamentos"
          class="flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors"
          :class="$route.path.startsWith('/prestacao/pagamentos') ? 'bg-blue-600 text-white shadow' : 'text-slate-300 hover:bg-slate-800 hover:text-white'"
        >
          <svg class="w-5 h-5 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Lançar Pagamentos
        </router-link>

        <router-link
          v-if="canViewManagement"
          to="/prestacao/despesas"
          class="flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors"
          :class="$route.path.startsWith('/prestacao/despesas') ? 'bg-blue-600 text-white shadow' : 'text-slate-300 hover:bg-slate-800 hover:text-white'"
        >
          <svg class="w-5 h-5 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
          Despesas (Fixas/Var.)
        </router-link>

        <router-link
          v-if="canViewManagement"
          to="/prestacao/relatorio"
          class="flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors"
          :class="$route.path.startsWith('/prestacao/relatorio') ? 'bg-blue-600 text-white shadow' : 'text-slate-300 hover:bg-slate-800 hover:text-white'"
        >
          <svg class="w-5 h-5 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          Prestação de Contas
        </router-link>

        <router-link
          v-if="canViewManagement"
          to="/prestacao/morador"
          class="flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors"
          :class="$route.path.startsWith('/prestacao/morador') ? 'bg-blue-600 text-white shadow' : 'text-slate-300 hover:bg-slate-800 hover:text-white'"
        >
          <svg class="w-5 h-5 mr-3 text-emerald-400 group-hover:text-emerald-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Prestações Publicadas
        </router-link>

        <div v-if="canViewManagement" class="pt-3 pb-1 px-3 text-xs font-semibold uppercase tracking-wider text-slate-400">
          Cadastros & Gestão
        </div>

        <router-link
          v-if="canViewManagement"
          to="/unidades"
          class="flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors"
          :class="$route.path.startsWith('/unidades') ? 'bg-blue-600 text-white shadow' : 'text-slate-300 hover:bg-slate-800 hover:text-white'"
        >
          <svg class="w-5 h-5 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 14v3m4-3v3m4-3v3M3 21h18M3 10h18M3 7l9-4 9 4M4 10h16v11H4V10z"/>
          </svg>
          Unidades
        </router-link>

        <router-link
          v-if="canViewManagement"
          to="/pessoas"
          class="flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors"
          :class="$route.path.startsWith('/pessoas') ? 'bg-blue-600 text-white shadow' : 'text-slate-300 hover:bg-slate-800 hover:text-white'"
        >
          <svg class="w-5 h-5 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/>
          </svg>
          Pessoas
        </router-link>

        <router-link
          v-if="canViewManagement"
          to="/vinculos"
          class="flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors"
          :class="$route.path.startsWith('/vinculos') ? 'bg-blue-600 text-white shadow' : 'text-slate-300 hover:bg-slate-800 hover:text-white'"
        >
          <svg class="w-5 h-5 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"/>
          </svg>
          Vínculos Unidade
        </router-link>

        <router-link
          v-if="canViewManagement"
          to="/funcionarios"
          class="flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors"
          :class="$route.path.startsWith('/funcionarios') ? 'bg-blue-600 text-white shadow' : 'text-slate-300 hover:bg-slate-800 hover:text-white'"
        >
          <svg class="w-5 h-5 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
          </svg>
          Funcionários
        </router-link>

        <router-link
          v-if="canViewManagement"
          to="/cargos"
          class="flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors"
          :class="$route.path.startsWith('/cargos') ? 'bg-blue-600 text-white shadow' : 'text-slate-300 hover:bg-slate-800 hover:text-white'"
        >
          <svg class="w-5 h-5 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
          </svg>
          Mandatos & Cargos
        </router-link>

        <div v-if="canViewUsers" class="pt-3 pb-1 px-3 text-xs font-semibold uppercase tracking-wider text-slate-400">
          Acessos & Segurança
        </div>

        <router-link
          v-if="canViewUsers"
          to="/usuarios"
          class="flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors"
          :class="$route.path.startsWith('/usuarios') ? 'bg-blue-600 text-white shadow' : 'text-slate-300 hover:bg-slate-800 hover:text-white'"
        >
          <svg class="w-5 h-5 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
          </svg>
          Usuários & Perfis
        </router-link>

        <div class="pt-3 pb-1 px-3 text-xs font-semibold uppercase tracking-wider text-slate-400">
          Área do Morador
        </div>

        <router-link
          to="/meu-espaco"
          class="flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors"
          :class="$route.path.startsWith('/meu-espaco') ? 'bg-blue-600 text-white shadow' : 'text-slate-300 hover:bg-slate-800 hover:text-white'"
        >
          <svg class="w-5 h-5 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>
          </svg>
          Meu Espaço (Unidades)
        </router-link>

        <router-link
          to="/prestacao/morador"
          class="flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors"
          :class="$route.path.startsWith('/prestacao/morador') ? 'bg-blue-600 text-white shadow' : 'text-slate-300 hover:bg-slate-800 hover:text-white'"
        >
          <svg class="w-5 h-5 mr-3 text-emerald-400 group-hover:text-emerald-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Prestações Publicadas
        </router-link>

        <router-link
          v-if="!canViewManagement"
          to="/prestacao/relatorio"
          class="flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors"
          :class="$route.path.startsWith('/prestacao/relatorio') ? 'bg-blue-600 text-white shadow' : 'text-slate-300 hover:bg-slate-800 hover:text-white'"
        >
          <svg class="w-5 h-5 mr-3 text-slate-400 group-hover:text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          Relatório de Prestação
        </router-link>
      </nav>

      <!-- Footer logout -->
      <div class="p-4 border-t border-slate-800">
        <button
          @click="handleLogout"
          class="w-full flex items-center justify-center px-4 py-2.5 bg-slate-800 hover:bg-rose-950/40 text-slate-300 hover:text-rose-400 rounded-lg text-sm font-medium border border-slate-700/60 transition-colors"
        >
          <svg class="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>
          </svg>
          Sair do Sistema
        </button>
      </div>
    </aside>

    <!-- Main Content Area -->
    <div class="flex-1 flex flex-col min-w-0 overflow-hidden">
      <!-- Main Body -->
      <main class="flex-1 overflow-y-auto p-6 md:p-8 bg-slate-50">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import { useRouter } from "vue-router"
import { useAuthStore } from "@/stores/auth"
import apiClient from "@/api/client"

const router = useRouter()
const authStore = useAuthStore()
const listaCondominiosGeral = ref([])

const fetchCondos = async () => {
  try {
    const res = await apiClient.get("/condominios/")
    listaCondominiosGeral.value = res.data.results || res.data
    if (!authStore.activeCondominioId && listaCondominiosGeral.value.length > 0) {
      const preferencial = listaCondominiosGeral.value.find(c => c.id === 3) || listaCondominiosGeral.value[0]
      authStore.setActiveCondominio(preferencial.id)
    }
  } catch (err) {
    console.error("Erro ao buscar condomínios:", err)
  }
}

onMounted(() => {
  fetchCondos()
})

const meusCondominios = computed(() => {
  if (authStore.user?.is_superuser) {
    return listaCondominiosGeral.value
  }
  const vinculos = authStore.user?.vinculos_condominios || []
  if (vinculos.length > 0) {
    return vinculos.map((v) => ({
      id: v.condominio_id,
      nome: v.condominio_nome,
    }))
  }
  return listaCondominiosGeral.value
})

const handleCondominioChange = (cid) => {
  authStore.setActiveCondominio(cid)
  window.location.reload()
}

const roleDisplayName = computed(() => {
  const map = {
    SINDICO: "Síndico",
    SUBSINDICO: "Subsíndico",
    CONSELHEIRO: "Conselheiro",
    CONDOMINO: "Condômino",
    FUNCIONARIO: "Funcionário",
  }
  return map[authStore.currentRole] || authStore.currentRole
})

const roleBadgeClass = computed(() => {
  const map = {
    SINDICO: "bg-blue-900/60 text-blue-300 border border-blue-700",
    SUBSINDICO: "bg-indigo-900/60 text-indigo-300 border border-indigo-700",
    CONSELHEIRO: "bg-amber-900/60 text-amber-300 border border-amber-700",
    CONDOMINO: "bg-emerald-900/60 text-emerald-300 border border-emerald-700",
    FUNCIONARIO: "bg-purple-900/60 text-purple-300 border border-purple-700",
  }
  return map[authStore.currentRole] || "bg-slate-700 text-slate-300"
})

const canViewManagement = computed(() => {
  return ["SINDICO", "SUBSINDICO", "CONSELHEIRO"].includes(authStore.currentRole)
})

const canViewUsers = computed(() => {
  return ["SINDICO", "SUBSINDICO"].includes(authStore.currentRole)
})

const handleProfileChange = (role) => {
  authStore.setActiveProfile(role)
  window.location.reload()
}

const handleLogout = () => {
  authStore.logout()
  router.push("/login")
}
</script>
