<template>
  <div class="space-y-6">
    <!-- Header com Seletor de Período -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-slate-800 tracking-tight flex items-center gap-2">
          <span class="p-2 bg-emerald-100 text-emerald-700 rounded-lg">
            <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
          </span>
          Lançamento de Pagamentos & Receitas
        </h1>
        <p class="text-sm text-slate-500 mt-1">
          Substitui a aba PAGAMENTOS da planilha. Baixa de cotas, isenções por mandato, cálculo de juros/multas e receitas extras.
        </p>
      </div>

      <!-- Seletor de Período -->
      <div class="flex items-center gap-3">
        <label class="text-xs font-semibold text-slate-500 uppercase">Período:</label>
        <select
          v-model="selectedPeriodoId"
          @change="changePeriodo"
          class="bg-white border border-slate-300 rounded-lg px-3 py-2 text-sm font-semibold text-slate-800 shadow-sm focus:ring-1 focus:ring-blue-500"
        >
          <option v-for="p in periodos" :key="p.id" :value="p.id">
            {{ p.mes_referencia_rotulo }} ({{ p.status }})
          </option>
        </select>
      </div>
    </div>

    <!-- Banner Informativo / Período Bloqueado -->
    <div
      v-if="currentPeriodo && currentPeriodo.status !== 'ABERTO'"
      class="bg-blue-50 border border-blue-200 text-blue-800 p-4 rounded-xl text-xs flex items-center justify-between"
    >
      <div class="flex items-center gap-2">
        <svg class="w-5 h-5 text-blue-600 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
        </svg>
        <span>
          Este período está com status <strong>{{ currentPeriodo.status }}</strong>. Os valores estão congelados para garantir a integridade histórica.
        </span>
      </div>
      <router-link
        :to="`/prestacao/relatorio/${currentPeriodo.id}`"
        class="px-3 py-1 bg-blue-600 text-white rounded text-xs font-medium hover:bg-blue-700 transition"
      >
        Ver Prestação
      </router-link>
    </div>

    <!-- Navegação em Abas (Cotas das 52 Unidades / Receitas Extras) -->
    <div class="flex border-b border-slate-200">
      <button
        @click="activeTab = 'cotas'"
        class="py-3 px-6 text-sm font-bold border-b-2 transition flex items-center gap-2"
        :class="activeTab === 'cotas' ? 'border-emerald-600 text-emerald-700' : 'border-transparent text-slate-500 hover:text-slate-700'"
      >
        <span>Cotas do Mês ({{ cotas.length }} Unidades)</span>
        <span class="text-xs px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 font-normal">
          {{ cotasPagasCount }} pagas
        </span>
        <span v-if="cotasIsentasCount > 0" class="text-xs px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 font-bold">
          {{ cotasIsentasCount }} isenta{{ cotasIsentasCount > 1 ? 's' : '' }}
        </span>
      </button>

      <button
        @click="activeTab = 'extras'"
        class="py-3 px-6 text-sm font-bold border-b-2 transition flex items-center gap-2"
        :class="activeTab === 'extras' ? 'border-emerald-600 text-emerald-700' : 'border-transparent text-slate-500 hover:text-slate-700'"
      >
        <span>Receitas Extras & Atrasos ({{ receitasExtras.length }})</span>
        <span class="text-xs px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 font-semibold">
          R$ {{ formatMoney(totalExtrasCalculado) }}
        </span>
      </button>
    </div>

    <!-- ================= ABA 1: COTAS REGULARES ================= -->
    <div v-if="activeTab === 'cotas'" class="space-y-4">
      <!-- Barra de Ferramentas / Marcação em Massa e Filtros -->
      <div class="bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-3">
        <!-- Filtros -->
        <div class="flex flex-wrap items-center gap-2">
          <input
            type="text"
            v-model="searchQuery"
            placeholder="Buscar por unidade..."
            class="text-xs border rounded-lg px-3 py-1.5 w-44 focus:ring-1 focus:ring-blue-500"
          />

          <select
            v-model="filterStatus"
            class="text-xs border rounded-lg px-3 py-1.5 focus:ring-1 focus:ring-blue-500 font-medium"
          >
            <option value="ALL">Todas as Cotas</option>
            <option value="PAGO">Somente Pagas</option>
            <option value="PENDENTE">Somente Pendentes</option>
            <option value="ISENTO">Somente Isentas</option>
          </select>
        </div>

        <!-- Ação em massa com botão de Dar Baixa e Remover Baixa -->
        <div v-if="currentPeriodo?.status === 'ABERTO'" class="flex flex-wrap items-center gap-2">
          <span class="text-xs text-slate-500 font-medium">
            Selecionadas: <strong>{{ selectedCotaIds.length }}</strong>
          </span>
          <input
            type="date"
            v-model="batchDataPagamento"
            class="text-xs border rounded-lg px-2 py-1.5"
            title="Data aplicada na baixa em massa"
          />
          <button
            @click="marcarEmMassa('BAIXAR')"
            :disabled="selectedCotaIds.length === 0 || isUpdating"
            class="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold transition disabled:opacity-50 shadow-sm flex items-center gap-1"
          >
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
            Baixar Selecionadas
          </button>
          <button
            @click="marcarEmMassa('REMOVER_BAIXA')"
            :disabled="selectedCotaIds.length === 0 || isUpdating"
            class="px-3 py-1.5 bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 rounded-lg text-xs font-semibold transition disabled:opacity-50 shadow-sm flex items-center gap-1"
          >
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
            Remover Baixa
          </button>
        </div>
      </div>

      <!-- Tabela Editável das Unidades -->
      <div class="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
        <div class="overflow-x-auto max-h-[600px] overflow-y-auto">
          <table class="w-full text-left border-collapse text-xs">
            <thead class="sticky top-0 bg-slate-900 text-white z-10">
              <tr>
                <th class="py-2.5 px-3 w-10 text-center">
                  <input
                    type="checkbox"
                    :checked="allFilteredSelected"
                    @change="toggleSelectAll"
                    class="rounded text-blue-600 focus:ring-0"
                  />
                </th>
                <th class="py-2.5 px-3 w-12 text-center">Nº</th>
                <th class="py-2.5 px-3">Unidade</th>
                <th class="py-2.5 px-3">Mês Ref.</th>
                <th class="py-2.5 px-3">Vencimento</th>
                <th class="py-2.5 px-3">Valor Título</th>
                <th class="py-2.5 px-3">Data Pagto</th>
                <th class="py-2.5 px-3">Cota (R$)</th>
                <th class="py-2.5 px-3">Valor Pago (R$)</th>
                <th class="py-2.5 px-3">Juros/Multa (R$)</th>
                <th class="py-2.5 px-3">Observação</th>
                <th class="py-2.5 px-3 text-center w-36">Ação de Baixa</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-200">
              <tr
                v-for="cota in filteredCotas"
                :key="cota.id"
                class="hover:bg-slate-50 transition-colors"
                :class="{
                  'bg-amber-50/40': cota.isento,
                  'bg-emerald-50/20': cota.data_pagamento && !cota.isento,
                  'bg-white': !cota.data_pagamento && !cota.isento
                }"
              >
                <!-- Checkbox -->
                <td class="py-2 px-3 text-center">
                  <input
                    v-if="!cota.isento"
                    type="checkbox"
                    :value="cota.id"
                    v-model="selectedCotaIds"
                    class="rounded text-blue-600 focus:ring-0"
                  />
                  <span v-else class="text-amber-500 font-bold" title="Isento de condomínio">•</span>
                </td>

                <!-- Nº -->
                <td class="py-2 px-3 text-center font-bold text-slate-700">
                  {{ cota.numero_ordem }}
                </td>

                <!-- Identificador Unidade + Badge Isento -->
                <td class="py-2 px-3 whitespace-nowrap">
                  <div class="flex items-center gap-1.5">
                    <span class="font-semibold text-slate-800">{{ cota.unidade_identificador }}</span>
                    <span
                      v-if="cota.isento"
                      class="px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300"
                      title="Isenção pelo mandato de gestão condominial"
                    >
                      ISENTO
                    </span>
                  </div>
                </td>

                <!-- Mês Ref -->
                <td class="py-2 px-3 text-slate-500 whitespace-nowrap">
                  {{ formatDate(cota.mes_referencia) }}
                </td>

                <!-- Vencimento -->
                <td class="py-2 px-3 text-slate-500 whitespace-nowrap">
                  {{ formatDate(cota.data_vencimento) }}
                </td>

                <!-- Valor Título -->
                <td class="py-2 px-3 text-slate-700 font-medium whitespace-nowrap font-mono">
                  R$ {{ formatMoney(cota.valor_titulo) }}
                </td>

                <!-- Data Pagamento -->
                <td class="py-2 px-2">
                  <input
                    type="date"
                    v-model="cota.data_pagamento"
                    @change="onDataPagamentoChange(cota)"
                    :disabled="currentPeriodo?.status !== 'ABERTO' || cota.isento"
                    class="border rounded px-2 py-1 text-xs w-32 focus:ring-1 focus:ring-blue-500 disabled:bg-slate-100 disabled:text-slate-400"
                  />
                </td>

                <!-- Cota Regular Base (com Máscara) -->
                <td class="py-2 px-2">
                  <div class="relative">
                    <span class="absolute left-1.5 top-1/2 -translate-y-1/2 text-slate-400 text-[10px]">R$</span>
                    <input
                      type="text"
                      :value="formatMoney(cota.cota)"
                      @input="onMoneyInput($event, cota, 'cota')"
                      @blur="recalculateRow(cota)"
                      :disabled="currentPeriodo?.status !== 'ABERTO' || cota.isento"
                      placeholder="0,00"
                      class="border rounded pl-6 pr-2 py-1 text-xs w-24 text-right font-mono focus:ring-1 focus:ring-blue-500 disabled:bg-slate-100 disabled:text-slate-400"
                    />
                  </div>
                </td>

                <!-- Valor Pago Efetivo (com Máscara) -->
                <td class="py-2 px-2">
                  <div class="relative">
                    <span class="absolute left-1.5 top-1/2 -translate-y-1/2 text-slate-400 text-[10px]">R$</span>
                    <input
                      type="text"
                      :value="formatMoney(cota.valor_pago)"
                      @input="onMoneyInput($event, cota, 'valor_pago')"
                      @blur="recalculateRow(cota)"
                      :disabled="currentPeriodo?.status !== 'ABERTO' || cota.isento"
                      placeholder="0,00"
                      class="border rounded pl-6 pr-2 py-1 text-xs w-24 text-right font-mono font-bold text-slate-800 focus:ring-1 focus:ring-blue-500 disabled:bg-slate-100 disabled:text-slate-400"
                    />
                  </div>
                </td>

                <!-- Juros / Multa -->
                <td class="py-2 px-3 whitespace-nowrap font-mono text-right">
                  <span
                    class="font-semibold"
                    :class="cota.juros_multa > 0 ? 'text-rose-600' : 'text-slate-400'"
                  >
                    R$ {{ formatMoney(cota.juros_multa) }}
                  </span>
                </td>

                <!-- Observação -->
                <td class="py-2 px-2">
                  <input
                    type="text"
                    v-model="cota.observacao"
                    @change="saveCota(cota)"
                    :disabled="currentPeriodo?.status !== 'ABERTO' || cota.isento"
                    placeholder="Obs..."
                    class="border rounded px-2 py-1 text-xs w-full min-w-[140px] focus:ring-1 focus:ring-blue-500 disabled:bg-slate-100 disabled:text-slate-400"
                  />
                </td>

                <!-- Coluna de Ação com Botões Explícitos -->
                <td class="py-2 px-3 text-center whitespace-nowrap">
                  <!-- Caso 1: Unidade Isenta -->
                  <div v-if="cota.isento" class="text-center">
                    <span class="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold text-amber-800 bg-amber-100">
                      Isento pelo Mandato
                    </span>
                  </div>

                  <!-- Caso 2: Cota Paga -> Botão [ Remover Baixa ] -->
                  <div v-else-if="cota.data_pagamento" class="flex items-center justify-center gap-1.5">
                    <button
                      v-if="currentPeriodo?.status === 'ABERTO'"
                      @click="removerBaixa(cota)"
                      class="inline-flex items-center px-2.5 py-1 bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-300 rounded-lg text-xs font-semibold transition shadow-xs"
                      title="Estornar baixa de pagamento"
                    >
                      <svg class="w-3.5 h-3.5 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
                      </svg>
                      Remover Baixa
                    </button>
                    <span v-else class="text-emerald-700 font-bold flex items-center gap-1">
                      ✓ Pago
                    </span>
                  </div>

                  <!-- Caso 3: Cota Pendente -> Botão [ Dar Baixa ] -->
                  <div v-else class="flex items-center justify-center">
                    <button
                      v-if="currentPeriodo?.status === 'ABERTO'"
                      @click="darBaixa(cota)"
                      class="inline-flex items-center px-2.5 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold transition shadow-sm"
                      title="Dar baixa no pagamento da cota"
                    >
                      <svg class="w-3.5 h-3.5 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                      </svg>
                      Dar Baixa
                    </button>
                    <span v-else class="text-slate-400 font-medium">
                      Pendente
                    </span>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Rodapé com Totalizadores da Planilha -->
        <div class="bg-slate-900 text-white p-4 flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs">
          <div class="flex items-center gap-6 flex-wrap">
            <div>
              <span class="text-slate-400 block">Total Cotas Regulares:</span>
              <strong class="text-base text-emerald-400 font-bold font-mono">
                R$ {{ formatMoney(totalCotasCalculado) }}
              </strong>
            </div>
            <div>
              <span class="text-slate-400 block">Outras Receitas (Extras):</span>
              <strong class="text-base text-amber-300 font-bold font-mono">
                R$ {{ formatMoney(totalExtrasCalculado) }}
              </strong>
            </div>
            <div>
              <span class="text-slate-400 block">Total Geral das Receitas:</span>
              <strong class="text-base text-white font-bold font-mono">
                R$ {{ formatMoney(totalGeralReceitas) }}
              </strong>
            </div>
          </div>

          <div class="text-slate-400">
            {{ cotasPagasCount }} de {{ totalCotasPagantesCount }} cotas quitadas
            <span v-if="cotasIsentasCount > 0" class="text-amber-400 font-semibold ml-1">
              ({{ cotasIsentasCount }} isenta{{ cotasIsentasCount > 1 ? 's' : '' }})
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- ================= ABA 2: RECEITAS EXTRAS ================= -->
    <div v-if="activeTab === 'extras'" class="space-y-4">
      <div class="bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex items-center justify-between">
        <div>
          <h3 class="font-bold text-slate-800 text-sm">Lançamento de Receitas Extras & Atrasos</h3>
          <p class="text-xs text-slate-500">
            Aluguel de vagas (R$ 100,00), rendimento CDB e juros de cotas anteriores recebidas em atraso.
          </p>
        </div>

        <button
          v-if="currentPeriodo?.status === 'ABERTO'"
          @click="openExtraModal()"
          class="px-3.5 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold transition shadow-sm flex items-center gap-1"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          Nova Receita Extra
        </button>
      </div>

      <!-- Tabela de Extras -->
      <div class="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
        <table class="w-full text-left border-collapse text-xs">
          <thead class="bg-slate-50 border-b border-slate-200 uppercase tracking-wider text-slate-500 font-semibold">
            <tr>
              <th class="py-3 px-4">Descrição da Entrada</th>
              <th class="py-3 px-4">Tipo</th>
              <th class="py-3 px-4">Unidade Relacionada</th>
              <th class="py-3 px-4">Data</th>
              <th class="py-3 px-4 text-right">Valor (R$)</th>
              <th class="py-3 px-4 text-right" v-if="currentPeriodo?.status === 'ABERTO'">Ações</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-200">
            <tr v-if="receitasExtras.length === 0">
              <td colspan="6" class="p-6 text-center text-slate-400">
                Nenhuma receita extra lançada neste período.
              </td>
            </tr>
            <tr v-for="extra in receitasExtras" :key="extra.id" class="hover:bg-slate-50">
              <td class="py-3 px-4 font-bold text-slate-800">
                {{ extra.descricao }}
              </td>
              <td class="py-3 px-4 text-slate-600">
                <span class="px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-100 text-slate-700">
                  {{ extra.tipo_display || extra.tipo }}
                </span>
              </td>
              <td class="py-3 px-4 text-slate-700">
                {{ extra.unidade_identificador || '-' }}
              </td>
              <td class="py-3 px-4 text-slate-500">
                {{ formatDate(extra.data) }}
              </td>
              <td class="py-3 px-4 font-bold text-emerald-700 font-mono text-right">
                R$ {{ formatMoney(extra.valor) }}
              </td>
              <td class="py-3 px-4 text-right space-x-2" v-if="currentPeriodo?.status === 'ABERTO'">
                <button @click="openExtraModal(extra)" class="text-blue-600 hover:underline font-semibold">Editar</button>
                <button @click="deleteExtra(extra)" class="text-rose-600 hover:underline font-semibold">Excluir</button>
              </td>
            </tr>
          </tbody>
          <tfoot class="bg-slate-50 border-t border-slate-200 font-bold">
            <tr>
              <td colspan="4" class="py-3 px-4 text-slate-700 uppercase text-[11px]">TOTAL OUTRAS RECEITAS:</td>
              <td class="py-3 px-4 text-emerald-700 font-mono text-right text-sm">R$ {{ formatMoney(totalExtrasCalculado) }}</td>
              <td v-if="currentPeriodo?.status === 'ABERTO'"></td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>

    <!-- Modal Receita Extra com Máscara de Moeda -->
    <div v-if="showExtraModal" class="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div class="bg-white rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl border border-slate-200">
        <h3 class="font-bold text-base text-slate-800">
          {{ editingExtraId ? 'Editar Receita Extra' : 'Nova Receita Extra' }}
        </h3>
        <form @submit.prevent="saveExtra" class="space-y-3 text-xs">
          <div>
            <label class="block font-medium text-slate-700 mb-1">Descrição *</label>
            <input
              type="text"
              v-model="extraForm.descricao"
              required
              placeholder="Ex: COTA REF. ALUGUEL - CASA 23"
              class="w-full border rounded-xl p-2.5 focus:ring-1 focus:ring-blue-500"
            />
          </div>

          <div>
            <label class="block font-medium text-slate-700 mb-1">Tipo de Receita *</label>
            <select v-model="extraForm.tipo" class="w-full border rounded-xl p-2.5 focus:ring-1 focus:ring-blue-500">
              <option value="ALUGUEL_VAGA">Aluguel de Vaga de Estacionamento</option>
              <option value="JUROS_MULTA">Juros e Multa de Atraso</option>
              <option value="COTA_ATRASADA">Cota Atrasada de Mês Anterior</option>
              <option value="RENDIMENTO_CDB">Rendimento Investimento CDB</option>
              <option value="OUTRO">Outra Receita Extra</option>
            </select>
          </div>

          <div>
            <label class="block font-medium text-slate-700 mb-1">Valor (R$) *</label>
            <div class="relative">
              <span class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 font-semibold text-xs">R$</span>
              <input
                type="text"
                :value="formatMoney(extraForm.valor)"
                @input="onMoneyInput($event, extraForm, 'valor')"
                required
                class="w-full pl-9 pr-3 py-2 border rounded-xl font-bold font-mono focus:ring-1 focus:ring-blue-500"
              />
            </div>
          </div>

          <div>
            <label class="block font-medium text-slate-700 mb-1">Data do Recebimento *</label>
            <input
              type="date"
              v-model="extraForm.data"
              required
              class="w-full border rounded-xl p-2.5 focus:ring-1 focus:ring-blue-500"
            />
          </div>

          <div class="pt-3 flex justify-end gap-2 border-t">
            <button
              type="button"
              @click="showExtraModal = false"
              class="px-4 py-2 border rounded-xl text-slate-600 hover:bg-slate-50 transition"
            >
              Cancelar
            </button>
            <button
              type="submit"
              class="px-5 py-2 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 transition shadow"
            >
              Salvar Entrada
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
const isUpdating = ref(false)
const periodos = ref([])
const selectedPeriodoId = ref(null)
const currentPeriodo = ref(null)
const activeTab = ref("cotas")

const cotas = ref([])
const receitasExtras = ref([])
const selectedCotaIds = ref([])
const batchDataPagamento = ref(new Date().toISOString().substring(0, 10))

const searchQuery = ref("")
const filterStatus = ref("ALL")

// Receita Extra Modal
const showExtraModal = ref(false)
const editingExtraId = ref(null)
const extraForm = ref({
  descricao: "",
  tipo: "ALUGUEL_VAGA",
  valor: 100.00,
  data: new Date().toISOString().substring(0, 10),
  unidade: null,
})

function formatDate(val) {
  if (!val) return "-"
  const d = new Date(val + "T00:00:00")
  return d.toLocaleDateString("pt-BR")
}

function formatMoney(val) {
  if (val === undefined || val === null || val === "") return "0,00"
  return Number(val).toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function onMoneyInput(e, targetObj, key) {
  let val = e.target.value.replace(/\D/g, "")
  if (!val) {
    targetObj[key] = 0
    e.target.value = "0,00"
    return
  }
  let num = parseInt(val, 10) / 100
  targetObj[key] = num
  e.target.value = num.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const filteredCotas = computed(() => {
  return cotas.value.filter(c => {
    if (filterStatus.value === "ISENTO" && !c.isento) return false
    if (filterStatus.value === "PAGO" && (!c.data_pagamento || c.isento)) return false
    if (filterStatus.value === "PENDENTE" && (c.data_pagamento || c.isento)) return false
    if (searchQuery.value) {
      const q = searchQuery.value.toLowerCase()
      const unid = (c.unidade_identificador || "").toLowerCase()
      const obs = (c.observacao || "").toLowerCase()
      return unid.includes(q) || obs.includes(q) || String(c.numero_ordem).includes(q)
    }
    return true
  })
})

const allFilteredSelected = computed(() => {
  const eligible = filteredCotas.value.filter(c => !c.isento)
  if (!eligible.length) return false
  return eligible.every(c => selectedCotaIds.value.includes(c.id))
})

function toggleSelectAll(e) {
  if (e.target.checked) {
    const ids = filteredCotas.value.filter(c => !c.isento).map(c => c.id)
    selectedCotaIds.value = Array.from(new Set([...selectedCotaIds.value, ...ids]))
  } else {
    const unselectIds = filteredCotas.value.map(c => c.id)
    selectedCotaIds.value = selectedCotaIds.value.filter(id => !unselectIds.includes(id))
  }
}

const cotasPagasCount = computed(() => {
  return cotas.value.filter(c => c.data_pagamento && !c.isento).length
})

const cotasIsentasCount = computed(() => {
  return cotas.value.filter(c => c.isento).length
})

const totalCotasPagantesCount = computed(() => {
  return cotas.value.filter(c => !c.isento).length
})

// Exclui completamente as cotas isentas do somatório regular
const totalCotasCalculado = computed(() => {
  return cotas.value.reduce((acc, c) => {
    if (c.data_pagamento && !c.isento) {
      return acc + (Number(c.cota) || Number(c.valor_titulo) || 0)
    }
    return acc
  }, 0)
})

const totalExtrasCalculado = computed(() => {
  return receitasExtras.value.reduce((acc, e) => acc + (Number(e.valor) || 0), 0)
})

const totalGeralReceitas = computed(() => {
  return totalCotasCalculado.value + totalExtrasCalculado.value
})

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

async function loadData() {
  if (!selectedPeriodoId.value) return
  loading.value = true
  try {
    currentPeriodo.value = periodos.value.find(p => p.id === selectedPeriodoId.value)

    const [cotasRes, extrasRes] = await Promise.all([
      financeiroApi.getCotas({ periodo: selectedPeriodoId.value }),
      financeiroApi.getReceitasExtras({ periodo: selectedPeriodoId.value }),
    ])
    cotas.value = cotasRes.data.results || cotasRes.data
    receitasExtras.value = extrasRes.data.results || extrasRes.data
  } catch (err) {
    console.error("Erro ao carregar pagamentos:", err)
  } finally {
    loading.value = false
  }
}

function changePeriodo() {
  router.push(`/prestacao/pagamentos/${selectedPeriodoId.value}`)
  loadData()
}

// Ação explícita de Dar Baixa com confirmação/data padrão
async function darBaixa(cota) {
  if (cota.isento) return
  const dataPgto = batchDataPagamento.value || new Date().toISOString().substring(0, 10)
  try {
    const res = await financeiroApi.darBaixaCota(cota.id, {
      data_pagamento: dataPgto,
      valor_pago: cota.valor_titulo,
      cota: cota.valor_titulo,
    })
    Object.assign(cota, res.data)
  } catch (err) {
    alert(err.response?.data?.error || "Erro ao dar baixa na cota.")
  }
}

// Ação explícita de Remover Baixa
async function removerBaixa(cota) {
  if (!confirm(`Deseja remover a baixa da unidade ${cota.unidade_identificador}?`)) return
  try {
    const res = await financeiroApi.removerBaixaCota(cota.id)
    Object.assign(cota, res.data)
  } catch (err) {
    alert(err.response?.data?.error || "Erro ao remover baixa da cota.")
  }
}

function onDataPagamentoChange(cota) {
  if (cota.isento) return
  if (cota.data_pagamento) {
    if (!cota.cota) cota.cota = cota.valor_titulo
    if (!cota.valor_pago) cota.valor_pago = cota.valor_titulo
    cota.status = "PAGO"
  } else {
    cota.cota = null
    cota.valor_pago = null
    cota.juros_multa = 0
    cota.status = "PENDENTE"
  }
  recalculateRow(cota)
}

function recalculateRow(cota) {
  if (cota.isento) return
  const cotaBase = Number(cota.cota) || 0
  const vPago = Number(cota.valor_pago) || 0
  if (vPago > cotaBase) {
    cota.juros_multa = Number((vPago - cotaBase).toFixed(2))
  } else {
    cota.juros_multa = 0
  }
  saveCota(cota)
}

async function saveCota(cota) {
  if (cota.isento) return
  try {
    await financeiroApi.updateCota(cota.id, {
      data_pagamento: cota.data_pagamento,
      cota: cota.cota,
      valor_pago: cota.valor_pago,
      juros_multa: cota.juros_multa,
      observacao: cota.observacao,
      status: cota.data_pagamento ? "PAGO" : "PENDENTE",
    })
  } catch (err) {
    console.error("Erro ao salvar cota:", err)
  }
}

async function marcarEmMassa(acao = "BAIXAR") {
  if (acao === "BAIXAR" && !batchDataPagamento.value) {
    alert("Selecione a data de pagamento para a baixa em massa.")
    return
  }
  if (acao === "REMOVER_BAIXA" && !confirm(`Deseja remover a baixa de ${selectedCotaIds.value.length} cota(s) selecionada(s)?`)) {
    return
  }

  isUpdating.value = true
  try {
    const res = await financeiroApi.marcarCotasEmMassa({
      cota_ids: selectedCotaIds.value,
      data_pagamento: batchDataPagamento.value,
      acao: acao,
    })
    selectedCotaIds.value = []
    alert(res.data.message)
    await loadData()
  } catch (err) {
    alert(err.response?.data?.error || "Erro ao processar cotas em massa.")
  } finally {
    isUpdating.value = false
  }
}

// Receitas Extras Modal handlers
function openExtraModal(extra = null) {
  if (extra) {
    editingExtraId.value = extra.id
    extraForm.value = { ...extra }
  } else {
    editingExtraId.value = null
    extraForm.value = {
      periodo: selectedPeriodoId.value,
      descricao: "",
      tipo: "ALUGUEL_VAGA",
      valor: 100.00,
      data: new Date().toISOString().substring(0, 10),
      unidade: null,
    }
  }
  showExtraModal.value = true
}

async function saveExtra() {
  try {
    extraForm.value.periodo = selectedPeriodoId.value
    if (editingExtraId.value) {
      await financeiroApi.updateReceitaExtra(editingExtraId.value, extraForm.value)
    } else {
      await financeiroApi.createReceitaExtra(extraForm.value)
    }
    showExtraModal.value = false
    await loadData()
  } catch (err) {
    alert("Erro ao salvar receita extra.")
  }
}

async function deleteExtra(extra) {
  if (!confirm(`Deseja remover "${extra.descricao}"?`)) return
  try {
    await financeiroApi.deleteReceitaExtra(extra.id)
    await loadData()
  } catch (err) {
    alert("Erro ao excluir receita extra.")
  }
}

onMounted(async () => {
  await loadPeriodos()
  await loadData()
})
</script>
