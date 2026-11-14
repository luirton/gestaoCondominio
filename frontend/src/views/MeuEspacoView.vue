<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="bg-gradient-to-r from-emerald-800 via-teal-800 to-slate-900 rounded-2xl p-6 text-white shadow-xl shadow-emerald-950/20">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <span class="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-white/20 text-emerald-100 border border-white/20">
            Portal do Condômino
          </span>
          <h2 class="text-2xl font-bold mt-2">
            Meu Espaço • {{ authStore.user?.first_name || authStore.user?.username }}
          </h2>
          <p class="text-emerald-100 text-xs mt-1">
            Seus dados cadastrais, unidades vinculadas, situação financeira e demonstrativos
          </p>
        </div>

        <div class="text-right flex items-center gap-4">
          <div v-if="unidades.length > 1">
            <label class="block text-[11px] text-emerald-200 mb-1 font-semibold text-left">Visualização Financeira:</label>
            <select
              v-model="unidadeSelecionadaId"
              @change="carregarSituacaoFinanceira"
              class="bg-emerald-950/80 border border-emerald-600 text-white text-xs rounded-lg px-3 py-1.5 focus:ring-2 focus:ring-white"
            >
              <option value="CONSOLIDADO">★ Todas as Unidades (Tudo Junto)</option>
              <option v-for="u in unidades" :key="u.unidade_id" :value="u.unidade_id">
                {{ u.identificador }} ({{ u.condominio_nome }})
              </option>
            </select>
          </div>
          <div>
            <p class="text-xs text-emerald-200">Unidades</p>
            <p class="text-3xl font-black">{{ unidades.length }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Meus Dados Cadastrais -->
    <div class="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm">
      <h3 class="text-xs font-bold text-slate-700 uppercase tracking-wider mb-4 flex items-center">
        <span class="mr-2">👤</span> Meus Dados Civis
      </h3>
      <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 text-xs">
        <div class="p-3 bg-slate-50 rounded-xl">
          <span class="text-slate-400 block mb-1">Nome Completo</span>
          <p class="font-semibold text-slate-800">{{ authStore.user?.pessoa_nome || authStore.user?.username }}</p>
        </div>
        <div class="p-3 bg-slate-50 rounded-xl">
          <span class="text-slate-400 block mb-1">Login de Acesso</span>
          <p class="font-semibold text-slate-800 font-mono">{{ authStore.user?.username }}</p>
        </div>
        <div class="p-3 bg-slate-50 rounded-xl">
          <span class="text-slate-400 block mb-1">E-mail</span>
          <p class="font-semibold text-slate-800">{{ authStore.user?.email || 'Não informado' }}</p>
        </div>
        <div class="p-3 bg-slate-50 rounded-xl">
          <span class="text-slate-400 block mb-1">Perfil Ativo</span>
          <span class="inline-block px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-bold">
            Condômino
          </span>
        </div>
      </div>
    </div>

    <!-- Minhas Unidades Vinculadas -->
    <div class="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center">
          <span class="mr-2">🏢</span> Minhas Unidades Vinculadas ({{ unidades.length }})
        </h3>
        <span class="text-[11px] text-slate-400">Clique ou use o seletor acima para alternar</span>
      </div>

      <div v-if="loading" class="text-center py-6 text-slate-400 text-xs">
        Carregando unidades...
      </div>

      <div v-else-if="unidades.length === 0" class="text-center py-8 text-slate-400 text-xs">
        Nenhuma unidade associada ao seu cadastro no momento. Entre em contato com a administração.
      </div>

      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div
          v-for="u in unidades"
          :key="u.vinculo_id"
          @click="selecionarUnidadeCard(u.unidade_id)"
          class="p-4 rounded-2xl border transition cursor-pointer relative"
          :class="u.unidade_id === unidadeSelecionadaId ? 'border-emerald-500 bg-emerald-50/30 ring-2 ring-emerald-500/20' : 'border-slate-200 bg-slate-50/50 hover:border-emerald-300'"
        >
          <div class="flex items-center justify-between">
            <div>
              <span class="text-[10px] text-slate-400 uppercase tracking-wider">{{ u.condominio_nome }}</span>
              <h4 class="text-lg font-bold text-slate-900 mt-0.5">
                {{ u.identificador }}
                <span v-if="u.bloco" class="text-xs text-slate-500 font-normal">({{ u.bloco }})</span>
              </h4>
            </div>
            <span
              v-if="u.responsavel"
              class="px-2 py-0.5 bg-amber-100 text-amber-800 font-bold text-[10px] rounded-full border border-amber-300"
            >
              ★ Responsável
            </span>
          </div>

          <div class="mt-3 pt-3 border-t border-slate-200 flex items-center justify-between text-[11px] text-slate-600">
            <span>Tipo: <strong class="text-slate-800">{{ u.tipo }}</strong></span>
            <span class="text-emerald-600 font-medium">Ver Extrato →</span>
          </div>
        </div>
      </div>
    </div>

    <!-- SITUAÇÃO FINANCEIRA & QUITAÇÃO (NADA CONSTA / DÉBITOS) -->
    <div class="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-5">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div class="flex items-center gap-2">
            <h3 class="text-sm font-bold text-slate-800 uppercase tracking-wider flex items-center">
              <span class="mr-2">⚖️</span> Situação Financeira & Quitação
            </h3>
            <span v-if="isConsolidado" class="px-2 py-0.5 bg-blue-100 text-blue-800 text-[10px] font-bold rounded-full">
              Visão Consolidada (Tudo Junto)
            </span>
          </div>
          <p class="text-xs text-slate-400 mt-0.5" v-if="extratoMorador">
            {{ isConsolidado
              ? `Consolidando ${unidades.length} unidade(s) • Atualizado até ${formatData(extratoMorador.data_atualizacao)}`
              : `Unidade avaliada: ${extratoMorador.unidade.identificador} • Atualizado até ${formatData(extratoMorador.data_atualizacao)}`
            }}
          </p>
        </div>

        <div class="flex items-center gap-2">
          <span
            v-if="statusFinanceiroCarregado"
            class="px-3 py-1 rounded-full text-xs font-bold"
            :class="temDebitoAberto ? 'bg-rose-100 text-rose-800 border border-rose-300' : 'bg-emerald-100 text-emerald-800 border border-emerald-300'"
          >
            {{ temDebitoAberto ? 'Pendências Financeiras' : 'Adimplente / Em Dia' }}
          </span>
        </div>
      </div>

      <div v-if="carregandoFinanceiro" class="text-center py-10 text-slate-400 text-xs">
        <svg class="w-6 h-6 animate-spin mx-auto text-blue-600 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        Verificando situação financeira da unidade...
      </div>

      <!-- CENÁRIO A: CONDÔMINO COM DÉBITOS EM ABERTO -->
      <div v-else-if="temDebitoAberto && extratoMorador" class="space-y-4">
        <div class="p-4 bg-rose-50 border border-rose-200 rounded-xl flex items-start gap-3">
          <svg class="w-6 h-6 text-rose-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <div class="text-xs text-rose-900 space-y-1">
            <p class="font-bold text-sm">
              {{ isConsolidado
                ? `Constam títulos pendentes de pagamento em suas unidades (${extratoMorador.unidades_com_debito_nomes}).`
                : `Constam títulos pendentes de pagamento para a sua unidade (${extratoMorador.unidade.identificador}).`
              }}
            </p>
            <p>
              Você possui <b>{{ extratoMorador.qtd_titulos }}</b> cota(s) em aberto totalizando
              <b>{{ formatMoeda(extratoMorador.totais.total_geral) }}</b> com encargos atualizados até {{ formatData(extratoMorador.data_atualizacao) }}.
            </p>
          </div>
        </div>

        <!-- Grade de débitos -->
        <div class="overflow-x-auto border border-slate-200 rounded-xl">
          <table class="w-full text-left text-xs border-collapse">
            <thead class="bg-slate-100 text-slate-700 font-bold border-b">
              <tr>
                <th class="p-2.5 text-center">#</th>
                <th class="p-2.5">Referência</th>
                <th class="p-2.5">Vencimento</th>
                <th class="p-2.5 text-center">Dias Atraso</th>
                <th class="p-2.5 text-right">Taxa</th>
                <th class="p-2.5 text-right">Multa</th>
                <th class="p-2.5 text-right">Juros</th>
                <th class="p-2.5 text-right">Total a Pagar</th>
                <th class="p-2.5">Observação / Unidade</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr v-for="it in extratoMorador.itens" :key="it.cota_id || it.item" class="hover:bg-slate-50">
                <td class="p-2.5 text-center font-bold text-slate-600">{{ it.item }}</td>
                <td class="p-2.5 font-medium text-slate-800">{{ it.periodo_rotulo }}</td>
                <td class="p-2.5 text-slate-700">{{ formatData(it.vencimento) }}</td>
                <td class="p-2.5 text-center text-slate-600">{{ it.dias_atraso }}</td>
                <td class="p-2.5 text-right text-slate-700">{{ formatMoeda(it.taxa) }}</td>
                <td class="p-2.5 text-right text-slate-700">{{ formatMoeda(it.multa) }}</td>
                <td class="p-2.5 text-right text-slate-700">{{ formatMoeda(it.juros) }}</td>
                <td class="p-2.5 text-right font-bold text-rose-700">{{ formatMoeda(it.total) }}</td>
                <td class="p-2.5 text-slate-600">{{ it.observacao || '-' }}</td>
              </tr>
            </tbody>
            <tfoot class="bg-slate-50 font-bold text-slate-800 border-t">
              <tr>
                <td colspan="4" class="p-2.5 text-left">SALDO DEVEDOR CONSOLIDADO:</td>
                <td class="p-2.5 text-right">{{ formatMoeda(extratoMorador.totais.taxa) }}</td>
                <td class="p-2.5 text-right">{{ formatMoeda(extratoMorador.totais.multa) }}</td>
                <td class="p-2.5 text-right">{{ formatMoeda(extratoMorador.totais.juros) }}</td>
                <td class="p-2.5 text-right text-rose-700 text-sm">{{ formatMoeda(extratoMorador.totais.total_geral) }}</td>
                <td></td>
              </tr>
            </tfoot>
          </table>
        </div>

        <div class="flex flex-col sm:flex-row justify-between items-center gap-3 pt-2">
          <p class="text-xs text-slate-500">
            Dúvidas ou negociações: contate <b>{{ extratoMorador.parametro?.email_cobranca }}</b>
          </p>
          <div class="flex items-center gap-3">
            <!-- Se for visão consolidada e houver algumas unidades adimplentes, permite emitir o Nada Consta das adimplentes -->
            <button
              v-if="isConsolidado && extratoMorador.qtd_unidades_em_dia > 0"
              @click="solicitarNadaConstaConsolidado"
              :disabled="emitindoCertidao"
              class="px-4 py-2.5 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white rounded-xl text-xs font-semibold inline-flex items-center gap-2 transition shadow-sm"
              :title="`Emitir Nada Consta concatenando as casas adimplentes: ${extratoMorador.unidades_em_dia_nomes}`"
            >
              <svg v-if="emitindoCertidao" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Nada Consta (Casas em Dia: {{ extratoMorador.unidades_em_dia_nomes }})
            </button>

            <!-- Baixar Aviso de Débito (Individual ou Tudo Junto) -->
            <button
              @click="baixarAvisoDebitoMorador"
              :disabled="baixandoPdfMorador"
              class="px-4 py-2.5 bg-rose-600 hover:bg-rose-700 disabled:opacity-50 text-white rounded-xl text-xs font-semibold inline-flex items-center gap-2 transition shadow-sm"
            >
              <svg v-if="baixandoPdfMorador" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              {{ isConsolidado ? 'Baixar Débitos Tudo Junto (PDF)' : 'Baixar Aviso de Débito (PDF)' }}
            </button>
          </div>
        </div>
      </div>

      <!-- CENÁRIO B: CONDÔMINO ADIMPLENTE (SEM DÉBITOS) -> EMISSÃO DO NADA CONSTA -->
      <div v-else-if="statusFinanceiroCarregado && !temDebitoAberto" class="p-6 bg-emerald-50/70 border border-emerald-200 rounded-2xl flex flex-col sm:flex-row items-center justify-between gap-6">
        <div class="space-y-1">
          <div class="flex items-center gap-2">
            <span class="text-emerald-800 font-bold text-base">
              {{ isConsolidado ? 'Parabéns! Todas as suas unidades estão 100% adimplentes.' : 'Parabéns! Sua unidade está 100% adimplente.' }}
            </span>
          </div>
          <p class="text-xs text-slate-600 max-w-xl">
            Não consta nenhuma pendência em aberto para
            <b>{{ isConsolidado ? 'todas as suas casas (' + extratoMorador?.unidade?.identificador + ')' : extratoMorador?.unidade?.identificador }}</b>.
            Você pode emitir a <b>Declaração de Nada Consta (Certidão de Quitação Condominial)</b> oficial com validade expressa até o final deste mês.
          </p>
        </div>

        <button
          @click="solicitarNadaConsta"
          :disabled="emitindoCertidao"
          class="px-5 py-3 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white rounded-xl text-xs font-bold shadow-lg shadow-emerald-700/20 inline-flex items-center gap-2 flex-shrink-0 transition"
        >
          <svg v-if="emitindoCertidao" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {{ isConsolidado ? 'Emitir Nada Consta Tudo Junto (PDF)' : 'Emitir Declaração de Nada Consta (PDF)' }}
        </button>
      </div>
    </div>

    <!-- PRESTAÇÃO DE CONTAS PUBLICADAS (ACESSO DIRETO) -->
    <div class="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm">
      <div class="flex items-center justify-between mb-4">
        <div>
          <h4 class="font-bold text-slate-800 text-sm flex items-center">
            <span class="mr-2">📊</span> Prestações de Contas Publicadas
          </h4>
          <p class="text-xs text-slate-400 mt-0.5">Balancetes mensais e demonstrativos aprovados para os moradores</p>
        </div>
        <router-link
          to="/prestacao/morador"
          class="px-4 py-2 bg-blue-50 hover:bg-blue-100 text-blue-700 font-semibold text-xs rounded-xl border border-blue-200 transition"
        >
          Acessar Prestações Publicadas →
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import { useAuthStore } from "@/stores/auth"
import apiClient from "@/api/client"
import { financeiroApi } from "@/api/financeiro"

const authStore = useAuthStore()
const unidades = ref([])
const unidadeSelecionadaId = ref(null)
const loading = ref(false)

// Financeiro / Nada Consta
const statusFinanceiroCarregado = ref(false)
const carregandoFinanceiro = ref(false)
const temDebitoAberto = ref(false)
const extratoMorador = ref(null)
const baixandoPdfMorador = ref(false)
const emitindoCertidao = ref(false)

const isConsolidado = computed(() => unidadeSelecionadaId.value === "CONSOLIDADO")

const formatMoeda = (val) => {
  if (val === undefined || val === null) return "R$ 0,00"
  const n = typeof val === "string" ? parseFloat(val) : val
  return n.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })
}

const formatData = (d) => {
  if (!d) return ""
  if (typeof d === "string" && d.includes("-")) {
    const [y, m, dia] = d.split("-")
    return `${dia}/${m}/${y}`
  }
  return d
}

const selecionarUnidadeCard = (unidId) => {
  unidadeSelecionadaId.value = unidId
  carregarSituacaoFinanceira()
}

const carregarSituacaoFinanceira = async () => {
  if (!unidadeSelecionadaId.value) return
  carregandoFinanceiro.value = true
  try {
    if (unidadeSelecionadaId.value === "CONSOLIDADO") {
      const res = await financeiroApi.getInadimplenciaConsolidadaMorador()
      extratoMorador.value = res.data
      temDebitoAberto.value = !res.data.esta_em_dia
    } else {
      const res = await financeiroApi.getInadimplenciaUnidade(unidadeSelecionadaId.value)
      extratoMorador.value = res.data
      temDebitoAberto.value = !res.data.esta_em_dia
    }
    statusFinanceiroCarregado.value = true
  } catch (err) {
    console.error("Erro ao verificar situação financeira:", err)
  } finally {
    carregandoFinanceiro.value = false
  }
}

const baixarAvisoDebitoMorador = async () => {
  baixandoPdfMorador.value = true
  try {
    let res
    let nomeArquivo
    if (isConsolidado.value) {
      res = await financeiroApi.getAvisoDebitoConsolidadoPdf()
      nomeArquivo = `aviso_debito_consolidado_${authStore.user?.username || 'morador'}.pdf`
    } else {
      res = await financeiroApi.getAvisoDebitoPdf(unidadeSelecionadaId.value)
      nomeArquivo = `aviso_debito_${extratoMorador.value?.unidade?.identificador?.replace(/\s+/g, '_')?.toLowerCase() || 'unidade'}.pdf`
    }
    const blob = new Blob([res.data], { type: "application/pdf" })
    const url = URL.createObjectURL(blob)
    const link = document.createElement("a")
    link.href = url
    link.download = nomeArquivo
    link.click()
    URL.revokeObjectURL(url)
  } catch (err) {
    console.error("Erro ao baixar PDF:", err)
    alert("Erro ao gerar o PDF de aviso de débito.")
  } finally {
    baixandoPdfMorador.value = false
  }
}

const solicitarNadaConstaConsolidado = async () => {
  emitindoCertidao.value = true
  try {
    const res = await financeiroApi.emitirNadaConstaConsolidado()
    if (res.data.sucesso) {
      const idsStr = res.data.ids ? res.data.ids.join(",") : ""
      const pdfRes = await financeiroApi.getNadaConstaConsolidadoPdf(idsStr)
      const blob = new Blob([pdfRes.data], { type: "application/pdf" })
      const url = URL.createObjectURL(blob)
      const link = document.createElement("a")
      link.href = url
      const unidadesStr = (res.data.unidades_adimplentes || []).join("_").toLowerCase().replace(/\s+/g, "")
      link.download = `nada_consta_consolidado_${unidadesStr || "adimplentes"}.pdf`
      link.click()
      URL.revokeObjectURL(url)
    }
  } catch (err) {
    console.error("Erro ao emitir nada consta consolidado:", err)
    alert(err.response?.data?.detail || "Não foi possível emitir a Certidão de Nada Consta.")
  } finally {
    emitindoCertidao.value = false
  }
}

const solicitarNadaConsta = async () => {
  if (isConsolidado.value) {
    return solicitarNadaConstaConsolidado()
  }

  if (!unidadeSelecionadaId.value) return
  emitindoCertidao.value = true

  try {
    const res = await financeiroApi.emitirNadaConsta(unidadeSelecionadaId.value)
    if (res.data.sucesso) {
      const pdfRes = await financeiroApi.getNadaConstaPdf(res.data.certidao.id)
      const blob = new Blob([pdfRes.data], { type: "application/pdf" })
      const url = URL.createObjectURL(blob)
      const link = document.createElement("a")
      link.href = url
      link.download = `nada_consta_${extratoMorador.value?.unidade?.identificador?.replace(/\s+/g, '_')?.toLowerCase() || 'certidao'}.pdf`
      link.click()
      URL.revokeObjectURL(url)
    }
  } catch (err) {
    console.error("Erro ao emitir nada consta:", err)
    alert(err.response?.data?.detail || "Não foi possível emitir a Certidão de Nada Consta.")
  } finally {
    emitindoCertidao.value = false
  }
}

const fetchMinhasUnidades = async () => {
  loading.value = true
  try {
    const res = await apiClient.get("/auth/me/")
    unidades.value = res.data.unidades_vinculadas || []
    if (unidades.value.length > 0) {
      // Se tiver mais de uma casa, pode iniciar em consolidado ou na primeira unidade
      unidadeSelecionadaId.value = unidades.value[0].unidade_id
      await carregarSituacaoFinanceira()
    }
  } catch (err) {
    console.error("Erro ao carregar dados do usuário:", err)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchMinhasUnidades()
})
</script>
