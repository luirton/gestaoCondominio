<template>
  <div class="space-y-6">
    <!-- Top Bar -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h2 class="text-xl font-bold text-slate-800">Cadastro de Pessoas</h2>
        <p class="text-xs text-slate-500">Dados civis de moradores, proprietários e colaboradores do seu condomínio</p>
      </div>

      <button
        v-if="authStore.canEdit"
        @click="openModal()"
        class="inline-flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-xl shadow transition"
      >
        + Cadastrar Pessoa
      </button>
    </div>

    <!-- Alert -->
    <div v-if="alertMessage" :class="alertClass" class="p-4 rounded-xl text-xs flex justify-between items-center shadow-sm">
      <span>{{ alertMessage }}</span>
      <button @click="alertMessage = ''" class="font-bold text-sm">&times;</button>
    </div>

    <!-- Search Input -->
    <div class="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
      <div class="w-full max-w-sm">
        <input
          v-model="searchQuery"
          @input="fetchPessoas"
          type="text"
          placeholder="Buscar por nome, CPF ou e-mail..."
          class="w-full text-xs px-3 py-2 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>
      <span class="text-xs text-slate-400">Total: {{ pessoas.length }} pessoas cadastradas</span>
    </div>

    <!-- Table -->
    <div class="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse text-xs">
          <thead>
            <tr class="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider">
              <th class="p-4">Nome Completo</th>
              <th class="p-4">CPF</th>
              <th class="p-4">Telefone</th>
              <th class="p-4">E-mail</th>
              <th class="p-4 text-center">Acesso ao Sistema</th>
              <th class="p-4 text-right">Ações</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 text-slate-700">
            <tr v-if="loading" class="text-center">
              <td colspan="6" class="p-8 text-slate-400">Carregando pessoas...</td>
            </tr>
            <tr v-else-if="pessoas.length === 0" class="text-center">
              <td colspan="6" class="p-8 text-slate-400">Nenhuma pessoa encontrada neste condomínio.</td>
            </tr>
            <tr v-for="item in pessoas" :key="item.id" class="hover:bg-slate-50/80 transition">
              <td class="p-4 font-semibold text-slate-900">{{ item.nome }}</td>
              <td class="p-4 font-mono text-slate-600">{{ item.cpf || '—' }}</td>
              <td class="p-4 text-slate-600">{{ item.telefone || '—' }}</td>
              <td class="p-4 text-slate-600">{{ item.email || '—' }}</td>
              <td class="p-4 text-center">
                <span
                  v-if="item.tem_usuario"
                  class="px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 text-[11px] font-medium"
                >
                  ✓ Usuário Ativo
                </span>
                <span
                  v-else
                  class="px-2 py-0.5 rounded-full bg-slate-100 text-slate-500 text-[11px]"
                >
                  Sem Login (Apenas Civil)
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
                  @click="deletePessoa(item)"
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
            {{ isEditing ? 'Editar Dados da Pessoa' : 'Nova Pessoa' }}
          </h3>
          <button @click="showModal = false" class="text-slate-400 hover:text-slate-600 text-lg font-bold">&times;</button>
        </div>

        <form @submit.prevent="savePessoa" class="p-5 space-y-4 text-xs">
          <!-- Alerta de Erro DENTRO do Modal -->
          <div v-if="modalErrorMessage" class="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-start justify-between">
            <div class="flex items-start">
              <span class="mr-2 text-rose-600 font-bold shrink-0">⚠️</span>
              <span class="leading-relaxed">{{ modalErrorMessage }}</span>
            </div>
            <button type="button" @click="modalErrorMessage = ''" class="text-rose-600 hover:text-rose-800 font-bold ml-2">&times;</button>
          </div>

          <div>
            <label class="block font-medium text-slate-700 mb-1">Nome Completo *</label>
            <input v-model="form.nome" required type="text" placeholder="Nome completo" class="w-full px-3 py-2 border rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none" />
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block font-medium text-slate-700 mb-1">CPF (com máscara)</label>
              <input
                v-model="form.cpf"
                @input="form.cpf = maskCPF(form.cpf)"
                placeholder="000.000.000-00"
                maxlength="14"
                type="text"
                class="w-full px-3 py-2 border rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none font-mono"
              />
            </div>
            <div>
              <label class="block font-medium text-slate-700 mb-1">Telefone / WhatsApp</label>
              <input
                v-model="form.telefone"
                @input="form.telefone = maskPhone(form.telefone)"
                placeholder="(11) 99999-9999"
                maxlength="15"
                type="text"
                class="w-full px-3 py-2 border rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none font-mono"
              />
            </div>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block font-medium text-slate-700 mb-1">E-mail</label>
              <input v-model="form.email" placeholder="email@exemplo.com" type="email" class="w-full px-3 py-2 border rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none" />
            </div>
            <div>
              <label class="block font-medium text-slate-700 mb-1">Data de Nascimento</label>
              <input v-model="form.data_nascimento" type="date" class="w-full px-3 py-2 border rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none" />
            </div>
          </div>

          <!-- Vínculo OBRIGATÓRIO com Unidade do Condomínio do Síndico -->
          <div v-if="!isEditing" class="p-3 bg-blue-50/70 rounded-xl border border-blue-200 space-y-2.5">
            <div class="flex items-center justify-between">
              <span class="font-bold text-blue-900 text-xs">Unidade do Condomínio (Obrigatório) *</span>
              <span class="text-[10px] text-blue-700 bg-blue-100 px-2 py-0.5 rounded-full font-bold">Obrigatório</span>
            </div>
            
            <div class="grid grid-cols-2 gap-2">
              <div>
                <label class="block text-[11px] text-slate-600 mb-1">Selecione a Unidade *</label>
                <select v-model="form.unidade_id" required class="w-full px-2.5 py-1.5 border rounded-lg bg-white focus:outline-none text-xs">
                  <option :value="null" disabled>Selecione uma unidade</option>
                  <option v-for="u in unidadesDisponiveis" :key="u.id" :value="u.id">
                    {{ u.identificador }} {{ u.bloco_torre ? '(' + u.bloco_torre + ')' : '' }}
                  </option>
                </select>
              </div>
              <div>
                <label class="block text-[11px] text-slate-600 mb-1">Tipo de Vínculo *</label>
                <select v-model="form.tipo_vinculo" required class="w-full px-2.5 py-1.5 border rounded-lg bg-white focus:outline-none text-xs">
                  <option value="PROPRIETARIO">Proprietário</option>
                  <option value="INQUILINO">Inquilino</option>
                  <option value="MORADOR">Morador / Dependente</option>
                  <option value="OUTRO">Outro</option>
                </select>
              </div>
            </div>

            <div class="flex items-center space-x-2 pt-1">
              <input id="pResp" v-model="form.responsavel" type="checkbox" class="rounded border-blue-300 text-blue-600 focus:ring-blue-500" />
              <label for="pResp" class="text-xs text-blue-900 font-medium">Responsável Financeiro / Legal da Unidade</label>
            </div>
          </div>

          <p class="text-[11px] text-slate-500 bg-slate-50 p-2.5 rounded-xl border border-slate-200">
            💡 Nota: Toda pessoa cadastrada fica automaticamente associada à unidade e ao seu condomínio ativo.
          </p>

          <div class="pt-4 border-t flex justify-end space-x-2">
            <button type="button" @click="showModal = false" class="px-4 py-2 border rounded-xl text-slate-600 hover:bg-slate-50 transition">
              Cancelar
            </button>
            <button type="submit" :disabled="saving" class="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white font-medium rounded-xl transition shadow">
              {{ saving ? 'Salvando...' : 'Salvar Pessoa' }}
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
import { maskCPF, maskPhone } from "@/utils/masks"

const authStore = useAuthStore()
const pessoas = ref([])
const unidadesDisponiveis = ref([])
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
  cpf: "",
  telefone: "",
  email: "",
  data_nascimento: null,
  unidade_id: null,
  tipo_vinculo: "MORADOR",
  responsavel: false,
})

const fetchUnidadesDisponiveis = async () => {
  try {
    const res = await apiClient.get("/unidades/", { params: { page_size: 500 } })
    unidadesDisponiveis.value = res.data.results || res.data
  } catch (err) {
    console.error("Erro ao carregar unidades:", err)
  }
}

const fetchPessoas = async () => {
  loading.value = true
  try {
    const res = await apiClient.get("/pessoas/", {
      params: { search: searchQuery.value },
    })
    pessoas.value = res.data.results || res.data
  } catch (err) {
    showAlert("Erro ao carregar pessoas.", "error")
  } finally {
    loading.value = false
  }
}

const showAlert = (msg, type = "success") => {
  alertMessage.value = msg
  alertClass.value = type === "success" ? "bg-emerald-50 text-emerald-800 border border-emerald-200" : "bg-rose-50 text-rose-800 border border-rose-200"
  setTimeout(() => (alertMessage.value = ""), 4000)
}

const openModal = async (item = null) => {
  modalErrorMessage.value = ""
  await fetchUnidadesDisponiveis()
  if (item) {
    isEditing.value = true
    selectedId.value = item.id
    form.value = {
      ...item,
      cpf: maskCPF(item.cpf || ""),
      telefone: maskPhone(item.telefone || ""),
      unidade_id: null,
      tipo_vinculo: "MORADOR",
      responsavel: false,
    }
  } else {
    isEditing.value = false
    selectedId.value = null
    form.value = {
      nome: "",
      cpf: "",
      telefone: "",
      email: "",
      data_nascimento: null,
      unidade_id: unidadesDisponiveis.value[0]?.id || null,
      tipo_vinculo: "MORADOR",
      responsavel: false,
    }
  }
  showModal.value = true
}

const savePessoa = async () => {
  saving.value = true
  modalErrorMessage.value = ""
  try {
    const payload = { ...form.value }
    if (!payload.cpf) payload.cpf = null

    if (isEditing.value) {
      await apiClient.put(`/pessoas/${selectedId.value}/`, payload)
      showAlert("Pessoa atualizada com sucesso!")
    } else {
      await apiClient.post("/pessoas/", payload)
      showAlert("Pessoa cadastrada com sucesso!")
    }
    showModal.value = false
    fetchPessoas()
  } catch (err) {
    const errorDetails = err.response?.data
    let msg = "Erro ao salvar pessoa."
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

const deletePessoa = async (item) => {
  if (!confirm(`Tem certeza que deseja excluir "${item.nome}"?`)) return
  try {
    await apiClient.delete(`/pessoas/${item.id}/`)
    showAlert("Pessoa excluída com sucesso!")
    fetchPessoas()
  } catch (err) {
    showAlert("Erro ao excluir pessoa.", "error")
  }
}

onMounted(() => {
  fetchPessoas()
})
</script>
