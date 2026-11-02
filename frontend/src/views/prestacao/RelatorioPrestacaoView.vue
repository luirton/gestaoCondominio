<template>
  <div class="space-y-6">
    <!-- Header com Seletor e Botões de Exportação -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-slate-800 tracking-tight flex items-center gap-2">
          <span class="p-2 bg-blue-100 text-blue-700 rounded-lg">
            <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </span>
          Relatório de Prestação de Contas
        </h1>
        <p class="text-sm text-slate-500 mt-1">
          Espelho oficial da aba PRESTAÇÃO. Relatório balancete para prestação em assembleia e publicação aos moradores.
        </p>
      </div>

      <div class="flex flex-wrap items-center gap-2">
        <!-- Seletor de Período -->
        <select
          v-if="periodosDisponiveis.length > 0"
          v-model="selectedPeriodoId"
          @change="changePeriodo"
          class="bg-white border border-slate-300 rounded-lg px-3 py-2 text-sm font-semibold text-slate-800 shadow-sm focus:ring-1 focus:ring-blue-500"
        >
          <option v-for="p in periodosDisponiveis" :key="p.id" :value="p.id">
            {{ p.mes_referencia_rotulo }} {{ (authStore.isSindico || authStore.isSubSindico) ? `(${p.status})` : '' }}
          </option>
        </select>

        <!-- Botão Exportar PDF -->
        <button
          v-if="currentPeriodo"
          @click="exportPdf"
          :disabled="exportingPdf"
          class="inline-flex items-center px-3.5 py-2 bg-rose-700 hover:bg-rose-800 text-white rounded-lg text-sm font-medium transition shadow-sm disabled:opacity-50"
        >
          <svg class="w-4 h-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
          </svg>
          {{ exportingPdf ? 'Gerando...' : 'Exportar PDF' }}
        </button>

        <!-- Botão Exportar Excel -->
        <button
          v-if="currentPeriodo"
          @click="exportExcel"
          :disabled="exportingExcel"
          class="inline-flex items-center px-3.5 py-2 bg-emerald-700 hover:bg-emerald-800 text-white rounded-lg text-sm font-medium transition shadow-sm disabled:opacity-50"
        >
          <svg class="w-4 h-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          {{ exportingExcel ? 'Gerando...' : 'Exportar Excel' }}
        </button>

        <!-- Ação Fechar Período (Síndico e Subsíndico) -->
        <button
          v-if="(authStore.isSindico || authStore.isSubSindico) && currentPeriodo?.status === 'ABERTO'"
          @click="fecharPeriodo"
          class="inline-flex items-center px-3.5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition shadow-sm"
        >
          Fechar Período
        </button>

        <!-- Ação Publicar (Síndico e Subsíndico) -->
        <button
          v-if="(authStore.isSindico || authStore.isSubSindico) && currentPeriodo?.status === 'FECHADO'"
          @click="publicarPeriodo"
          class="inline-flex items-center px-3.5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-sm font-medium transition shadow-sm"
        >
          Publicar para Moradores
        </button>

        <!-- Ação Reabrir (Síndico e Subsíndico) -->
        <button
          v-if="(authStore.isSindico || authStore.isSubSindico) && currentPeriodo?.status !== 'ABERTO'"
          @click="reabrirPeriodo"
          class="inline-flex items-center px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-medium transition border"
        >
          Reabrir Período
        </button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="p-12 text-center text-slate-500">
      <div class="inline-block animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full mb-3"></div>
      <p>Consolidando balancete do período...</p>
    </div>

    <div v-else-if="!currentPeriodo" class="bg-white border border-slate-200 rounded-2xl p-12 text-center text-slate-500 shadow-sm max-w-xl mx-auto space-y-3">
      <div class="w-12 h-12 bg-amber-100 text-amber-700 rounded-full flex items-center justify-center mx-auto text-xl">
        📋
      </div>
      <h3 class="text-base font-bold text-slate-800">Nenhuma prestação de contas pública disponível</h3>
      <p class="text-xs text-slate-500">
        {{ (authStore.isSindico || authStore.isSubSindico) ? 'Não encontramos prestações de contas cadastradas.' : 'As prestações de contas deste condomínio ainda estão em fase de fechamento e serão disponibilizadas assim que forem publicadas pela administração.' }}
      </p>
    </div>

    <!-- FOLHA DO RELATÓRIO OFICIAL (Estilo Papel / Fiel à Planilha Original) -->
    <div v-else class="max-w-4xl mx-auto bg-white border border-slate-200 shadow-xl rounded-xl p-8 space-y-6 print:border-0 print:shadow-none print:p-0">
      <!-- Cabeçalho Institucional -->
      <div class="text-center border-b border-slate-200 pb-5">
        <h2 class="text-xl font-extrabold text-slate-900 tracking-wide uppercase">
          {{ currentPeriodo.condominio_nome || 'CONDOMÍNIO HORTÊNCIAS III' }}
        </h2>
        <p class="text-xs text-slate-600 mt-1">
          Rua Manuel Teixeira de Melo, nº 827 – José de Alencar - Fortaleza/CE
        </p>
        <p class="text-xs text-slate-500">
          CNPJ: 06.275.266/0001-23
        </p>
        <div class="mt-3 inline-block px-4 py-1.5 bg-blue-50 text-blue-900 rounded-lg border border-blue-200 text-xs font-bold tracking-wide">
          PRESTAÇÃO DE CONTAS DO PERÍODO DE {{ formatDate(currentPeriodo.data_inicio_prestacao) }} A {{ formatDate(currentPeriodo.data_fim_prestacao) }}
        </div>
      </div>

      <!-- SEÇÃO 1: RECEITAS -->
      <div class="space-y-2">
        <div class="bg-teal-800 text-white px-4 py-2 rounded-t-lg font-bold text-xs uppercase tracking-wider flex justify-between">
          <span>RECEITAS</span>
          <span>VALOR (R$)</span>
        </div>
        <table class="w-full text-xs text-left">
          <tbody class="divide-y divide-slate-100">
            <tr>
              <td class="py-2.5 px-4 text-slate-800">
                COTAS – REFERENTES AO MÊS DE {{ currentPeriodo.mes_referencia_rotulo }} COM VENC. EM {{ formatDate(currentPeriodo.data_vencimento) }}
              </td>
              <td class="py-2.5 px-4 text-right font-medium text-slate-800 whitespace-nowrap">
                R$ {{ formatMoney(totais.total_cotas_regulares) }}
              </td>
            </tr>
            <tr>
              <td class="py-2.5 px-4 text-slate-800">
                COTAS – (RECEBIMENTO EM ATRASO / ACORDO / ANTECIPAÇÃO / OUTROS)
              </td>
              <td class="py-2.5 px-4 text-right font-medium text-slate-800 whitespace-nowrap">
                R$ {{ formatMoney(totais.total_receitas_extras) }}
              </td>
            </tr>
            <tr>
              <td class="py-2.5 px-4 text-slate-800">
                RENDIMENTO INVESTIMENTO CDB
              </td>
              <td class="py-2.5 px-4 text-right font-medium text-slate-800 whitespace-nowrap">
                R$ 0,00
              </td>
            </tr>
          </tbody>
          <tfoot>
            <tr class="bg-teal-50 border-t border-teal-200 font-bold text-teal-900">
              <td class="py-2.5 px-4">TOTAL DAS RECEITAS</td>
              <td class="py-2.5 px-4 text-right text-sm">R$ {{ formatMoney(totais.total_receitas) }}</td>
            </tr>
          </tfoot>
        </table>
      </div>

      <!-- SEÇÃO 2: DESPESAS FIXAS -->
      <div class="space-y-2">
        <div class="bg-slate-900 text-white px-4 py-2 rounded-t-lg font-bold text-xs uppercase tracking-wider flex justify-between">
          <span>DESPESAS FIXAS</span>
          <span>VALOR (R$)</span>
        </div>
        <table class="w-full text-xs text-left">
          <tbody class="divide-y divide-slate-100">
            <tr v-for="d in despesasFixas" :key="d.id" class="hover:bg-slate-50">
              <td class="py-2 px-4 text-slate-800">
                {{ d.descricao }}
              </td>
              <td class="py-2 px-4 text-right font-medium text-slate-800 whitespace-nowrap">
                R$ {{ formatMoney(d.valor) }}
              </td>
            </tr>
          </tbody>
          <tfoot>
            <tr class="bg-slate-100 border-t border-slate-300 font-bold text-slate-900">
              <td class="py-2.5 px-4">TOTAL DAS DESPESAS FIXAS</td>
              <td class="py-2.5 px-4 text-right text-sm">R$ {{ formatMoney(totais.total_despesas_fixas) }}</td>
            </tr>
          </tfoot>
        </table>
      </div>

      <!-- SEÇÃO 3: DESPESAS VARIÁVEIS -->
      <div class="space-y-2">
        <div class="bg-slate-700 text-white px-4 py-2 rounded-t-lg font-bold text-xs uppercase tracking-wider flex justify-between">
          <span>DESPESAS VARIÁVEIS</span>
          <span>VALOR (R$)</span>
        </div>
        <table class="w-full text-xs text-left">
          <tbody class="divide-y divide-slate-100">
            <tr v-for="d in despesasVariaveis" :key="d.id" class="hover:bg-slate-50">
              <td class="py-2 px-4 text-slate-800">
                {{ d.descricao }}
              </td>
              <td class="py-2 px-4 text-right font-medium text-slate-800 whitespace-nowrap">
                R$ {{ formatMoney(d.valor) }}
              </td>
            </tr>
          </tbody>
          <tfoot>
            <tr class="bg-slate-100 border-t border-slate-300 font-bold text-slate-900">
              <td class="py-2.5 px-4">TOTAL DAS DESPESAS VARIÁVEIS</td>
              <td class="py-2.5 px-4 text-right text-sm">R$ {{ formatMoney(totais.total_despesas_variaveis) }}</td>
            </tr>
          </tfoot>
        </table>
      </div>

      <!-- SEÇÃO 4: RESULTADO CONTA CORRENTE -->
      <div class="space-y-2">
        <div class="bg-blue-900 text-white px-4 py-2 rounded-t-lg font-bold text-xs uppercase tracking-wider flex justify-between">
          <span>RESULTADO CONTA CORRENTE</span>
          <span>VALOR (R$)</span>
        </div>
        <table class="w-full text-xs text-left">
          <tbody class="divide-y divide-slate-100">
            <tr>
              <td class="py-2 px-4 text-slate-700">SALDO ANTERIOR INTER (CC)</td>
              <td class="py-2 px-4 text-right font-medium text-slate-800">R$ {{ formatMoney(totais.saldo_anterior_cc) }}</td>
            </tr>
            <tr>
              <td class="py-2 px-4 text-slate-700">SALDO ANTERIOR INTER (APLICAÇÃO)</td>
              <td class="py-2 px-4 text-right font-medium text-slate-800">R$ {{ formatMoney(totais.saldo_anterior_aplicacao) }}</td>
            </tr>
            <tr>
              <td class="py-2 px-4 text-slate-700">SALDO PORQUINHO (FÉRIAS/DÉCIMO)</td>
              <td class="py-2 px-4 text-right font-medium text-slate-800">R$ {{ formatMoney(totais.saldo_anterior_porquinho) }}</td>
            </tr>
            <tr class="bg-slate-50 font-bold text-slate-900">
              <td class="py-2.5 px-4">SALDO ANTERIOR TOTAL</td>
              <td class="py-2.5 px-4 text-right">R$ {{ formatMoney(totais.saldo_anterior_total) }}</td>
            </tr>
            <tr>
              <td class="py-2 px-4 text-slate-700">RECEITAS DO MÊS</td>
              <td class="py-2 px-4 text-right font-medium text-emerald-700">R$ {{ formatMoney(totais.total_receitas) }}</td>
            </tr>
            <tr class="bg-blue-50/60 font-bold text-blue-900">
              <td class="py-2.5 px-4">SUB TOTAL</td>
              <td class="py-2.5 px-4 text-right text-sm">R$ {{ formatMoney(totais.subtotal) }}</td>
            </tr>
            <tr>
              <td class="py-2 px-4 text-slate-700">TOTAL DAS DESPESAS DO MÊS</td>
              <td class="py-2 px-4 text-right font-medium text-rose-700">R$ {{ formatMoney(totais.total_despesas) }}</td>
            </tr>
            <tr class="bg-emerald-50 font-extrabold text-emerald-900 border-t-2 border-emerald-300">
              <td class="py-3 px-4 text-sm">SALDO MÊS</td>
              <td class="py-3 px-4 text-right text-base">R$ {{ formatMoney(totais.saldo_mes) }}</td>
            </tr>
            <tr class="bg-slate-100 font-bold text-slate-900">
              <td class="py-2.5 px-4">
                TOTAL DO SALDO BANCÁRIO (INTER CONTA CORRENTE) {{ formatDate(currentPeriodo.data_saldo_bancario || currentPeriodo.data_fim_prestacao) }}
              </td>
              <td class="py-2.5 px-4 text-right text-sm">R$ {{ formatMoney(totais.total_saldo_bancario) }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- OBSERVAÇÃO AUTOMÁTICA DA DIFERENÇA -->
      <div class="p-3.5 bg-slate-50 border border-slate-200 rounded-lg text-xs italic text-slate-700">
        <strong>OBS:</strong> {{ totais.observacao_diferenca }}
      </div>

      <!-- ASSINATURA DIGITAL DO SÍNDICO -->
      <div class="pt-8 text-center space-y-1">
        <p class="text-xs text-slate-500 mb-6">
          Fortaleza/CE, {{ formatDate(currentPeriodo.data_assinatura) }}
        </p>
        <div class="inline-block border-t border-slate-400 pt-2 w-72">
          <p class="text-xs font-bold text-slate-900">Síndico</p>
          <p class="text-sm font-extrabold text-slate-800 uppercase tracking-wide">
            {{ currentPeriodo.sindico_nome || 'JOSÉ MARTINS DA SILVA FILHO' }}
          </p>
          <p class="text-xs text-slate-500">
            CPF: {{ currentPeriodo.sindico_cpf || '447.260.903-72' }}
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from "vue"
import { useRoute, useRouter } from "vue-router"
import { useAuthStore } from "@/stores/auth"
import financeiroApi from "@/api/financeiro"

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const loading = ref(true)
const exportingPdf = ref(false)
const exportingExcel = ref(false)
const periodos = ref([])
const selectedPeriodoId = ref(null)
const currentPeriodo = ref(null)
const despesas = ref([])
const totais = ref({
  total_cotas_regulares: 0,
  total_receitas_extras: 0,
  total_receitas: 0,
  total_despesas_fixas: 0,
  total_despesas_variaveis: 0,
  total_despesas: 0,
  saldo_anterior_cc: 0,
  saldo_anterior_aplicacao: 0,
  saldo_anterior_porquinho: 0,
  saldo_anterior_total: 0,
  subtotal: 0,
  saldo_mes: 0,
  total_saldo_bancario: 0,
  observacao_diferenca: "",
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

const despesasFixas = computed(() => despesas.value.filter(d => d.tipo === "FIXA"))
const despesasVariaveis = computed(() => despesas.value.filter(d => d.tipo === "VARIAVEL"))

const periodosDisponiveis = computed(() => {
  if (authStore.isSindico || authStore.isSubSindico) return periodos.value
  return periodos.value.filter(p => p.status === "PUBLICADO")
})

async function loadPeriodos() {
  try {
    const res = await financeiroApi.getPeriodos()
    periodos.value = res.data.results || res.data
    const disponiveis = periodosDisponiveis.value
    const pIdParam = route.params.periodoId
    if (pIdParam && disponiveis.some(p => Number(p.id) === Number(pIdParam))) {
      selectedPeriodoId.value = Number(pIdParam)
    } else if (disponiveis.length > 0) {
      // Prioriza uma prestação publicada ou com movimentação ao invés de período vazio
      const pub = disponiveis.find(p => p.status === "PUBLICADO") || disponiveis[0]
      selectedPeriodoId.value = pub.id
    } else {
      selectedPeriodoId.value = null
    }
  } catch (err) {
    console.error("Erro ao carregar períodos:", err)
  }
}

async function loadData() {
  if (!selectedPeriodoId.value) {
    if (periodosDisponiveis.value.length > 0) {
      const pub = periodosDisponiveis.value.find(p => p.status === "PUBLICADO") || periodosDisponiveis.value[0]
      selectedPeriodoId.value = pub.id
    } else {
      currentPeriodo.value = null
      return
    }
  }
  loading.value = true
  try {
    const p = periodosDisponiveis.value.find(item => Number(item.id) === Number(selectedPeriodoId.value))
    if (!p) {
      if (periodosDisponiveis.value.length > 0) {
        selectedPeriodoId.value = periodosDisponiveis.value[0].id
        currentPeriodo.value = periodosDisponiveis.value[0]
      } else {
        currentPeriodo.value = null
        loading.value = false
        return
      }
    } else {
      currentPeriodo.value = p
    }

    const [totaisRes, despesasRes] = await Promise.all([
      financeiroApi.getTotais(selectedPeriodoId.value),
      financeiroApi.getDespesas({ periodo: selectedPeriodoId.value }),
    ])
    totais.value = totaisRes.data
    despesas.value = despesasRes.data.results || despesasRes.data
  } catch (err) {
    console.error("Erro ao carregar relatório:", err)
    if (!totais.value?.total_receitas && currentPeriodo.value?.totais) {
      totais.value = currentPeriodo.value.totais
    }
  } finally {
    loading.value = false
  }
}

function changePeriodo() {
  router.push(`/prestacao/relatorio/${selectedPeriodoId.value}`)
  loadData()
}

watch(
  () => route.params.periodoId,
  (newId) => {
    if (newId) {
      selectedPeriodoId.value = Number(newId)
    } else if (periodosDisponiveis.value.length > 0) {
      const pub = periodosDisponiveis.value.find(p => p.status === "PUBLICADO") || periodosDisponiveis.value[0]
      selectedPeriodoId.value = pub.id
    }
    loadData()
  }
)

async function exportPdf() {
  exportingPdf.value = true
  try {
    const res = await financeiroApi.exportarPdf(selectedPeriodoId.value)
    const blob = new Blob([res.data], { type: "application/pdf" })
    const link = document.createElement("a")
    link.href = URL.createObjectURL(blob)
    link.download = `Prestacao_Contas_${currentPeriodo.value.mes_referencia_rotulo.replace('/', '_')}.pdf`
    link.click()
  } catch (err) {
    alert("Erro ao exportar PDF.")
  } finally {
    exportingPdf.value = false
  }
}

async function exportExcel() {
  exportingExcel.value = true
  try {
    const res = await financeiroApi.exportarExcel(selectedPeriodoId.value)
    const blob = new Blob([res.data], {
      type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    })
    const link = document.createElement("a")
    link.href = URL.createObjectURL(blob)
    link.download = `Prestacao_Contas_${currentPeriodo.value.mes_referencia_rotulo.replace('/', '_')}.xlsx`
    link.click()
  } catch (err) {
    alert("Erro ao exportar Excel.")
  } finally {
    exportingExcel.value = false
  }
}

async function fecharPeriodo() {
  if (!confirm("Tem certeza que deseja fechar a prestação de contas? Os valores serão congelados em snapshot.")) return
  try {
    await financeiroApi.fecharPeriodo(selectedPeriodoId.value)
    alert("Período fechado com sucesso.")
    await loadPeriodos()
    await loadData()
  } catch (err) {
    alert(err.response?.data?.error || "Erro ao fechar período.")
  }
}

async function publicarPeriodo() {
  if (!confirm("Publicar a prestação de contas tornará o balancete visível para todos os moradores. Confirmar?")) return
  try {
    await financeiroApi.publicarPeriodo(selectedPeriodoId.value)
    alert("Período publicado com sucesso.")
    await loadPeriodos()
    await loadData()
  } catch (err) {
    alert(err.response?.data?.error || "Erro ao publicar período.")
  }
}

async function reabrirPeriodo() {
  if (!confirm("Deseja reabrir este período para edição?")) return
  try {
    await financeiroApi.reabrirPeriodo(selectedPeriodoId.value)
    alert("Período reaberto com sucesso.")
    await loadPeriodos()
    await loadData()
  } catch (err) {
    alert(err.response?.data?.error || "Erro ao reabrir período.")
  }
}

onMounted(async () => {
  await loadPeriodos()
  await loadData()
})
</script>
