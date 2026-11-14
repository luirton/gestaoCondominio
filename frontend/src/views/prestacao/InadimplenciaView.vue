<template>
  <div class="space-y-6">
    <!-- Cabeçalho -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-slate-800">Gestão de Inadimplência & Cobrança</h1>
        <p class="text-slate-500 text-sm">
          Acompanhamento de débitos, emissão de avisos de cobrança em atraso e parâmetros financeiros.
        </p>
      </div>

      <div class="flex items-center gap-3">
        <button
          @click="abrirModalParametros"
          class="inline-flex items-center gap-2 px-4 py-2 border border-slate-300 rounded-lg text-sm font-medium text-slate-700 bg-white hover:bg-slate-50 shadow-sm transition"
        >
          <svg class="w-4 h-4 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          Parâmetros de Cobrança
        </button>

        <button
          @click="carregarDados"
          class="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium shadow-sm transition"
        >
          <svg class="w-4 h-4" :class="{ 'animate-spin': carregando }" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Atualizar
        </button>
      </div>
    </div>

    <!-- Cards de Resumo Financeiro da Inadimplência -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
        <span class="text-xs font-semibold text-slate-500 uppercase tracking-wider">Unidades Inadimplentes</span>
        <div class="mt-2 flex items-baseline justify-between">
          <span class="text-2xl font-bold text-slate-900">{{ relatorio?.total_inadimplentes || 0 }}</span>
          <span class="text-xs font-medium px-2 py-0.5 rounded-full" :class="taxaBadgeColor">
            {{ relatorio?.taxa_inadimplencia_percentual || 0 }}% do condomínio
          </span>
        </div>
      </div>

      <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
        <span class="text-xs font-semibold text-slate-500 uppercase tracking-wider">Principal em Atraso</span>
        <div class="mt-2 text-2xl font-bold text-slate-900">
          {{ formatMoeda(relatorio?.totais_consolidados?.total_taxas) }}
        </div>
        <p class="text-xs text-slate-400 mt-1">{{ relatorio?.totais_consolidados?.total_titulos || 0 }} títulos vencidos</p>
      </div>

      <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
        <span class="text-xs font-semibold text-slate-500 uppercase tracking-wider">Multas & Juros Apurados</span>
        <div class="mt-2 text-2xl font-bold text-amber-600">
          {{ formatMoeda((relatorio?.totais_consolidados?.total_multas || 0) + (relatorio?.totais_consolidados?.total_juros || 0)) }}
        </div>
        <p class="text-xs text-slate-400 mt-1">
          Multa: {{ formatMoeda(relatorio?.totais_consolidados?.total_multas) }} | Juros: {{ formatMoeda(relatorio?.totais_consolidados?.total_juros) }}
        </p>
      </div>

      <div class="bg-white p-5 rounded-xl border border-rose-200 bg-rose-50/30 shadow-sm">
        <span class="text-xs font-semibold text-rose-700 uppercase tracking-wider">Saldo Devedor Consolidado</span>
        <div class="mt-2 text-2xl font-bold text-rose-700">
          {{ formatMoeda(relatorio?.totais_consolidados?.total_saldo_devedor) }}
        </div>
        <p class="text-xs text-rose-500 mt-1">Calculado até {{ formatData(relatorio?.data_atualizacao) }}</p>
      </div>
    </div>

    <!-- Filtros e Barra de Ações -->
    <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col md:flex-row gap-4 items-center justify-between">
      <div class="flex flex-1 items-center gap-3 w-full md:w-auto">
        <div class="relative flex-1 max-w-sm">
          <input
            v-model="filtroTexto"
            type="text"
            placeholder="Buscar por unidade ou proprietário..."
            class="w-full pl-9 pr-4 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <svg class="w-4 h-4 text-slate-400 absolute left-3 top-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>

        <select
          v-model="filtroCriticidade"
          class="border border-slate-300 rounded-lg text-sm px-3 py-2 bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="TODOS">Todas as Unidades</option>
          <option value="AJUIZAMENTO">Sujeito a Ajuizamento (6+ parcelas)</option>
          <option value="ATE_3">Até 3 parcelas</option>
        </select>
      </div>

      <div class="text-xs text-slate-500">
        Mostrando <b>{{ devedoresFiltrados.length }}</b> de <b>{{ relatorio?.devedores?.length || 0 }}</b> inadimplentes
      </div>
    </div>

    <!-- Tabela de Inadimplentes -->
    <div class="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      <div v-if="carregando" class="p-12 text-center text-slate-500">
        <svg class="w-8 h-8 animate-spin mx-auto text-blue-600 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        Carregando dados de inadimplência...
      </div>

      <div v-else-if="devedoresFiltrados.length === 0" class="p-12 text-center">
        <svg class="w-12 h-12 text-emerald-500 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <h3 class="text-base font-semibold text-slate-800">Nenhum débito encontrado!</h3>
        <p class="text-sm text-slate-500 mt-1">Todas as unidades estão em dia com suas cotas para os critérios selecionados.</p>
      </div>

      <div v-else class="overflow-x-auto">
        <table class="w-full text-left border-collapse text-sm">
          <thead>
            <tr class="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold text-xs uppercase tracking-wider">
              <th class="p-4">Unidade</th>
              <th class="p-4">Proprietário / Morador</th>
              <th class="p-4 text-center">Qtd. Parcelas</th>
              <th class="p-4 text-right">Taxa Principal</th>
              <th class="p-4 text-right">Multas + Juros</th>
              <th class="p-4 text-right">Total Devedor</th>
              <th class="p-4 text-center">Ações</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr
              v-for="dev in devedoresFiltrados"
              :key="dev.unidade.id"
              class="hover:bg-slate-50/80 transition-colors"
              :class="{ 'bg-rose-50/20': dev.sujeito_ajuizamento }"
            >
              <td class="p-4 font-bold text-slate-900">
                <div class="flex items-center gap-2">
                  <span>{{ dev.unidade.identificador }}</span>
                  <span
                    v-if="dev.sujeito_ajuizamento"
                    title="Débito com 6 ou mais parcelas em atraso (Sujeito a Ajuizamento)"
                    class="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-100 text-rose-700 border border-rose-200"
                  >
                    Ajuizamento
                  </span>
                </div>
              </td>
              <td class="p-4">
                <div class="font-medium text-slate-800">{{ dev.responsavel.nome }}</div>
                <div class="text-xs text-slate-400">{{ dev.responsavel.email || 'Sem e-mail cadastrado' }}</div>
              </td>
              <td class="p-4 text-center font-semibold text-slate-700">
                <span class="inline-block px-2.5 py-1 rounded-full text-xs font-semibold" :class="dev.qtd_titulos >= 6 ? 'bg-rose-100 text-rose-800' : 'bg-amber-100 text-amber-800'">
                  {{ dev.qtd_titulos }} cotas
                </span>
              </td>
              <td class="p-4 text-right font-medium text-slate-700">
                {{ formatMoeda(dev.totais.taxa) }}
              </td>
              <td class="p-4 text-right font-medium text-amber-700">
                {{ formatMoeda(dev.totais.multa + dev.totais.juros) }}
              </td>
              <td class="p-4 text-right font-bold text-rose-700 text-base">
                {{ formatMoeda(dev.totais.total_geral) }}
              </td>
              <td class="p-4 text-center">
                <div class="flex items-center justify-center gap-2">
                  <!-- Botão Detalhes / Ver Espelho da Planilha -->
                  <button
                    @click="abrirModalDetalhes(dev)"
                    title="Visualizar Espelho dos Débitos"
                    class="p-1.5 text-slate-600 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition"
                  >
                    <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  </button>

                  <!-- Botão Download PDF do Aviso de Débito -->
                  <button
                    @click="baixarPdf(dev)"
                    :disabled="baixandoPdfId === dev.unidade.id"
                    title="Baixar Aviso de Débito em PDF"
                    class="p-1.5 text-slate-600 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition disabled:opacity-50"
                  >
                    <svg v-if="baixandoPdfId === dev.unidade.id" class="w-5 h-5 animate-spin text-rose-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                    <svg v-else class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </button>

                  <!-- Botão Enviar E-mail com edição livre -->
                  <button
                    @click="abrirModalEmail(dev)"
                    title="Enviar Cobrança por E-mail"
                    class="p-1.5 text-slate-600 hover:text-emerald-600 hover:bg-emerald-50 rounded-lg transition"
                  >
                    <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- MODAL 1: DETALHAMENTO DA FICHA DE COBRANÇA (ESPELHO DA PLANILHA) -->
    <div
      v-if="modalDetalhesAberto && unidadeSelecionada"
      class="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4"
    >
      <div class="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] flex flex-col overflow-hidden animate-fadeIn">
        <!-- Topo da Ficha -->
        <div class="p-6 bg-slate-800 text-white flex items-center justify-between">
          <div>
            <span class="text-xs font-semibold uppercase tracking-wider text-blue-400">Aviso de Débito em Atraso</span>
            <h2 class="text-xl font-bold mt-0.5">{{ unidadeSelecionada.unidade.identificador }} - {{ unidadeSelecionada.responsavel.nome }}</h2>
          </div>
          <div class="flex items-center gap-2">
            <button
              @click="baixarPdf(unidadeSelecionada)"
              :disabled="baixandoPdfId === unidadeSelecionada.unidade.id"
              class="px-3 py-1.5 bg-rose-600 hover:bg-rose-700 disabled:opacity-50 text-white rounded-lg text-xs font-semibold inline-flex items-center gap-1.5 transition"
            >
              <svg v-if="baixandoPdfId === unidadeSelecionada.unidade.id" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Baixar PDF Oficial
            </button>
            <button @click="modalDetalhesAberto = false" class="text-slate-400 hover:text-white p-1">
              <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <!-- Grade de Itens (Tabela Idêntica à Planilha) -->
        <div class="p-6 overflow-y-auto space-y-4">
          <div class="text-xs text-slate-500 flex justify-between items-center border-b pb-2">
            <span>Cálculo atualizado até: <b>{{ formatData(unidadeSelecionada.data_atualizacao) }}</b></span>
            <span>Regra de Juros: <b>0,24% ao dia</b> | Multa: <b>R$ 10,00</b></span>
          </div>

          <table class="w-full text-left border-collapse text-xs">
            <thead>
              <tr class="bg-blue-900 text-white font-bold">
                <th class="p-2.5 text-center">#</th>
                <th class="p-2.5">Vencimento</th>
                <th class="p-2.5 text-center">Dias Atraso</th>
                <th class="p-2.5 text-right">Taxa (R$)</th>
                <th class="p-2.5 text-right">Multa (R$)</th>
                <th class="p-2.5 text-right">Juros (R$)</th>
                <th class="p-2.5 text-right">Total a Pagar</th>
                <th class="p-2.5">Observação</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-200">
              <tr v-for="it in unidadeSelecionada.itens" :key="it.cota_id" class="hover:bg-slate-50">
                <td class="p-2.5 text-center font-bold text-slate-600">{{ it.item }}</td>
                <td class="p-2.5 font-medium text-slate-800">{{ formatData(it.vencimento) }}</td>
                <td class="p-2.5 text-center text-slate-600">{{ it.dias_atraso }}</td>
                <td class="p-2.5 text-right text-slate-700">{{ formatMoeda(it.taxa) }}</td>
                <td class="p-2.5 text-right text-slate-700">{{ formatMoeda(it.multa) }}</td>
                <td class="p-2.5 text-right text-slate-700">{{ formatMoeda(it.juros) }}</td>
                <td class="p-2.5 text-right font-bold text-slate-900">{{ formatMoeda(it.total) }}</td>
                <td class="p-2.5 text-slate-500 italic">{{ it.observacao || '-' }}</td>
              </tr>
            </tbody>
            <tfoot>
              <tr class="bg-rose-700 text-white font-bold text-sm">
                <td colspan="3" class="p-3 text-left">SALDO DEVEDOR CONSOLIDADO</td>
                <td class="p-3 text-right">{{ formatMoeda(unidadeSelecionada.totais.taxa) }}</td>
                <td class="p-3 text-right">{{ formatMoeda(unidadeSelecionada.totais.multa) }}</td>
                <td class="p-3 text-right">{{ formatMoeda(unidadeSelecionada.totais.juros) }}</td>
                <td class="p-3 text-right text-base">{{ formatMoeda(unidadeSelecionada.totais.total_geral) }}</td>
                <td></td>
              </tr>
            </tfoot>
          </table>

          <div class="p-4 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-900 space-y-1">
            <p><b>OBS.:</b> {{ unidadeSelecionada.parametro?.prazo_negociacao_info }}</p>
            <p><b>OBS.:</b> {{ unidadeSelecionada.parametro?.aviso_protesto_info }}</p>
            <p><b>OBS.:</b> {{ unidadeSelecionada.parametro?.aviso_ajuizamento_info }}</p>
          </div>
        </div>

        <div class="p-4 bg-slate-50 border-t border-slate-200 flex justify-end">
          <button
            @click="modalDetalhesAberto = false"
            class="px-4 py-2 bg-slate-200 hover:bg-slate-300 text-slate-800 rounded-lg text-sm font-medium transition"
          >
            Fechar
          </button>
        </div>
      </div>
    </div>

    <!-- MODAL 2: ENVIO DE E-MAIL COM EDIÇÃO LIVRE DO TEXTO -->
    <div
      v-if="modalEmailAberto && unidadeSelecionada"
      class="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4"
    >
      <div class="bg-white rounded-2xl shadow-2xl max-w-2xl w-full overflow-hidden animate-fadeIn">
        <div class="p-6 bg-slate-900 text-white flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-blue-600/30 flex items-center justify-center text-blue-400">
              <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </div>
            <div>
              <h2 class="text-lg font-bold">Enviar Cobrança por E-mail</h2>
              <p class="text-xs text-slate-400">Unidade: {{ unidadeSelecionada.unidade.identificador }} ({{ formatMoeda(unidadeSelecionada.totais.total_geral) }})</p>
            </div>
          </div>
          <button @click="modalEmailAberto = false" class="text-slate-400 hover:text-white">
            <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form @submit.prevent="dispararEmailCobranca" class="p-6 space-y-4">
          <div>
            <label class="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">Destinatário(s)</label>
            <input
              v-model="formEmail.destinatario"
              type="text"
              required
              placeholder="ex: morador@email.com, proprietario@email.com"
              class="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <p class="text-[11px] text-slate-400 mt-1">Você pode separar múltiplos e-mails com vírgula.</p>
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">Assunto do E-mail</label>
            <input
              v-model="formEmail.assunto"
              type="text"
              required
              class="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <div class="flex items-center justify-between mb-1">
              <label class="block text-xs font-semibold text-slate-700 uppercase tracking-wider">
                Mensagem do E-mail (Edição Livre)
              </label>
              <button
                type="button"
                @click="restaurarMensagemPadrao"
                class="text-xs text-blue-600 hover:underline"
              >
                Restaurar texto padrão
              </button>
            </div>
            <textarea
              v-model="formEmail.mensagem"
              rows="8"
              required
              class="w-full p-3 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 font-sans leading-relaxed"
              placeholder="Digite a mensagem que o condômino irá receber..."
            ></textarea>
          </div>

          <div class="p-3 bg-slate-50 border border-slate-200 rounded-lg flex items-center gap-3">
            <svg class="w-6 h-6 text-rose-600 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
            </svg>
            <div class="text-xs text-slate-600">
              <span class="font-semibold text-slate-800">Anexo Automático:</span>
              O PDF oficial do <b>Aviso de Débito em Atraso</b> será gerado com os cálculos do dia e anexado automaticamente ao e-mail.
            </div>
          </div>

          <div v-if="erroEnvio" class="p-3 bg-rose-50 border border-rose-200 text-rose-700 rounded-lg text-xs">
            {{ erroEnvio }}
          </div>

          <div class="flex justify-end gap-3 pt-2">
            <button
              type="button"
              @click="modalEmailAberto = false"
              class="px-4 py-2 border border-slate-300 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              Cancelar
            </button>
            <button
              type="submit"
              :disabled="enviandoEmail"
              class="px-5 py-2 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white rounded-lg text-sm font-medium inline-flex items-center gap-2 shadow-sm transition"
            >
              <svg v-if="enviandoEmail" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              {{ enviandoEmail ? 'Disparando...' : 'Confirmar e Enviar E-mail' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- MODAL 3: PARÂMETROS DE COBRANÇA COM HISTÓRICO DE VIGÊNCIAS -->
    <div
      v-if="modalParametrosAberto"
      class="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4"
    >
      <div class="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] flex flex-col overflow-hidden animate-fadeIn">
        <div class="p-6 bg-slate-800 text-white flex items-center justify-between">
          <div>
            <h2 class="text-lg font-bold">Parâmetros de Cobrança & Vigências</h2>
            <p class="text-xs text-slate-400 mt-0.5">Histórico de regras de multas e juros por período de vencimento</p>
          </div>
          <button @click="modalParametrosAberto = false" class="text-slate-400 hover:text-white">
            <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div class="p-6 overflow-y-auto space-y-6">
          <!-- Tabela de Histórico de Vigências Cadastradas -->
          <div>
            <h3 class="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2 flex items-center justify-between">
              <span>📜 Histórico de Vigências Registradas</span>
              <span class="text-[11px] text-slate-400 font-normal">Cálculo pela data de vencimento da cota</span>
            </h3>
            <div class="border border-slate-200 rounded-xl overflow-hidden">
              <table class="w-full text-left text-xs border-collapse">
                <thead class="bg-slate-50 text-slate-600 font-semibold border-b">
                  <tr>
                    <th class="p-2.5">Início Vigência</th>
                    <th class="p-2.5">Fim Vigência</th>
                    <th class="p-2.5">Multa</th>
                    <th class="p-2.5">Juros Diário</th>
                    <th class="p-2.5 text-center">Status</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-slate-100">
                  <tr v-for="vig in listaHistoricoParametros" :key="vig.id" :class="{ 'bg-blue-50/40 font-medium': !vig.data_fim }">
                    <td class="p-2.5 text-slate-800 font-bold">{{ formatData(vig.data_inicio) }}</td>
                    <td class="p-2.5 text-slate-600">{{ vig.data_fim ? formatData(vig.data_fim) : 'Atualmente em vigor' }}</td>
                    <td class="p-2.5 text-slate-800">
                      {{ vig.tipo_multa === 'FIXO' ? formatMoeda(vig.valor_multa) : `${vig.valor_multa}%` }}
                    </td>
                    <td class="p-2.5 text-slate-800">{{ (parseFloat(vig.percentual_juros_dia) * 100).toFixed(2) }}% / dia</td>
                    <td class="p-2.5 text-center">
                      <span v-if="!vig.data_fim" class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">
                        Ativa
                      </span>
                      <span v-else class="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-100 text-slate-600">
                        Encerrada
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <hr class="border-slate-200" />

          <!-- Formulário de Alteração / Nova Vigência -->
          <form @submit.prevent="salvarParametros" class="space-y-4">
            <h3 class="text-xs font-bold text-slate-700 uppercase tracking-wider">
              ⚙️ Atualizar Regra Atual ou Criar Nova Vigência
            </h3>

            <div class="p-3 bg-blue-50/60 border border-blue-200 rounded-xl space-y-2">
              <label class="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" v-model="criarNovaVigencia" class="rounded text-blue-600 focus:ring-blue-500" />
                <span class="text-xs font-bold text-blue-900">Iniciar uma nova vigência a partir de uma data específica</span>
              </label>
              <div v-if="criarNovaVigencia" class="pt-2">
                <label class="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Data de Início da Nova Vigência
                </label>
                <input
                  v-model="novaDataInicio"
                  type="date"
                  required
                  class="w-full px-3 py-2 border border-blue-300 rounded-lg text-sm bg-white"
                />
                <p class="text-[11px] text-blue-600 mt-1">
                  A vigência anterior será encerrada automaticamente no dia imediatamente anterior.
                </p>
              </div>
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">Tipo de Multa</label>
                <select
                  v-model="parametrosForm.tipo_multa"
                  class="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white"
                >
                  <option value="FIXO">Valor Fixo (R$)</option>
                  <option value="PERCENTUAL">Percentual (%)</option>
                </select>
              </div>

              <div>
                <label class="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  {{ parametrosForm.tipo_multa === 'FIXO' ? 'Valor da Multa (R$)' : 'Percentual da Multa (%)' }}
                </label>
                <input
                  v-model="parametrosForm.valor_multa"
                  type="number"
                  step="0.01"
                  required
                  class="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
                />
              </div>
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Juros por Dia (Fator Decimal)
                </label>
                <input
                  v-model="parametrosForm.percentual_juros_dia"
                  type="number"
                  step="0.0001"
                  required
                  class="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
                />
                <p class="text-[11px] text-slate-400 mt-0.5">Ex: 0.0024 = 0,24% ao dia</p>
              </div>

              <div>
                <label class="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Qtd. Cotas para Ajuizamento
                </label>
                <input
                  v-model="parametrosForm.qtd_parcelas_ajuizamento"
                  type="number"
                  min="1"
                  required
                  class="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
                />
              </div>
            </div>

            <div>
              <label class="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">E-mail de Contato para Cobrança</label>
              <input
                v-model="parametrosForm.email_cobranca"
                type="email"
                required
                class="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
              />
            </div>

            <div>
              <label class="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">Texto: Prazo de Negociação</label>
              <input
                v-model="parametrosForm.prazo_negociacao_info"
                type="text"
                class="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
              />
            </div>

            <div class="flex justify-end gap-3 pt-3">
              <button
                type="button"
                @click="modalParametrosAberto = false"
                class="px-4 py-2 border border-slate-300 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-50"
              >
                Cancelar
              </button>
              <button
                type="submit"
                :disabled="salvandoParametros"
                class="px-5 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-lg text-sm font-medium transition"
              >
                {{ salvandoParametros ? 'Salvando...' : (criarNovaVigencia ? 'Criar Nova Vigência' : 'Salvar Regra Vigente') }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import { financeiroApi } from "@/api/financeiro"

const relatorio = ref(null)
const carregando = ref(false)
const filtroTexto = ref("")
const filtroCriticidade = ref("TODOS")

// Modais
const modalDetalhesAberto = ref(false)
const modalEmailAberto = ref(false)
const modalParametrosAberto = ref(false)
const unidadeSelecionada = ref(null)

// Envio de E-mail
const formEmail = ref({
  destinatario: "",
  assunto: "",
  mensagem: "",
})
const enviandoEmail = ref(false)
const erroEnvio = ref("")

// Parâmetros de Cobrança
const parametrosForm = ref({
  tipo_multa: "FIXO",
  valor_multa: 10.00,
  percentual_juros_dia: 0.0024,
  qtd_parcelas_ajuizamento: 6,
  email_cobranca: "condominiohortenciasiii@gmail.com",
  prazo_negociacao_info: "O PRAZO PARA NEGOCIAÇÃO OU RENEGOCIAÇÃO DE DÍVIDAS ENCERRA-SE NO FINAL DESTE MÊS.",
})
const salvandoParametros = ref(false)

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

const taxaBadgeColor = computed(() => {
  const taxa = relatorio.value?.taxa_inadimplencia_percentual || 0
  if (taxa > 15) return "bg-rose-100 text-rose-800"
  if (taxa > 5) return "bg-amber-100 text-amber-800"
  return "bg-emerald-100 text-emerald-800"
})

const devedoresFiltrados = computed(() => {
  if (!relatorio.value?.devedores) return []
  return relatorio.value.devedores.filter((dev) => {
    // Filtro de texto
    const busca = filtroTexto.value.toLowerCase().trim()
    const matchTexto =
      !busca ||
      dev.unidade.identificador.toLowerCase().includes(busca) ||
      dev.responsavel.nome.toLowerCase().includes(busca)

    // Filtro de criticidade
    let matchCrit = true
    if (filtroCriticidade.value === "AJUIZAMENTO") {
      matchCrit = dev.sujeito_ajuizamento
    } else if (filtroCriticidade.value === "ATE_3") {
      matchCrit = dev.qtd_titulos <= 3
    }

    return matchTexto && matchCrit
  })
})

const baixandoPdfId = ref(null)

const baixarPdf = async (dev) => {
  if (!dev) return
  baixandoPdfId.value = dev.unidade.id
  try {
    const res = await financeiroApi.getAvisoDebitoPdf(dev.unidade.id)
    const blob = new Blob([res.data], { type: "application/pdf" })
    const url = URL.createObjectURL(blob)
    const link = document.createElement("a")
    link.href = url
    link.download = `aviso_debito_${dev.unidade.identificador.replace(/\s+/g, '_').toLowerCase()}.pdf`
    link.click()
    URL.revokeObjectURL(url)
  } catch (err) {
    console.error("Erro ao baixar PDF:", err)
    alert("Erro ao gerar o PDF de aviso de débito.")
  } finally {
    baixandoPdfId.value = null
  }
}

const carregarDados = async () => {
  carregando.value = true
  try {
    const res = await financeiroApi.getInadimplenciaGeral()
    relatorio.value = res.data
  } catch (err) {
    console.error("Erro ao carregar inadimplência:", err)
  } finally {
    carregando.value = false
  }
}

const getPdfUrl = (unidadeId) => {
  return financeiroApi.getAvisoDebitoPdfUrl(unidadeId)
}

const abrirModalDetalhes = (dev) => {
  unidadeSelecionada.value = dev
  modalDetalhesAberto.value = true
}

const abrirModalEmail = (dev) => {
  unidadeSelecionada.value = dev
  erroEnvio.value = ""
  
  // Pré-preenche os dados com liberdade de edição
  const emails = dev.responsavel.emails_todos?.length
    ? dev.responsavel.emails_todos.join(", ")
    : dev.responsavel.email || ""

  formEmail.value = {
    destinatario: emails,
    assunto: `[${dev.condominio.nome}] Aviso de Débito em Atraso - ${dev.unidade.identificador}`,
    mensagem: dev.parametro?.mensagem_email_padrao || (
      `Prezado(a) ${dev.responsavel.nome},\n\n` +
      `Constatamos títulos pendentes referentes à ${dev.unidade.identificador}.\n` +
      `Encaminhamos anexo o demonstrativo com os cálculos de encargos.\n\n` +
      `Atenciosamente,\nAdministração do Condomínio`
    ),
  }
  modalEmailAberto.value = true
}

const restaurarMensagemPadrao = () => {
  if (unidadeSelecionada.value?.parametro?.mensagem_email_padrao) {
    formEmail.value.mensagem = unidadeSelecionada.value.parametro.mensagem_email_padrao
  }
}

const dispararEmailCobranca = async () => {
  if (!unidadeSelecionada.value) return
  enviandoEmail.value = true
  erroEnvio.value = ""

  try {
    await financeiroApi.enviarEmailCobranca(unidadeSelecionada.value.unidade.id, {
      destinatario_email: formEmail.value.destinatario,
      assunto: formEmail.value.assunto,
      mensagem: formEmail.value.mensagem,
    })
    modalEmailAberto.value = false
    alert("E-mail de cobrança enviado com sucesso acompanhado do PDF em anexo!")
  } catch (err) {
    console.error("Erro ao enviar e-mail:", err)
    erroEnvio.value = err.response?.data?.erro || err.response?.data?.detail || "Falha ao enviar e-mail de cobrança."
  } finally {
    enviandoEmail.value = false
  }
}

const listaHistoricoParametros = ref([])
const criarNovaVigencia = ref(false)
const novaDataInicio = ref("")

const abrirModalParametros = async () => {
  modalParametrosAberto.value = true
  criarNovaVigencia.value = false
  novaDataInicio.value = ""
  try {
    const [resAtual, resHist] = await Promise.all([
      financeiroApi.getParametrosCobranca(),
      financeiroApi.getHistoricoParametrosCobranca(),
    ])
    parametrosForm.value = resAtual.data
    listaHistoricoParametros.value = resHist.data
  } catch (err) {
    console.error("Erro ao carregar parâmetros:", err)
  }
}

const salvarParametros = async () => {
  salvandoParametros.value = true
  try {
    const payload = { ...parametrosForm.value }
    if (criarNovaVigencia.value && novaDataInicio.value) {
      payload.nova_data_inicio = novaDataInicio.value
    }
    await financeiroApi.salvarParametrosCobranca(payload)
    modalParametrosAberto.value = false
    alert(criarNovaVigencia.value ? "Nova vigência de cobrança criada com sucesso!" : "Parâmetros atualizados com sucesso!")
    carregarDados()
  } catch (err) {
    console.error("Erro ao salvar parâmetros:", err)
    alert("Erro ao salvar parâmetros de cobrança.")
  } finally {
    salvandoParametros.value = false
  }
}

onMounted(() => {
  carregarDados()
})
</script>

<style scoped>
@keyframes fadeIn {
  from { opacity: 0; transform: scale(0.97); }
  to { opacity: 1; transform: scale(1); }
}
.animate-fadeIn {
  animation: fadeIn 0.15s ease-out forwards;
}
</style>
