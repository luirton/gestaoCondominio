<template>
  <div class="space-y-6">
    <!-- Header Banner -->
    <div class="bg-gradient-to-r from-blue-700 via-blue-600 to-indigo-700 rounded-2xl p-6 text-white shadow-xl shadow-blue-900/10 flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div>
        <div class="flex items-center gap-2 mb-1">
          <span class="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-white/20 text-blue-100 border border-white/20">
            {{ stats.condominio_atual?.nome || 'Condomínio Vinculado' }}
          </span>
        </div>
        <h2 class="text-2xl font-bold tracking-tight">
          Olá, {{ authStore.user?.first_name || authStore.user?.username }}!
        </h2>
        <p class="text-blue-100 text-sm mt-1">
          Visão Geral da Gestão • Perfil Ativo:
          <span class="font-semibold underline decoration-blue-300">{{ roleTitle }}</span>
        </p>
      </div>

      <div v-if="authStore.isSindico || authStore.isSubSindico" class="flex flex-wrap items-center gap-2">
        <router-link
          to="/prestacao/periodos"
          class="px-4 py-2 bg-white/10 hover:bg-white/20 backdrop-blur border border-white/20 text-white rounded-xl text-xs font-semibold transition"
        >
          ⚙️ Períodos de Prestação
        </router-link>
        <router-link
          to="/cargos"
          class="px-4 py-2 bg-white text-blue-700 hover:bg-blue-50 rounded-xl text-xs font-semibold shadow transition"
        >
          👔 Mandatos & Cargos
        </router-link>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="py-12 flex flex-col justify-center items-center text-slate-500">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-3"></div>
      <p class="text-sm">Carregando painel e última prestação de contas...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="p-4 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 text-sm">
      {{ error }}
    </div>

    <div v-else class="space-y-6">
      <!-- BLOCO 1: Informações da Última Prestação de Contas -->
      <div v-if="stats.ultima_prestacao" class="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-5">
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-100 pb-4">
          <div class="flex items-center gap-3">
            <div class="w-12 h-12 rounded-xl bg-blue-100 text-blue-700 flex items-center justify-center font-black text-lg shadow-sm">
              📊
            </div>
            <div>
              <div class="flex items-center gap-2">
                <h3 class="text-lg font-bold text-slate-900">
                  Última Prestação de Contas • {{ stats.ultima_prestacao.mes_referencia_rotulo }}
                </h3>
                <span
                  class="px-2.5 py-0.5 text-xs font-bold rounded-full"
                  :class="{
                    'bg-emerald-100 text-emerald-800 border border-emerald-300': stats.ultima_prestacao.status === 'PUBLICADO',
                    'bg-blue-100 text-blue-800 border border-blue-300': stats.ultima_prestacao.status === 'FECHADO',
                    'bg-amber-100 text-amber-800 border border-amber-300': stats.ultima_prestacao.status === 'ABERTO'
                  }"
                >
                  {{ stats.ultima_prestacao.status }}
                </span>
              </div>
              <p class="text-xs text-slate-500 mt-0.5">
                Vigência: {{ formatDate(stats.ultima_prestacao.data_inicio_prestacao) }} a {{ formatDate(stats.ultima_prestacao.data_fim_prestacao) }} •
                Vencimento Cota: {{ formatDate(stats.ultima_prestacao.data_vencimento) }} (R$ {{ formatMoney(stats.ultima_prestacao.valor_cota_total || stats.ultima_prestacao.valor_cota_padrao) }})
                <span v-if="stats.ultima_prestacao.cota_extra" class="text-indigo-600 font-semibold">
                  (Inclui Cota Extra: R$ {{ formatMoney(stats.ultima_prestacao.cota_extra) }})
                </span>
              </p>
            </div>
          </div>

          <div class="flex items-center gap-2">
            <router-link
              :to="`/prestacao/relatorio/${stats.ultima_prestacao.id}`"
              class="inline-flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-semibold shadow-sm transition"
            >
              Ver Prestação Completa →
            </router-link>
            <router-link
              v-if="authStore.isSindico || authStore.isSubSindico"
              :to="`/prestacao/pagamentos/${stats.ultima_prestacao.id}`"
              class="inline-flex items-center px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition"
            >
              Pagamentos
            </router-link>
            <router-link
              v-if="authStore.isSindico || authStore.isSubSindico"
              :to="`/prestacao/despesas/${stats.ultima_prestacao.id}`"
              class="inline-flex items-center px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition"
            >
              Despesas
            </router-link>
          </div>
        </div>

        <!-- Cards Financeiros da Última Prestação -->
        <div
          class="grid grid-cols-1 sm:grid-cols-2 gap-4"
          :class="(authStore.isSindico || authStore.isSubSindico) ? 'lg:grid-cols-4' : 'lg:grid-cols-3'"
        >
          <!-- Receitas -->
          <div class="bg-slate-50/70 border border-slate-200/80 rounded-xl p-4">
            <span class="text-[11px] font-bold uppercase tracking-wider text-slate-500 block">Total Receitas</span>
            <div class="text-2xl font-extrabold text-emerald-700 mt-1">
              R$ {{ formatMoney(stats.ultima_prestacao.totais?.total_receitas) }}
            </div>
            <p class="text-[11px] text-slate-500 mt-1">
              Cotas: R$ {{ formatMoney(stats.ultima_prestacao.totais?.total_cotas_regulares) }} | Extras: R$ {{ formatMoney(stats.ultima_prestacao.totais?.total_receitas_extras) }}
            </p>
          </div>

          <!-- Despesas -->
          <div class="bg-slate-50/70 border border-slate-200/80 rounded-xl p-4">
            <span class="text-[11px] font-bold uppercase tracking-wider text-slate-500 block">Total Despesas</span>
            <div class="text-2xl font-extrabold text-rose-700 mt-1">
              R$ {{ formatMoney(stats.ultima_prestacao.totais?.total_despesas) }}
            </div>
            <p class="text-[11px] text-slate-500 mt-1">
              Fixas: R$ {{ formatMoney(stats.ultima_prestacao.totais?.total_despesas_fixas) }} | Var: R$ {{ formatMoney(stats.ultima_prestacao.totais?.total_despesas_variaveis) }}
            </p>
          </div>

          <!-- Saldo Mês -->
          <div class="bg-slate-50/70 border border-slate-200/80 rounded-xl p-4">
            <span class="text-[11px] font-bold uppercase tracking-wider text-slate-500 block">Saldo do Mês</span>
            <div class="text-2xl font-extrabold text-blue-700 mt-1">
              R$ {{ formatMoney(stats.ultima_prestacao.totais?.saldo_mes) }}
            </div>
            <p class="text-[11px] text-slate-500 mt-1">
              Resultado operacional do período
            </p>
          </div>

          <!-- Conciliação e Status Cotas (Síndico e Subsíndico) -->
          <div v-if="authStore.isSindico || authStore.isSubSindico" class="bg-slate-50/70 border border-slate-200/80 rounded-xl p-4">
            <span class="text-[11px] font-bold uppercase tracking-wider text-slate-500 block">Cotas Pagas</span>
            <div class="text-2xl font-extrabold text-slate-800 mt-1 flex items-baseline gap-1">
              <span class="text-emerald-700">{{ stats.ultima_prestacao.cotas_pagas }}</span>
              <span class="text-xs text-slate-400 font-normal">/ {{ stats.ultima_prestacao.cotas_total }}</span>
            </div>
            <p class="text-[11px] text-slate-500 mt-1">
              <span class="text-rose-600 font-semibold">{{ stats.ultima_prestacao.cotas_pendentes }} pendentes</span>
              <span v-if="stats.ultima_prestacao.cotas_isentas" class="text-amber-700 ml-1">
                ({{ stats.ultima_prestacao.cotas_isentas }} isentas)
              </span>
            </p>
          </div>
        </div>

        <!-- Observação de Diferença / Conciliação -->
        <div v-if="stats.ultima_prestacao.totais?.observacao_diferenca" class="p-3 bg-blue-50/60 border border-blue-200 rounded-xl text-xs text-blue-900 flex items-start gap-2">
          <svg class="w-4 h-4 text-blue-600 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>{{ stats.ultima_prestacao.totais.observacao_diferenca }}</span>
        </div>
      </div>

      <div v-else class="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm text-center py-8">
        <p class="text-slate-500 text-sm">Nenhuma prestação de contas cadastrada ou publicada para este condomínio.</p>
      </div>

      <!-- BLOCO 2: Equipe & Gestão (Síndico, Subsíndico, Conselheiros e Funcionários com Contatos) -->
      <div class="space-y-4">
        <div class="flex items-center justify-between">
          <div>
            <h3 class="text-lg font-bold text-slate-900 flex items-center gap-2">
              <span>👔</span> Equipe & Gestão do Condomínio
            </h3>
            <p class="text-xs text-slate-500 mt-0.5">
              Corpo diretivo ativo, canais diretos de contato do síndico, subsíndico e equipe operacional.
            </p>
          </div>

          <router-link
            v-if="authStore.isSindico || authStore.isSubSindico"
            to="/cargos"
            class="text-xs font-semibold text-blue-600 hover:text-blue-800 hover:underline"
          >
            Gerenciar Mandatos →
          </router-link>
        </div>

        <!-- Grid: Síndico e Subsíndico em Destaque com Contatos -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
          <!-- Card Síndico(a) -->
          <div
            v-for="sind in (stats.equipe_gestao?.sindicos || [])"
            :key="sind.id"
            class="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm hover:shadow-md transition relative overflow-hidden"
          >
            <div class="flex items-start justify-between gap-3">
              <div class="flex items-start gap-3.5">
                <div class="w-12 h-12 rounded-xl bg-blue-100 text-blue-700 flex items-center justify-center font-bold text-xl shadow-inner shrink-0">
                  👔
                </div>
                <div>
                  <div class="flex items-center gap-2">
                    <span class="px-2 py-0.5 bg-blue-100 text-blue-800 text-[10px] font-extrabold uppercase rounded-full">
                      Síndico(a) Geral
                    </span>
                    <span v-if="sind.unidade" class="text-xs text-slate-500 font-medium">
                      Unidade: <strong class="text-slate-800">{{ sind.unidade }}</strong>
                    </span>
                  </div>
                  <h4 class="text-base font-bold text-slate-900 mt-1">
                    {{ sind.nome }}
                  </h4>
                  <p class="text-xs text-slate-500 mt-0.5">
                    Mandato: {{ formatDate(sind.data_inicio) }} {{ sind.data_fim ? `até ${formatDate(sind.data_fim)}` : '(Vigente)' }}
                  </p>
                </div>
              </div>
            </div>

            <!-- Canais de Contato Destacados -->
            <div class="mt-4 pt-4 border-t border-slate-100 grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
              <div class="p-2.5 bg-slate-50 rounded-xl flex items-center gap-2.5">
                <span class="text-base">📞</span>
                <div class="min-w-0">
                  <span class="text-[10px] font-bold uppercase text-slate-400 block">Telefone / WhatsApp</span>
                  <a
                    v-if="sind.telefone"
                    :href="`tel:${sind.telefone.replace(/\D/g, '')}`"
                    class="font-bold text-blue-700 hover:underline truncate block"
                  >
                    {{ sind.telefone }}
                  </a>
                  <span v-else class="text-slate-400 italic">Não informado</span>
                </div>
              </div>

              <div class="p-2.5 bg-slate-50 rounded-xl flex items-center gap-2.5">
                <span class="text-base">✉️</span>
                <div class="min-w-0">
                  <span class="text-[10px] font-bold uppercase text-slate-400 block">E-mail</span>
                  <a
                    v-if="sind.email"
                    :href="`mailto:${sind.email}`"
                    class="font-bold text-blue-700 hover:underline truncate block"
                  >
                    {{ sind.email }}
                  </a>
                  <span v-else class="text-slate-400 italic">Não informado</span>
                </div>
              </div>
            </div>

            <div class="absolute top-0 right-0 w-24 h-24 bg-blue-500/5 rounded-bl-full pointer-events-none"></div>
          </div>

          <!-- Card Subsíndico(a) -->
          <div
            v-for="sub in (stats.equipe_gestao?.subsindicos || [])"
            :key="sub.id"
            class="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm hover:shadow-md transition relative overflow-hidden"
          >
            <div class="flex items-start justify-between gap-3">
              <div class="flex items-start gap-3.5">
                <div class="w-12 h-12 rounded-xl bg-indigo-100 text-indigo-700 flex items-center justify-center font-bold text-xl shadow-inner shrink-0">
                  🛡️
                </div>
                <div>
                  <div class="flex items-center gap-2">
                    <span class="px-2 py-0.5 bg-indigo-100 text-indigo-800 text-[10px] font-extrabold uppercase rounded-full">
                      Subsíndico(a)
                    </span>
                    <span v-if="sub.unidade" class="text-xs text-slate-500 font-medium">
                      Unidade: <strong class="text-slate-800">{{ sub.unidade }}</strong>
                    </span>
                  </div>
                  <h4 class="text-base font-bold text-slate-900 mt-1">
                    {{ sub.nome }}
                  </h4>
                  <p class="text-xs text-slate-500 mt-0.5">
                    Mandato: {{ formatDate(sub.data_inicio) }} {{ sub.data_fim ? `até ${formatDate(sub.data_fim)}` : '(Vigente)' }}
                  </p>
                </div>
              </div>
            </div>

            <!-- Canais de Contato Destacados -->
            <div class="mt-4 pt-4 border-t border-slate-100 grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
              <div class="p-2.5 bg-slate-50 rounded-xl flex items-center gap-2.5">
                <span class="text-base">📞</span>
                <div class="min-w-0">
                  <span class="text-[10px] font-bold uppercase text-slate-400 block">Telefone / WhatsApp</span>
                  <a
                    v-if="sub.telefone"
                    :href="`tel:${sub.telefone.replace(/\D/g, '')}`"
                    class="font-bold text-indigo-700 hover:underline truncate block"
                  >
                    {{ sub.telefone }}
                  </a>
                  <span v-else class="text-slate-400 italic">Não informado</span>
                </div>
              </div>

              <div class="p-2.5 bg-slate-50 rounded-xl flex items-center gap-2.5">
                <span class="text-base">✉️</span>
                <div class="min-w-0">
                  <span class="text-[10px] font-bold uppercase text-slate-400 block">E-mail</span>
                  <a
                    v-if="sub.email"
                    :href="`mailto:${sub.email}`"
                    class="font-bold text-indigo-700 hover:underline truncate block"
                  >
                    {{ sub.email }}
                  </a>
                  <span v-else class="text-slate-400 italic">Não informado</span>
                </div>
              </div>
            </div>

            <div class="absolute top-0 right-0 w-24 h-24 bg-indigo-500/5 rounded-bl-full pointer-events-none"></div>
          </div>

          <!-- Caso não haja Síndico ou Sub cadastrado -->
          <div
            v-if="(!stats.equipe_gestao?.sindicos || stats.equipe_gestao.sindicos.length === 0) && (!stats.equipe_gestao?.subsindicos || stats.equipe_gestao.subsindicos.length === 0)"
            class="col-span-full p-6 bg-slate-50 rounded-2xl border border-slate-200 text-center text-slate-500 text-sm"
          >
            Nenhum mandato de Síndico ou Subsíndico ativo cadastrado no momento.
            <router-link to="/cargos" class="text-blue-600 font-semibold hover:underline block mt-1">
              Cadastrar mandato agora →
            </router-link>
          </div>
        </div>

        <!-- Conselheiros e Funcionários -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
          <!-- Conselheiros -->
          <div class="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-3">
            <div class="flex items-center justify-between border-b pb-2">
              <h4 class="font-bold text-slate-800 text-sm flex items-center gap-2">
                <span>⚖️</span> Conselho Fiscal & Consultivo
              </h4>
              <span class="text-[11px] font-semibold text-slate-500">
                {{ stats.equipe_gestao?.conselheiros?.length || 0 }} membros
              </span>
            </div>

            <div v-if="!stats.equipe_gestao?.conselheiros || stats.equipe_gestao.conselheiros.length === 0" class="py-4 text-center text-slate-400 text-xs">
              Nenhum conselheiro ativo registrado.
            </div>

            <div v-else class="space-y-2">
              <div
                v-for="cons in stats.equipe_gestao.conselheiros"
                :key="cons.id"
                class="p-2.5 bg-slate-50 rounded-xl flex items-center justify-between text-xs"
              >
                <div>
                  <span class="font-bold text-slate-800 block">{{ cons.nome }}</span>
                  <span class="text-[11px] text-slate-500">{{ cons.cargo_display }}</span>
                </div>
                <div class="text-right text-[11px] text-slate-600">
                  <span v-if="cons.telefone" class="block font-medium">{{ cons.telefone }}</span>
                  <span v-if="cons.unidade" class="text-slate-400 block">{{ cons.unidade }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Quadro de Funcionários -->
          <div class="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-3">
            <div class="flex items-center justify-between border-b pb-2">
              <h4 class="font-bold text-slate-800 text-sm flex items-center gap-2">
                <span>👷</span> Funcionários & Equipe Operacional
              </h4>
              <router-link
                v-if="authStore.isSindico || authStore.isSubSindico"
                to="/funcionarios"
                class="text-[11px] font-semibold text-blue-600 hover:underline"
              >
                {{ stats.equipe_gestao?.funcionarios?.length || 0 }} ativos →
              </router-link>
              <span v-else class="text-[11px] font-medium text-slate-400">
                {{ stats.equipe_gestao?.funcionarios?.length || 0 }} ativos
              </span>
            </div>

            <div v-if="!stats.equipe_gestao?.funcionarios || stats.equipe_gestao.funcionarios.length === 0" class="py-4 text-center text-slate-400 text-xs">
              Nenhum funcionário ativo cadastrado no momento.
            </div>

            <div v-else class="space-y-2">
              <div
                v-for="func in stats.equipe_gestao.funcionarios"
                :key="func.id"
                class="p-2.5 bg-slate-50 rounded-xl flex items-center justify-between text-xs"
              >
                <div>
                  <span class="font-bold text-slate-800 block">{{ func.nome }}</span>
                  <span class="text-[11px] text-amber-700 font-semibold">{{ func.cargo_display }}</span>
                </div>
                <div class="text-right text-[11px] text-slate-500">
                  <span class="block">Admissão: {{ formatDate(func.data_admissao) }}</span>
                  <span v-if="func.telefone" class="text-slate-700 font-medium">{{ func.telefone }}</span>
                </div>
              </div>
            </div>
          </div>
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

function formatDate(val) {
  if (!val) return "-"
  const d = new Date(val + "T00:00:00")
  return d.toLocaleDateString("pt-BR")
}

function formatMoney(val) {
  if (val === undefined || val === null || val === "") return "0,00"
  return Number(val).toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const fetchStats = async () => {
  loading.value = true
  error.value = null
  try {
    const res = await apiClient.get("/dashboard/stats/")
    stats.value = res.data
  } catch (err) {
    error.value = "Não foi possível carregar as informações do condomínio."
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchStats()
})
</script>
