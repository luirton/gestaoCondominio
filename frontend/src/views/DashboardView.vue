<template>
  <div class="space-y-6">
    <!-- Header Banner -->
    <div class="bg-gradient-to-r from-blue-700 via-blue-600 to-indigo-700 rounded-2xl p-6 text-white shadow-xl shadow-blue-900/10 flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div>
        <h2 class="text-2xl font-bold tracking-tight">
          Olá, {{ authStore.user?.first_name || authStore.user?.username }}!
        </h2>
        <p class="text-blue-100 text-sm mt-1">
          Visão Geral da Gestão • Perfil: 
          <span class="font-semibold underline decoration-blue-300">{{ roleTitle }}</span>
        </p>
      </div>

      <div class="flex items-center gap-2">
        <router-link
          v-if="authStore.canEdit"
          to="/unidades"
          class="px-4 py-2 bg-white/10 hover:bg-white/20 backdrop-blur border border-white/20 text-white rounded-xl text-xs font-semibold transition"
        >
          + Nova Unidade
        </router-link>
        <router-link
          v-if="authStore.canEdit"
          to="/pessoas"
          class="px-4 py-2 bg-white text-blue-700 hover:bg-blue-50 rounded-xl text-xs font-semibold shadow transition"
        >
          + Cadastrar Pessoa
        </router-link>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="py-12 flex justify-center items-center">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="p-4 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 text-sm">
      {{ error }}
    </div>

    <!-- Content for Síndico / Subsíndico / Conselheiro -->
    <div v-else class="space-y-6">
      <!-- KPI Cards Grid -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
        <!-- Card 1: Unidades -->
        <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition">
          <div class="flex items-center justify-between">
            <span class="text-xs font-semibold uppercase tracking-wider text-slate-500">Unidades</span>
            <div class="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center font-bold">
              🚪
            </div>
          </div>
          <div class="mt-3">
            <h3 class="text-3xl font-bold text-slate-800">{{ stats.total_unidades || 0 }}</h3>
            <p class="text-xs text-slate-500 mt-1">Apartamentos / Casas</p>
          </div>
        </div>

        <!-- Card 2: Pessoas e Moradores -->
        <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition">
          <div class="flex items-center justify-between">
            <span class="text-xs font-semibold uppercase tracking-wider text-slate-500">Pessoas / Vínculos</span>
            <div class="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center font-bold">
              👥
            </div>
          </div>
          <div class="mt-3">
            <h3 class="text-3xl font-bold text-slate-800">{{ stats.total_pessoas || 0 }}</h3>
            <p class="text-xs text-emerald-600 font-medium mt-1">{{ stats.vinculos_ativos || 0 }} vínculos ativos</p>
          </div>
        </div>

        <!-- Card 3: Funcionários e Mandatos -->
        <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition">
          <div class="flex items-center justify-between">
            <span class="text-xs font-semibold uppercase tracking-wider text-slate-500">Equipe & Gestão</span>
            <div class="w-10 h-10 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center font-bold">
              👔
            </div>
          </div>
          <div class="mt-3">
            <h3 class="text-3xl font-bold text-slate-800">{{ stats.total_funcionarios_ativos || 0 }}</h3>
            <p class="text-xs text-slate-500 mt-1">{{ stats.mandatos_ativos || 0 }} mandatos vigentes</p>
          </div>
        </div>
      </div>

      <!-- Preparation for Financial Module Callout -->
      <div class="bg-gradient-to-r from-slate-900 to-slate-800 text-white rounded-2xl p-6 border border-slate-700 shadow-sm">
        <div class="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <div class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-500/20 text-blue-300 border border-blue-400/30 mb-2">
              Próxima Fase: Módulo Financeiro
            </div>
            <h4 class="text-lg font-bold">Entidades Prontas para Boletos & Rateios</h4>
            <p class="text-slate-400 text-sm mt-1 max-w-2xl">
              As Unidades já possuem <strong>Fração Ideal</strong> calculada, e cada Unidade possui sua flag de 
              <strong>Responsável Legal/Financeiro</strong> definida nos Vínculos para faturamento de boletos.
            </p>
          </div>

          <router-link
            to="/vinculos"
            class="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-xl transition shadow"
          >
            Verificar Responsáveis de Unidades →
          </router-link>
        </div>
      </div>

      <!-- Quick Shortcuts Grid -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <h4 class="font-bold text-slate-800 text-base mb-2">🏢 Gestão de Unidades</h4>
          <p class="text-xs text-slate-500 mb-4">Cadastre blocos, apartamentos, frações ideais e visualize os moradores ativos.</p>
          <router-link to="/unidades" class="text-blue-600 text-xs font-semibold hover:underline">
            Acessar Unidades & Moradores →
          </router-link>
        </div>

        <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <h4 class="font-bold text-slate-800 text-base mb-2">👥 Base de Pessoas</h4>
          <p class="text-xs text-slate-500 mb-4">Cadastro civil de proprietários, inquilinos e dependentes (com ou sem usuário).</p>
          <router-link to="/pessoas" class="text-blue-600 text-xs font-semibold hover:underline">
            Acessar Cadastro de Pessoas →
          </router-link>
        </div>

        <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <h4 class="font-bold text-slate-800 text-base mb-2">🛡️ Governança & Mandatos</h4>
          <p class="text-xs text-slate-500 mb-4">Registro do corpo diretivo: Síndicos, Subsíndicos e Conselheiros por mandato.</p>
          <router-link to="/cargos" class="text-blue-600 text-xs font-semibold hover:underline">
            Acessar Mandatos Condominiais →
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import { useAuthStore } from "@/stores/auth"
import apiClient from "@/api/client"

const authStore = useAuthStore()
const loading = ref(true)
const error = ref(null)
const stats = ref({})

const roleTitle = computed(() => {
  const map = {
    SINDICO: "Síndico (Acesso Total)",
    SUBSINDICO: "Subsíndico (Operacional)",
    CONSELHEIRO: "Conselheiro Fiscal/Consultivo (Auditoria)",
    CONDOMINO: "Condômino",
    FUNCIONARIO: "Funcionário / Operacional",
  }
  return map[authStore.currentRole] || authStore.currentRole
})

const fetchStats = async () => {
  loading.value = true
  error.value = null
  try {
    const res = await apiClient.get("/dashboard/stats/")
    stats.value = res.data
  } catch (err) {
    error.value = "Não foi possível carregar os dados estatísticos do condomínio."
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchStats()
})
</script>
