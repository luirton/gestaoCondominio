<template>
  <div class="space-y-6">
    <!-- Top Bar -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h2 class="text-xl font-bold text-slate-800">Unidades Habitacionais</h2>
        <p class="text-xs text-slate-500">Gestão de apartamentos, frações ideais e moradores do condomínio ativo</p>
      </div>

      <button
        v-if="authStore.canEdit"
        @click="openModal()"
        class="inline-flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-xl shadow transition"
      >
        + Nova Unidade
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
          @input="fetchUnidades"
          type="text"
          placeholder="Buscar por unidade (ex: 101, Apto)..."
          class="text-xs px-3 py-2 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 w-64"
        />

        <select
          v-if="condominios.length > 1"
          v-model="selectedCondominioFilter"
          @change="fetchUnidades"
          class="text-xs px-3 py-2 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">Todos os Meus Condomínios</option>
          <option v-for="c in condominios" :key="c.id" :value="c.id">{{ c.nome }}</option>
        </select>
      </div>
      <span class="text-xs text-slate-400">Total: {{ unidades.length }} unidades</span>
    </div>

    <!-- Table -->
    <div class="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse text-xs">
          <thead>
            <tr class="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider">
              <th class="p-4">Identificador</th>
              <th class="p-4">Bloco / Torre</th>
              <th class="p-4">Condomínio</th>
              <th class="p-4">Moradores / Responsável</th>
              <th class="p-4 text-right">Ações</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 text-slate-700">
            <tr v-if="loading" class="text-center">
              <td colspan="5" class="p-8 text-slate-400">Carregando unidades...</td>
            </tr>
            <tr v-else-if="unidades.length === 0" class="text-center">
              <td colspan="5" class="p-8 text-slate-400">Nenhuma unidade cadastrada neste condomínio.</td>
            </tr>
            <tr v-for="item in unidades" :key="item.id" class="hover:bg-slate-50/80 transition">
              <td class="p-4 font-bold text-slate-900">{{ item.identificador }}</td>
              <td class="p-4 text-slate-600 font-medium">{{ item.bloco_torre || '—' }}</td>
              <td class="p-4 text-slate-600">{{ item.condominio_nome }}</td>
              <td class="p-4">
                <div v-if="item.moradores_ativos?.length > 0" class="space-y-1">
                  <div
                    v-for="m in item.moradores_ativos"
                    :key="m.id"
                    class="inline-flex items-center gap-1.5 mr-2 px-2 py-0.5 rounded-md text-[11px] bg-slate-100 text-slate-800"
                  >
                    <span>{{ m.pessoa_nome }} ({{ m.tipo }})</span>
                    <span v-if="m.responsavel" class="px-1 py-0.2 rounded bg-amber-100 text-amber-800 font-bold text-[10px]">
                      Responsável
                    </span>
                  </div>
                </div>
                <span v-else class="text-slate-400 italic">Desocupada / Sem vínculo</span>
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
                  @click="deleteUnidade(item)"
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
            {{ isEditing ? 'Editar Unidade' : 'Nova Unidade' }}
          </h3>
          <button @click="showModal = false" class="text-slate-400 hover:text-slate-600 text-lg font-bold">&times;</button>
        </div>

        <form @submit.prevent="saveUnidade" class="p-5 space-y-4 text-xs">
          <!-- Alerta de Erro DENTRO do Modal -->
          <div v-if="modalErrorMessage" class="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-start justify-between">
            <div class="flex items-start">
              <span class="mr-2 text-rose-600 font-bold shrink-0">⚠️</span>
              <span class="leading-relaxed">{{ modalErrorMessage }}</span>
            </div>
            <button type="button" @click="modalErrorMessage = ''" class="text-rose-600 hover:text-rose-800 font-bold ml-2">&times;</button>
          </div>

          <div v-if="condominios.length > 1">
            <label class="block font-medium text-slate-700 mb-1">Condomínio *</label>
            <select v-model="form.condominio" required class="w-full px-3 py-2 border rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none">
              <option value="" disabled>Selecione um condomínio</option>
              <option v-for="c in condominios" :key="c.id" :value="c.id">{{ c.nome }}</option>
            </select>
          </div>
          <div v-else class="p-3 bg-slate-50 rounded-xl border border-slate-200">
            <span class="text-[11px] text-slate-500 block">Condomínio Vinculado:</span>
            <span class="text-xs font-bold text-slate-800">{{ condominios[0]?.nome }}</span>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block font-medium text-slate-700 mb-1">Identificador (Ex: 101, Apto 101) *</label>
              <input v-model="form.identificador" required type="text" class="w-full px-3 py-2 border rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none uppercase" />
            </div>
            <div>
              <label class="block font-medium text-slate-700 mb-1">Bloco / Torre</label>
              <input v-model="form.bloco_torre" placeholder="Ex: Torre A" type="text" class="w-full px-3 py-2 border rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none uppercase" />
            </div>
          </div>

          <div>
            <label class="block font-medium text-slate-700 mb-1">Observações</label>
            <textarea v-model="form.observacoes" rows="2" class="w-full px-3 py-2 border rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none" placeholder="Vagas de garagem, sol, reformas..."></textarea>
          </div>

          <div class="pt-4 border-t flex justify-end space-x-2">
            <button type="button" @click="showModal = false" class="px-4 py-2 border rounded-xl text-slate-600 hover:bg-slate-50 transition">
              Cancelar
            </button>
            <button type="submit" :disabled="saving" class="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white font-medium rounded-xl transition shadow">
              {{ saving ? 'Salvando...' : 'Salvar Unidade' }}
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
const unidades = ref([])
const condominios = ref([])
const loading = ref(false)
const saving = ref(false)
const searchQuery = ref("")
const selectedCondominioFilter = ref("")
const alertMessage = ref("")
const alertClass = ref("")
const modalErrorMessage = ref("")

const showModal = ref(false)
const isEditing = ref(false)
const selectedId = ref(null)

const form = ref({
  condominio: "",
  identificador: "",
  bloco_torre: "",
  fracao_ideal: null,
  area_privativa: null,
  observacoes: "",
})

const fetchCondominios = async () => {
  try {
    const res = await apiClient.get("/condominios/")
    condominios.value = res.data.results || res.data
    if (!form.value.condominio && condominios.value.length > 0) {
      form.value.condominio = condominios.value[0].id
    }
  } catch (err) {
    console.error(err)
  }
}

const fetchUnidades = async () => {
  loading.value = true
  try {
    const params = { search: searchQuery.value }
    if (selectedCondominioFilter.value) {
      params.condominio = selectedCondominioFilter.value
    }
    const res = await apiClient.get("/unidades/", { params })
    unidades.value = res.data.results || res.data
  } catch (err) {
    showAlert("Erro ao carregar unidades.", "error")
  } finally {
    loading.value = false
  }
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
      condominio: defaultCondoId,
      identificador: "",
      bloco_torre: "",
      fracao_ideal: null,
      area_privativa: null,
      observacoes: "",
    }
  }
  showModal.value = true
}

const saveUnidade = async () => {
  saving.value = true
  modalErrorMessage.value = ""
  try {
    if (isEditing.value) {
      await apiClient.put(`/unidades/${selectedId.value}/`, form.value)
      showAlert("Unidade atualizada com sucesso!")
    } else {
      await apiClient.post("/unidades/", form.value)
      showAlert("Unidade cadastrada com sucesso!")
    }
    showModal.value = false
    fetchUnidades()
  } catch (err) {
    const errorDetails = err.response?.data
    let msg = "Erro ao salvar unidade."
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

const deleteUnidade = async (item) => {
  if (!confirm(`Tem certeza que deseja excluir a unidade "${item.identificador}"?`)) return
  try {
    await apiClient.delete(`/unidades/${item.id}/`)
    showAlert("Unidade excluída com sucesso!")
    fetchUnidades()
  } catch (err) {
    showAlert("Erro ao excluir unidade.", "error")
  }
}

onMounted(async () => {
  await fetchCondominios()
  await fetchUnidades()
})
</script>
