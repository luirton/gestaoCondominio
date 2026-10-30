<template>
  <div class="space-y-6">
    <!-- Top Bar -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h2 class="text-xl font-bold text-slate-800">Vínculos Pessoa-Unidade</h2>
        <p class="text-xs text-slate-500">Histórico de proprietários, inquilinos, moradores e responsável legal/financeiro</p>
      </div>

      <button
        v-if="authStore.canEdit"
        @click="openModal()"
        class="inline-flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-xl shadow transition"
      >
        + Novo Vínculo com Unidade
      </button>
    </div>

    <!-- Alert -->
    <div v-if="alertMessage" :class="alertClass" class="p-4 rounded-xl text-xs flex justify-between items-center shadow-sm">
      <span>{{ alertMessage }}</span>
      <button @click="alertMessage = ''" class="font-bold text-sm">&times;</button>
    </div>

    <!-- Filters & Search -->
    <div class="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-3">
      <div class="flex flex-wrap items-center gap-3 w-full sm:w-auto">
        <input
          v-model="searchQuery"
          @input="fetchVinculos"
          type="text"
          placeholder="Buscar por morador ou unidade..."
          class="text-xs px-3 py-2 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 w-64"
        />

        <label class="flex items-center space-x-2 text-xs text-slate-700 cursor-pointer">
          <input
            v-model="filterApenasAtivos"
            @change="fetchVinculos"
            type="checkbox"
            class="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
          />
          <span>Exibir apenas vínculos ativos</span>
        </label>
      </div>
      <span class="text-xs text-slate-400">Total: {{ vinculos.length }} registros</span>
    </div>

    <!-- Table -->
    <div class="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse text-xs">
          <thead>
            <tr class="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider">
              <th class="p-4">Pessoa / Morador</th>
              <th class="p-4">Unidade</th>
              <th class="p-4">Condomínio</th>
              <th class="p-4">Tipo de Vínculo</th>
              <th class="p-4">Período</th>
              <th class="p-4 text-center">Responsável Legal</th>
              <th class="p-4 text-center">Status</th>
              <th class="p-4 text-right">Ações</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 text-slate-700">
            <tr v-if="loading" class="text-center">
              <td colspan="8" class="p-8 text-slate-400">Carregando vínculos...</td>
            </tr>
            <tr v-else-if="vinculos.length === 0" class="text-center">
              <td colspan="8" class="p-8 text-slate-400">Nenhum vínculo registrado neste condomínio.</td>
            </tr>
            <tr v-for="item in vinculos" :key="item.id" class="hover:bg-slate-50/80 transition">
              <td class="p-4 font-bold text-slate-900">{{ item.pessoa_nome }}</td>
              <td class="p-4 text-blue-600 font-bold">
                {{ item.unidade_identificador }}
                <span v-if="item.unidade_bloco" class="text-slate-500 font-normal">({{ item.unidade_bloco }})</span>
              </td>
              <td class="p-4 text-slate-600">{{ item.condominio_nome }}</td>
              <td class="p-4">
                <span class="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-slate-100 text-slate-700">
                  {{ item.tipo_display }}
                </span>
              </td>
              <td class="p-4 text-slate-600">
                {{ formatDate(item.data_inicio) }} → {{ item.data_fim ? formatDate(item.data_fim) : 'Atual' }}
              </td>
              <td class="p-4 text-center">
                <span
                  v-if="item.responsavel"
                  class="px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-200 font-bold text-[11px]"
                >
                  ★ Sim
                </span>
                <span v-else class="text-slate-400 text-[11px]">Não</span>
              </td>
              <td class="p-4 text-center">
                <span
                  :class="!item.data_fim ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-slate-100 text-slate-500 border-slate-200'"
                  class="px-2 py-0.5 rounded-full border text-[11px] font-medium"
                >
                  {{ !item.data_fim ? 'Ativo' : 'Encerrado (Histórico)' }}
                </span>
              </td>
              <td class="p-4 text-right space-x-2">
                <button
                  v-if="authStore.canEdit"
                  @click="openModal(item)"
                  class="px-2.5 py-1 text-slate-700 hover:bg-slate-100 border border-slate-300 rounded-lg transition"
                >
                  Editar
                </button>
                <button
                  v-if="authStore.canDelete"
                  @click="deleteVinculo(item)"
                  class="px-2.5 py-1 text-rose-600 hover:bg-rose-50 border border-rose-200 rounded-lg transition"
                >
                  Excluir
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Modal Form (z-50 com mensagem de erro DENTRO do popup) -->
    <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4">
      <div class="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-md overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        <div class="p-5 border-b border-slate-100 flex items-center justify-between bg-slate-50">
          <h3 class="font-bold text-sm text-slate-800">
            {{ isEditing ? 'Editar Vínculo' : 'Novo Vínculo com Unidade' }}
          </h3>
          <button @click="showModal = false" class="text-slate-400 hover:text-slate-600 text-lg font-bold">&times;</button>
        </div>

        <form @submit.prevent="saveVinculo" class="p-5 space-y-4 text-xs">
          <!-- Alerta de Erro DENTRO do Modal -->
          <div v-if="modalErrorMessage" class="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-start justify-between">
            <div class="flex items-start">
              <span class="mr-2 text-rose-600 font-bold shrink-0">⚠️</span>
              <span class="leading-relaxed">{{ modalErrorMessage }}</span>
            </div>
            <button type="button" @click="modalErrorMessage = ''" class="text-rose-600 hover:text-rose-800 font-bold ml-2">&times;</button>
          </div>

          <div>
            <label class="block font-medium text-slate-700 mb-1">Pessoa / Morador *</label>
            <select v-model="form.pessoa" required class="w-full px-3 py-2 border rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none">
              <option value="" disabled>Selecione a pessoa</option>
              <option v-for="p in pessoas" :key="p.id" :value="p.id">{{ p.nome }} (CPF: {{ p.cpf || 'Não inf.' }})</option>
            </select>
          </div>

          <div>
            <div class="flex items-center justify-between mb-1">
              <label class="font-medium text-slate-700">Unidade *</label>
              <input
                v-model="filtroBuscaUnidade"
                type="text"
                placeholder="Filtrar unidades..."
                class="px-2 py-0.5 text-[11px] border rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-500 w-36"
              />
            </div>
            <select v-model="form.unidade" required class="w-full px-3 py-2 border rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none">
              <option value="" disabled>Selecione a unidade</option>
              <option v-for="u in unidadesFiltradas" :key="u.id" :value="u.id">
                {{ u.identificador }} {{ u.bloco_torre ? '- Bloco ' + u.bloco_torre : '' }} ({{ u.condominio_nome }})
              </option>
            </select>
            <p class="text-[10px] text-slate-400 mt-1">Exibindo {{ unidadesFiltradas.length }} de {{ unidades.length }} unidades encontradas.</p>
          </div>

          <div>
            <label class="block font-medium text-slate-700 mb-1">Tipo de Vínculo *</label>
            <select v-model="form.tipo" required class="w-full px-3 py-2 border rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none">
              <option value="PROPRIETARIO">Proprietário</option>
              <option value="INQUILINO">Inquilino</option>
              <option value="MORADOR">Morador / Dependente</option>
              <option value="OUTRO">Outro</option>
            </select>
          </div>

          <div v-if="form.tipo === 'OUTRO'">
            <label class="block font-medium text-slate-700 mb-1">Descrição do Vínculo *</label>
            <input v-model="form.descricao_outro" required placeholder="Ex: Procurador, Administrador judicial..." type="text" class="w-full px-3 py-2 border rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none" />
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block font-medium text-slate-700 mb-1">Data Início *</label>
              <input v-model="form.data_inicio" required type="date" class="w-full px-3 py-2 border rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none" />
            </div>
            <div>
              <label class="block font-medium text-slate-700 mb-1">Data Fim (em branco se ativo)</label>
              <input v-model="form.data_fim" type="date" class="w-full px-3 py-2 border rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none" />
            </div>
          </div>

          <div class="p-3 bg-amber-50 rounded-xl border border-amber-200">
            <label class="flex items-center space-x-2 cursor-pointer">
              <input v-model="form.responsavel" type="checkbox" class="rounded border-amber-400 text-amber-600 focus:ring-amber-500" />
              <span class="font-bold text-amber-900">Responsável Financeiro / Legal pela Unidade</span>
            </label>
            <p class="text-[10px] text-amber-800 mt-1">
              Habilita esta pessoa a receber os boletos e notificações emitidas para esta unidade. (Permitido apenas 1 responsável ativo por unidade).
            </p>
          </div>

          <div class="pt-4 border-t flex justify-end space-x-2">
            <button type="button" @click="showModal = false" class="px-4 py-2 border rounded-xl text-slate-600 hover:bg-slate-50 transition">
              Cancelar
            </button>
            <button type="submit" :disabled="saving" class="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white font-medium rounded-xl transition shadow">
              {{ saving ? 'Salvando...' : 'Salvar Vínculo' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import apiClient from "@/api/client"
import { useAuthStore } from "@/stores/auth"

const authStore = useAuthStore()
const vinculos = ref([])
const pessoas = ref([])
const unidades = ref([])
const loading = ref(false)
const saving = ref(false)
const searchQuery = ref("")
const filtroBuscaUnidade = ref("")
const filterApenasAtivos = ref(false)
const alertMessage = ref("")
const alertClass = ref("")
const modalErrorMessage = ref("")

const unidadesFiltradas = computed(() => {
  if (!filtroBuscaUnidade.value.trim()) return unidades.value
  const termo = filtroBuscaUnidade.value.toLowerCase()
  return unidades.value.filter(u => 
    (u.identificador && u.identificador.toLowerCase().includes(termo)) ||
    (u.bloco_torre && u.bloco_torre.toLowerCase().includes(termo))
  )
})

const showModal = ref(false)
const isEditing = ref(false)
const selectedId = ref(null)

const form = ref({
  pessoa: "",
  unidade: "",
  tipo: "MORADOR",
  data_inicio: new Date().toISOString().split("T")[0],
  data_fim: null,
  responsavel: false,
  descricao_outro: "",
})

const fetchAuxiliaryData = async () => {
  try {
    const [resPessoas, resUnidades] = await Promise.all([
      apiClient.get("/pessoas/"),
      apiClient.get("/unidades/"),
    ])
    pessoas.value = resPessoas.data.results || resPessoas.data
    unidades.value = resUnidades.data.results || resUnidades.data
  } catch (err) {
    console.error(err)
  }
}

const fetchVinculos = async () => {
  loading.value = true
  try {
    const params = { search: searchQuery.value }
    if (filterApenasAtivos.value) {
      params.ativos = "true"
    }
    const res = await apiClient.get("/vinculos-unidade/", { params })
    vinculos.value = res.data.results || res.data
  } catch (err) {
    showAlert("Erro ao carregar vínculos.", "error")
  } finally {
    loading.value = false
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return ""
  const parts = dateStr.split("-")
  if (parts.length === 3) return `${parts[2]}/${parts[1]}/${parts[0]}`
  return dateStr
}

const showAlert = (msg, type = "success") => {
  alertMessage.value = msg
  alertClass.value = type === "success" ? "bg-emerald-50 text-emerald-800 border border-emerald-200" : "bg-rose-50 text-rose-800 border border-rose-200"
  setTimeout(() => (alertMessage.value = ""), 4000)
}

const openModal = (item = null) => {
  modalErrorMessage.value = ""
  if (item) {
    isEditing.value = true
    selectedId.value = item.id
    form.value = { ...item }
  } else {
    isEditing.value = false
    selectedId.value = null
    form.value = {
      pessoa: pessoas.value[0]?.id || "",
      unidade: unidades.value[0]?.id || "",
      tipo: "MORADOR",
      data_inicio: new Date().toISOString().split("T")[0],
      data_fim: null,
      responsavel: false,
      descricao_outro: "",
    }
  }
  showModal.value = true
}

const saveVinculo = async () => {
  saving.value = true
  modalErrorMessage.value = ""
  try {
    if (isEditing.value) {
      await apiClient.put(`/vinculos-unidade/${selectedId.value}/`, form.value)
      showAlert("Vínculo atualizado com sucesso!")
    } else {
      await apiClient.post("/vinculos-unidade/", form.value)
      showAlert("Vínculo registrado com sucesso!")
    }
    showModal.value = false
    fetchVinculos()
  } catch (err) {
    const errorDetails = err.response?.data
    let msg = "Erro ao salvar vínculo."
    if (errorDetails && typeof errorDetails === "object") {
      msg = Object.entries(errorDetails)
        .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(", ") : v}`)
        .join(" | ")
    }
    modalErrorMessage.value = msg
  } finally {
    saving.value = false
  }
}

const deleteVinculo = async (item) => {
  if (!confirm(`Tem certeza que deseja excluir o vínculo de "${item.pessoa_nome}"?`)) return
  try {
    await apiClient.delete(`/vinculos-unidade/${item.id}/`)
    showAlert("Vínculo excluído com sucesso!")
    fetchVinculos()
  } catch (err) {
    showAlert("Erro ao excluir vínculo.", "error")
  }
}

onMounted(async () => {
  await fetchAuxiliaryData()
  await fetchVinculos()
})
</script>
