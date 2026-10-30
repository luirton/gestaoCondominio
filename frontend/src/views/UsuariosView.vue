<template>
  <div class="space-y-6">
    <!-- Top Bar -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h2 class="text-xl font-bold text-slate-800">Usuários & Credenciais</h2>
        <p class="text-xs text-slate-500">Gestão de acessos, vinculação com pessoa física e atribuição de perfis por condomínio</p>
      </div>

      <button
        v-if="authStore.canEdit"
        @click="openModal()"
        class="inline-flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-xl shadow transition"
      >
        + Novo Usuário
      </button>
    </div>

    <!-- Subsíndico Protection Notice -->
    <div v-if="authStore.isSubSindico" class="p-3 bg-amber-50 rounded-xl border border-amber-200 text-amber-900 text-xs">
      ℹ️ Como <strong>Subsíndico</strong>, você tem permissão para cadastrar e editar usuários, mas a exclusão permanente de contas é reservada exclusivamente ao <strong>Síndico</strong>.
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
          @input="fetchUsuarios"
          type="text"
          placeholder="Buscar por login, e-mail ou nome da pessoa..."
          class="w-full text-xs px-3 py-2 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>
      <span class="text-xs text-slate-400">Total: {{ usuarios.length }} contas</span>
    </div>

    <!-- Table -->
    <div class="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse text-xs">
          <thead>
            <tr class="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider">
              <th class="p-4">Login (Username)</th>
              <th class="p-4">E-mail</th>
              <th class="p-4">Pessoa Vinculada</th>
              <th class="p-4">Perfis & Condomínios</th>
              <th class="p-4 text-center">Status</th>
              <th class="p-4 text-right">Ações</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 text-slate-700">
            <tr v-if="loading" class="text-center">
              <td colspan="6" class="p-8 text-slate-400">Carregando usuários...</td>
            </tr>
            <tr v-else-if="usuarios.length === 0" class="text-center">
              <td colspan="6" class="p-8 text-slate-400">Nenhum usuário cadastrado neste condomínio.</td>
            </tr>
            <tr v-for="item in usuarios" :key="item.id" class="hover:bg-slate-50/80 transition">
              <td class="p-4 font-bold text-slate-900">
                {{ item.username }}
                <span v-if="item.is_superuser" class="ml-1 text-[10px] bg-red-100 text-red-700 px-1.5 py-0.2 rounded font-bold">
                  Superadmin
                </span>
              </td>
              <td class="p-4 text-slate-600">{{ item.email || '—' }}</td>
              <td class="p-4">
                <span v-if="item.pessoa_nome" class="font-medium text-slate-800">{{ item.pessoa_nome }}</span>
                <span v-else class="text-slate-400 italic">Nenhuma (Admin do Sistema)</span>
              </td>
              <td class="p-4">
                <div v-if="item.vinculos_condominios?.length > 0" class="space-y-1">
                  <div
                    v-for="v in item.vinculos_condominios"
                    :key="v.id"
                    class="inline-flex items-center gap-1 mr-2 px-2 py-0.5 rounded-md text-[11px] bg-blue-50 text-blue-800 border border-blue-200"
                  >
                    <span>{{ v.perfil_nome }}</span>
                    <span class="text-slate-400">@ {{ v.condominio_nome }}</span>
                  </div>
                </div>
                <span v-else class="text-slate-400 italic">Sem perfil associado</span>
              </td>
              <td class="p-4 text-center">
                <span :class="item.is_active ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-slate-100 text-slate-500 border-slate-200'" class="px-2 py-0.5 rounded-full border text-[11px] font-medium">
                  {{ item.is_active ? 'Ativo' : 'Inativo' }}
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
                  v-if="authStore.canDelete && !item.is_superuser"
                  @click="deleteUsuario(item)"
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
      <div class="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-lg overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        <div class="p-5 border-b border-slate-100 flex items-center justify-between bg-slate-50">
          <h3 class="font-bold text-sm text-slate-800">
            {{ isEditing ? 'Editar Usuário' : 'Novo Usuário de Acesso' }}
          </h3>
          <button @click="showModal = false" class="text-slate-400 hover:text-slate-600 text-lg font-bold">&times;</button>
        </div>

        <form @submit.prevent="saveUsuario" class="p-5 space-y-4 text-xs">
          <!-- Alerta de Erro DENTRO do Modal -->
          <div v-if="modalErrorMessage" class="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-start justify-between">
            <div class="flex items-start">
              <span class="mr-2 text-rose-600 font-bold shrink-0">⚠️</span>
              <span class="leading-relaxed">{{ modalErrorMessage }}</span>
            </div>
            <button type="button" @click="modalErrorMessage = ''" class="text-rose-600 hover:text-rose-800 font-bold ml-2">&times;</button>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block font-medium text-slate-700 mb-1">Login (Username) *</label>
              <input v-model="form.username" required type="text" placeholder="ex: mariana.silva" class="w-full px-3 py-2 border rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none" />
            </div>
            <div>
              <label class="block font-medium text-slate-700 mb-1">E-mail</label>
              <input v-model="form.email" type="email" placeholder="email@exemplo.com" class="w-full px-3 py-2 border rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none" />
            </div>
          </div>

          <div>
            <label class="block font-medium text-slate-700 mb-1">
              {{ isEditing ? 'Alterar Senha (deixe em branco para manter a atual)' : 'Senha de Acesso *' }}
            </label>
            <input v-model="form.password" :required="!isEditing" type="password" placeholder="••••••••" class="w-full px-3 py-2 border rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none" />
          </div>

          <div>
            <div class="flex items-center justify-between mb-1">
              <label class="font-medium text-slate-700">Pessoa Vinculada (Opcional)</label>
              <input
                v-model="filtroBuscaPessoa"
                type="text"
                placeholder="Filtrar por nome ou CPF..."
                class="px-2 py-0.5 text-[11px] border rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-500 w-48"
              />
            </div>
            <select v-model="form.pessoa" class="w-full px-3 py-2 border rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none">
              <option :value="null">Nenhuma (Usuário exclusivo do sistema)</option>
              <option v-for="p in pessoasFiltradas" :key="p.id" :value="p.id">{{ p.nome }} (CPF: {{ p.cpf || 'Não inf.' }})</option>
            </select>
            <p class="text-[10px] text-slate-400 mt-1">
              Exibindo {{ pessoasFiltradas.length }} de {{ pessoas.length }} pessoas. Conecta a credencial de login aos dados civis e moradia.
            </p>
          </div>

          <!-- Atribuição de Perfil e Condomínio -->
          <div class="p-3 bg-slate-50 rounded-xl border border-slate-200 space-y-3">
            <h4 class="font-bold text-slate-800 text-[11px] uppercase tracking-wider">Perfil & Condomínio de Acesso</h4>
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-slate-600 mb-1">Condomínio *</label>
                <select v-if="condominios.length > 1" v-model="perfilForm.condominio" required class="w-full px-3 py-2 border rounded-xl bg-white focus:outline-none">
                  <option v-for="c in condominios" :key="c.id" :value="c.id">{{ c.nome }}</option>
                </select>
                <div v-else class="px-3 py-2 bg-slate-100 rounded-xl text-slate-800 font-semibold text-xs border border-slate-200">
                  {{ condominios[0]?.nome }}
                </div>
              </div>
              <div>
                <label class="block text-slate-600 mb-1">Perfil de Permissão *</label>
                <select v-model="perfilForm.perfil" required class="w-full px-3 py-2 border rounded-xl bg-white focus:outline-none">
                  <option value="SINDICO">Síndico (Acesso Total)</option>
                  <option value="SUBSINDICO">Subsíndico</option>
                  <option value="CONSELHEIRO">Conselheiro</option>
                  <option value="CONDOMINO">Condômino</option>
                  <option value="FUNCIONARIO">Funcionário</option>
                </select>
              </div>
            </div>
          </div>

          <div class="flex items-center space-x-2 pt-1">
            <input id="userAtivo" v-model="form.is_active" type="checkbox" class="rounded border-slate-300 text-blue-600 focus:ring-blue-500" />
            <label for="userAtivo" class="text-slate-700 font-medium">Conta Ativa</label>
          </div>

          <div class="pt-4 border-t flex justify-end space-x-2">
            <button type="button" @click="showModal = false" class="px-4 py-2 border rounded-xl text-slate-600 hover:bg-slate-50 transition">
              Cancelar
            </button>
            <button type="submit" :disabled="saving" class="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white font-medium rounded-xl transition shadow">
              {{ saving ? 'Salvando...' : 'Salvar Usuário' }}
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
const usuarios = ref([])
const pessoas = ref([])
const condominios = ref([])
const loading = ref(false)
const saving = ref(false)
const searchQuery = ref("")
const filtroBuscaPessoa = ref("")
const alertMessage = ref("")
const alertClass = ref("")
const modalErrorMessage = ref("")

const pessoasFiltradas = computed(() => {
  if (!filtroBuscaPessoa.value.trim()) return pessoas.value
  const termoTexto = filtroBuscaPessoa.value.toLowerCase().trim()
  const apenasNumeros = filtroBuscaPessoa.value.replace(/\D/g, "")
  return pessoas.value.filter(p => {
    const nomeMatch = p.nome && p.nome.toLowerCase().includes(termoTexto)
    const cpfPuro = (p.cpf || "").replace(/\D/g, "")
    const cpfMatch = apenasNumeros ? cpfPuro.includes(apenasNumeros) : false
    return nomeMatch || cpfMatch
  })
})

const showModal = ref(false)
const isEditing = ref(false)
const selectedId = ref(null)

const form = ref({
  username: "",
  email: "",
  password: "",
  pessoa: null,
  is_active: true,
})

const perfilForm = ref({
  condominio: "",
  perfil: "CONDOMINO",
})

const fetchAuxiliaryData = async () => {
  try {
    const [resPessoas, resCond] = await Promise.all([
      apiClient.get("/pessoas/"),
      apiClient.get("/condominios/"),
    ])
    pessoas.value = resPessoas.data.results || resPessoas.data
    condominios.value = resCond.data.results || resCond.data
    if (!perfilForm.value.condominio && condominios.value.length > 0) {
      perfilForm.value.condominio = condominios.value[0].id
    }
  } catch (err) {
    console.error(err)
  }
}

const fetchUsuarios = async () => {
  loading.value = true
  try {
    const res = await apiClient.get("/usuarios/", {
      params: { search: searchQuery.value },
    })
    usuarios.value = res.data.results || res.data
  } catch (err) {
    showAlert("Erro ao carregar usuários.", "error")
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
  filtroBuscaPessoa.value = ""
  if (item) {
    isEditing.value = true
    selectedId.value = item.id
    form.value = {
      username: item.username,
      email: item.email,
      password: "",
      pessoa: item.pessoa,
      is_active: item.is_active,
    }
    if (item.vinculos_condominios?.length > 0) {
      perfilForm.value.condominio = item.vinculos_condominios[0].condominio
      perfilForm.value.perfil = item.vinculos_condominios[0].perfil
    }
  } else {
    isEditing.value = false
    selectedId.value = null
    form.value = {
      username: "",
      email: "",
      password: "",
      pessoa: null,
      is_active: true,
    }
    const defaultCondoId = (authStore.activeCondominioId && condominios.value.some(c => String(c.id) === String(authStore.activeCondominioId)))
      ? Number(authStore.activeCondominioId)
      : (condominios.value[0]?.id || "")

    perfilForm.value = {
      condominio: defaultCondoId,
      perfil: "CONDOMINO",
    }
  }
  showModal.value = true
}

const saveUsuario = async () => {
  saving.value = true
  modalErrorMessage.value = ""
  try {
    let userId = selectedId.value
    if (isEditing.value) {
      const payload = { ...form.value }
      if (!payload.password) delete payload.password
      await apiClient.put(`/usuarios/${userId}/`, payload)
      showAlert("Usuário atualizado com sucesso!")
    } else {
      const res = await apiClient.post("/usuarios/", form.value)
      userId = res.data.id
      showAlert("Usuário cadastrado com sucesso!")
    }

    if (userId && perfilForm.value.condominio && perfilForm.value.perfil) {
      try {
        await apiClient.post("/usuarios-condominios/", {
          usuario: userId,
          condominio: perfilForm.value.condominio,
          perfil: perfilForm.value.perfil,
          ativo: true,
        })
      } catch (vinculoErr) {
        console.log("Perfil já associado ou atualizado:", vinculoErr)
      }
    }

    showModal.value = false
    fetchUsuarios()
  } catch (err) {
    const errorDetails = err.response?.data
    let msg = "Erro ao salvar usuário."
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

const deleteUsuario = async (item) => {
  if (!confirm(`Tem certeza que deseja excluir o usuário "${item.username}"?`)) return
  try {
    await apiClient.delete(`/usuarios/${item.id}/`)
    showAlert("Usuário excluído com sucesso!")
    fetchUsuarios()
  } catch (err) {
    showAlert("Erro ao excluir usuário. Subsíndicos não têm permissão para exclusão.", "error")
  }
}

onMounted(async () => {
  await fetchAuxiliaryData()
  await fetchUsuarios()
})
</script>
