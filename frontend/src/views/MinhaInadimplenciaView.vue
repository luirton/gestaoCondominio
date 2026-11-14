<template>
  <div class="space-y-6">
    <!-- Cabeçalho -->
    <div class="bg-gradient-to-r from-slate-900 to-slate-800 rounded-2xl p-6 text-white shadow-xl shadow-slate-950/20">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <span class="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-white/20 text-slate-200 border border-white/20">
            Autoatendimento do Condômino
          </span>
          <h1 class="text-2xl font-bold mt-2">
            Minhas Finanças & Quitação
          </h1>
          <p class="text-slate-300 text-xs mt-1">
            Consulte a situação financeira da sua unidade, emita o espelho de débitos ou retire a Certidão de Nada Consta.
          </p>
        </div>

        <div v-if="unidades.length > 1" class="w-full sm:w-auto">
          <label class="block text-[11px] text-slate-300 mb-1 font-semibold">Selecione a Unidade:</label>
          <select
            v-model="unidadeSelecionadaId"
            @change="carregarExtrato"
            class="w-full sm:w-48 bg-slate-800 border border-slate-600 text-white text-xs rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500"
          >
            <option v-for="u in unidades" :key="u.unidade_id" :value="u.unidade_id">
              {{ u.identificador }} ({{ u.condominio_nome }})
            </option>
          </select>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="carregando" class="bg-white rounded-2xl p-12 text-center border border-slate-200 shadow-sm text-slate-500 text-sm">
      <svg class="w-8 h-8 animate-spin mx-auto text-blue-600 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
      </svg>
      Consultando pendências financeiras no sistema...
    </div>

    <!-- Erro ou Sem Unidade -->
    <div v-else-if="unidades.length === 0" class="bg-white rounded-2xl p-12 text-center border border-slate-200 shadow-sm">
      <svg class="w-12 h-12 text-slate-300 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
      </svg>
      <h3 class="text-base font-bold text-slate-700">Nenhuma unidade vinculada</h3>
      <p class="text-xs text-slate-400 mt-1">Seu cadastro não possui nenhuma casa ou unidade vinculada. Procure o síndico.</p>
    </div>

    <div v-else-if="extrato" class="space-y-6">
      <!-- Status Card Principal -->
      <div
        class="p-6 rounded-2xl border shadow-sm flex flex-col md:flex-row items-center justify-between gap-6"
        :class="extrato.esta_em_dia ? 'bg-emerald-50/70 border-emerald-200' : 'bg-rose-50/70 border-rose-200'"
      >
        <div class="flex items-start gap-4">
          <div
            class="w-12 h-12 rounded-2xl flex items-center justify-center flex-shrink-0 shadow-inner"
            :class="extrato.esta_em_dia ? 'bg-emerald-100 text-emerald-600' : 'bg-rose-100 text-rose-600'"
          >
            <svg v-if="extrato.esta_em_dia" class="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <svg v-else class="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>

          <div>
            <div class="flex items-center gap-2">
              <h2 class="text-lg font-bold" :class="extrato.esta_em_dia ? 'text-emerald-950' : 'text-rose-950'">
                {{ extrato.unidade.identificador }} - {{ extrato.esta_em_dia ? 'Situação Regular (Adimplente)' : 'Débitos Pendentes em Atraso' }}
              </h2>
              <span
                class="px-2.5 py-0.5 rounded-full text-[11px] font-bold uppercase"
                :class="extrato.esta_em_dia ? 'bg-emerald-200 text-emerald-800' : 'bg-rose-200 text-rose-800'"
              >
                {{ extrato.esta_em_dia ? 'Em dia' : 'Inadimplente' }}
              </span>
            </div>
            <p class="text-xs mt-1" :class="extrato.esta_em_dia ? 'text-emerald-800' : 'text-rose-800'">
              {{ extrato.esta_em_dia
                ? 'Parabéns! Não consta nenhuma taxa condominial pendente para a sua casa até a presente data.'
                : `Constam ${extrato.qtd_titulos} cota(s) pendente(s) com vencimento expirado. Saldo total atualizado: ${formatMoeda(extrato.totais.total_geral)}.`
              }}
            </p>
          </div>
        </div>

        <!-- Ação do Botão Principal -->
        <div class="flex-shrink-0 w-full md:w-auto">
          <!-- Se estiver em dia: Emitir Nada Consta -->
          <button
            v-if="extrato.esta_em_dia"
            @click="emitirNadaConsta"
            :disabled="emitindoNadaConsta"
            class="w-full md:w-auto px-5 py-3 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white rounded-xl text-xs font-bold shadow-lg shadow-emerald-700/20 inline-flex items-center justify-center gap-2 transition"
          >
            <svg v-if="emitindoNadaConsta" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {{ emitindoNadaConsta ? 'Gerando Certidão...' : 'Emitir Declaração de Nada Consta (PDF)' }}
          </button>

          <!-- Se estiver com débitos: Baixar Espelho do Aviso de Débito em PDF -->
          <button
            v-else
            @click="baixarAvisoDebito"
            :disabled="baixandoPdf"
            class="w-full md:w-auto px-5 py-3 bg-rose-600 hover:bg-rose-700 disabled:opacity-50 text-white rounded-xl text-xs font-bold shadow-lg shadow-rose-700/20 inline-flex items-center justify-center gap-2 transition"
          >
            <svg v-if="baixandoPdf" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            {{ baixandoPdf ? 'Baixando...' : 'Baixar Aviso de Débito em PDF' }}
          </button>
        </div>
      </div>

      <!-- Tabela Analítica de Débitos (Exibida se houver inadimplência) -->
      <div v-if="!extrato.esta_em_dia" class="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div class="p-5 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h3 class="font-bold text-slate-800 text-sm">Demonstrativo Detalhado de Títulos Vencidos</h3>
            <p class="text-xs text-slate-400 mt-0.5">Encargos apurados até {{ formatData(extrato.data_atualizacao) }}</p>
          </div>
          <span class="text-xs font-semibold text-rose-700 bg-rose-50 px-3 py-1 rounded-full border border-rose-200">
            Total a Pagar: {{ formatMoeda(extrato.totais.total_geral) }}
          </span>
        </div>

        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs border-collapse">
            <thead class="bg-slate-50 text-slate-600 font-bold border-b">
              <tr>
                <th class="p-3 text-center">Item</th>
                <th class="p-3">Referência</th>
                <th class="p-3">Vencimento</th>
                <th class="p-3 text-center">Dias Vencidos</th>
                <th class="p-3 text-right">Taxa (R$)</th>
                <th class="p-3 text-right">Multa (R$)</th>
                <th class="p-3 text-right">Juros (R$)</th>
                <th class="p-3 text-right">Total (R$)</th>
                <th class="p-3">Observações</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr v-for="it in extrato.itens" :key="it.cota_id" class="hover:bg-slate-50/80">
                <td class="p-3 text-center font-bold text-slate-600">{{ it.item }}</td>
                <td class="p-3 font-semibold text-slate-800">{{ it.periodo_rotulo }}</td>
                <td class="p-3 text-slate-700">{{ formatData(it.vencimento) }}</td>
                <td class="p-3 text-center text-slate-700">{{ it.dias_atraso }}</td>
                <td class="p-3 text-right text-slate-700">{{ formatMoeda(it.taxa) }}</td>
                <td class="p-3 text-right text-slate-700">{{ formatMoeda(it.multa) }}</td>
                <td class="p-3 text-right text-slate-700">{{ formatMoeda(it.juros) }}</td>
                <td class="p-3 text-right font-bold text-rose-700">{{ formatMoeda(it.total) }}</td>
                <td class="p-3 text-slate-500 italic">{{ it.observacao || '-' }}</td>
              </tr>
            </tbody>
            <tfoot class="bg-slate-50 text-slate-800 font-bold border-t">
              <tr>
                <td colspan="4" class="p-3 text-left">SUBTOTAIS E SALDO DEVEDOR:</td>
                <td class="p-3 text-right">{{ formatMoeda(extrato.totais.taxa) }}</td>
                <td class="p-3 text-right">{{ formatMoeda(extrato.totais.multa) }}</td>
                <td class="p-3 text-right">{{ formatMoeda(extrato.totais.juros) }}</td>
                <td class="p-3 text-right text-rose-700 text-sm">{{ formatMoeda(extrato.totais.total_geral) }}</td>
                <td></td>
              </tr>
            </tfoot>
          </table>
        </div>

        <!-- Orientações de Pagamento e Contato -->
        <div class="p-5 bg-amber-50/70 border-t border-amber-200 text-xs text-amber-900 space-y-1">
          <p class="font-bold mb-1">Orientações da Administração:</p>
          <p>• {{ extrato.parametro?.prazo_negociacao_info }}</p>
          <p>• {{ extrato.parametro?.aviso_protesto_info }}</p>
          <p v-if="extrato.sujeito_ajuizamento" class="font-bold text-rose-800">
            • {{ extrato.parametro?.aviso_ajuizamento_info }}
          </p>
          <div class="pt-2 text-slate-700">
            <b>Canal para envio de comprovantes e acordos:</b> {{ extrato.parametro?.email_cobranca }}
            <span v-if="extrato.parametro?.telefone_cobranca"> | WhatsApp: {{ extrato.parametro?.telefone_cobranca }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue"
import apiClient from "@/api/client"
import { financeiroApi } from "@/api/financeiro"

const unidades = ref([])
const unidadeSelecionadaId = ref(null)
const extrato = ref(null)
const carregando = ref(false)
const baixandoPdf = ref(false)
const emitindoNadaConsta = ref(false)

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

const carregarUnidades = async () => {
  carregando.value = true
  try {
    const res = await apiClient.get("/auth/me/")
    unidades.value = res.data.unidades_vinculadas || []
    if (unidades.value.length > 0) {
      unidadeSelecionadaId.value = unidades.value[0].unidade_id
      await carregarExtrato()
    }
  } catch (err) {
    console.error("Erro ao carregar unidades do morador:", err)
  } finally {
    carregando.value = false
  }
}

const carregarExtrato = async () => {
  if (!unidadeSelecionadaId.value) return
  carregando.value = true
  try {
    const res = await financeiroApi.getInadimplenciaUnidade(unidadeSelecionadaId.value)
    extrato.value = res.data
  } catch (err) {
    console.error("Erro ao carregar extrato da unidade:", err)
  } finally {
    carregando.value = false
  }
}

const baixarAvisoDebito = async () => {
  if (!unidadeSelecionadaId.value) return
  baixandoPdf.value = true
  try {
    const res = await financeiroApi.getAvisoDebitoPdf(unidadeSelecionadaId.value)
    const blob = new Blob([res.data], { type: "application/pdf" })
    const url = URL.createObjectURL(blob)
    const link = document.createElement("a")
    link.href = url
    link.download = `aviso_debito_${extrato.value?.unidade?.identificador?.replace(/\s+/g, '_')?.toLowerCase() || 'unidade'}.pdf`
    link.click()
    URL.revokeObjectURL(url)
  } catch (err) {
    console.error("Erro ao baixar PDF:", err)
    alert("Erro ao gerar o PDF de aviso de débito.")
  } finally {
    baixandoPdf.value = false
  }
}

const emitirNadaConsta = async () => {
  if (!unidadeSelecionadaId.value) return
  emitindoNadaConsta.value = true
  try {
    const res = await financeiroApi.emitirNadaConsta(unidadeSelecionadaId.value)
    if (res.data.sucesso) {
      const pdfRes = await financeiroApi.getNadaConstaPdf(res.data.certidao.id)
      const blob = new Blob([pdfRes.data], { type: "application/pdf" })
      const url = URL.createObjectURL(blob)
      const link = document.createElement("a")
      link.href = url
      link.download = `nada_consta_${extrato.value?.unidade?.identificador?.replace(/\s+/g, '_')?.toLowerCase() || 'certidao'}.pdf`
      link.click()
      URL.revokeObjectURL(url)
    }
  } catch (err) {
    console.error("Erro ao emitir nada consta:", err)
    alert(err.response?.data?.detail || "Não foi possível emitir a Certidão de Nada Consta.")
  } finally {
    emitindoNadaConsta.value = false
  }
}

onMounted(() => {
  carregarUnidades()
})
</script>
