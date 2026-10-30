<template>
  <div class="space-y-6">
    <!-- Top Bar -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h2 class="text-xl font-bold text-slate-800">Mandatos & Cargos Condominiais</h2>
        <p class="text-xs text-slate-500">Gestão e governança: Síndicos, Subsíndicos e Conselheiros por período eleito</p>
      </div>

      <button
        v-if="authStore.canEdit"
        @click="openModal()"
        class="inline-flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-xl shadow transition"
      >
        + Novo Mandato
      </button>
    </div>

    <!-- Alert -->
    <div v-if="alertMessage" :class="alertClass" class="p-4 rounded-xl text-xs flex justify-between items-center shadow-sm">
      <span>{{ alertMessage }}</span>
      <button @click="alertMessage = ''" class="font-bold text-sm">&times;</button>
    </div>

    <!-- Search & Filter -->
    <div class="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
      <div class="w-full max-w-sm">
        <input
          v-model="searchQuery"
          @input="fetchCargos"
          type="text"
          placeholder="Buscar por membro, cargo ou condomínio..."
          class="w-full text-xs px-3 py-2 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>
      <span class="text-xs text-slate-400">Total: {{ cargos.length }} mandatos</span>
    </div>

    <!-- Table -->
    <div class="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse text-xs">
          <thead>
            <tr class="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider">
              <th class="p-4">Membro da Gestão</th>
              <th class="p-4">Cargo Condominial</th>
              <th class="p-4">Condomínio</th>
              <th class="p-4">Início do Mandato</th>
              <th class="p-4">Término do Mandato</th>
              <th class="p-4 text-center">Status</th>
              <th class="p-4 text-right">Ações</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 text-slate-700">
            <tr v-if="loading" class="text-center">
              <td colspan="7" class="p-8 text-slate-400">Carregando mandatos...</td>
            </tr>
            <tr v-else-if="cargos.length === 0" class="text-center">
              <td colspan="7" class="p-8 text-slate-400">Nenhum mandato cadastrado neste condomínio.</td>
            </tr>
            <tr v-for="item in cargos" :key="item.id" class="hover:bg-slate-50/80 transition">
              <td class="p-4 font-bold text-slate-900">
                {{ item.pessoa_nome }}
                <p class="text-[11px] font-normal text-slate-500 font-mono">{{ item.pessoa_cpf || 'Sem CPF' }}</p>
              </td>
              <td class="p-4">
                <span class="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-blue-50 text-blue-700 border border-blue-200">
                  {{ item.cargo_display }}
                </span>
              </td>
              <td class="p-4 text-slate-600">{{ item.condominio_nome }}</td>
              <td class="p-4 text-slate-600">{{ formatDate(item.data_inicio) }}</td>
              <td class="p-4 text-slate-600">{{ item.data_fim ? formatDate(item.data_fim) : 'Indeterminado' }}</td>
              <td class="p-4 text-center">
                <span :class="item.ativo ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-slate-100 text-slate-500 border-slate-200'" class="px-2 py-0.5 rounded-full border text-[11px] font-medium">
                  {{ item.ativo ? 'Mandato Vigente' : 'Encerrado' }}
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
                  @click="deleteCargo(item)"
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
            {{ isEditing ? 'Editar Mandato' : 'Novo Mandato Condominial' }}
          </h3>
          <button @click="showModal = false" class="text-slate-400 hover:text-slate-600 text-lg font-bold">&times;</button>
        </div>

        <form @submit.prevent="saveCargo" class="p-5 space-y-4 text-xs">
          <!-- Alerta de Erro DENTRO do Modal -->
          <div v-if="modalErrorMessage" class="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-start justify-between">
            <div class="flex items-start">
              <span class="mr-2 text-rose-600 font-bold shrink-0">⚠️</span>
              <span class="leading-relaxed">{{ modalErrorMessage }}</span>
            </div>
            <button type="button" @click="modalErrorMessage = ''" class="text-rose-600 hover:text-rose-800 font-bold ml-2">&times;</button>
          </div>

          <div>
            <label class="block font-medium text-slate-700 mb-1">Pessoa Eleita *</label>
            <select v-model="form.pessoa" required class="w-full px-3 py-2 border rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none">
              <option value="" disabled>Selecione a pessoa</option>
              <option v-for="p in pessoas" :key="p.id" :value="p.id">{{ p.nome }} (CPF: {{ p.cpf || 'Não inf.' }})</option>
            </select>
          </div>

          <div v-if="condominios.length > 1">
            <label class="block font-medium text-slate-700 mb-1">Condomínio *</label>
            <select v-model="form.condominio" required class="w-full px-3 py-2 border rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none">
              <option value="" disabled>Selecione o condomínio</option>
              <option v-for="c in condominios" :key="c.id" :value="c.id">{{ c.nome }}</option>
            </select>
          </div>
          <div v-else class="p-3 bg-slate-50 rounded-xl border border-slate-200">
            <span class="text-[11px] text-slate-500 block">Condomínio Vinculado:</span>
            <span class="text-xs font-bold text-slate-800">{{ condominios[0]?.nome }}</span>
          </div>

          <div>
            <label class="block font-medium text-slate-700 mb-1">Cargo *</label>
            <select v-model="form.cargo" required class="w-full px-3 py-2 border rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none">
              <option value="SINDICO">Síndico(a)</option>
              <option value="SUBSINDICO">Subsíndico(a)</option>
              <option value="CONSELHEIRO_FISCAL">Conselheiro(a) Fiscal</option>
              <option value="CONSELHEIRO_CONSULTIVO">Conselheiro(a) Consultivo</option>
              <option value="OUTRO">Outro Cargo</option>
            </select>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block font-medium text-slate-700 mb-1">Início do Mandato *</label>
              <input v-model="form.data_inicio" required type="date" class="w-full px-3 py-2 border rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none" />
            </div>
            <div>
              <label class="block font-medium text-slate-700 mb-1">Término Previsto</label>
              <input v-model="form.data_fim" type="date" class="w-full px-3 py-2 border rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none" />
            </div>
          </div>

          <div class="flex items-center space-x-2 pt-1">
            <input id="mandatoAtivo" v-model="form.ativo" type="checkbox" class="rounded border-slate-300 text-blue-600 focus:ring-blue-500" />
            <label for="mandatoAtivo" class="text-slate-700 font-medium">Mandato Vigente / Ativo</label>
          </div>

          <div class="pt-4 border-t flex justify-end space-x-2">
            <button type="button" @click="showModal = false" class="px-4 py-2 border rounded-xl text-slate-600 hover:bg-slate-50 transition">
              Cancelar
            </button>
            <button type="submit" :disabled="saving" class="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white font-medium rounded-xl transition shadow">
              {{ saving ? 'Salvando...' : 'Salvar Mandato' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue"
import apiClient from "@/api/client"
import { useAuthStore } from "@/stores/auth"

const authStore = useAuthStore()
const cargos = ref([])
const pessoas = ref([])
const condominios = ref([])
const loading = ref(false)
const saving = ref(false)
const searchQuery = ref("")
const alertMessage = ref("")
const alertClass = ref("")
const modalErrorMessage = ref("")

const showModal = ref(false)
const isEditing = ref(false)
const selectedId = ref(null)

const form = ref({
  pessoa: "",
  condominio: "",
  cargo: "SINDICO",
  data_inicio: new Date().toISOString().split("T")[0],
  data_fim: null,
  ativo: true,
})

const fetchAuxiliaryData = async () => {
  try {
    const [resPessoas, resCond] = await Promise.all([
      apiClient.get("/pessoas/"),
      apiClient.get("/condominios/"),
    ])
    pessoas.value = resPessoas.data.results || resPessoas.data
    condominios.value = resCond.data.results || resCond.data
    if (!form.value.condominio && condominios.value.length > 0) {
      form.value.condominio = condominios.value[0].id
    }
  } catch (err) {
    console.error(err)
  }
}

const fetchCargos = async () => {
  loading.value = true
  try {
    const res = await apiClient.get("/cargos-condominiais/", {
      params: { search: searchQuery.value },
    })
    cargos.value = res.data.results || res.data
  } catch (err) {
    showAlert("Erro ao carregar mandatos.", "error")
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
    const defaultCondoId = (authStore.activeCondominioId && condominios.value.some(c => String(c.id) === String(authStore.activeCondominioId)))
      ? Number(authStore.activeCondominioId)
      : (condominios.value[0]?.id || "")

    form.value = {
      pessoa: pessoas.value[0]?.id || "",
      condominio: defaultCondoId,
      cargo: "SINDICO",
      data_inicio: new Date().toISOString().split("T")[0],
      data_fim: null,
      ativo: true,
    }
  }
  showModal.value = true
}

const saveCargo = async () => {
  saving.value = true
  modalErrorMessage.value = ""
  try {
    if (isEditing.value) {
      await apiClient.put(`/cargos-condominiais/${selectedId.value}/`, form.value)
      showAlert("Mandato atualizado com sucesso!")
    } else {
      await apiClient.post("/cargos-condominiais/", form.value)
      showAlert("Mandato registrado com sucesso!")
    }
    showModal.value = false
    fetchCargos()
  } catch (err) {
    const errorDetails = err.response?.data
    let msg = "Erro ao salvar mandato."
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

const deleteCargo = async (item) => {
  if (!confirm(`Tem certeza que deseja excluir o mandato de "${item.pessoa_nome}"?`)) return
  try {
    await apiClient.delete(`/cargos-condominiais/${item.id}/`)
    showAlert("Mandato excluído com sucesso!")
    fetchCargos()
  } catch (err) {
    showAlert("Erro ao excluir mandato.", "error")
  }
}

onMounted(async () => {
  await fetchAuxiliaryData()
  await fetchCargos()
})
</script>
