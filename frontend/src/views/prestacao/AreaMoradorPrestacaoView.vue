<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-slate-800 tracking-tight flex items-center gap-2">
          <span class="p-2 bg-emerald-100 text-emerald-700 rounded-lg">
            <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
            </svg>
          </span>
          Prestações de Contas Publicadas
        </h1>
        <p class="text-sm text-slate-500 mt-1">
          Transparência condominial, consulta de cotas e acesso aos balancetes oficiais publicados da administração.
        </p>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="p-12 text-center text-slate-500">
      <div class="inline-block animate-spin w-8 h-8 border-4 border-emerald-600 border-t-transparent rounded-full mb-3"></div>
      <p>Carregando prestações publicadas do condomínio...</p>
    </div>

    <div v-else class="space-y-8">
      <!-- Seção Principal: Prestações de Contas Publicadas do Condomínio com Select -->
      <div class="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
        <!-- Top bar com Select de Prestações Publicadas -->
        <div class="p-5 border-b border-slate-200 bg-slate-50/80 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 class="font-bold text-slate-900 text-base flex items-center gap-2">
              <span>📋</span> Balancetes e Prestações Oficiais Publicadas
            </h2>
            <p class="text-xs text-slate-500 mt-0.5">
              Selecione o mês para visualizar o balancete aprovado e baixar o relatório assinado em PDF.
            </p>
          </div>

          <!-- Select com as prestações publicadas -->
          <div class="flex items-center gap-2.5">
            <label class="text-xs font-bold text-slate-700 whitespace-nowrap">
              Prestação Publicada:
            </label>
            <select
              v-model="selectedPrestacaoId"
              class="bg-white border border-slate-300 rounded-xl px-3.5 py-2 text-xs font-bold text-slate-800 shadow-sm focus:ring-2 focus:ring-emerald-500 focus:outline-none min-w-[240px]"
            >
              <option v-for="p in prestacoesPublicadas" :key="p.id" :value="p.id">
                {{ p.mes_referencia_rotulo }} • {{ p.condominio_nome || 'Condomínio' }}
              </option>
            </select>
          </div>
        </div>

        <div v-if="prestacoesPublicadas.length === 0" class="p-10 text-center text-slate-400 text-sm">
          <div class="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center mx-auto mb-2 text-xl">
            📭
          </div>
          <p class="font-semibold text-slate-600">Nenhuma prestação publicada disponível para este condomínio.</p>
          <p class="text-xs text-slate-400 mt-1">
            As prestações de contas aparecem aqui assim que forem fechadas e publicadas pela administração.
          </p>
        </div>

        <!-- Spotlight da Prestação Selecionada no Select -->
        <div v-else-if="currentPrestacao" class="p-6 space-y-6">
          <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-emerald-50/50 border border-emerald-200/80 rounded-2xl p-5">
            <div class="flex items-start gap-4">
              <div class="w-14 h-14 rounded-2xl bg-emerald-600 text-white flex items-center justify-center font-black text-xl shadow-md shrink-0">
                📄
              </div>
              <div>
                <div class="flex items-center gap-2">
                  <span class="px-2.5 py-0.5 bg-emerald-100 text-emerald-800 text-[11px] font-bold rounded-full border border-emerald-300">
                    PUBLICADO OFICIAL
                  </span>
                  <span class="text-xs font-bold text-slate-700">
                    {{ currentPrestacao.condominio_nome }}
                  </span>
                </div>
                <h3 class="text-xl font-extrabold text-slate-900 mt-1">
                  Prestação de Contas • {{ currentPrestacao.mes_referencia_rotulo }}
                </h3>
                <p class="text-xs text-slate-600 mt-0.5">
                  Vigência: <strong>{{ formatDate(currentPrestacao.data_inicio) }}</strong> a <strong>{{ formatDate(currentPrestacao.data_fim) }}</strong> •
                  Síndico Responsável: <strong>{{ currentPrestacao.sindico_nome }}</strong>
                </p>
              </div>
            </div>

            <div class="flex flex-wrap items-center gap-2">
              <router-link
                :to="`/prestacao/relatorio/${currentPrestacao.id}`"
                class="inline-flex items-center px-4 py-2.5 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-semibold shadow-sm transition"
              >
                Visualizar Balancete Completo →
              </router-link>

              <button
                @click="downloadPdf(currentPrestacao)"
                class="inline-flex items-center px-4 py-2.5 bg-rose-600 hover:bg-rose-700 text-white rounded-xl text-xs font-semibold transition shadow-sm"
              >
                <svg class="w-4 h-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                Baixar PDF Assinado
              </button>
            </div>
          </div>

          <!-- Cards dos Resultados Consolidados do Período Selecionado -->
          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div class="bg-white border border-slate-200 rounded-xl p-4 shadow-xs">
              <span class="text-[11px] font-bold uppercase tracking-wider text-slate-500 block">Total Receitas</span>
              <div class="text-2xl font-bold text-emerald-700 mt-1">
                R$ {{ formatMoney(currentPrestacao.total_receitas) }}
              </div>
              <p class="text-[11px] text-slate-500 mt-1">
                Cotas + Receitas Extras
              </p>
            </div>

            <div class="bg-white border border-slate-200 rounded-xl p-4 shadow-xs">
              <span class="text-[11px] font-bold uppercase tracking-wider text-slate-500 block">Total Despesas</span>
              <div class="text-2xl font-bold text-rose-700 mt-1">
                R$ {{ formatMoney(currentPrestacao.total_despesas) }}
              </div>
              <p class="text-[11px] text-slate-500 mt-1">
                Fixas: R$ {{ formatMoney(currentPrestacao.total_despesas_fixas) }} | Var: R$ {{ formatMoney(currentPrestacao.total_despesas_variaveis) }}
              </p>
            </div>

            <div class="bg-white border border-slate-200 rounded-xl p-4 shadow-xs">
              <span class="text-[11px] font-bold uppercase tracking-wider text-slate-500 block">Saldo do Mês</span>
              <div class="text-2xl font-bold text-blue-700 mt-1">
                R$ {{ formatMoney(currentPrestacao.saldo_mes) }}
              </div>
              <p class="text-[11px] text-slate-500 mt-1">
                Resultado operacional líquido
              </p>
            </div>

            <div class="bg-white border border-slate-200 rounded-xl p-4 shadow-xs">
              <span class="text-[11px] font-bold uppercase tracking-wider text-slate-500 block">Cotas Pagas</span>
              <div class="text-2xl font-bold text-slate-800 mt-1 flex items-baseline gap-1">
                <span class="text-emerald-700">{{ currentPrestacao.cotas_pagas }}</span>
                <span class="text-xs text-slate-400 font-normal">/ {{ currentPrestacao.cotas_total }}</span>
              </div>
              <p class="text-[11px] text-slate-500 mt-1">
                <span class="text-emerald-700 font-semibold">{{ currentPrestacao.cotas_pagas }} quitadas</span>
                <span v-if="currentPrestacao.cotas_pendentes > 0" class="text-rose-600 font-semibold ml-1">
                  • {{ currentPrestacao.cotas_pendentes }} pendente{{ currentPrestacao.cotas_pendentes > 1 ? 's' : '' }}
                </span>
                <span v-if="currentPrestacao.cotas_isentas > 0" class="text-amber-700 font-medium ml-1">
                  ({{ currentPrestacao.cotas_isentas }} isenta{{ currentPrestacao.cotas_isentas > 1 ? 's' : '' }})
                </span>
              </p>
            </div>
          </div>
        </div>

        <!-- Tabela com histórico de todas as prestações publicadas do condomínio -->
        <div v-if="prestacoesPublicadas.length > 0" class="border-t border-slate-200">
          <div class="p-4 bg-slate-50 border-b border-slate-200">
            <h4 class="text-xs font-bold uppercase tracking-wider text-slate-700">
              Histórico de Prestações Publicadas do Condomínio
            </h4>
          </div>

          <table class="w-full text-left border-collapse text-xs">
            <thead class="bg-slate-100 text-slate-600 uppercase font-semibold">
              <tr>
                <th class="py-3 px-4">Referência</th>
                <th class="py-3 px-4">Condomínio</th>
                <th class="py-3 px-4">Vigência</th>
                <th class="py-3 px-4 text-right">Receitas (R$)</th>
                <th class="py-3 px-4 text-right">Despesas (R$)</th>
                <th class="py-3 px-4 text-right">Saldo Mês (R$)</th>
                <th class="py-3 px-4 text-right">Ações</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-200">
              <tr
                v-for="p in prestacoesPublicadas"
                :key="p.id"
                class="hover:bg-slate-50 transition-colors"
                :class="{ 'bg-emerald-50/40': selectedPrestacaoId === p.id }"
              >
                <td class="py-3 px-4 font-bold text-slate-900">
                  {{ p.mes_referencia_rotulo }}
                </td>
                <td class="py-3 px-4 text-slate-600 font-medium">
                  {{ p.condominio_nome }}
                </td>
                <td class="py-3 px-4 text-slate-500">
                  {{ formatDate(p.data_inicio) }} a {{ formatDate(p.data_fim) }}
                </td>
                <td class="py-3 px-4 text-right font-medium text-emerald-700">
                  R$ {{ formatMoney(p.total_receitas) }}
                </td>
                <td class="py-3 px-4 text-right font-medium text-rose-700">
                  R$ {{ formatMoney(p.total_despesas) }}
                </td>
                <td class="py-3 px-4 text-right font-bold text-blue-700">
                  R$ {{ formatMoney(p.saldo_mes) }}
                </td>
                <td class="py-3 px-4 text-right space-x-2">
                  <button
                    @click="selectedPrestacaoId = p.id"
                    class="text-blue-600 hover:underline font-semibold"
                  >
                    Selecionar
                  </button>
                  <router-link
                    :to="`/prestacao/relatorio/${p.id}`"
                    class="text-slate-700 hover:underline"
                  >
                    Ver Detalhes
                  </router-link>
                  <button
                    @click="downloadPdf(p)"
                    class="text-rose-600 hover:underline font-semibold"
                  >
                    PDF
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Bloco 2: Minhas Cotas Condominiais (se houver unidades vinculadas ao usuário logado) -->
      <div v-if="minhasCotas.length > 0" class="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
        <div class="p-4 border-b border-slate-200 bg-slate-50 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h2 class="font-bold text-slate-800 text-base flex items-center gap-2">
              <span>🏠</span> Minhas Cotas Condominiais
            </h2>
            <p class="text-xs text-slate-500">Histórico de pagamento e status da cota da sua unidade.</p>
          </div>

          <!-- Resumo de status das minhas cotas -->
          <div class="flex items-center gap-2 text-xs">
            <span class="px-2.5 py-1 rounded-lg bg-emerald-50 text-emerald-700 border border-emerald-200 font-semibold">
              {{ minhasCotasPagasCount }} quitada{{ minhasCotasPagasCount !== 1 ? 's' : '' }}
            </span>
            <span v-if="minhasCotasPendentesCount > 0" class="px-2.5 py-1 rounded-lg bg-rose-50 text-rose-700 border border-rose-200 font-semibold">
              {{ minhasCotasPendentesCount }} pendente{{ minhasCotasPendentesCount !== 1 ? 's' : '' }}
            </span>
            <span v-if="minhasCotasIsentasCount > 0" class="px-2.5 py-1 rounded-lg bg-amber-50 text-amber-800 border border-amber-300 font-semibold">
              {{ minhasCotasIsentasCount }} isenta{{ minhasCotasIsentasCount !== 1 ? 's' : '' }}
            </span>
          </div>
        </div>

        <table class="w-full text-left border-collapse text-xs">
          <thead class="bg-slate-100 text-slate-600 uppercase font-semibold">
            <tr>
              <th class="py-3 px-4">Unidade</th>
              <th class="py-3 px-4">Período de Ref.</th>
              <th class="py-3 px-4">Vencimento</th>
              <th class="py-3 px-4">Valor Título</th>
              <th class="py-3 px-4">Data Pagamento</th>
              <th class="py-3 px-4">Valor Pago</th>
              <th class="py-3 px-4">Status</th>
              <th class="py-3 px-4 text-right">Situação</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-200">
            <tr
              v-for="cota in minhasCotas"
              :key="cota.id"
              class="hover:bg-slate-50 transition-colors"
              :class="{
                'bg-amber-50/40': cota.isento || cota.status === 'ISENTO',
                'bg-emerald-50/20': cota.status === 'PAGO' && !cota.isento
              }"
            >
              <td class="py-3 px-4 font-bold text-slate-800">
                <div class="flex items-center gap-1.5">
                  <span>{{ cota.unidade }}</span>
                  <span
                    v-if="cota.isento || cota.status === 'ISENTO'"
                    class="px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300"
                    title="Isenção pelo mandato de gestão condominial"
                  >
                    ISENTO
                  </span>
                </div>
              </td>
              <td class="py-3 px-4 text-slate-600 font-medium">{{ cota.periodo_rotulo }}</td>
              <td class="py-3 px-4 text-slate-500">{{ formatDate(cota.data_vencimento) }}</td>
              <td class="py-3 px-4 text-slate-700 font-mono">
                <span v-if="cota.isento || cota.status === 'ISENTO'" class="text-amber-800 font-semibold" title="Titular isento pelo mandato">
                  R$ {{ formatMoney(cota.valor_titulo) }}
                </span>
                <span v-else>R$ {{ formatMoney(cota.valor_titulo) }}</span>
              </td>
              <td class="py-3 px-4 text-slate-600">
                <span v-if="cota.isento || cota.status === 'ISENTO'" class="text-amber-700 font-medium italic">Isento</span>
                <span v-else>{{ formatDate(cota.data_pagamento) }}</span>
              </td>
              <td class="py-3 px-4 font-bold text-slate-800 font-mono">
                <span v-if="cota.isento || cota.status === 'ISENTO'" class="text-amber-800 font-semibold">R$ 0,00</span>
                <span v-else>{{ cota.valor_pago ? `R$ ${formatMoney(cota.valor_pago)}` : '-' }}</span>
              </td>
              <td class="py-3 px-4">
                <span
                  v-if="cota.isento || cota.status === 'ISENTO'"
                  class="px-2 py-0.5 rounded text-[11px] font-bold bg-amber-100 text-amber-800 border border-amber-300"
                >
                  ISENTO
                </span>
                <span
                  v-else-if="cota.status === 'PAGO'"
                  class="px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-100 text-emerald-800"
                >
                  PAGO
                </span>
                <span
                  v-else
                  class="px-2 py-0.5 rounded text-[11px] font-bold bg-rose-100 text-rose-800"
                >
                  PENDENTE
                </span>
              </td>
              <td class="py-3 px-4 text-right">
                <span
                  v-if="cota.isento || cota.status === 'ISENTO'"
                  class="text-amber-700 font-semibold flex items-center justify-end gap-1"
                >
                  <span>★</span> Isento (Mandato)
                </span>
                <span v-else-if="cota.status === 'PAGO'" class="text-emerald-600 font-medium">Quitada</span>
                <span v-else class="text-rose-600 font-medium">Aguardando Baixa</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import financeiroApi from "@/api/financeiro"

const loading = ref(true)
const minhasCotas = ref([])
const prestacoesPublicadas = ref([])
const selectedPrestacaoId = ref(null)

const currentPrestacao = computed(() => {
  if (!selectedPrestacaoId.value) return prestacoesPublicadas.value[0] || null
  return prestacoesPublicadas.value.find(p => p.id === selectedPrestacaoId.value) || prestacoesPublicadas.value[0] || null
})

const minhasCotasPagasCount = computed(() => {
  return minhasCotas.value.filter(c => c.status === "PAGO" && !c.isento).length
})

const minhasCotasIsentasCount = computed(() => {
  return minhasCotas.value.filter(c => c.isento || c.status === "ISENTO").length
})

const minhasCotasPendentesCount = computed(() => {
  return minhasCotas.value.filter(c => !c.isento && c.status !== "ISENTO" && c.status !== "PAGO" && !c.data_pagamento).length
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

async function loadData() {
  loading.value = true
  try {
    const activeCondId = localStorage.getItem("active_condominio_id")
    const res = await financeiroApi.getAreaMorador(activeCondId ? { condominio: activeCondId } : {})
    minhasCotas.value = res.data.minhas_cotas || []
    prestacoesPublicadas.value = res.data.prestacoes_publicadas || []
    if (prestacoesPublicadas.value.length > 0) {
      selectedPrestacaoId.value = prestacoesPublicadas.value[0].id
    }
  } catch (err) {
    console.error("Erro ao carregar área do morador:", err)
  } finally {
    loading.value = false
  }
}

async function downloadPdf(prestacao) {
  try {
    const res = await financeiroApi.exportarPdf(prestacao.id)
    const blob = new Blob([res.data], { type: "application/pdf" })
    const link = document.createElement("a")
    link.href = URL.createObjectURL(blob)
    link.download = `Prestacao_Contas_${(prestacao.mes_referencia_rotulo || 'periodo').replace('/', '_')}.pdf`
    link.click()
  } catch (err) {
    alert("Erro ao baixar PDF da prestação.")
  }
}

onMounted(() => {
  loadData()
})
</script>
