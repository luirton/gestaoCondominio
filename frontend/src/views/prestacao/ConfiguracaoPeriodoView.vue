<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-slate-800 tracking-tight flex items-center gap-2">
          <span class="p-2 bg-indigo-100 text-indigo-700 rounded-lg">
            <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </span>
          Períodos de Prestação de Contas
        </h1>
        <p class="text-sm text-slate-500 mt-1">
          Configuração de parâmetros de datas, saldos anteriores e bancários por conta e geração das cotas mensais.
        </p>
      </div>

      <button
        @click="openModal()"
        class="inline-flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition shadow-sm"
      >
        <svg class="w-4 h-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        Novo Período
      </button>
    </div>

    <!-- Tabela de Períodos -->
    <div class="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
      <div v-if="loading" class="p-12 text-center text-slate-500">
        <div class="inline-block animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full mb-3"></div>
        <p>Carregando períodos...</p>
      </div>

      <div v-else-if="periodos.length === 0" class="p-12 text-center text-slate-500">
        <p>Nenhum período cadastrado até o momento.</p>
      </div>

      <table v-else class="w-full text-left border-collapse text-sm">
        <thead>
          <tr class="bg-slate-50 border-b border-slate-200 text-xs font-semibold uppercase tracking-wider text-slate-500">
            <th class="py-3 px-4">Referência</th>
            <th class="py-3 px-4">Período de Prestação</th>
            <th class="py-3 px-4">Vencimento Cota</th>
            <th class="py-3 px-4">Cotas Pagas</th>
            <th class="py-3 px-4">Saldo Mês</th>
            <th class="py-3 px-4">Status</th>
            <th class="py-3 px-4 text-right">Ações</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-200">
          <tr v-for="p in periodos" :key="p.id" class="hover:bg-slate-50/80 transition-colors">
            <td class="py-3.5 px-4 font-bold text-slate-800">
              {{ p.mes_referencia_rotulo }}
            </td>
            <td class="py-3.5 px-4 text-slate-600">
              {{ formatDate(p.data_inicio_prestacao) }} a {{ formatDate(p.data_fim_prestacao) }}
            </td>
            <td class="py-3.5 px-4 text-slate-600">
              {{ formatDate(p.data_vencimento) }} (R$ {{ formatMoney(p.valor_cota_total || p.valor_cota_padrao) }})
              <span v-if="p.cota_extra" class="block text-[11px] text-indigo-600 font-medium">
                (Base: R$ {{ formatMoney(p.valor_cota_padrao) }} + Extra: R$ {{ formatMoney(p.cota_extra) }})
              </span>
            </td>
            <td class="py-3.5 px-4">
              <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-slate-100 text-slate-700">
                {{ p.qtd_cotas_pagas }} / {{ p.qtd_cotas_total }}
              </span>
              <span v-if="p.qtd_cotas_isentas" class="ml-1 text-[11px] text-amber-700 font-medium">
                ({{ p.qtd_cotas_isentas }} isenta{{ p.qtd_cotas_isentas > 1 ? 's' : '' }})
              </span>
            </td>
            <td class="py-3.5 px-4 font-bold text-blue-700">
              R$ {{ formatMoney(p.totais?.saldo_mes) }}
            </td>
            <td class="py-3.5 px-4">
              <span
                class="px-2.5 py-0.5 text-xs font-semibold rounded-full"
                :class="{
                  'bg-emerald-100 text-emerald-800': p.status === 'PUBLICADO',
                  'bg-blue-100 text-blue-800': p.status === 'FECHADO',
                  'bg-amber-100 text-amber-800': p.status === 'ABERTO'
                }"
              >
                {{ p.status }}
              </span>
            </td>
            <td class="py-3.5 px-4 text-right space-x-1">
              <button
                v-if="p.status === 'ABERTO' && p.qtd_cotas_total === 0"
                @click="gerarCotas(p)"
                class="px-2.5 py-1 bg-emerald-50 text-emerald-700 hover:bg-emerald-100 rounded text-xs font-medium border border-emerald-200 transition"
                title="Gera cotas para todas as unidades ativas"
              >
                Gerar Cotas
              </button>

              <router-link
                :to="`/prestacao/pagamentos/${p.id}`"
                class="px-2.5 py-1 bg-slate-100 text-slate-700 hover:bg-slate-200 rounded text-xs font-medium transition"
              >
                Pagamentos
              </router-link>

              <router-link
                :to="`/prestacao/relatorio/${p.id}`"
                class="px-2.5 py-1 bg-blue-50 text-blue-700 hover:bg-blue-100 rounded text-xs font-medium border border-blue-200 transition"
              >
                Prestação
              </router-link>

              <button
                @click="openModal(p)"
                class="px-2.5 py-1 text-slate-600 hover:text-slate-800 hover:bg-slate-100 rounded text-xs font-medium border border-slate-200 transition"
                title="Editar parâmetros"
              >
                Editar
              </button>

              <button
                @click="excluirPeriodo(p)"
                class="px-2.5 py-1 text-rose-600 hover:text-rose-800 hover:bg-rose-50 rounded text-xs font-medium border border-rose-200 transition"
                title="Excluir prestação de contas"
              >
                Excluir
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modal de Criação / Edição de Período (Aba PROPRIEDADES) -->
    <div v-if="showModal" class="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div class="bg-white rounded-2xl max-w-4xl w-full shadow-2xl border border-slate-200 overflow-hidden transform transition-all my-8">
        <div class="px-6 py-4 bg-slate-900 text-white flex items-center justify-between">
          <h3 class="font-bold text-base flex items-center gap-2">
            <svg class="w-5 h-5 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            {{ editingId ? 'Editar Parâmetros do Período' : 'Novo Período de Prestação' }}
          </h3>
          <button @click="showModal = false" class="text-slate-400 hover:text-white">
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form @submit.prevent="savePeriodo" class="p-6 space-y-6 max-h-[82vh] overflow-y-auto">
          <!-- Campo Condomínio Vinculado -->
          <div class="p-3 bg-slate-50 rounded-xl border border-slate-200">
            <label class="block text-xs font-bold text-slate-700 mb-1 flex items-center gap-1.5">
              <span>🏢</span> Condomínio *
            </label>
            <select
              v-model="form.condominio"
              @change="onCondominioChange"
              required
              class="w-full text-xs font-bold bg-white border border-slate-300 rounded-lg p-2 text-slate-800 focus:ring-1 focus:ring-blue-500 shadow-xs"
            >
              <option v-for="c in condominiosList" :key="c.id" :value="c.id">
                {{ c.nome }} {{ c.cidade ? `(${c.cidade})` : '' }}
              </option>
            </select>
          </div>

          <!-- Bloco 0: Seleção Automática pelo Rótulo Calendário -->
          <div class="p-4 bg-indigo-50 border border-indigo-200 rounded-xl shadow-sm">
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <label class="block text-xs font-bold text-indigo-900 mb-1">
                  📅 Preenchimento Automático pelo Calendário (Rótulo)
                </label>
                <p class="text-[11px] text-indigo-700">
                  Ao selecionar o mês e ano, preenche automaticamente o rótulo, primeiro/último dia de prestação, referência e vencimentos.
                </p>
              </div>
              <div class="flex items-center gap-2">
                <input
                  type="month"
                  v-model="seletorMesAno"
                  @change="aplicarPreenchimentoAutomaticoDatas"
                  class="text-xs px-3 py-2 border border-indigo-300 rounded-lg bg-white font-bold text-indigo-900 focus:ring-2 focus:ring-indigo-500 shadow-sm"
                />
                <button
                  type="button"
                  @click="aplicarPreenchimentoAutomaticoDatas"
                  class="px-3 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-lg shadow-sm transition"
                >
                  Preencher
                </button>
              </div>
            </div>
          </div>

          <!-- Bloco 1: Datas e Referências -->
          <div>
            <h4 class="text-xs font-bold uppercase tracking-wider text-blue-600 mb-3 border-b pb-1">
              1. Tabela de Datas & Referências
            </h4>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div>
                <label class="block text-xs font-medium text-slate-700 mb-1">Rótulo do Mês *</label>
                <input
                  type="text"
                  v-model="form.mes_referencia_rotulo"
                  placeholder="Ex: SETEMBRO/2026"
                  required
                  class="w-full text-xs border rounded-lg p-2 font-bold focus:ring-1 focus:ring-blue-500"
                />
              </div>

              <div>
                <label class="block text-xs font-medium text-slate-700 mb-1">Mês de Referência (Último dia) *</label>
                <input
                  type="date"
                  v-model="form.mes_referencia"
                  @change="onMesReferenciaChange"
                  required
                  class="w-full text-xs border rounded-lg p-2 focus:ring-1 focus:ring-blue-500"
                />
              </div>

              <div>
                <label class="block text-xs font-medium text-slate-700 mb-1">Data de Vencimento da Cota *</label>
                <input
                  type="date"
                  v-model="form.data_vencimento"
                  required
                  class="w-full text-xs border rounded-lg p-2 focus:ring-1 focus:ring-blue-500"
                />
              </div>

              <div>
                <label class="block text-xs font-medium text-slate-700 mb-1">Início da Prestação (1º dia) *</label>
                <input
                  type="date"
                  v-model="form.data_inicio_prestacao"
                  required
                  class="w-full text-xs border rounded-lg p-2 focus:ring-1 focus:ring-blue-500"
                />
              </div>

              <div>
                <label class="block text-xs font-medium text-slate-700 mb-1">Fim da Prestação (Último dia) *</label>
                <input
                  type="date"
                  v-model="form.data_fim_prestacao"
                  required
                  class="w-full text-xs border rounded-lg p-2 focus:ring-1 focus:ring-blue-500"
                />
              </div>

              <div>
                <label class="block text-xs font-medium text-slate-700 mb-1">Data do Saldo Bancário Final</label>
                <input
                  type="date"
                  v-model="form.data_saldo_bancario"
                  class="w-full text-xs border rounded-lg p-2 focus:ring-1 focus:ring-blue-500"
                />
              </div>

              <div>
                <label class="block text-xs font-medium text-slate-700 mb-1">Mês Próx. Vencimento</label>
                <input
                  type="text"
                  v-model="form.mes_prox_vencimento"
                  placeholder="Ex: OUTUBRO"
                  class="w-full text-xs border rounded-lg p-2 focus:ring-1 focus:ring-blue-500"
                />
              </div>

              <div>
                <label class="block text-xs font-medium text-slate-700 mb-1">Data Próx. Vencimento</label>
                <input
                  type="date"
                  v-model="form.data_prox_vencimento"
                  class="w-full text-xs border rounded-lg p-2 focus:ring-1 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>

          <!-- Bloco 2: Valores Parametrizados da Cota -->
          <div>
            <h4 class="text-xs font-bold uppercase tracking-wider text-blue-600 mb-3 border-b pb-1">
              2. Valores Parametrizados da Cota
            </h4>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <label class="block text-xs font-medium text-slate-700 mb-1">Valor Padrão da Cota *</label>
                <div class="relative">
                  <span class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 font-semibold text-xs">R$</span>
                  <input
                    type="text"
                    :value="formatMoney(form.valor_cota_padrao)"
                    @input="onMoneyInput($event, form, 'valor_cota_padrao')"
                    required
                    class="w-full pl-9 pr-3 py-2 text-xs border rounded-lg font-bold font-mono focus:ring-1 focus:ring-blue-500"
                  />
                </div>
              </div>
              <div>
                <label class="block text-xs font-medium text-slate-700 mb-1">Cota Extra (R$ - Opcional)</label>
                <div class="relative">
                  <span class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 font-semibold text-xs">R$</span>
                  <input
                    type="text"
                    :value="form.cota_extra != null ? formatMoney(form.cota_extra) : ''"
                    @input="onMoneyInputNullable($event, form, 'cota_extra')"
                    placeholder="0,00 (Opcional)"
                    class="w-full pl-9 pr-3 py-2 text-xs border rounded-lg font-bold font-mono focus:ring-1 focus:ring-blue-500"
                  />
                </div>
                <p v-if="form.cota_extra" class="text-[11px] text-indigo-600 font-medium mt-1">
                  Cota total somada: R$ {{ formatMoney((Number(form.valor_cota_padrao) || 0) + (Number(form.cota_extra) || 0)) }}
                </p>
              </div>
            </div>
          </div>

          <!-- Bloco 3: Mestre-Detalhe de Saldos por Conta Bancária -->
          <div>
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3 border-b pb-1">
              <div>
                <h4 class="text-xs font-bold uppercase tracking-wider text-blue-600">
                  3. Saldos Anteriores & Bancário (Mestre-Detalhe por Conta)
                </h4>
                <p class="text-[11px] text-slate-500">
                  Saldos anteriores são carregados automaticamente da prestação anterior ao mês de referência.
                </p>
              </div>
              <div class="flex items-center gap-2">
                <button
                  type="button"
                  @click="carregarSaldosPeriodoAnterior(true)"
                  :disabled="loadingSaldosAnt"
                  class="px-2.5 py-1.5 bg-blue-50 text-blue-700 hover:bg-blue-100 rounded-lg text-xs font-semibold border border-blue-200 transition flex items-center gap-1 shadow-sm disabled:opacity-50"
                  title="Puxar os saldos finais da prestação anterior"
                >
                  <svg class="w-3.5 h-3.5" :class="{ 'animate-spin': loadingSaldosAnt }" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  {{ loadingSaldosAnt ? 'Carregando...' : 'Carregar da Prestação Anterior' }}
                </button>
                <button
                  type="button"
                  @click="abrirModalNovaConta"
                  class="px-2.5 py-1.5 bg-emerald-50 text-emerald-700 hover:bg-emerald-100 rounded-lg text-xs font-semibold border border-emerald-200 transition flex items-center gap-1 shadow-sm"
                >
                  + Cadastrar Tipo de Conta
                </button>
              </div>
            </div>

            <div class="border border-slate-200 rounded-xl overflow-hidden shadow-sm">
              <table class="w-full text-xs text-left border-collapse">
                <thead class="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider">
                  <tr>
                    <th class="p-3">Conta / Instituição</th>
                    <th class="p-3">Tipo de Conta</th>
                    <th class="p-3 w-44 text-right">Saldo Anterior (R$)</th>
                    <th class="p-3 w-44 text-right">Saldo Final Bancário (R$)</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-slate-100">
                  <tr v-if="saldosContasForm.length === 0">
                    <td colspan="4" class="p-4 text-center text-slate-400">
                      Nenhuma conta cadastrada. Clique em "+ Cadastrar Tipo de Conta" acima.
                    </td>
                  </tr>
                  <tr v-for="item in saldosContasForm" :key="item.conta" class="hover:bg-slate-50/80">
                    <td class="p-3">
                      <span class="font-bold text-slate-800 block">{{ item.descricao }}</span>
                      <span class="text-[11px] text-slate-500">{{ item.banco_nome }} - Ag: {{ item.agencia || '-' }} / CC: {{ item.conta_num || '-' }}</span>
                    </td>
                    <td class="p-3">
                      <span class="px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-100 text-slate-700">
                        {{ item.tipo_display }}
                      </span>
                    </td>
                    <td class="p-3 text-right">
                      <div class="relative">
                        <span class="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400 font-medium text-[11px]">R$</span>
                        <input
                          type="text"
                          :value="formatMoney(item.saldo_anterior)"
                          @input="onMoneyInput($event, item, 'saldo_anterior')"
                          class="w-full pl-8 pr-2 py-1.5 border rounded-lg text-xs font-mono font-bold text-slate-800 text-right focus:ring-1 focus:ring-blue-500"
                        />
                      </div>
                    </td>
                    <td class="p-3 text-right">
                      <div class="relative">
                        <span class="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400 font-medium text-[11px]">R$</span>
                        <input
                          type="text"
                          :value="formatMoney(item.saldo_final)"
                          @input="onMoneyInput($event, item, 'saldo_final')"
                          class="w-full pl-8 pr-2 py-1.5 border rounded-lg text-xs font-mono font-bold text-slate-800 text-right focus:ring-1 focus:ring-blue-500"
                        />
                      </div>
                    </td>
                  </tr>
                </tbody>
                <tfoot class="bg-slate-50 border-t border-slate-200 font-bold text-slate-800">
                  <tr>
                    <td colspan="2" class="p-3 text-right uppercase text-[11px] text-slate-500">
                      Totais Somados:
                    </td>
                    <td class="p-3 text-right font-mono text-emerald-700 text-sm">
                      R$ {{ formatMoney(totalSaldoAnteriorCalculado) }}
                    </td>
                    <td class="p-3 text-right font-mono text-blue-700 text-sm">
                      R$ {{ formatMoney(totalSaldoFinalCalculado) }}
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>

          <!-- Bloco 4: Responsável Síndico (Campos Bloqueados para Edição Manual) -->
          <div>
            <div class="flex items-center justify-between mb-3 border-b pb-1">
              <div>
                <h4 class="text-xs font-bold uppercase tracking-wider text-blue-600">
                  4. Assinatura do Síndico
                </h4>
                <p class="text-[11px] text-slate-500">
                  Preenchimento automático do síndico ativo. Bloqueado para edição direta.
                </p>
              </div>
              <button
                type="button"
                @click="carregarSindicoAtivo"
                class="text-[11px] px-2.5 py-1 rounded-md bg-blue-50 text-blue-700 hover:bg-blue-100 font-semibold border border-blue-200 transition flex items-center gap-1 shadow-xs"
                title="Sincroniza automaticamente o nome e CPF do síndico ativo no condomínio"
              >
                <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Sincronizar Síndico Ativo
              </button>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div>
                <label class="block text-xs font-medium text-slate-700 mb-1">Nome do Síndico (Bloqueado)</label>
                <input
                  type="text"
                  :value="form.sindico_nome"
                  readonly
                  tabindex="-1"
                  class="w-full text-xs border rounded-lg p-2 bg-slate-100 text-slate-700 font-bold cursor-not-allowed select-none focus:outline-none"
                />
              </div>
              <div>
                <label class="block text-xs font-medium text-slate-700 mb-1">CPF do Síndico (Bloqueado)</label>
                <input
                  type="text"
                  :value="form.sindico_cpf"
                  readonly
                  tabindex="-1"
                  placeholder="000.000.000-00"
                  class="w-full text-xs border rounded-lg p-2 bg-slate-100 text-slate-700 font-mono font-bold cursor-not-allowed select-none focus:outline-none"
                />
              </div>
              <div>
                <label class="block text-xs font-medium text-slate-700 mb-1">Data da Assinatura (Bloqueada)</label>
                <input
                  type="date"
                  :value="form.data_assinatura"
                  readonly
                  tabindex="-1"
                  class="w-full text-xs border rounded-lg p-2 bg-slate-100 text-slate-700 font-bold cursor-not-allowed select-none focus:outline-none"
                />
              </div>
            </div>
          </div>

          <div v-if="errorMessage" class="p-3 bg-rose-50 text-rose-700 text-xs rounded-lg border border-rose-200">
            {{ errorMessage }}
          </div>

          <!-- Botoes -->
          <div class="pt-4 border-t border-slate-200 flex items-center justify-end gap-2">
            <button
              type="button"
              @click="showModal = false"
              class="px-4 py-2 border rounded-lg text-xs font-medium text-slate-700 hover:bg-slate-50 transition"
            >
              Cancelar
            </button>
            <button
              type="submit"
              :disabled="saving"
              class="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-medium disabled:opacity-50 transition shadow"
            >
              {{ saving ? 'Salvando...' : 'Salvar Período' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Mini-Modal para Cadastro de Nova Conta Bancária -->
    <div v-if="showModalConta" class="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div class="bg-white rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl border border-slate-200">
        <div class="flex items-center justify-between border-b pb-3">
          <h3 class="font-bold text-sm text-slate-800">
            Cadastrar Conta Bancária do Condomínio
          </h3>
          <button @click="showModalConta = false" class="text-slate-400 hover:text-slate-600 text-lg font-bold">&times;</button>
        </div>

        <form @submit.prevent="salvarNovaContaBancaria" class="space-y-3 text-xs">
          <div>
            <label class="block font-medium text-slate-700 mb-1">Banco / Instituição *</label>
            <input
              type="text"
              v-model="formConta.banco_nome"
              required
              placeholder="Ex: Banco Inter, Caixa, Nubank"
              class="w-full px-3 py-2 border rounded-xl"
            />
          </div>

          <div>
            <label class="block font-medium text-slate-700 mb-1">Tipo de Conta *</label>
            <select v-model="formConta.tipo_conta" required class="w-full px-3 py-2 border rounded-xl">
              <option value="CORRENTE">Conta Corrente</option>
              <option value="APLICACAO">Aplicação Financeira / CDB</option>
              <option value="POUPANCA">Conta Poupança</option>
              <option value="RESERVA">Reserva / Férias e 13º</option>
              <option value="OUTRO">Outro Tipo</option>
            </select>
          </div>

          <div>
            <label class="block font-medium text-slate-700 mb-1">Descrição / Identificação *</label>
            <input
              type="text"
              v-model="formConta.descricao"
              required
              placeholder="Ex: Conta Corrente Operacional"
              class="w-full px-3 py-2 border rounded-xl"
            />
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block font-medium text-slate-700 mb-1">Agência</label>
              <input
                type="text"
                v-model="formConta.agencia"
                placeholder="0001"
                class="w-full px-3 py-2 border rounded-xl"
              />
            </div>
            <div>
              <label class="block font-medium text-slate-700 mb-1">Número da Conta</label>
              <input
                type="text"
                v-model="formConta.conta"
                placeholder="1234567-8"
                class="w-full px-3 py-2 border rounded-xl"
              />
            </div>
          </div>

          <div class="pt-3 flex justify-end gap-2 border-t">
            <button
              type="button"
              @click="showModalConta = false"
              class="px-3 py-2 border rounded-xl text-slate-600 hover:bg-slate-50"
            >
              Cancelar
            </button>
            <button
              type="submit"
              :disabled="savingConta"
              class="px-4 py-2 bg-emerald-600 text-white rounded-xl font-medium hover:bg-emerald-700"
            >
              {{ savingConta ? 'Salvando...' : 'Salvar Conta' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import financeiroApi from "@/api/financeiro"
import apiClient from "@/api/client"

const loading = ref(true)
const periodos = ref([])
const condominiosList = ref([])
const showModal = ref(false)
const editingId = ref(null)
const saving = ref(false)
const errorMessage = ref("")

const seletorMesAno = ref("")
const contasBancarias = ref([])
const saldosContasForm = ref([])
const loadingSaldosAnt = ref(false)

const condominioNomeAtual = computed(() => {
  const condId = form.value.condominio
  const c = condominiosList.value.find(item => item.id === condId)
  if (c) return c.nome
  if (periodos.value.length > 0) {
    const p = periodos.value.find(item => item.condominio === condId)
    if (p?.condominio_nome) return p.condominio_nome
    if (periodos.value[0]?.condominio_nome) return periodos.value[0].condominio_nome
  }
  return "Condomínio Vinculado"
})

// Mini-Modal Conta Bancária
const showModalConta = ref(false)
const savingConta = ref(false)
const formConta = ref({
  banco_nome: "Banco Inter",
  tipo_conta: "CORRENTE",
  descricao: "",
  agencia: "",
  conta: "",
})

const form = ref({
  condominio: null,
  mes_referencia: "",
  mes_referencia_rotulo: "",
  data_vencimento: "",
  mes_prox_vencimento: "",
  data_prox_vencimento: "",
  data_inicio_prestacao: "",
  data_fim_prestacao: "",
  valor_cota_padrao: 380.00,
  cota_extra: null,
  saldo_anterior_cc: 0,
  saldo_anterior_aplicacao: 0,
  saldo_anterior_porquinho: 0,
  total_saldo_bancario: 0,
  data_saldo_bancario: "",
  sindico_nome: "",
  sindico_cpf: "",
  data_assinatura: "",
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

function onMoneyInputNullable(e, targetObj, key) {
  let val = e.target.value.replace(/\D/g, "")
  if (!val) {
    targetObj[key] = null
    e.target.value = ""
    return
  }
  let num = parseInt(val, 10) / 100
  targetObj[key] = num
  e.target.value = num.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function onMesReferenciaChange() {
  if (!form.value.mes_referencia) return
  const parts = form.value.mes_referencia.split("-")
  if (parts.length >= 2) {
    const ano = parseInt(parts[0], 10)
    const mes = parseInt(parts[1], 10)
    const ultimoDia = new Date(ano, mes, 0).getDate()
    form.value.data_assinatura = `${ano}-${String(mes).padStart(2, "0")}-${String(ultimoDia).padStart(2, "0")}`
  }
}

const totalSaldoAnteriorCalculado = computed(() => {
  return saldosContasForm.value.reduce((acc, item) => acc + (Number(item.saldo_anterior) || 0), 0)
})

const totalSaldoFinalCalculado = computed(() => {
  return saldosContasForm.value.reduce((acc, item) => acc + (Number(item.saldo_final) || 0), 0)
})

function aplicarPreenchimentoAutomaticoDatas() {
  if (!seletorMesAno.value) return
  const [anoStr, mesStr] = seletorMesAno.value.split("-")
  const ano = parseInt(anoStr, 10)
  const mes = parseInt(mesStr, 10) // 1 a 12

  const nomesMeses = [
    "JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO",
    "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"
  ]

  const nomeMesAtual = nomesMeses[mes - 1]
  const ultimoDia = new Date(ano, mes, 0).getDate()

  // 1. Rótulo: SETEMBRO/2026
  form.value.mes_referencia_rotulo = `${nomeMesAtual}/${ano}`

  // 2. Mês de referência: último dia do mês
  form.value.mes_referencia = `${ano}-${String(mes).padStart(2, "0")}-${String(ultimoDia).padStart(2, "0")}`

  // 3. Início e fim da prestação: 1º e último dia do mês
  form.value.data_inicio_prestacao = `${ano}-${String(mes).padStart(2, "0")}-01`
  form.value.data_fim_prestacao = `${ano}-${String(mes).padStart(2, "0")}-${String(ultimoDia).padStart(2, "0")}`
  form.value.data_saldo_bancario = `${ano}-${String(mes).padStart(2, "0")}-${String(ultimoDia).padStart(2, "0")}`

  // 4. Data de vencimento da cota: dia 05 do mês seguinte
  const proxMesIndex = mes % 12 // 0 a 11
  const proxAno = mes === 12 ? ano + 1 : ano
  const nomeProxMes = nomesMeses[proxMesIndex]

  form.value.data_vencimento = `${proxAno}-${String(proxMesIndex + 1).padStart(2, "0")}-05`
  form.value.mes_prox_vencimento = nomeProxMes

  // Próximo vencimento: dia 05 do 2º mês seguinte
  const proxProxMesIndex = (mes + 1) % 12
  const proxProxAno = mes >= 11 ? ano + 1 : ano
  form.value.data_prox_vencimento = `${proxProxAno}-${String(proxProxMesIndex + 1).padStart(2, "0")}-05`

  // Data da assinatura: sempre o último dia do mês de referência
  form.value.data_assinatura = `${ano}-${String(mes).padStart(2, "0")}-${String(ultimoDia).padStart(2, "0")}`

  // Sempre carrega os saldos da prestação anterior se for um novo período
  if (!editingId.value) {
    carregarSaldosPeriodoAnterior(false)
  }
}

async function carregarSaldosPeriodoAnterior(notificar = false) {
  const condId = form.value.condominio || localStorage.getItem("active_condominio_id")
  if (!condId) return
  loadingSaldosAnt.value = true
  try {
    const res = await financeiroApi.getSaldosPeriodoAnterior({
      condominio: condId,
      mes_referencia: form.value.data_inicio_prestacao || form.value.mes_referencia || seletorMesAno.value,
    })
    if (res.data?.encontrado && res.data.saldos_contas) {
      const mapaSaldosAnt = {}
      for (const sc of res.data.saldos_contas) {
        mapaSaldosAnt[sc.conta] = Number(sc.saldo_final) || 0
      }
      for (const item of saldosContasForm.value) {
        if (mapaSaldosAnt[item.conta] !== undefined) {
          item.saldo_anterior = mapaSaldosAnt[item.conta]
        }
      }
      if (res.data.saldo_anterior_cc !== undefined) {
        form.value.saldo_anterior_cc = Number(res.data.saldo_anterior_cc) || 0
      }
      if (res.data.saldo_anterior_aplicacao !== undefined) {
        form.value.saldo_anterior_aplicacao = Number(res.data.saldo_anterior_aplicacao) || 0
      }
      if (res.data.saldo_anterior_porquinho !== undefined) {
        form.value.saldo_anterior_porquinho = Number(res.data.saldo_anterior_porquinho) || 0
      }
      if (notificar) {
        alert(`Saldos finais da prestação anterior (${res.data.periodo_anterior_rotulo}) carregados com sucesso!`)
      }
    } else if (notificar) {
      alert("Nenhuma prestação anterior localizada para este condomínio.")
    }
  } catch (err) {
    console.error("Erro ao carregar saldos da prestação anterior:", err)
    if (notificar) alert("Erro ao carregar saldos da prestação anterior.")
  } finally {
    loadingSaldosAnt.value = false
  }
}

async function onCondominioChange() {
  await carregarContasBancarias(form.value.condominio)
  inicializarSaldosContasForm(editingId.value ? form.value : null)
  await carregarSindicoAtivo()
  if (!editingId.value) {
    await carregarSaldosPeriodoAnterior(false)
  }
}

async function carregarSindicoAtivo() {
  const condId = form.value.condominio || localStorage.getItem("active_condominio_id")
  if (!condId) return
  try {
    const res = await financeiroApi.getSindicoAtivo(condId)
    if (res.data?.nome) {
      form.value.sindico_nome = res.data.nome
      form.value.sindico_cpf = res.data.cpf || ""
    }
  } catch (err) {
    console.error("Erro ao buscar síndico ativo:", err)
  }
}

async function carregarContasBancarias(condId) {
  try {
    const res = await financeiroApi.getContasBancarias({ condominio: condId })
    contasBancarias.value = res.data.results || res.data
  } catch (err) {
    console.error("Erro ao carregar contas bancárias:", err)
  }
}

function inicializarSaldosContasForm(periodo = null) {
  const saldosExistentes = periodo?.saldos_contas || []
  const saldosMap = {}
  for (const s of saldosExistentes) {
    saldosMap[s.conta] = s
  }

  saldosContasForm.value = contasBancarias.value.map(c => {
    const ex = saldosMap[c.id]
    return {
      conta: c.id,
      conta_id: c.id,
      banco_nome: c.banco_nome,
      descricao: c.descricao,
      tipo_display: c.tipo_display,
      agencia: c.agencia,
      conta_num: c.conta,
      saldo_anterior: ex ? Number(ex.saldo_anterior) : 0,
      saldo_final: ex ? Number(ex.saldo_final) : 0,
    }
  })
}

async function loadPeriodos() {
  loading.value = true
  try {
    const res = await financeiroApi.getPeriodos()
    periodos.value = res.data.results || res.data
  } catch (err) {
    console.error("Erro ao carregar períodos:", err)
  } finally {
    loading.value = false
  }
}

async function openModal(periodo = null) {
  errorMessage.value = ""
  let activeCondId = localStorage.getItem("active_condominio_id")
  if (!activeCondId && periodos.value.length > 0) {
    activeCondId = periodos.value[0].condominio
  }
  const condId = periodo?.condominio || activeCondId || 1

  await carregarContasBancarias(condId)

  if (periodo) {
    editingId.value = periodo.id
    form.value = { ...periodo }
    if (periodo.mes_referencia) {
      seletorMesAno.value = periodo.mes_referencia.substring(0, 7)
    }
    inicializarSaldosContasForm(periodo)
  } else {
    editingId.value = null

    // Projeta o próximo mês com base nos períodos existentes para evitar duplicidade
    let proximoMesAno = new Date().toISOString().substring(0, 7)
    if (periodos.value.length > 0) {
      const datasFim = periodos.value
        .map(p => p.data_fim_prestacao)
        .filter(Boolean)
        .sort()
      if (datasFim.length > 0) {
        const ultDataStr = datasFim[datasFim.length - 1] // ex: '2026-10-31'
        const [anoU, mesU] = ultDataStr.split("-").map(Number)
        const proxMes = mesU === 12 ? 1 : mesU + 1
        const proxAno = mesU === 12 ? anoU + 1 : anoU
        proximoMesAno = `${proxAno}-${String(proxMes).padStart(2, "0")}`
      }
    }
    seletorMesAno.value = proximoMesAno

    form.value = {
      condominio: condId,
      mes_referencia: "",
      mes_referencia_rotulo: "",
      data_vencimento: "",
      mes_prox_vencimento: "",
      data_prox_vencimento: "",
      data_inicio_prestacao: "",
      data_fim_prestacao: "",
      valor_cota_padrao: 380.00,
      cota_extra: null,
      saldo_anterior_cc: 0,
      saldo_anterior_aplicacao: 0,
      saldo_anterior_porquinho: 0,
      total_saldo_bancario: 0,
      data_saldo_bancario: "",
      sindico_nome: "",
      sindico_cpf: "",
      data_assinatura: "",
    }

    aplicarPreenchimentoAutomaticoDatas()
    await carregarSindicoAtivo()
    inicializarSaldosContasForm(null)
    await carregarSaldosPeriodoAnterior(false)
  }
  showModal.value = true
}

function abrirModalNovaConta() {
  formConta.value = {
    banco_nome: "Banco Inter",
    tipo_conta: "CORRENTE",
    descricao: "",
    agencia: "",
    conta: "",
  }
  showModalConta.value = true
}

async function salvarNovaContaBancaria() {
  savingConta.value = true
  try {
    const condId = form.value.condominio || 1
    const res = await financeiroApi.createContaBancaria({
      ...formConta.value,
      condominio: condId,
    })
    showModalConta.value = false
    await carregarContasBancarias(condId)
    // Adiciona nova linha ao formulário de saldos
    saldosContasForm.value.push({
      conta: res.data.id,
      conta_id: res.data.id,
      banco_nome: res.data.banco_nome,
      descricao: res.data.descricao,
      tipo_display: res.data.tipo_display,
      agencia: res.data.agencia,
      conta_num: res.data.conta,
      saldo_anterior: 0,
      saldo_final: 0,
    })
  } catch (err) {
    alert("Erro ao cadastrar conta bancária.")
  } finally {
    savingConta.value = false
  }
}

async function savePeriodo() {
  saving.value = true
  errorMessage.value = ""

  // Prepara payload com master-detail saldos_contas arredondando para 2 casas decimais
  const payload = {
    ...form.value,
    total_saldo_bancario: Number(Number(totalSaldoFinalCalculado.value || 0).toFixed(2)),
    saldo_anterior_cc: Number(Number(form.value.saldo_anterior_cc || 0).toFixed(2)),
    saldo_anterior_aplicacao: Number(Number(form.value.saldo_anterior_aplicacao || 0).toFixed(2)),
    saldo_anterior_porquinho: Number(Number(form.value.saldo_anterior_porquinho || 0).toFixed(2)),
    valor_cota_padrao: Number(Number(form.value.valor_cota_padrao || 0).toFixed(2)),
    cota_extra: form.value.cota_extra != null && form.value.cota_extra > 0 ? Number(Number(form.value.cota_extra).toFixed(2)) : null,
    saldos_contas: saldosContasForm.value.map(s => ({
      conta: s.conta,
      saldo_anterior: Number(Number(s.saldo_anterior || 0).toFixed(2)),
      saldo_final: Number(Number(s.saldo_final || 0).toFixed(2)),
    })),
  }

  try {
    if (editingId.value) {
      await financeiroApi.updatePeriodo(editingId.value, payload)
    } else {
      await financeiroApi.createPeriodo(payload)
    }
    showModal.value = false
    await loadPeriodos()
  } catch (err) {
    const data = err.response?.data
    if (typeof data === "object") {
      const msgs = []
      for (const [k, v] of Object.entries(data)) {
        const vStr = typeof v === "object" ? JSON.stringify(v) : String(v)
        if (
          vStr.includes("unique_periodo_por_condominio") ||
          vStr.includes("set único") ||
          vStr.includes("data_inicio_prestacao, data_fim_prestacao")
        ) {
          msgs.push("Já existe uma prestação de contas cadastrada para este condomínio no mesmo mês/intervalo de datas. Selecione outro mês no calendário ou edite o período já existente.")
        } else {
          msgs.push(`${k === "non_field_errors" ? "Aviso" : k}: ${vStr}`)
        }
      }
      errorMessage.value = msgs.join(" | ")
    } else {
      errorMessage.value = "Erro ao salvar período."
    }
  } finally {
    saving.value = false
  }
}

async function excluirPeriodo(periodo) {
  if (periodo.status === "PUBLICADO") {
    alert("Este período está com status PUBLICADO. Para excluí-lo, reabra-o primeiro na tela de Prestação.")
    return
  }
  if (!confirm(`Atenção: Deseja realmente excluir o período de prestação "${periodo.mes_referencia_rotulo}"?\n\nTodas as cotas geradas, despesas e saldos vinculados a este período serão excluídos permanentemente.`)) {
    return
  }
  try {
    await financeiroApi.deletePeriodo(periodo.id)
    alert("Período de prestação de contas excluído com sucesso.")
    await loadPeriodos()
  } catch (err) {
    alert(err.response?.data?.error || err.response?.data?.detail || "Erro ao excluir período.")
  }
}

async function gerarCotas(periodo) {
  const valorExibir = formatMoney(periodo.valor_cota_total || periodo.valor_cota_padrao)
  if (!confirm(`Deseja gerar as cotas de R$ ${valorExibir} para todas as unidades ativas? (Titulares com mandatos isentos receberão status ISENTO)`)) return
  try {
    const res = await financeiroApi.gerarCotas(periodo.id)
    alert(res.data.message)
    await loadPeriodos()
  } catch (err) {
    alert(err.response?.data?.error || "Erro ao gerar cotas.")
  }
}

onMounted(async () => {
  try {
    const res = await apiClient.get("/condominios/")
    condominiosList.value = res.data.results || res.data
  } catch (e) {
    console.error("Erro ao buscar condominios:", e)
  }
  await loadPeriodos()
})
</script>
