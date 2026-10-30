<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="bg-gradient-to-r from-emerald-700 to-teal-800 rounded-2xl p-6 text-white shadow-xl shadow-emerald-950/20">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <span class="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-white/20 text-emerald-100 border border-white/20">
            Portal do Morador
          </span>
          <h2 class="text-2xl font-bold mt-2">
            Meu Espaço • {{ authStore.user?.first_name || authStore.user?.username }}
          </h2>
          <p class="text-emerald-100 text-xs mt-1">
            Consulte seus dados cadastrais, unidades vinculadas e avisos do condomínio
          </p>
        </div>

        <div class="text-right">
          <p class="text-xs text-emerald-200">Unidades Ativas</p>
          <p class="text-3xl font-black">{{ unidades.length }}</p>
        </div>
      </div>
    </div>

    <!-- Dados Civis Cadastrados -->
    <div class="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm">
      <h3 class="text-sm font-bold text-slate-800 uppercase tracking-wider mb-4 flex items-center">
        <span class="mr-2">👤</span> Meus Dados Civis
      </h3>
      <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 text-xs">
        <div class="p-3 bg-slate-50 rounded-xl">
          <span class="text-slate-400 block mb-1">Nome Completo</span>
          <p class="font-semibold text-slate-800">{{ authStore.user?.pessoa_nome || authStore.user?.username }}</p>
        </div>
        <div class="p-3 bg-slate-50 rounded-xl">
          <span class="text-slate-400 block mb-1">Login de Acesso</span>
          <p class="font-semibold text-slate-800 font-mono">{{ authStore.user?.username }}</p>
        </div>
        <div class="p-3 bg-slate-50 rounded-xl">
          <span class="text-slate-400 block mb-1">E-mail</span>
          <p class="font-semibold text-slate-800">{{ authStore.user?.email || 'Não informado' }}</p>
        </div>
        <div class="p-3 bg-slate-50 rounded-xl">
          <span class="text-slate-400 block mb-1">Perfil no Sistema</span>
          <span class="inline-block px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-bold">
            Condômino
          </span>
        </div>
      </div>
    </div>

    <!-- Minhas Unidades -->
    <div class="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm">
      <h3 class="text-sm font-bold text-slate-800 uppercase tracking-wider mb-4 flex items-center">
        <span class="mr-2">🏢</span> Minhas Unidades Vinculadas
      </h3>

      <div v-if="loading" class="text-center py-6 text-slate-400 text-xs">
        Carregando unidades...
      </div>

      <div v-else-if="unidades.length === 0" class="text-center py-8 text-slate-400 text-xs">
        Nenhuma unidade associada ao seu cadastro no momento. Entre em contato com a administração.
      </div>

      <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div
          v-for="u in unidades"
          :key="u.vinculo_id"
          class="p-5 rounded-2xl border border-slate-200 hover:border-emerald-300 transition bg-slate-50/50"
        >
          <div class="flex items-center justify-between">
            <div>
              <span class="text-xs text-slate-400">{{ u.condominio_nome }}</span>
              <h4 class="text-xl font-bold text-slate-900 mt-0.5">
                {{ u.identificador }}
                <span v-if="u.bloco" class="text-sm text-slate-500 font-normal">({{ u.bloco }})</span>
              </h4>
            </div>
            <span
              v-if="u.responsavel"
              class="px-2.5 py-1 bg-amber-100 text-amber-800 font-bold text-xs rounded-full border border-amber-300"
            >
              ★ Responsável Legal
            </span>
          </div>

          <div class="mt-4 pt-4 border-t border-slate-200 flex items-center justify-between text-xs text-slate-600">
            <span>Tipo de Ocupação: <strong class="text-slate-800">{{ u.tipo }}</strong></span>
            <span class="text-emerald-600 font-medium">Vínculo Ativo</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Antecipação Módulo Financeiro -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div class="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm">
        <div class="flex items-center justify-between mb-3">
          <h4 class="font-bold text-slate-800 text-sm">📄 Boletos & Segunda Via</h4>
          <span class="text-[10px] bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full font-bold">Módulo Financeiro</span>
        </div>
        <p class="text-xs text-slate-500 mb-4">
          Nenhum boleto em aberto. Quando a fase de boletos for integrada, seus lançamentos e código de barras PIX aparecerão aqui.
        </p>
        <button disabled class="w-full py-2 bg-slate-100 text-slate-400 font-medium text-xs rounded-xl cursor-not-allowed">
          Nenhum Débito Pendente
        </button>
      </div>

      <div class="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm">
        <div class="flex items-center justify-between mb-3">
          <h4 class="font-bold text-slate-800 text-sm">📊 Prestação de Contas Publicada</h4>
          <span class="text-[10px] bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full font-bold">Transparência</span>
        </div>
        <p class="text-xs text-slate-500 mb-4">
          Acesse os balancetes mensais e demonstrativos aprovados pelo Conselho Consultivo e Fiscal do condomínio.
        </p>
        <button class="w-full py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium text-xs rounded-xl transition">
          Ver Demonstrativos Publicados
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue"
import { useAuthStore } from "@/stores/auth"
import apiClient from "@/api/client"

const authStore = useAuthStore()
const unidades = ref([])
const loading = ref(false)

const fetchMinhasUnidades = async () => {
  loading.value = true
  try {
    const res = await apiClient.get("/auth/me/")
    unidades.value = res.data.unidades_vinculadas || []
  } catch (err) {
    console.error("Erro ao carregar dados do usuário:", err)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchMinhasUnidades()
})
</script>
