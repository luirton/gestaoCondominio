<template>
  <div class="space-y-6">
    <!-- Header com Seletor de Período -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-slate-800 tracking-tight flex items-center gap-2">
          <span class="p-2 bg-emerald-100 text-emerald-700 rounded-lg">
            <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
          </span>
          Lançamento de Pagamentos & Receitas
        </h1>
        <p class="text-sm text-slate-500 mt-1">
          Substitui a aba PAGAMENTOS da planilha. Baixa de cotas, cálculo de juros/multas e receitas extras.
        </p>
      </div>

      <!-- Seletor de Período -->
      <div class="flex items-center gap-3">
        <label class="text-xs font-semibold text-slate-500 uppercase">Período:</label>
        <select
          v-model="selectedPeriodoId"
          @change="changePeriodo"
          class="bg-white border border-slate-300 rounded-lg px-3 py-2 text-sm font-semibold text-slate-800 shadow-sm focus:ring-1 focus:ring-blue-500"
        >
          <option v-for="p in periodos" :key="p.id" :value="p.id">
            {{ p.mes_referencia_rotulo }} ({{ p.status }})
          </option>
        </select>
      </div>
    </div>

    <!-- Banner Informativo / Período Bloqueado -->
    <div
      v-if="currentPeriodo && currentPeriodo.status !== 'ABERTO'"
      class="bg-blue-50 border border-blue-200 text-blue-800 p-4 rounded-xl text-xs flex items-center justify-between"
    >
      <div class="flex items-center gap-2">
        <svg class="w-5 h-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
        </svg>
        <span>
          Este período está com status <strong>{{ currentPeriodo.status }}</strong>. Os valores estão congelados para garantir a rastreabilidade histórica.
        </span>
      </div>
      <router-link
        :to="`/prestacao/relatorio/${currentPeriodo.id}`"
        class="px-3 py-1 bg-blue-600 text-white rounded text-xs font-medium hover:bg-blue-700"
      >
        Ver Prestação Fechada
      </router-link>
    </div>

    <!-- Navegação em Abas (Cotas das 52 Unidades / Receitas Extras) -->
    <div class="flex border-b border-slate-200">
      <button
        @click="activeTab = 'cotas'"
        class="py-3 px-6 text-sm font-bold border-b-2 transition flex items-center gap-2"
        :class="activeTab === 'cotas' ? 'border-emerald-600 text-emerald-700' : 'border-transparent text-slate-500 hover:text-slate-700'"
      >
        <span>Cotas do Mês ({{ cotas.length }} Unidades)</span>
        <span class="text-xs px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 font-normal">
          {{ cotasPagasCount }} pagas
        </span>
      </button>

      <button
        @click="activeTab = 'extras'"
        class="py-3 px-6 text-sm font-bold border-b-2 transition flex items-center gap-2"
        :class="activeTab === 'extras' ? 'border-emerald-600 text-emerald-700' : 'border-transparent text-slate-500 hover:text-slate-700'"
      >
        <span>Receitas Extras & Atrasos ({{ receitasExtras.length }})</span>
        <span class="text-xs px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 font-semibold">
          R$ {{ formatMoney(totalExtrasCalculado) }}
        </span>
      </button>
    </div>

    <!-- ================= ABA 1: COTAS REGULARES ================= -->
    <div v-if="activeTab === 'cotas'" class="space-y-4">
      <!-- Barra de Ferramentas / Marcação em Massa e Filtros -->
      <div class="bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-3">
        <!-- Filtros -->
        <div class="flex flex-wrap items-center gap-2">
          <input
            type="text"
            v-model="searchQuery"
            placeholder="Buscar unidade..."
            class="text-xs border rounded-lg px-3 py-1.5 w-44 focus:ring-1 focus:ring-blue-500"
          />

          <select
            v-model="filterStatus"
            class="text-xs border rounded-lg px-3 py-1.5 focus:ring-1 focus:ring-blue-500"
          >
            <option value="ALL">Todas as Cotas</option>
            <option value="PAGO">Somente Pagas</option>
            <option value="PENDENTE">Somente Pendentes</option>
          </select>
        </div>

        <!-- Ação em massa -->
        <div v-if="currentPeriodo?.status === 'ABERTO'" class="flex items-center gap-2">
          <span class="text-xs text-slate-500 font-medium">
            Selecionadas: <strong>{{ selectedCotaIds.length }}</strong>
          </span>
          <input
            type="date"
            v-model="batchDataPagamento"
            class="text-xs border rounded-lg px-2 py-1"
          />
          <button
            @click="marcarEmMassa"
            :disabled="selectedCotaIds.length === 0 || isUpdating"
            class="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-medium transition disabled:opacity-50"
          >
            Baixar Selecionadas
          </button>
        </div>
      </div>

      <!-- Tabela Editável das 52 Casas -->
      <div class="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
        <div class="overflow-x-auto max-h-[600px] overflow-y-auto">
          <table class="w-full text-left border-collapse text-xs">
            <thead class="sticky top-0 bg-slate-900 text-white z-10">
              <tr>
                <th class="py-2.5 px-3 w-10 text-center">
                  <input
                    type="checkbox"
                    :checked="allFilteredSelected"
                    @change="toggleSelectAll"
                    class="rounded text-blue-600 focus:ring-0"
                  />
                </th>
                <th class="py-2.5 px-3 w-12 text-center">Nº</th>
                <th class="py-2.5 px-3">Unidade</th>
                <th class="py-2.5 px-3">Mês Ref.</th>
                <th class="py-2.5 px-3">Vencimento</th>
                <th class="py-2.5 px-3">Valor Título</th>
                <th class="py-2.5 px-3">Data Pagto</th>
                <th class="py-2.5 px-3">Cota (R$)</th>
                <th class="py-2.5 px-3">Valor Pago (R$)</th>
                <th class="py-2.5 px-3">Juros/Multa (R$)</th>
                <th class="py-2.5 px-3">Observação</th>
                <th class="py-2.5 px-3 text-right">Ação</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-200">
              <tr
                v-for="cota in filteredCotas"
                :key="cota.id"
                class="hover:bg-slate-50 transition-colors"
                :class="cota.data_pagamento ? 'bg-emerald-50/20' : 'bg-white'"
              >
                <!-- Checkbox -->
                <td class="py-2 px-3 text-center">
                  <input
                    type="checkbox"
                    :value="cota.id"
                    v-model="selectedCotaIds"
                    class="rounded text-blue-600 focus:ring-0"
                  />
                </td>

                <!-- Nº -->
                <td class="py-2 px-3 text-center font-bold text-slate-700">
                  {{ cota.numero_ordem }}
                </td>

                <!-- Identificador Unidade -->
                <td class="py-2 px-3 font-semibold text-slate-800 whitespace-nowrap">
                  {{ cota.unidade_identificador }}
                </td>

                <!-- Mês Ref -->
                <td class="py-2 px-3 text-slate-500 whitespace-nowrap">
                  {{ formatDate(cota.mes_referencia) }}
                </td>

                <!-- Vencimento -->
                <td class="py-2 px-3 text-slate-500 whitespace-nowrap">
                  {{ formatDate(cota.data_vencimento) }}
                </td>

                <!-- Valor Título -->
                <td class="py-2 px-3 text-slate-700 font-medium whitespace-nowrap">
                  R$ {{ formatMoney(cota.valor_titulo) }}
                </td>

                <!-- Data Pagamento (Editável) -->
                <td class="py-2 px-2">
                  <input
                    type="date"
                    v-model="cota.data_pagamento"
                    @change="onDataPagamentoChange(cota)"
                    :disabled="currentPeriodo?.status !== 'ABERTO'"
                    class="border rounded px-2 py-1 text-xs w-32 focus:ring-1 focus:ring-blue-500 disabled:bg-slate-100"
                  />
                </td>

                <!-- Cota Regular Base (Editável) -->
                <td class="py-2 px-2">
                  <input
                    type="number"
                    step="0.01"
                    v-model="cota.cota"
                    @change="recalculateRow(cota)"
                    :disabled="currentPeriodo?.status !== 'ABERTO'"
                    placeholder="0.00"
                    class="border rounded px-2 py-1 text-xs w-24 focus:ring-1 focus:ring-blue-500 disabled:bg-slate-100"
                  />
                </td>

                <!-- Valor Pago Efetivo (Editável) -->
                <td class="py-2 px-2">
                  <input
                    type="number"
                    step="0.01"
                    v-model="cota.valor_pago"
                    @change="recalculateRow(cota)"
                    :disabled="currentPeriodo?.status !== 'ABERTO'"
                    placeholder="0.00"
                    class="border rounded px-2 py-1 text-xs w-24 font-bold text-slate-800 focus:ring-1 focus:ring-blue-500 disabled:bg-slate-100"
                  />
                </td>

                <!-- Juros / Multa -->
                <td class="py-2 px-3 whitespace-nowrap">
                  <span
                    class="font-semibold"
                    :class="cota.juros_multa > 0 ? 'text-rose-600' : 'text-slate-400'"
                  >
                    R$ {{ formatMoney(cota.juros_multa) }}
                  </span>
                </td>

                <!-- Observação (Editável) -->
                <td class="py-2 px-2">
                  <input
                    type="text"
                    v-model="cota.observacao"
                    @change="saveCota(cota)"
                    :disabled="currentPeriodo?.status !== 'ABERTO'"
                    placeholder="Obs..."
                    class="border rounded px-2 py-1 text-xs w-full min-w-[150px] focus:ring-1 focus:ring-blue-500 disabled:bg-slate-100"
                  />
                </td>

                <!-- Ação Salvar/Limpar -->
                <td class="py-2 px-3 text-right whitespace-nowrap">
                  <button
                    v-if="cota.data_pagamento && currentPeriodo?.status === 'ABERTO'"
                    @click="limparPagamento(cota)"
                    class="text-xs text-rose-500 hover:text-rose-700 font-medium"
                    title="Desfazer pagamento"
                  >
                    Desfazer
                  </button>
                  <span v-else-if="cota.data_pagamento" class="text-emerald-600 font-bold">
                    ✓ Pago
                  </span>
                  <span v-else class="text-slate-400">
                    Pendente
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Rodapé com Totalizadores da Planilha -->
        <div class="bg-slate-900 text-white p-4 flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs">
          <div class="flex items-center gap-6">
            <div>
              <span class="text-slate-400 block">Total Cotas Regulares:</span>
              <strong class="text-base text-emerald-400 font-bold">
                R$ {{ formatMoney(totalCotasCalculado) }}
              </strong>
            </div>
            <div>
              <span class="text-slate-400 block">Outras Receitas (Extras):</span>
              <strong class="text-base text-amber-300 font-bold">
                R$ {{ formatMoney(totalExtrasCalculado) }}
              </strong>
            </div>
            <div>
              <span class="text-slate-400 block">Total Geral das Receitas:</span>
              <strong class="text-base text-white font-bold">
                R$ {{ formatMoney(totalGeralReceitas) }}
              </strong>
            </div>
          </div>

          <div class="text-slate-400">
            {{ cotasPagasCount }} de {{ cotas.length }} cotas quitadas no período
          </div>
        </div>
      </div>
    </div>

    <!-- ================= ABA 2: RECEITAS EXTRAS ================= -->
    <div v-if="activeTab === 'extras'" class="space-y-4">
      <div class="bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex items-center justify-between">
        <div>
          <h3 class="font-bold text-slate-800 text-sm">Lançamento de Receitas Extras & Atrasos</h3>
          <p class="text-xs text-slate-500">
            Aluguel de vagas (R$ 100,00), rendimento CDB e juros de cotas anteriores recebidas em atraso.
          </p>
        </div>

        <button
          v-if="currentPeriodo?.status === 'ABERTO'"
          @click="openExtraModal()"
          class="px-3.5 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-medium transition"
        >
          + Adicionar Receita Extra
        </button>
      </div>

      <!-- Tabela de Extras -->
      <div class="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
        <table class="w-full text-left border-collapse text-xs">
          <thead class="bg-slate-50 border-b border-slate-200 uppercase tracking-wider text-slate-500 font-semibold">
            <tr>
              <th class="py-3 px-4">Descrição da Entrada</th>
              <th class="py-3 px-4">Tipo</th>
              <th class="py-3 px-4">Unidade Relacionada</th>
              <th class="py-3 px-4">Data</th>
              <th class="py-3 px-4">Valor (R$)</th>
              <th class="py-3 px-4 text-right" v-if="currentPeriodo?.status === 'ABERTO'">Ações</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-200">
            <tr v-for="extra in receitasExtras" :key="extra.id" class="hover:bg-slate-50">
              <td class="py-3 px-4 font-bold text-slate-800">
                {{ extra.descricao }}
              </td>
              <td class="py-3 px-4 text-slate-600">
                {{ extra.tipo_display || extra.tipo }}
              </td>
              <td class="py-3 px-4 text-slate-700">
                {{ extra.unidade_identificador || '-' }}
              </td>
              <td class="py-3 px-4 text-slate-500">
                {{ formatDate(extra.data) }}
              </td>
              <td class="py-3 px-4 font-bold text-emerald-700">
                R$ {{ formatMoney(extra.valor) }}
              </td>
              <td class="py-3 px-4 text-right space-x-2" v-if="currentPeriodo?.status === 'ABERTO'">
                <button @click="openExtraModal(extra)" class="text-blue-600 hover:underline">Editar</button>
                <button @click="deleteExtra(extra)" class="text-rose-600 hover:underline">Excluir</button>
              </td>
            </tr>
          </tbody>
          <tfoot class="bg-slate-50 border-t border-slate-200 font-bold">
            <tr>
              <td colspan="4" class="py-3 px-4 text-slate-700">TOTAL OUTRAS RECEITAS:</td>
              <td class="py-3 px-4 text-emerald-700">R$ {{ formatMoney(totalExtrasCalculado) }}</td>
              <td v-if="currentPeriodo?.status === 'ABERTO'"></td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>

    <!-- Modal Receita Extra -->
    <div v-if="showExtraModal" class="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div class="bg-white rounded-xl max-w-md w-full p-6 space-y-4 shadow-xl">
        <h3 class="font-bold text-base text-slate-800">
          {{ editingExtraId ? 'Editar Receita Extra' : 'Nova Receita Extra' }}
        </h3>
        <form @submit.prevent="saveExtra" class="space-y-3">
          <div>
            <label class="block text-xs font-medium text-slate-700 mb-1">Descrição</label>
            <input
              type="text"
              v-model="extraForm.descricao"
              required
              placeholder="Ex: COTA REF. ALUGUEL - CASA 23"
              class="w-full text-xs border rounded-lg p-2"
            />
          </div>

          <div>
            <label class="block text-xs font-medium text-slate-700 mb-1">Tipo</label>
            <select v-model="extraForm.tipo" class="w-full text-xs border rounded-lg p-2">
              <option value="ALUGUEL_VAGA">Aluguel de Vaga</option>
              <option value="JUROS_MULTA">Juros e Multa de Atraso</option>
              <option value="COTA_ATRASADA">Cota Atrasada de Mês Anterior</option>
              <option value="RENDIMENTO_CDB">Rendimento Investimento CDB</option>
              <option value="OUTRO">Outra Receita</option>
            </select>
          </div>

          <div>
            <label class="block text-xs font-medium text-slate-700 mb-1">Valor (R$)</label>
            <input
              type="number"
              step="0.01"
              v-model="extraForm.valor"
              required
              class="w-full text-xs border rounded-lg p-2 font-bold"
            />
          </div>

          <div>
            <label class="block text-xs font-medium text-slate-700 mb-1">Data</label>
            <input
              type="date"
              v-model="extraForm.data"
              required
              class="w-full text-xs border rounded-lg p-2"
            />
          </div>

          <div class="pt-3 flex justify-end gap-2 border-t">
            <button
              type="button"
              @click="showExtraModal = false"
              class="px-3 py-1.5 border rounded-lg text-xs"
            >
              Cancelar
            </button>
            <button
              type="submit"
              class="px-4 py-1.5 bg-blue-600 text-white rounded-lg text-xs font-medium hover:bg-blue-700"
            >
              Salvar
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from "vue"
import { useRoute, useRouter } from "vue-router"
import financeiroApi from "@/api/financeiro"

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const isUpdating = ref(false)
const periodos = ref([])
const selectedPeriodoId = ref(null)
const currentPeriodo = ref(null)
const activeTab = ref("cotas")

const cotas = ref([])
const receitasExtras = ref([])
const selectedCotaIds = ref([])
const batchDataPagamento = ref(new Date().toISOString().substring(0, 10))

const searchQuery = ref("")
const filterStatus = ref("ALL")

// Receita Extra Modal
const showExtraModal = ref(false)
const editingExtraId = ref(null)
const extraForm = ref({
  descricao: "",
  tipo: "ALUGUEL_VAGA",
  valor: 100.00,
  data: new Date().toISOString().substring(0, 10),
  unidade: null,
})

function formatDate(val) {
  if (!val) return "-"
  const d = new Date(val + "T00:00:00")
  return d.toLocaleDateString("pt-BR")
}

function formatMoney(val) {
  if (val === undefined || val === null) return "0,00"
  return Number(val).toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const filteredCotas = computed(() => {
  return cotas.value.filter(c => {
    if (filterStatus.value === "PAGO" && !c.data_pagamento) return false
    if (filterStatus.value === "PENDENTE" && c.data_pagamento) return false
    if (searchQuery.value) {
      const q = searchQuery.value.toLowerCase()
      const unid = (c.unidade_identificador || "").toLowerCase()
      const obs = (c.observacao || "").toLowerCase()
      return unid.includes(q) || obs.includes(q) || String(c.numero_ordem).includes(q)
    }
    return true
  })
})

const allFilteredSelected = computed(() => {
  if (!filteredCotas.value.length) return false
  return filteredCotas.value.every(c => selectedCotaIds.value.includes(c.id))
})

function toggleSelectAll(e) {
  if (e.target.checked) {
    const ids = filteredCotas.value.map(c => c.id)
    selectedCotaIds.value = Array.from(new Set([...selectedCotaIds.value, ...ids]))
  } else {
    const unselectIds = filteredCotas.value.map(c => c.id)
    selectedCotaIds.value = selectedCotaIds.value.filter(id => !unselectIds.includes(id))
  }
}

const cotasPagasCount = computed(() => {
  return cotas.value.filter(c => c.data_pagamento).length
})

const totalCotasCalculado = computed(() => {
  return cotas.value.reduce((acc, c) => {
    if (c.data_pagamento) {
      return acc + (Number(c.cota) || Number(c.valor_titulo) || 0)
    }
    return acc
  }, 0)
})

const totalExtrasCalculado = computed(() => {
  return receitasExtras.value.reduce((acc, e) => acc + (Number(e.valor) || 0), 0)
})

const totalGeralReceitas = computed(() => {
  return totalCotasCalculado.value + totalExtrasCalculado.value
})

async function loadPeriodos() {
  const res = await financeiroApi.getPeriodos()
  periodos.value = res.data.results || res.data
  const pIdParam = route.params.periodoId
  if (pIdParam) {
    selectedPeriodoId.value = Number(pIdParam)
  } else if (periodos.value.length > 0) {
    selectedPeriodoId.value = periodos.value[0].id
  }
}

async function loadData() {
  if (!selectedPeriodoId.value) return
  loading.value = true
  try {
    currentPeriodo.value = periodos.value.find(p => p.id === selectedPeriodoId.value)

    const [cotasRes, extrasRes] = await Promise.all([
      financeiroApi.getCotas({ periodo: selectedPeriodoId.value }),
      financeiroApi.getReceitasExtras({ periodo: selectedPeriodoId.value }),
    ])
    cotas.value = cotasRes.data.results || cotasRes.data
    receitasExtras.value = extrasRes.data.results || extrasRes.data
  } catch (err) {
    console.error("Erro ao carregar pagamentos:", err)
  } finally {
    loading.value = false
  }
}

function changePeriodo() {
  router.push(`/prestacao/pagamentos/${selectedPeriodoId.value}`)
  loadData()
}

function onDataPagamentoChange(cota) {
  if (cota.data_pagamento) {
    if (!cota.cota) cota.cota = cota.valor_titulo
    if (!cota.valor_pago) cota.valor_pago = cota.valor_titulo
    cota.status = "PAGO"
  } else {
    cota.cota = null
    cota.valor_pago = null
    cota.juros_multa = 0
    cota.status = "PENDENTE"
  }
  recalculateRow(cota)
}

function recalculateRow(cota) {
  const cotaBase = Number(cota.cota) || 0
  const vPago = Number(cota.valor_pago) || 0
  if (vPago > cotaBase) {
    cota.juros_multa = Number((vPago - cotaBase).toFixed(2))
  } else {
    cota.juros_multa = 0
  }
  saveCota(cota)
}

async function saveCota(cota) {
  try {
    await financeiroApi.updateCota(cota.id, {
      data_pagamento: cota.data_pagamento,
      cota: cota.cota,
      valor_pago: cota.valor_pago,
      juros_multa: cota.juros_multa,
      observacao: cota.observacao,
      status: cota.data_pagamento ? "PAGO" : "PENDENTE",
    })
  } catch (err) {
    console.error("Erro ao salvar cota:", err)
  }
}

async function limparPagamento(cota) {
  cota.data_pagamento = null
  cota.cota = null
  cota.valor_pago = null
  cota.juros_multa = 0
  cota.status = "PENDENTE"
  await saveCota(cota)
}

async function marcarEmMassa() {
  if (!batchDataPagamento.value) {
    alert("Selecione a data de pagamento.")
    return
  }
  isUpdating.value = true
  try {
    await financeiroApi.marcarCotasEmMassa({
      cota_ids: selectedCotaIds.value,
      data_pagamento: batchDataPagamento.value,
    })
    selectedCotaIds.value = []
    await loadData()
  } catch (err) {
    alert("Erro ao marcar cotas em massa.")
  } finally {
    isUpdating.value = false
  }
}

// Receitas Extras Modal handlers
function openExtraModal(extra = null) {
  if (extra) {
    editingExtraId.value = extra.id
    extraForm.value = { ...extra }
  } else {
    editingExtraId.value = null
    extraForm.value = {
      periodo: selectedPeriodoId.value,
      descricao: "",
      tipo: "ALUGUEL_VAGA",
      valor: 100.00,
      data: new Date().toISOString().substring(0, 10),
      unidade: null,
    }
  }
  showExtraModal.value = true
}

async function saveExtra() {
  try {
    extraForm.value.periodo = selectedPeriodoId.value
    if (editingExtraId.value) {
      await financeiroApi.updateReceitaExtra(editingExtraId.value, extraForm.value)
    } else {
      await financeiroApi.createReceitaExtra(extraForm.value)
    }
    showExtraModal.value = false
    await loadData()
  } catch (err) {
    alert("Erro ao salvar receita extra.")
  }
}

async function deleteExtra(extra) {
  if (!confirm(`Deseja remover "${extra.descricao}"?`)) return
  try {
    await financeiroApi.deleteReceitaExtra(extra.id)
    await loadData()
  } catch (err) {
    alert("Erro ao excluir receita extra.")
  }
}

onMounted(async () => {
  await loadPeriodos()
  await loadData()
})
</script>
