<template>
  <div class="min-h-screen bg-slate-900 flex flex-col justify-center py-12 sm:px-6 lg:px-8 relative overflow-hidden">
    <!-- Decorative background elements -->
    <div class="absolute -top-40 -right-40 w-96 h-96 bg-blue-600/20 rounded-full blur-3xl pointer-events-none"></div>
    <div class="absolute -bottom-40 -left-40 w-96 h-96 bg-indigo-600/20 rounded-full blur-3xl pointer-events-none"></div>

    <div class="sm:mx-auto sm:w-full sm:max-w-md z-10">
      <div class="flex justify-center">
        <div class="w-14 h-14 rounded-2xl bg-blue-600 flex items-center justify-center font-black text-2xl text-white shadow-xl shadow-blue-500/30">
          CG
        </div>
      </div>
      <h2 class="mt-4 text-center text-3xl font-extrabold text-white tracking-tight">
        CondoGestão
      </h2>
      <p class="mt-2 text-center text-sm text-slate-400">
        Plataforma Integrada de Gestão Condominial
      </p>
    </div>

    <div class="mt-8 sm:mx-auto sm:w-full sm:max-w-md z-10 px-4 sm:px-0">
      <div class="bg-slate-800/90 backdrop-blur-md py-8 px-6 shadow-2xl rounded-2xl border border-slate-700 sm:px-10">
        <!-- Tabs Switcher -->
        <div class="flex border-b border-slate-700 mb-6">
          <button
            type="button"
            @click="switchTab('login')"
            :class="activeTab === 'login' ? 'border-b-2 border-blue-500 text-white font-bold' : 'text-slate-400 hover:text-slate-200'"
            class="flex-1 pb-3 text-center text-sm font-semibold transition"
          >
            Acessar Sistema
          </button>
          <button
            type="button"
            @click="switchTab('register')"
            :class="activeTab === 'register' ? 'border-b-2 border-blue-500 text-white font-bold' : 'text-slate-400 hover:text-slate-200'"
            class="flex-1 pb-3 text-center text-sm font-semibold transition"
          >
            Primeiro Acesso (Morador)
          </button>
        </div>

        <!-- ABA 1: LOGIN -->
        <div v-if="activeTab === 'login'">
          <form class="space-y-5" @submit.prevent="handleSubmit">
            <div v-if="errorMessage" class="p-3 rounded-lg bg-rose-950/60 border border-rose-800 text-rose-300 text-sm flex items-center">
              <svg class="w-5 h-5 mr-2 shrink-0 text-rose-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>{{ errorMessage }}</span>
            </div>

            <div>
              <label class="block text-sm font-medium text-slate-200">Usuário</label>
              <div class="mt-1">
                <input
                  v-model="username"
                  type="text"
                  required
                  autocomplete="username"
                  placeholder="Ex: admin, mariana, jose"
                  class="appearance-none block w-full px-3 py-2.5 border border-slate-600 rounded-xl bg-slate-900/80 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm transition"
                />
              </div>
            </div>

            <div>
              <label class="block text-sm font-medium text-slate-200">Senha</label>
              <div class="mt-1">
                <input
                  v-model="password"
                  type="password"
                  required
                  autocomplete="current-password"
                  placeholder="••••••••"
                  class="appearance-none block w-full px-3 py-2.5 border border-slate-600 rounded-xl bg-slate-900/80 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm transition"
                />
              </div>
            </div>

            <div>
              <button
                type="submit"
                :disabled="loading"
                class="w-full flex justify-center py-2.5 px-4 border border-transparent rounded-xl shadow-lg text-sm font-semibold text-white bg-blue-600 hover:bg-blue-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 transition"
              >
                <svg v-if="loading" class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                {{ loading ? "Autenticando via JWT..." : "Entrar no Sistema" }}
              </button>
            </div>
          </form>

          <div class="mt-4 text-center">
            <button
              type="button"
              @click="switchTab('register')"
              class="text-xs text-blue-400 hover:text-blue-300 font-medium transition"
            >
              É morador e ainda não tem senha? Cadastre-se aqui
            </button>
          </div>

          <!-- Quick Demo Accounts -->
          <div class="mt-8 pt-6 border-t border-slate-700/80">
            <p class="text-xs text-slate-400 text-center font-medium uppercase tracking-wider mb-3">
              Contas de Teste Pré-Configuradas (Clique p/ preencher)
            </p>
            <div class="grid grid-cols-3 gap-2">
              <button
                type="button"
                @click="setCredentials('admin', 'admin123')"
                class="px-2 py-2 bg-slate-900 hover:bg-slate-700/80 border border-slate-700 rounded-lg text-xs font-medium text-slate-300 text-center transition"
              >
                <span class="block text-blue-400 font-bold">Síndico</span>
                admin
              </button>
              <button
                type="button"
                @click="setCredentials('mariana', 'senha123')"
                class="px-2 py-2 bg-slate-900 hover:bg-slate-700/80 border border-slate-700 rounded-lg text-xs font-medium text-slate-300 text-center transition"
              >
                <span class="block text-emerald-400 font-bold">Condômina</span>
                mariana
              </button>
              <button
                type="button"
                @click="setCredentials('jose', 'senha123')"
                class="px-2 py-2 bg-slate-900 hover:bg-slate-700/80 border border-slate-700 rounded-lg text-xs font-medium text-slate-300 text-center transition"
              >
                <span class="block text-purple-400 font-bold">Porteiro</span>
                jose
              </button>
            </div>
          </div>
        </div>

        <!-- ABA 2: AUTO-CADASTRO DE MORADOR -->
        <div v-else>
          <!-- Mensagem de Sucesso -->
          <div v-if="regSuccessMessage" class="p-4 rounded-xl bg-emerald-950/70 border border-emerald-800 text-emerald-200 text-xs space-y-3">
            <div class="flex items-start">
              <span class="text-lg mr-2 text-emerald-400 shrink-0">✅</span>
              <div>
                <strong class="font-bold block text-sm text-emerald-300">Cadastro Concluído!</strong>
                <p class="mt-1 leading-relaxed">{{ regSuccessMessage }}</p>
              </div>
            </div>
            <button
              type="button"
              @click="goToLoginAfterSuccess"
              class="w-full py-2 px-3 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg font-bold text-xs shadow transition text-center"
            >
              Fazer Login Agora
            </button>
          </div>

          <!-- Formulário de Cadastro -->
          <form v-else class="space-y-4" @submit.prevent="handleRegister">
            <div class="p-3 bg-blue-950/40 rounded-xl border border-blue-900/60 text-blue-300 text-xs leading-relaxed">
              ℹ️ Para criar seu acesso, seu <strong>CPF</strong> deve estar previamente registrado pela administração do seu condomínio na lista de pessoas/moradores.
            </div>

            <div v-if="regErrorMessage" class="p-3 rounded-lg bg-rose-950/60 border border-rose-800 text-rose-300 text-xs flex items-start">
              <span class="mr-2 text-rose-400 font-bold shrink-0">⚠️</span>
              <span>{{ regErrorMessage }}</span>
            </div>

            <div>
              <label class="block text-xs font-medium text-slate-200">CPF do Morador *</label>
              <div class="mt-1">
                <input
                  v-model="regForm.cpf"
                  @input="onCpfInput"
                  type="text"
                  required
                  placeholder="000.000.000-00"
                  class="appearance-none block w-full px-3 py-2 border border-slate-600 rounded-xl bg-slate-900/80 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 text-xs"
                />
              </div>
              <span class="text-[10px] text-slate-400">Verificará seu registro prévio no condomínio.</span>
            </div>

            <div>
              <label class="block text-xs font-medium text-slate-200">Nome de Usuário (Login) *</label>
              <div class="mt-1">
                <input
                  v-model="regForm.username"
                  type="text"
                  required
                  placeholder="ex: mariana.silva"
                  class="appearance-none block w-full px-3 py-2 border border-slate-600 rounded-xl bg-slate-900/80 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 text-xs"
                />
              </div>
            </div>

            <div>
              <label class="block text-xs font-medium text-slate-200">E-mail para Confirmação *</label>
              <div class="mt-1">
                <input
                  v-model="regForm.email"
                  type="email"
                  required
                  placeholder="seu.email@exemplo.com"
                  class="appearance-none block w-full px-3 py-2 border border-slate-600 rounded-xl bg-slate-900/80 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 text-xs"
                />
              </div>
              <span class="text-[10px] text-slate-400">Enviaremos os dados de confirmação para esta caixa postal.</span>
            </div>

            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-xs font-medium text-slate-200">Senha *</label>
                <div class="mt-1">
                  <input
                    v-model="regForm.password"
                    type="password"
                    required
                    placeholder="••••••••"
                    class="appearance-none block w-full px-3 py-2 border border-slate-600 rounded-xl bg-slate-900/80 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 text-xs"
                  />
                </div>
              </div>
              <div>
                <label class="block text-xs font-medium text-slate-200">Confirmar Senha *</label>
                <div class="mt-1">
                  <input
                    v-model="regForm.confirmPassword"
                    type="password"
                    required
                    placeholder="••••••••"
                    class="appearance-none block w-full px-3 py-2 border border-slate-600 rounded-xl bg-slate-900/80 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 text-xs"
                  />
                </div>
              </div>
            </div>

            <div class="pt-2">
              <button
                type="submit"
                :disabled="regLoading"
                class="w-full flex justify-center py-2.5 px-4 border border-transparent rounded-xl shadow-lg text-xs font-semibold text-white bg-blue-600 hover:bg-blue-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 transition"
              >
                <svg v-if="regLoading" class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                {{ regLoading ? "Validando e Cadastrando..." : "Cadastrar meu Acesso" }}
              </button>
            </div>

            <div class="text-center pt-2">
              <button
                type="button"
                @click="switchTab('login')"
                class="text-xs text-slate-400 hover:text-slate-200 transition"
              >
                ← Já possui cadastro? Fazer Login
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue"
import { useRouter } from "vue-router"
import { useAuthStore } from "@/stores/auth"
import apiClient from "@/api/client"
import { maskCPF } from "@/utils/masks"

const router = useRouter()
const authStore = useAuthStore()

const activeTab = ref("login")

// Login state
const username = ref("admin")
const password = ref("admin123")
const loading = ref(false)
const errorMessage = ref("")

// Register state
const regForm = ref({
  cpf: "",
  username: "",
  email: "",
  password: "",
  confirmPassword: "",
})
const regLoading = ref(false)
const regErrorMessage = ref("")
const regSuccessMessage = ref("")

const switchTab = (tab) => {
  activeTab.value = tab
  errorMessage.value = ""
  regErrorMessage.value = ""
}

const onCpfInput = () => {
  regForm.value.cpf = maskCPF(regForm.value.cpf)
}

const setCredentials = (u, p) => {
  username.value = u
  password.value = p
  errorMessage.value = ""
}

const handleSubmit = async () => {
  loading.value = true
  errorMessage.value = ""
  try {
    await authStore.login(username.value, password.value)
    
    // Redireciona de acordo com o perfil
    if (authStore.currentRole === "CONDOMINO") {
      router.push("/meu-espaco")
    } else {
      router.push("/")
    }
  } catch (err) {
    errorMessage.value = authStore.error || "Falha na autenticação. Verifique suas credenciais."
  } finally {
    loading.value = false
  }
}

const handleRegister = async () => {
  regErrorMessage.value = ""
  regSuccessMessage.value = ""

  if (regForm.value.password !== regForm.value.confirmPassword) {
    regErrorMessage.value = "As senhas digitadas não conferem."
    return
  }

  if (regForm.value.password.length < 4) {
    regErrorMessage.value = "A senha deve conter no mínimo 4 caracteres."
    return
  }

  regLoading.value = true
  try {
    const res = await apiClient.post("/auth/register-condomino/", {
      cpf: regForm.value.cpf,
      username: regForm.value.username,
      email: regForm.value.email,
      password: regForm.value.password,
    })

    regSuccessMessage.value = res.data?.detail || "Cadastro concluído! Enviamos um e-mail de confirmação para você."
  } catch (err) {
    const data = err.response?.data
    if (data?.detail) {
      regErrorMessage.value = data.detail
    } else if (typeof data === "object") {
      regErrorMessage.value = Object.entries(data)
        .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(", ") : v}`)
        .join(" | ")
    } else {
      regErrorMessage.value = "Não foi possível realizar o cadastro. Verifique os dados ou contate o síndico."
    }
  } finally {
    regLoading.value = false
  }
}

const goToLoginAfterSuccess = () => {
  username.value = regForm.value.username
  password.value = regForm.value.password
  activeTab.value = "login"
  regSuccessMessage.value = ""
}
</script>
