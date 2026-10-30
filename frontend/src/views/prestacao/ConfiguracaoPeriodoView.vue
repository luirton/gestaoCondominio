<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-slate-800 tracking-tight flex items-center gap-2">
          <span class="p-2 bg-indigo-100 text-indigo-700 rounded-lg">
            <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </span>
          Períodos de Prestação de Contas
        </h1>
        <p class="text-sm text-slate-500 mt-1">
          Configuração de parâmetros de datas, saldos anteriores e geração das cotas mensais.
        </p>
      </div>

      <button
        @click="openModal()"
        class="inline-flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition shadow-sm"
      >
        <svg class="w-4 h-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        Novo Período
      </button>
    </div>

    <!-- Tabela de Períodos -->
    <div class="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
      <div v-if="loading" class="p-12 text-center text-slate-500">
        <div class="inline-block animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full mb-3"></div>
        <p>Carregando períodos...</p>
      </div>

      <div v-else-if="periodos.length === 0" class="p-12 text-center text-slate-500">
        <p>Nenhum período cadastrado até o momento.</p>
      </div>

      <table v-else class="w-full text-left border-collapse text-sm">
        <thead>
          <tr class="bg-slate-50 border-b border-slate-200 text-xs font-semibold uppercase tracking-wider text-slate-500">
            <th class="py-3 px-4">Referência</th>
            <th class="py-3 px-4">Período de Prestação</th>
            <th class="py-3 px-4">Vencimento Cota</th>
            <th class="py-3 px-4">Cotas Pagas</th>
            <th class="py-3 px-4">Saldo Mês</th>
            <th class="py-3 px-4">Status</th>
            <th class="py-3 px-4 text-right">Ações</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-200">
          <tr v-for="p in periodos" :key="p.id" class="hover:bg-slate-50/80 transition-colors">
            <td class="py-3.5 px-4 font-bold text-slate-800">
              {{ p.mes_referencia_rotulo }}
            </td>
            <td class="py-3.5 px-4 text-slate-600">
              {{ formatDate(p.data_inicio_prestacao) }} a {{ formatDate(p.data_fim_prestacao) }}
            </td>
            <td class="py-3.5 px-4 text-slate-600">
              {{ formatDate(p.data_vencimento) }} (R$ {{ formatMoney(p.valor_cota_padrao) }})
            </td>
            <td class="py-3.5 px-4">
              <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-slate-100 text-slate-700">
                {{ p.qtd_cotas_pagas }} / {{ p.qtd_cotas_total }}
              </span>
            </td>
            <td class="py-3.5 px-4 font-bold text-blue-700">
              R$ {{ formatMoney(p.totais?.saldo_mes) }}
            </td>
            <td class="py-3.5 px-4">
              <span
                class="px-2.5 py-0.5 text-xs font-semibold rounded-full"
                :class="{
                  'bg-emerald-100 text-emerald-800': p.status === 'PUBLICADO',
                  'bg-blue-100 text-blue-800': p.status === 'FECHADO',
                  'bg-amber-100 text-amber-800': p.status === 'ABERTO'
                }"
              >
                {{ p.status }}
              </span>
            </td>
            <td class="py-3.5 px-4 text-right space-x-1">
              <button
                v-if="p.status === 'ABERTO' && p.qtd_cotas_total === 0"
                @click="gerarCotas(p)"
                class="px-2.5 py-1 bg-emerald-50 text-emerald-700 hover:bg-emerald-100 rounded text-xs font-medium border border-emerald-200 transition"
                title="Gera cotas para todas as unidades ativas"
              >
                Gerar Cotas
              </button>

              <router-link
                :to="`/prestacao/pagamentos/${p.id}`"
                class="px-2.5 py-1 bg-slate-100 text-slate-700 hover:bg-slate-200 rounded text-xs font-medium transition"
              >
                Pagamentos
              </router-link>

              <router-link
                :to="`/prestacao/relatorio/${p.id}`"
                class="px-2.5 py-1 bg-blue-50 text-blue-700 hover:bg-blue-100 rounded text-xs font-medium border border-blue-200 transition"
              >
                Prestação
              </router-link>

              <button
                @click="openModal(p)"
                class="px-2 py-1 text-slate-500 hover:text-slate-800 text-xs font-medium"
                title="Editar parâmetros"
              >
                Editar
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modal de Criação / Edição de Período (Aba PROPRIEDADES) -->
    <div v-if="showModal" class="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div class="bg-white rounded-2xl max-w-3xl w-full shadow-2xl border border-slate-200 overflow-hidden transform transition-all">
        <div class="px-6 py-4 bg-slate-900 text-white flex items-center justify-between">
          <h3 class="font-bold text-base flex items-center gap-2">
            <svg class="w-5 h-5 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            {{ editingId ? 'Editar Parâmetros do Período' : 'Novo Período de Prestação' }}
          </h3>
          <button @click="showModal = false" class="text-slate-400 hover:text-white">
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form @submit.prevent="savePeriodo" class="p-6 space-y-5 max-h-[80vh] overflow-y-auto">
          <!-- Bloco 1: Datas e Referências -->
          <div>
            <h4 class="text-xs font-bold uppercase tracking-wider text-blue-600 mb-3 border-b pb-1">
              1. Tabela de Datas & Referências
            </h4>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div>
                <label class="block text-xs font-medium text-slate-700 mb-1">Mês de Referência (Data)</label>
                <input
                  type="date"
                  v-model="form.mes_referencia"
                  required
                  class="w-full text-xs border rounded-lg p-2 focus:ring-1 focus:ring-blue-500"
                />
              </div>

              <div>
                <label class="block text-xs font-medium text-slate-700 mb-1">Rótulo do Mês</label>
                <input
                  type="text"
                  v-model="form.mes_referencia_rotulo"
                  placeholder="Ex: SETEMBRO/2026"
                  required
                  class="w-full text-xs border rounded-lg p-2 focus:ring-1 focus:ring-blue-500"
                />
              </div>

              <div>
                <label class="block text-xs font-medium text-slate-700 mb-1">Data de Vencimento</label>
                <input
                  type="date"
                  v-model="form.data_vencimento"
                  required
                  class="w-full text-xs border rounded-lg p-2 focus:ring-1 focus:ring-blue-500"
                />
              </div>

              <div>
                <label class="block text-xs font-medium text-slate-700 mb-1">Início da Prestação</label>
                <input
                  type="date"
                  v-model="form.data_inicio_prestacao"
                  required
                  class="w-full text-xs border rounded-lg p-2 focus:ring-1 focus:ring-blue-500"
                />
              </div>

              <div>
                <label class="block text-xs font-medium text-slate-700 mb-1">Fim da Prestação</label>
                <input
                  type="date"
                  v-model="form.data_fim_prestacao"
                  required
                  class="w-full text-xs border rounded-lg p-2 focus:ring-1 focus:ring-blue-500"
                />
              </div>

              <div>
                <label class="block text-xs font-medium text-slate-700 mb-1">Mês Próx. Vencimento</label>
                <input
                  type="text"
                  v-model="form.mes_prox_vencimento"
                  placeholder="Ex: OUTUBRO"
                  class="w-full text-xs border rounded-lg p-2 focus:ring-1 focus:ring-blue-500"
                />
              </div>

              <div>
                <label class="block text-xs font-medium text-slate-700 mb-1">Data Próx. Vencimento</label>
                <input
                  type="date"
                  v-model="form.data_prox_vencimento"
                  class="w-full text-xs border rounded-lg p-2 focus:ring-1 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>

          <!-- Bloco 2: Valores Padrão -->
          <div>
            <h4 class="text-xs font-bold uppercase tracking-wider text-blue-600 mb-3 border-b pb-1">
              2. Valores Parametrizados (R$)
            </h4>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <label class="block text-xs font-medium text-slate-700 mb-1">Valor Padrão da Cota (R$)</label>
                <input
                  type="number"
                  step="0.01"
                  v-model="form.valor_cota_padrao"
                  required
                  class="w-full text-xs border rounded-lg p-2 focus:ring-1 focus:ring-blue-500"
                />
              </div>
              <div>
                <label class="block text-xs font-medium text-slate-700 mb-1">Valor Padrão Vaga Estacionamento (R$)</label>
                <input
                  type="number"
                  step="0.01"
                  v-model="form.valor_vaga_padrao"
                  required
                  class="w-full text-xs border rounded-lg p-2 focus:ring-1 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>

          <!-- Bloco 3: Saldos Anteriores & Bancário -->
          <div>
            <h4 class="text-xs font-bold uppercase tracking-wider text-blue-600 mb-3 border-b pb-1">
              3. Saldos Anteriores & Bancário (Resultado Conta Corrente)
            </h4>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div>
                <label class="block text-xs font-medium text-slate-700 mb-1">Saldo Anterior Inter (CC)</label>
                <input
                  type="number"
                  step="0.01"
                  v-model="form.saldo_anterior_cc"
                  class="w-full text-xs border rounded-lg p-2 focus:ring-1 focus:ring-blue-500"
                />
              </div>
              <div>
                <label class="block text-xs font-medium text-slate-700 mb-1">Saldo Anterior Aplicação (CDB)</label>
                <input
                  type="number"
                  step="0.01"
                  v-model="form.saldo_anterior_aplicacao"
                  class="w-full text-xs border rounded-lg p-2 focus:ring-1 focus:ring-blue-500"
                />
              </div>
              <div>
                <label class="block text-xs font-medium text-slate-700 mb-1">Saldo Porquinho (Férias/13º)</label>
                <input
                  type="number"
                  step="0.01"
                  v-model="form.saldo_anterior_porquinho"
                  class="w-full text-xs border rounded-lg p-2 focus:ring-1 focus:ring-blue-500"
                />
              </div>
              <div>
                <label class="block text-xs font-medium text-slate-700 mb-1">Total Saldo Bancário Final</label>
                <input
                  type="number"
                  step="0.01"
                  v-model="form.total_saldo_bancario"
                  class="w-full text-xs border rounded-lg p-2 focus:ring-1 focus:ring-blue-500"
                />
              </div>
              <div>
                <label class="block text-xs font-medium text-slate-700 mb-1">Data do Saldo Bancário</label>
                <input
                  type="date"
                  v-model="form.data_saldo_bancario"
                  class="w-full text-xs border rounded-lg p-2 focus:ring-1 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>

          <!-- Bloco 4: Responsável Síndico -->
          <div>
            <h4 class="text-xs font-bold uppercase tracking-wider text-blue-600 mb-3 border-b pb-1">
              4. Assinatura do Síndico
            </h4>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div>
                <label class="block text-xs font-medium text-slate-700 mb-1">Nome do Síndico</label>
                <input
                  type="text"
                  v-model="form.sindico_nome"
                  class="w-full text-xs border rounded-lg p-2 focus:ring-1 focus:ring-blue-500"
                />
              </div>
              <div>
                <label class="block text-xs font-medium text-slate-700 mb-1">CPF do Síndico</label>
                <input
                  type="text"
                  v-model="form.sindico_cpf"
                  placeholder="000.000.000-00"
                  class="w-full text-xs border rounded-lg p-2 focus:ring-1 focus:ring-blue-500"
                />
              </div>
              <div>
                <label class="block text-xs font-medium text-slate-700 mb-1">Data da Assinatura</label>
                <input
                  type="date"
                  v-model="form.data_assinatura"
                  class="w-full text-xs border rounded-lg p-2 focus:ring-1 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>

          <div v-if="errorMessage" class="p-3 bg-rose-50 text-rose-700 text-xs rounded-lg border border-rose-200">
            {{ errorMessage }}
          </div>

          <!-- Botoes -->
          <div class="pt-3 border-t border-slate-200 flex items-center justify-end gap-2">
            <button
              type="button"
              @click="showModal = false"
              class="px-4 py-2 border rounded-lg text-xs font-medium text-slate-700 hover:bg-slate-50"
            >
              Cancelar
            </button>
            <button
              type="submit"
              :disabled="saving"
              class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-medium disabled:opacity-50"
            >
              {{ saving ? 'Salvando...' : 'Salvar Período' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue"
import financeiroApi from "@/api/financeiro"
import apiClient from "@/api/client"

const loading = ref(true)
const periodos = ref([])
const showModal = ref(false)
const editingId = ref(null)
const saving = ref(false)
const errorMessage = ref("")

const form = ref({
  condominio: null,
  mes_referencia: "",
  mes_referencia_rotulo: "",
  data_vencimento: "",
  mes_prox_vencimento: "OUTUBRO",
  data_prox_vencimento: "",
  data_inicio_prestacao: "",
  data_fim_prestacao: "",
  valor_cota_padrao: 380.00,
  valor_vaga_padrao: 100.00,
  saldo_anterior_cc: 0,
  saldo_anterior_aplicacao: 0,
  saldo_anterior_porquinho: 0,
  total_saldo_bancario: 0,
  data_saldo_bancario: "",
  sindico_nome: "JOSÉ MARTINS DA SILVA FILHO",
  sindico_cpf: "447.260.903-72",
  data_assinatura: "",
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

async function loadPeriodos() {
  loading.value = true
  try {
    const res = await financeiroApi.getPeriodos()
    periodos.value = res.data.results || res.data
  } catch (err) {
    console.error("Erro ao carregar períodos:", err)
  } finally {
    loading.value = false
  }
}

async function openModal(periodo = null) {
  errorMessage.value = ""
  if (periodo) {
    editingId.value = periodo.id
    form.value = { ...periodo }
  } else {
    editingId.value = null
    // Pega o id do condomínio ativo
    let activeCondId = localStorage.getItem("active_condominio_id")
    if (!activeCondId && periodos.value.length > 0) {
      activeCondId = periodos.value[0].condominio
    }
    form.value = {
      condominio: activeCondId || 1,
      mes_referencia: new Date().toISOString().substring(0, 10),
      mes_referencia_rotulo: "",
      data_vencimento: "",
      mes_prox_vencimento: "",
      data_prox_vencimento: "",
      data_inicio_prestacao: "",
      data_fim_prestacao: "",
      valor_cota_padrao: 380.00,
      valor_vaga_padrao: 100.00,
      saldo_anterior_cc: 0,
      saldo_anterior_aplicacao: 0,
      saldo_anterior_porquinho: 0,
      total_saldo_bancario: 0,
      data_saldo_bancario: "",
      sindico_nome: "JOSÉ MARTINS DA SILVA FILHO",
      sindico_cpf: "447.260.903-72",
      data_assinatura: "",
    }
  }
  showModal.value = true
}

async function savePeriodo() {
  saving.value = true
  errorMessage.value = ""
  try {
    if (editingId.value) {
      await financeiroApi.updatePeriodo(editingId.value, form.value)
    } else {
      await financeiroApi.createPeriodo(form.value)
    }
    showModal.value = false
    await loadPeriodos()
  } catch (err) {
    const data = err.response?.data
    errorMessage.value = typeof data === "object" ? JSON.stringify(data) : "Erro ao salvar período."
  } finally {
    saving.value = false
  }
}

async function gerarCotas(periodo) {
  if (!confirm(`Deseja gerar as cotas de R$ ${periodo.valor_cota_padrao} para todas as unidades ativas?`)) return
  try {
    const res = await financeiroApi.gerarCotas(periodo.id)
    alert(res.data.message)
    await loadPeriodos()
  } catch (err) {
    alert(err.response?.data?.error || "Erro ao gerar cotas.")
  }
}

onMounted(() => {
  loadPeriodos()
})
</script>
