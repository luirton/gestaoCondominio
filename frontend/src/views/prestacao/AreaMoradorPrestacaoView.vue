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
          Espaço do Condômino: Prestações & Cotas
        </h1>
        <p class="text-sm text-slate-500 mt-1">
          Transparência condominial, consulta de cotas e acesso às prestações de contas aprovadas.
        </p>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="p-12 text-center text-slate-500">
      <div class="inline-block animate-spin w-8 h-8 border-4 border-emerald-600 border-t-transparent rounded-full mb-3"></div>
      <p>Carregando dados da sua unidade...</p>
    </div>

    <div v-else class="space-y-8">
      <!-- Bloco 1: Minhas Cotas Condominiais -->
      <div class="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
        <div class="p-4 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
          <div>
            <h2 class="font-bold text-slate-800 text-base">Minhas Cotas Condominiais</h2>
            <p class="text-xs text-slate-500">Histórico de pagamento e status da cota da sua unidade.</p>
          </div>
        </div>

        <div v-if="minhasCotas.length === 0" class="p-8 text-center text-slate-400 text-sm">
          Nenhuma cota registrada para as suas unidades até o momento.
        </div>

        <table v-else class="w-full text-left border-collapse text-xs">
          <thead class="bg-slate-100 text-slate-600 uppercase font-semibold">
            <tr>
              <th class="py-3 px-4">Unidade</th>
              <th class="py-3 px-4">Período de Ref.</th>
              <th class="py-3 px-4">Vencimento</th>
              <th class="py-3 px-4">Valor Título</th>
              <th class="py-3 px-4">Data Pagamento</th>
              <th class="py-3 px-4">Valor Pago</th>
              <th class="py-3 px-4">Status</th>
              <th class="py-3 px-4 text-right">Comprovante</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-200">
            <tr v-for="cota in minhasCotas" :key="cota.id" class="hover:bg-slate-50">
              <td class="py-3 px-4 font-bold text-slate-800">{{ cota.unidade }}</td>
              <td class="py-3 px-4 text-slate-600 font-medium">{{ cota.periodo_rotulo }}</td>
              <td class="py-3 px-4 text-slate-500">{{ formatDate(cota.data_vencimento) }}</td>
              <td class="py-3 px-4 text-slate-700">R$ {{ formatMoney(cota.valor_titulo) }}</td>
              <td class="py-3 px-4 text-slate-600">{{ formatDate(cota.data_pagamento) }}</td>
              <td class="py-3 px-4 font-bold text-slate-800">
                {{ cota.valor_pago ? `R$ ${formatMoney(cota.valor_pago)}` : '-' }}
              </td>
              <td class="py-3 px-4">
                <span
                  class="px-2 py-0.5 rounded text-[11px] font-bold"
                  :class="cota.status === 'PAGO' ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'"
                >
                  {{ cota.status }}
                </span>
              </td>
              <td class="py-3 px-4 text-right">
                <span v-if="cota.status === 'PAGO'" class="text-emerald-600 font-medium">Quitada</span>
                <span v-else class="text-rose-600 font-medium">Aguardando Baixa</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Bloco 2: Prestações de Contas Publicadas -->
      <div class="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
        <div class="p-4 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
          <div>
            <h2 class="font-bold text-slate-800 text-base">Prestações de Contas Publicadas</h2>
            <p class="text-xs text-slate-500">Balancetes oficiais aprovados e disponibilizados pela administração.</p>
          </div>
        </div>

        <div v-if="prestacoesPublicadas.length === 0" class="p-8 text-center text-slate-400 text-sm">
          Nenhuma prestação publicada disponível no momento.
        </div>

        <div v-else class="divide-y divide-slate-100">
          <div
            v-for="p in prestacoesPublicadas"
            :key="p.id"
            class="p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 hover:bg-slate-50 transition"
          >
            <div class="flex items-start gap-4">
              <div class="w-12 h-12 rounded-xl bg-blue-100 text-blue-700 flex items-center justify-center font-bold text-lg">
                <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <div>
                <h3 class="font-bold text-slate-900 text-base">Prestação de Contas - {{ p.mes_referencia_rotulo }}</h3>
                <p class="text-xs text-slate-500 mt-0.5">
                  Vigência: {{ formatDate(p.data_inicio) }} a {{ formatDate(p.data_fim) }} • Síndico: {{ p.sindico_nome }}
                </p>
                <div class="mt-2 flex flex-wrap gap-4 text-xs">
                  <span class="text-slate-600">Receitas: <strong class="text-emerald-700">R$ {{ formatMoney(p.total_receitas) }}</strong></span>
                  <span class="text-slate-600">Despesas: <strong class="text-rose-700">R$ {{ formatMoney(p.total_despesas) }}</strong></span>
                  <span class="text-slate-600">Saldo Mês: <strong class="text-blue-700">R$ {{ formatMoney(p.saldo_mes) }}</strong></span>
                </div>
              </div>
            </div>

            <div class="flex items-center gap-2">
              <router-link
                :to="`/prestacao/relatorio/${p.id}`"
                class="px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold transition"
              >
                Visualizar Detalhado
              </router-link>

              <button
                @click="downloadPdf(p)"
                class="inline-flex items-center px-3.5 py-2 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-xs font-semibold transition shadow-sm"
              >
                <svg class="w-4 h-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                Baixar PDF
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue"
import financeiroApi from "@/api/financeiro"

const loading = ref(true)
const minhasCotas = ref([])
const prestacoesPublicadas = ref([])

function formatDate(val) {
  if (!val) return "-"
  const d = new Date(val + "T00:00:00")
  return d.toLocaleDateString("pt-BR")
}

function formatMoney(val) {
  if (val === undefined || val === null) return "0,00"
  return Number(val).toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

async function loadData() {
  loading.value = true
  try {
    const res = await financeiroApi.getAreaMorador()
    minhasCotas.value = res.data.minhas_cotas || []
    prestacoesPublicadas.value = res.data.prestacoes_publicadas || []
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
    link.download = `Prestacao_Contas_${prestacao.mes_referencia_rotulo.replace('/', '_')}.pdf`
    link.click()
  } catch (err) {
    alert("Erro ao baixar PDF da prestação.")
  }
}

onMounted(() => {
  loadData()
})
</script>
