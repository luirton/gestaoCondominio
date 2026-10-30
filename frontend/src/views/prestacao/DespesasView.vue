<template>
  <div class="space-y-6">
    <!-- Header com Seletor de Período -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-slate-800 tracking-tight flex items-center gap-2">
          <span class="p-2 bg-rose-100 text-rose-700 rounded-lg">
            <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
          </span>
          Gestão de Despesas do Período
        </h1>
        <p class="text-sm text-slate-500 mt-1">
          Controle de despesas fixas e variáveis com upload e auditoria de comprovantes fiscais.
        </p>
      </div>

      <div class="flex flex-wrap items-center gap-3">
        <!-- Seletor de Período -->
        <select
          v-model="selectedPeriodoId"
          @change="changePeriodo"
          class="bg-white border border-slate-300 rounded-lg px-3 py-2 text-sm font-semibold text-slate-800 shadow-sm focus:ring-1 focus:ring-blue-500"
        >
          <option v-for="p in periodos" :key="p.id" :value="p.id">
            {{ p.mes_referencia_rotulo }} ({{ p.status }})
          </option>
        </select>

        <button
          v-if="currentPeriodo?.status === 'ABERTO'"
          @click="openModal()"
          class="inline-flex items-center px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-sm font-medium transition shadow-sm"
        >
          <svg class="w-4 h-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          Nova Despesa
        </button>
      </div>
    </div>

    <!-- Cards de Totais de Despesas -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div class="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
        <span class="text-xs font-semibold uppercase text-slate-500">Despesas Fixas</span>
        <div class="text-xl font-bold text-slate-800 mt-1">
          R$ {{ formatMoney(totalFixas) }}
        </div>
        <p class="text-xs text-slate-400 mt-0.5">{{ despesasFixasCount }} lançamentos (salários, tributos, contratos)</p>
      </div>

      <div class="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
        <span class="text-xs font-semibold uppercase text-slate-500">Despesas Variáveis</span>
        <div class="text-xl font-bold text-slate-800 mt-1">
          R$ {{ formatMoney(totalVariaveis) }}
        </div>
        <p class="text-xs text-slate-400 mt-0.5">{{ despesasVariaveisCount }} lançamentos (materiais, reparos, extras)</p>
      </div>

      <div class="bg-white border border-rose-200 bg-rose-50/30 rounded-xl p-4 shadow-sm">
        <span class="text-xs font-bold uppercase text-rose-700">Total das Despesas do Mês</span>
        <div class="text-2xl font-bold text-rose-700 mt-1">
          R$ {{ formatMoney(totalGeral) }}
        </div>
        <p class="text-xs text-slate-500 mt-0.5">{{ despesas.length }} despesas registradas no total</p>
      </div>
    </div>

    <!-- Filtros e Busca -->
    <div class="bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-3">
      <div class="flex flex-wrap items-center gap-2">
        <input
          type="text"
          v-model="searchQuery"
          placeholder="Buscar descrição ou fornecedor..."
          class="text-xs border rounded-lg px-3 py-1.5 w-60 focus:ring-1 focus:ring-blue-500"
        />

        <select
          v-model="filterTipo"
          class="text-xs border rounded-lg px-3 py-1.5 focus:ring-1 focus:ring-blue-500"
        >
          <option value="ALL">Todos os Tipos (Fixas + Variáveis)</option>
          <option value="FIXA">Somente Fixas</option>
          <option value="VARIAVEL">Somente Variáveis</option>
        </select>
      </div>
    </div>

    <!-- Tabela de Despesas -->
    <div class="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
      <div v-if="loading" class="p-12 text-center text-slate-500">
        <div class="inline-block animate-spin w-8 h-8 border-4 border-rose-600 border-t-transparent rounded-full mb-3"></div>
        <p>Carregando despesas...</p>
      </div>

      <div v-else-if="filteredDespesas.length === 0" class="p-12 text-center text-slate-500 text-sm">
        Nenhuma despesa localizada com os filtros atuais.
      </div>

      <table v-else class="w-full text-left border-collapse text-xs">
        <thead class="bg-slate-50 border-b border-slate-200 text-slate-500 uppercase font-semibold">
          <tr>
            <th class="py-3 px-4">Tipo</th>
            <th class="py-3 px-4">Categoria</th>
            <th class="py-3 px-4">Descrição da Despesa</th>
            <th class="py-3 px-4">Fornecedor / Doc</th>
            <th class="py-3 px-4">Data Pagto</th>
            <th class="py-3 px-4">Comprovante</th>
            <th class="py-3 px-4 text-right">Valor (R$)</th>
            <th class="py-3 px-4 text-right" v-if="currentPeriodo?.status === 'ABERTO'">Ações</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-200">
          <tr v-for="d in filteredDespesas" :key="d.id" class="hover:bg-slate-50/80 transition-colors">
            <td class="py-3 px-4 whitespace-nowrap">
              <span
                class="px-2 py-0.5 rounded text-[11px] font-bold"
                :class="d.tipo === 'FIXA' ? 'bg-blue-100 text-blue-800' : 'bg-purple-100 text-purple-800'"
              >
                {{ d.tipo }}
              </span>
            </td>
            <td class="py-3 px-4 font-medium text-slate-700 whitespace-nowrap">
              {{ d.categoria_display || d.categoria }}
            </td>
            <td class="py-3 px-4 font-semibold text-slate-900">
              {{ d.descricao }}
            </td>
            <td class="py-3 px-4 text-slate-500 whitespace-nowrap">
              <span v-if="d.fornecedor">{{ d.fornecedor }}</span>
              <span v-if="d.numero_documento" class="text-slate-400 block text-[11px]">{{ d.numero_documento }}</span>
              <span v-if="!d.fornecedor && !d.numero_documento">-</span>
            </td>
            <td class="py-3 px-4 text-slate-600 whitespace-nowrap">
              {{ formatDate(d.data_pagamento) }}
            </td>
            <td class="py-3 px-4 whitespace-nowrap">
              <a
                v-if="d.comprovante"
                :href="d.comprovante"
                target="_blank"
                class="inline-flex items-center text-blue-600 hover:text-blue-800 font-medium"
              >
                <svg class="w-3.5 h-3.5 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                </svg>
                Anexo
              </a>
              <span v-else class="text-slate-400 text-[11px]">Sem anexo</span>
            </td>
            <td class="py-3 px-4 text-right font-bold text-slate-900 whitespace-nowrap">
              R$ {{ formatMoney(d.valor) }}
            </td>
            <td class="py-3 px-4 text-right whitespace-nowrap space-x-2" v-if="currentPeriodo?.status === 'ABERTO'">
              <button @click="openModal(d)" class="text-blue-600 hover:underline">Editar</button>
              <button @click="deleteDespesa(d)" class="text-rose-600 hover:underline">Excluir</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modal Nova / Editar Despesa -->
    <div v-if="showModal" class="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div class="bg-white rounded-xl max-w-xl w-full p-6 space-y-4 shadow-xl">
        <h3 class="font-bold text-base text-slate-800">
          {{ editingId ? 'Editar Despesa' : 'Nova Despesa' }}
        </h3>

        <form @submit.prevent="saveDespesa" class="space-y-3">
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-medium text-slate-700 mb-1">Tipo de Despesa</label>
              <select v-model="form.tipo" class="w-full text-xs border rounded-lg p-2" required>
                <option value="FIXA">Despesa Fixa</option>
                <option value="VARIAVEL">Despesa Variável</option>
              </select>
            </div>

            <div>
              <label class="block text-xs font-medium text-slate-700 mb-1">Categoria</label>
              <select v-model="form.categoria" class="w-full text-xs border rounded-lg p-2" required>
                <option value="SALARIO">Salário Funcionários</option>
                <option value="ANTECIPACAO_SALARIO">Antecipação de Salário</option>
                <option value="FERIAS">Férias</option>
                <option value="DECIMO_TERCEIRO">13º Salário</option>
                <option value="GPS">GPS / Previdência</option>
                <option value="FGTS">FGTS</option>
                <option value="ZELADOR_DIARISTA">Zelador Diarista</option>
                <option value="TRANSPORTE">Transporte Funcionários</option>
                <option value="REFEICAO">Refeições Funcionários</option>
                <option value="SINDICO">Pró-Labore Síndico</option>
                <option value="ENEL">Energia (Enel)</option>
                <option value="AGUA_CAGECE">Água / Cagece</option>
                <option value="CONTABILIDADE">Contador / Assessoria</option>
                <option value="DEDETIZACAO">Dedetização</option>
                <option value="COLETA_RESIDUOS">Coleta de Resíduos</option>
                <option value="MATERIAL_LIMPEZA">Material de Limpeza</option>
                <option value="MANUTENCAO">Manutenção / Obras</option>
                <option value="EXTRA_PORTARIA">Serviço Extra Portaria</option>
                <option value="CERTIFICADO_DIGITAL">Certificado Digital</option>
                <option value="EQUIPAMENTOS">Equipamentos e Insumos</option>
                <option value="OUTRO">Outros</option>
              </select>
            </div>
          </div>

          <div>
            <label class="block text-xs font-medium text-slate-700 mb-1">Descrição</label>
            <input
              type="text"
              v-model="form.descricao"
              required
              placeholder="Ex: REF. 10/2026 - ENEL"
              class="w-full text-xs border rounded-lg p-2"
            />
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-medium text-slate-700 mb-1">Fornecedor / Beneficiário</label>
              <input
                type="text"
                v-model="form.fornecedor"
                placeholder="Ex: Enel Ceará"
                class="w-full text-xs border rounded-lg p-2"
              />
            </div>

            <div>
              <label class="block text-xs font-medium text-slate-700 mb-1">Nº NF / Recibo / Cupom</label>
              <input
                type="text"
                v-model="form.numero_documento"
                placeholder="Ex: NF 4543"
                class="w-full text-xs border rounded-lg p-2"
              />
            </div>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-medium text-slate-700 mb-1">Valor (R$)</label>
              <input
                type="number"
                step="0.01"
                v-model="form.valor"
                required
                class="w-full text-xs border rounded-lg p-2 font-bold text-slate-800"
              />
            </div>

            <div>
              <label class="block text-xs font-medium text-slate-700 mb-1">Data de Pagamento</label>
              <input
                type="date"
                v-model="form.data_pagamento"
                required
                class="w-full text-xs border rounded-lg p-2"
              />
            </div>
          </div>

          <div>
            <label class="block text-xs font-medium text-slate-700 mb-1">Comprovante (PDF ou Imagem)</label>
            <input
              type="file"
              @change="onFileChange"
              accept=".pdf,image/*"
              class="w-full text-xs border rounded-lg p-2"
            />
          </div>

          <div class="pt-3 flex justify-end gap-2 border-t">
            <button
              type="button"
              @click="showModal = false"
              class="px-3 py-1.5 border rounded-lg text-xs"
            >
              Cancelar
            </button>
            <button
              type="submit"
              :disabled="saving"
              class="px-4 py-1.5 bg-rose-600 text-white rounded-lg text-xs font-medium hover:bg-rose-700 disabled:opacity-50"
            >
              {{ saving ? 'Salvando...' : 'Salvar Despesa' }}
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
const saving = ref(false)
const periodos = ref([])
const selectedPeriodoId = ref(null)
const currentPeriodo = ref(null)
const despesas = ref([])

const searchQuery = ref("")
const filterTipo = ref("ALL")

const showModal = ref(false)
const editingId = ref(null)
const formFile = ref(null)
const form = ref({
  tipo: "FIXA",
  categoria: "SALARIO",
  descricao: "",
  fornecedor: "",
  numero_documento: "",
  valor: 0.00,
  data_pagamento: new Date().toISOString().substring(0, 10),
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

const filteredDespesas = computed(() => {
  return despesas.value.filter(d => {
    if (filterTipo.value !== "ALL" && d.tipo !== filterTipo.value) return false
    if (searchQuery.value) {
      const q = searchQuery.value.toLowerCase()
      const desc = (d.descricao || "").toLowerCase()
      const forn = (d.fornecedor || "").toLowerCase()
      const doc = (d.numero_documento || "").toLowerCase()
      return desc.includes(q) || forn.includes(q) || doc.includes(q)
    }
    return true
  })
})

const totalFixas = computed(() => {
  return despesas.value.filter(d => d.tipo === "FIXA").reduce((acc, d) => acc + Number(d.valor || 0), 0)
})

const totalVariaveis = computed(() => {
  return despesas.value.filter(d => d.tipo === "VARIAVEL").reduce((acc, d) => acc + Number(d.valor || 0), 0)
})

const totalGeral = computed(() => {
  return totalFixas.value + totalVariaveis.value
})

const despesasFixasCount = computed(() => despesas.value.filter(d => d.tipo === "FIXA").length)
const despesasVariaveisCount = computed(() => despesas.value.filter(d => d.tipo === "VARIAVEL").length)

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

async function loadDespesas() {
  if (!selectedPeriodoId.value) return
  loading.value = true
  try {
    currentPeriodo.value = periodos.value.find(p => p.id === selectedPeriodoId.value)
    const res = await financeiroApi.getDespesas({ periodo: selectedPeriodoId.value })
    despesas.value = res.data.results || res.data
  } catch (err) {
    console.error("Erro ao carregar despesas:", err)
  } finally {
    loading.value = false
  }
}

function changePeriodo() {
  router.push(`/prestacao/despesas/${selectedPeriodoId.value}`)
  loadDespesas()
}

function onFileChange(e) {
  formFile.value = e.target.files[0] || null
}

function openModal(despesa = null) {
  formFile.value = null
  if (despesa) {
    editingId.value = despesa.id
    form.value = { ...despesa }
  } else {
    editingId.value = null
    form.value = {
      tipo: "FIXA",
      categoria: "SALARIO",
      descricao: "",
      fornecedor: "",
      numero_documento: "",
      valor: 0.00,
      data_pagamento: new Date().toISOString().substring(0, 10),
    }
  }
  showModal.value = true
}

async function saveDespesa() {
  saving.value = true
  try {
    const formData = new FormData()
    formData.append("periodo", selectedPeriodoId.value)
    formData.append("tipo", form.value.tipo)
    formData.append("categoria", form.value.categoria)
    formData.append("descricao", form.value.descricao)
    formData.append("fornecedor", form.value.fornecedor || "")
    formData.append("numero_documento", form.value.numero_documento || "")
    formData.append("valor", form.value.valor)
    formData.append("data_pagamento", form.value.data_pagamento)
    if (formFile.value) {
      formData.append("comprovante", formFile.value)
    }

    if (editingId.value) {
      await financeiroApi.updateDespesa(editingId.value, formData)
    } else {
      await financeiroApi.createDespesa(formData)
    }
    showModal.value = false
    await loadDespesas()
  } catch (err) {
    alert("Erro ao salvar despesa.")
  } finally {
    saving.value = false
  }
}

async function deleteDespesa(d) {
  if (!confirm(`Deseja remover a despesa "${d.descricao}"?`)) return
  try {
    await financeiroApi.deleteDespesa(d.id)
    await loadDespesas()
  } catch (err) {
    alert("Erro ao excluir despesa.")
  }
}

onMounted(async () => {
  await loadPeriodos()
  await loadDespesas()
})
</script>
