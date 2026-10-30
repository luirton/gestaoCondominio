<template>
  <div class="space-y-6">
    <!-- Top Header -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-slate-800 tracking-tight flex items-center gap-2">
          <span class="p-2 bg-blue-100 text-blue-700 rounded-lg">
            <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </span>
          Dashboard de Prestação de Contas
        </h1>
        <p class="text-sm text-slate-500 mt-1">
          Visão executiva de receitas, despesas, conciliação e fechamento mensal.
        </p>
      </div>

      <!-- Ações rápidas -->
      <div class="flex flex-wrap items-center gap-2">
        <router-link
          v-if="periodoAtual"
          :to="`/prestacao/pagamentos/${periodoAtual.periodo_id}`"
          class="inline-flex items-center px-3.5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-sm font-medium transition shadow-sm"
        >
          <svg class="w-4 h-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Lançar Pagamentos
        </router-link>

        <router-link
          v-if="periodoAtual"
          :to="`/prestacao/despesas/${periodoAtual.periodo_id}`"
          class="inline-flex items-center px-3.5 py-2 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-sm font-medium transition shadow-sm"
        >
          <svg class="w-4 h-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
          Lançar Despesas
        </router-link>

        <router-link
          v-if="periodoAtual"
          :to="`/prestacao/relatorio/${periodoAtual.periodo_id}`"
          class="inline-flex items-center px-3.5 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-sm font-medium transition shadow-sm"
        >
          <svg class="w-4 h-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          Ver Prestação
        </router-link>

        <router-link
          to="/prestacao/periodos"
          class="inline-flex items-center px-3 py-2 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-lg text-sm font-medium transition shadow-sm"
        >
          Gerenciar Períodos
        </router-link>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="p-12 text-center text-slate-500">
      <div class="inline-block animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full mb-3"></div>
      <p>Carregando dados financeiros...</p>
    </div>

    <div v-else-if="!periodoAtual" class="bg-amber-50 border border-amber-200 rounded-xl p-8 text-center">
      <h3 class="text-lg font-bold text-amber-800 mb-2">Nenhum período de prestação cadastrado</h3>
      <p class="text-sm text-amber-700 mb-4">Crie o primeiro período para iniciar o lançamento de cotas e despesas.</p>
      <router-link
        to="/prestacao/periodos"
        class="inline-flex items-center px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-lg text-sm font-medium"
      >
        Configurar Período Inicial
      </router-link>
    </div>

    <div v-else class="space-y-6">
      <!-- Status Banner do Período Atual -->
      <div class="bg-white border border-slate-200 rounded-xl p-5 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div class="flex items-center gap-3">
          <div class="w-12 h-12 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center font-bold text-lg">
            {{ periodoAtual.rotulo.split('/')[0].substring(0, 3) }}
          </div>
          <div>
            <div class="flex items-center gap-2">
              <h2 class="text-lg font-bold text-slate-800">Período de Referência: {{ periodoAtual.rotulo }}</h2>
              <span
                class="px-2.5 py-0.5 text-xs font-semibold rounded-full"
                :class="{
                  'bg-emerald-100 text-emerald-800': periodoAtual.status === 'PUBLICADO',
                  'bg-blue-100 text-blue-800': periodoAtual.status === 'FECHADO',
                  'bg-amber-100 text-amber-800': periodoAtual.status === 'ABERTO'
                }"
              >
                {{ periodoAtual.status }}
              </span>
            </div>
            <p class="text-xs text-slate-500 mt-0.5">
              {{ periodoAtual.totais.observacao_diferenca }}
            </p>
          </div>
        </div>

        <div class="flex items-center gap-3 text-xs text-slate-600 bg-slate-50 px-4 py-2.5 rounded-lg border border-slate-200">
          <div>
            <span class="text-slate-400 block">Cotas Pagas</span>
            <strong class="text-emerald-600 text-sm font-bold">{{ periodoAtual.cotas_pagas }}</strong>
          </div>
          <div class="w-px h-6 bg-slate-200"></div>
          <div>
            <span class="text-slate-400 block">Pendentes</span>
            <strong class="text-rose-600 text-sm font-bold">{{ periodoAtual.cotas_pendentes }}</strong>
          </div>
          <div v-if="periodoAtual.cotas_isentas" class="w-px h-6 bg-slate-200"></div>
          <div v-if="periodoAtual.cotas_isentas">
            <span class="text-slate-400 block">Isentas</span>
            <strong class="text-amber-600 text-sm font-bold">{{ periodoAtual.cotas_isentas }}</strong>
          </div>
          <div class="w-px h-6 bg-slate-200"></div>
          <div>
            <span class="text-slate-400 block">Sem Comprovante</span>
            <strong class="text-amber-600 text-sm font-bold">{{ periodoAtual.despesas_sem_comprovante }}</strong>
          </div>
        </div>
      </div>

      <!-- 4 Cards de Métricas Principais -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <!-- Card 1: Receitas -->
        <div class="bg-white border border-slate-200 rounded-xl p-5 shadow-sm relative overflow-hidden">
          <div class="flex items-center justify-between">
            <span class="text-xs font-semibold uppercase tracking-wider text-slate-500">Total Receitas</span>
            <div class="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 11l5-5m0 0l5 5m-5-5v12" />
              </svg>
            </div>
          </div>
          <div class="mt-3">
            <div class="text-2xl font-bold text-slate-800">
              R$ {{ formatMoney(periodoAtual.totais.total_receitas) }}
            </div>
            <p class="text-xs text-slate-500 mt-1">
              R$ {{ formatMoney(periodoAtual.totais.total_cotas_regulares) }} cotas + R$ {{ formatMoney(periodoAtual.totais.total_receitas_extras) }} extras
            </p>
          </div>
          <div class="absolute bottom-0 left-0 right-0 h-1 bg-emerald-500"></div>
        </div>

        <!-- Card 2: Despesas -->
        <div class="bg-white border border-slate-200 rounded-xl p-5 shadow-sm relative overflow-hidden">
          <div class="flex items-center justify-between">
            <span class="text-xs font-semibold uppercase tracking-wider text-slate-500">Total Despesas</span>
            <div class="w-8 h-8 rounded-lg bg-rose-50 text-rose-600 flex items-center justify-center">
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 13l-5 5m0 0l-5-5m5 5V6" />
              </svg>
            </div>
          </div>
          <div class="mt-3">
            <div class="text-2xl font-bold text-slate-800">
              R$ {{ formatMoney(periodoAtual.totais.total_despesas) }}
            </div>
            <p class="text-xs text-slate-500 mt-1">
              Fixas: R$ {{ formatMoney(periodoAtual.totais.total_despesas_fixas) }} | Var: R$ {{ formatMoney(periodoAtual.totais.total_despesas_variaveis) }}
            </p>
          </div>
          <div class="absolute bottom-0 left-0 right-0 h-1 bg-rose-500"></div>
        </div>

        <!-- Card 3: Saldo do Mês -->
        <div class="bg-white border border-slate-200 rounded-xl p-5 shadow-sm relative overflow-hidden">
          <div class="flex items-center justify-between">
            <span class="text-xs font-semibold uppercase tracking-wider text-slate-500">Saldo do Mês</span>
            <div class="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
              </svg>
            </div>
          </div>
          <div class="mt-3">
            <div class="text-2xl font-bold text-blue-700">
              R$ {{ formatMoney(periodoAtual.totais.saldo_mes) }}
            </div>
            <p class="text-xs text-slate-500 mt-1">
              Subtotal: R$ {{ formatMoney(periodoAtual.totais.subtotal) }}
            </p>
          </div>
          <div class="absolute bottom-0 left-0 right-0 h-1 bg-blue-600"></div>
        </div>

        <!-- Card 4: Saldo Bancário Final -->
        <div class="bg-white border border-slate-200 rounded-xl p-5 shadow-sm relative overflow-hidden">
          <div class="flex items-center justify-between">
            <span class="text-xs font-semibold uppercase tracking-wider text-slate-500">Saldo Bancário (Inter CC)</span>
            <div class="w-8 h-8 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center">
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
              </svg>
            </div>
          </div>
          <div class="mt-3">
            <div class="text-2xl font-bold text-slate-800">
              R$ {{ formatMoney(periodoAtual.totais.total_saldo_bancario) }}
            </div>
            <p class="text-xs text-slate-500 mt-1 flex items-center gap-1">
              <span v-if="periodoAtual.totais.diferenca_saldo == 0" class="text-emerald-600 font-semibold flex items-center gap-0.5">
                <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                </svg>
                100% Conciliado
              </span>
              <span v-else class="text-rose-600 font-semibold">
                Diferença: R$ {{ formatMoney(periodoAtual.totais.diferenca_saldo) }}
              </span>
            </p>
          </div>
          <div class="absolute bottom-0 left-0 right-0 h-1 bg-indigo-600"></div>
        </div>
      </div>

      <!-- Gráfico / Comparativo de Períodos e Alertas -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Visualização Histórica -->
        <div class="lg:col-span-2 bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
          <div class="flex items-center justify-between mb-4">
            <h3 class="font-bold text-slate-800 text-base">Evolução: Receitas vs Despesas</h3>
            <span class="text-xs text-slate-500">Últimos períodos registrados</span>
          </div>

          <div v-if="historico.length === 0" class="py-12 text-center text-slate-400 text-sm">
            Histórico insuficiente para gráficos.
          </div>

          <div v-else class="space-y-4 pt-2">
            <div v-for="item in historico" :key="item.periodo_id" class="border-b border-slate-100 pb-3 last:border-0">
              <div class="flex items-center justify-between text-xs font-semibold mb-1">
                <span class="text-slate-700 font-bold">{{ item.rotulo }}</span>
                <span class="text-slate-500">Saldo Mês: <strong class="text-blue-600">R$ {{ formatMoney(item.saldo_mes) }}</strong></span>
              </div>
              <div class="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <div class="flex justify-between text-[11px] text-slate-500 mb-0.5">
                    <span>Receitas</span>
                    <span class="font-medium text-emerald-700">R$ {{ formatMoney(item.receitas) }}</span>
                  </div>
                  <div class="h-2.5 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      class="h-full bg-emerald-500 rounded-full"
                      :style="{ width: calculateBarWidth(item.receitas, maxValor) + '%' }"
                    ></div>
                  </div>
                </div>

                <div>
                  <div class="flex justify-between text-[11px] text-slate-500 mb-0.5">
                    <span>Despesas</span>
                    <span class="font-medium text-rose-700">R$ {{ formatMoney(item.despesas) }}</span>
                  </div>
                  <div class="h-2.5 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      class="h-full bg-rose-500 rounded-full"
                      :style="{ width: calculateBarWidth(item.despesas, maxValor) + '%' }"
                    ></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Card de Alertas & Conciliação -->
        <div class="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4">
          <h3 class="font-bold text-slate-800 text-base">Alertas & Auditoria</h3>

          <div class="space-y-3">
            <!-- Alerta Inadimplência -->
            <div class="p-3.5 rounded-lg border bg-slate-50 flex items-start gap-3" :class="periodoAtual.cotas_pendentes > 0 ? 'border-amber-200 bg-amber-50/50' : 'border-slate-200'">
              <div class="p-1.5 rounded-md" :class="periodoAtual.cotas_pendentes > 0 ? 'bg-amber-100 text-amber-700' : 'bg-emerald-100 text-emerald-700'">
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <div class="text-xs">
                <strong class="block text-slate-800">Cotas em Aberto</strong>
                <p class="text-slate-500 mt-0.5" v-if="periodoAtual.cotas_pendentes > 0">
                  Existem <strong>{{ periodoAtual.cotas_pendentes }} unidades</strong> sem confirmação de pagamento para este mês.
                </p>
                <p class="text-emerald-700 mt-0.5" v-else>
                  Todas as unidades do período encontram-se quitadas!
                </p>
              </div>
            </div>

            <!-- Alerta Comprovantes -->
            <div class="p-3.5 rounded-lg border bg-slate-50 flex items-start gap-3" :class="periodoAtual.despesas_sem_comprovante > 0 ? 'border-amber-200 bg-amber-50/50' : 'border-slate-200'">
              <div class="p-1.5 rounded-md" :class="periodoAtual.despesas_sem_comprovante > 0 ? 'bg-amber-100 text-amber-700' : 'bg-emerald-100 text-emerald-700'">
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                </svg>
              </div>
              <div class="text-xs">
                <strong class="block text-slate-800">Comprovantes de Despesas</strong>
                <p class="text-slate-500 mt-0.5" v-if="periodoAtual.despesas_sem_comprovante > 0">
                  <strong>{{ periodoAtual.despesas_sem_comprovante }} despesas</strong> sem anexo de comprovante ou nota fiscal.
                </p>
                <p class="text-emerald-700 mt-0.5" v-else>
                  100% das despesas possuem comprovantes anexados.
                </p>
              </div>
            </div>

            <!-- Alerta Diferença -->
            <div class="p-3.5 rounded-lg border bg-blue-50/50 border-blue-200 flex items-start gap-3">
              <div class="p-1.5 rounded-md bg-blue-100 text-blue-700">
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div class="text-xs">
                <strong class="block text-slate-800">Regra de Diferença</strong>
                <p class="text-slate-600 mt-0.5 leading-relaxed">
                  {{ periodoAtual.totais.observacao_diferenca }}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from "vue"
import financeiroApi from "@/api/financeiro"

const loading = ref(true)
const periodoAtual = ref(null)
const historico = ref([])

const maxValor = computed(() => {
  if (!historico.value.length) return 1
  let max = 1
  historico.value.forEach(h => {
    if (h.receitas > max) max = h.receitas
    if (h.despesas > max) max = h.despesas
  })
  return max
})

function calculateBarWidth(val, max) {
  if (!max || max === 0) return 0
  return Math.min(Math.round((val / max) * 100), 100)
}

function formatMoney(val) {
  if (val === undefined || val === null) return "0,00"
  return Number(val).toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

async function loadData() {
  loading.value = true
  try {
    const res = await financeiroApi.getDashboard()
    periodoAtual.value = res.data.periodo_atual
    historico.value = res.data.historico_grafico || []
  } catch (err) {
    console.error("Erro ao carregar dashboard financeiro:", err)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadData()
})
</script>
