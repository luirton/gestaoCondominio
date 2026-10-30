<template>
  <div class="space-y-6">
    <!-- Top Bar -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h2 class="text-xl font-bold text-slate-800">Condomínios</h2>
        <p class="text-xs text-slate-500">Visualização dos dados dos condomínios sob sua gestão</p>
      </div>

      <div class="p-2.5 px-3 bg-amber-50 rounded-xl border border-amber-200 text-amber-800 text-xs flex items-center">
        <span class="mr-1.5 font-bold">ℹ️</span>
        <span>O cadastro e gerenciamento global de novos condomínios é restrito ao <strong>Super Painel</strong>.</span>
      </div>
    </div>

    <!-- Page Feedback Message -->
    <div v-if="alertMessage" :class="alertClass" class="p-4 rounded-xl text-xs flex justify-between items-center shadow-sm">
      <span>{{ alertMessage }}</span>
      <button @click="alertMessage = ''" class="font-bold text-sm">&times;</button>
    </div>

    <!-- Search Input -->
    <div class="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
      <div class="w-full max-w-sm">
        <input
          v-model="searchQuery"
          @input="fetchCondominios"
          type="text"
          placeholder="Buscar por nome, CNPJ ou cidade..."
          class="w-full text-xs px-3 py-2 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>
      <span class="text-xs text-slate-400">Total: {{ condominios.length }} condomínios</span>
    </div>

    <!-- Table -->
    <div class="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse text-xs">
          <thead>
            <tr class="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider">
              <th class="p-4">Nome</th>
              <th class="p-4">CNPJ</th>
              <th class="p-4">Endereço</th>
              <th class="p-4">Cidade/UF</th>
              <th class="p-4 text-center">Unidades</th>
              <th class="p-4 text-center">Status</th>
              <th class="p-4 text-right">Ações</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 text-slate-700">
            <tr v-if="loading" class="text-center">
              <td colspan="7" class="p-8 text-slate-400">Carregando condomínios...</td>
            </tr>
            <tr v-else-if="condominios.length === 0" class="text-center">
              <td colspan="7" class="p-8 text-slate-400">Nenhum condomínio encontrado.</td>
            </tr>
            <tr v-for="item in condominios" :key="item.id" class="hover:bg-slate-50/80 transition">
              <td class="p-4 font-semibold text-slate-900">{{ item.nome }}</td>
              <td class="p-4 font-mono text-slate-600">{{ item.cnpj || '—' }}</td>
              <td class="p-4 text-slate-600">{{ item.endereco }}, {{ item.numero || 'S/N' }}</td>
              <td class="p-4 text-slate-600">{{ item.cidade }}/{{ item.uf }}</td>
              <td class="p-4 text-center">
                <span class="px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 font-medium">
                  {{ item.total_unidades }}
                </span>
              </td>
              <td class="p-4 text-center">
                <span :class="item.ativo ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-rose-50 text-rose-700 border-rose-200'" class="px-2 py-0.5 rounded-full border text-[11px] font-medium">
                  {{ item.ativo ? 'Ativo' : 'Inativo' }}
                </span>
              </td>
              <td class="p-4 text-right space-x-2">
                <button
                  @click="openModal(item)"
                  class="px-2.5 py-1 text-slate-700 hover:bg-slate-100 border border-slate-300 rounded-lg transition"
                >
                  Ver Detalhes
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Modal Form (z-50 com mensagem de erro DENTRO do popup) -->
    <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4">
      <div class="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-lg overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        <div class="p-5 border-b border-slate-100 flex items-center justify-between bg-slate-50">
          <h3 class="font-bold text-sm text-slate-800">
            {{ isEditing ? 'Editar Condomínio' : 'Novo Condomínio' }}
          </h3>
          <button @click="showModal = false" class="text-slate-400 hover:text-slate-600 text-lg font-bold">&times;</button>
        </div>

        <form @submit.prevent="saveCondominio" class="p-5 space-y-4 text-xs">
          <!-- Alerta de Erro DENTRO do Modal -->
          <div v-if="modalErrorMessage" class="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-start justify-between">
            <div class="flex items-start">
              <span class="mr-2 text-rose-600 font-bold shrink-0">⚠️</span>
              <span class="leading-relaxed">{{ modalErrorMessage }}</span>
            </div>
            <button type="button" @click="modalErrorMessage = ''" class="text-rose-600 hover:text-rose-800 font-bold ml-2">&times;</button>
          </div>

          <div>
            <label class="block font-medium text-slate-700 mb-1">Nome do Condomínio *</label>
            <input v-model="form.nome" required type="text" placeholder="Ex: Condomínio Residencial Jardins" class="w-full px-3 py-2 border rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none" />
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block font-medium text-slate-700 mb-1">CNPJ</label>
              <input
                v-model="form.cnpj"
                @input="form.cnpj = maskCNPJ(form.cnpj)"
                placeholder="00.000.000/0000-00"
                maxlength="18"
                type="text"
                class="w-full px-3 py-2 border rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none font-mono"
              />
            </div>
            <div>
              <label class="block font-medium text-slate-700 mb-1">CEP</label>
              <input
                v-model="form.cep"
                @input="form.cep = maskCEP(form.cep)"
                placeholder="00000-000"
                maxlength="9"
                type="text"
                class="w-full px-3 py-2 border rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none font-mono"
              />
            </div>
          </div>

          <div class="grid grid-cols-3 gap-3">
            <div class="col-span-2">
              <label class="block font-medium text-slate-700 mb-1">Endereço / Logradouro *</label>
              <input v-model="form.endereco" required type="text" placeholder="Rua, Avenida..." class="w-full px-3 py-2 border rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none" />
            </div>
            <div>
              <label class="block font-medium text-slate-700 mb-1">Número</label>
              <input v-model="form.numero" type="text" placeholder="100" class="w-full px-3 py-2 border rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none" />
            </div>
          </div>

          <div class="grid grid-cols-3 gap-3">
            <div>
              <label class="block font-medium text-slate-700 mb-1">Complemento</label>
              <input v-model="form.complemento" type="text" placeholder="Bloco A, etc." class="w-full px-3 py-2 border rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none" />
            </div>
            <div>
              <label class="block font-medium text-slate-700 mb-1">Cidade</label>
              <input v-model="form.cidade" type="text" class="w-full px-3 py-2 border rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none" />
            </div>
            <div>
              <label class="block font-medium text-slate-700 mb-1">UF</label>
              <input v-model="form.uf" maxlength="2" type="text" class="w-full px-3 py-2 border rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none uppercase" />
            </div>
          </div>

          <div class="flex items-center space-x-2 pt-2">
            <input id="ativo" v-model="form.ativo" type="checkbox" class="rounded border-slate-300 text-blue-600 focus:ring-blue-500" />
            <label for="ativo" class="text-slate-700 font-medium">Condomínio Ativo</label>
          </div>

          <div class="pt-4 border-t flex justify-end space-x-2">
            <button type="button" @click="showModal = false" class="px-4 py-2 border rounded-xl text-slate-600 hover:bg-slate-50 transition">
              Fechar
            </button>
            <button v-if="authStore.user?.is_superuser" type="submit" :disabled="saving" class="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white font-medium rounded-xl transition shadow">
              {{ saving ? 'Salvando...' : 'Salvar Alterações' }}
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
import { maskCNPJ, maskCEP } from "@/utils/masks"

const authStore = useAuthStore()
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
  nome: "",
  cnpj: "",
  endereco: "",
  numero: "",
  complemento: "",
  bairro: "",
  cidade: "São Paulo",
  uf: "SP",
  cep: "",
  ativo: true,
})

const fetchCondominios = async () => {
  loading.value = true
  try {
    const res = await apiClient.get("/condominios/", {
      params: { search: searchQuery.value },
    })
    condominios.value = res.data.results || res.data
  } catch (err) {
    showAlert("Erro ao carregar condomínios.", "error")
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
    form.value = {
      ...item,
      cnpj: maskCNPJ(item.cnpj || ""),
      cep: maskCEP(item.cep || ""),
    }
  } else {
    isEditing.value = false
    selectedId.value = null
    form.value = {
      nome: "",
      cnpj: "",
      endereco: "",
      numero: "",
      complemento: "",
      bairro: "",
      cidade: "São Paulo",
      uf: "SP",
      cep: "",
      ativo: true,
    }
  }
  showModal.value = true
}

const saveCondominio = async () => {
  saving.value = true
  modalErrorMessage.value = ""
  try {
    const payload = { ...form.value }
    if (!payload.cnpj) payload.cnpj = null

    if (isEditing.value) {
      await apiClient.put(`/condominios/${selectedId.value}/`, payload)
      showAlert("Condomínio atualizado com sucesso!")
    } else {
      await apiClient.post("/condominios/", payload)
      showAlert("Condomínio cadastrado com sucesso!")
    }
    showModal.value = false
    fetchCondominios()
  } catch (err) {
    const errorDetails = err.response?.data
    let msg = "Erro ao salvar condomínio."
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

const deleteCondominio = async (item) => {
  if (!confirm(`Tem certeza que deseja excluir o condomínio "${item.nome}"?`)) return
  try {
    await apiClient.delete(`/condominios/${item.id}/`)
    showAlert("Condomínio excluído com sucesso!")
    fetchCondominios()
  } catch (err) {
    showAlert("Erro ao excluir condomínio. Apenas Síndico pode realizar exclusões.", "error")
  }
}

onMounted(() => {
  fetchCondominios()
})
</script>
