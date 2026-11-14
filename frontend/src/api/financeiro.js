import apiClient from "./client"

export const financeiroApi = {
  // Dashboard
  getDashboard() {
    return apiClient.get("/financeiro/dashboard/")
  },

  // Contas Bancárias
  getContasBancarias(params = {}) {
    return apiClient.get("/financeiro/contas-bancarias/", { params: { page_size: 500, ...params } })
  },
  createContaBancaria(data) {
    return apiClient.post("/financeiro/contas-bancarias/", data)
  },
  updateContaBancaria(id, data) {
    return apiClient.patch(`/financeiro/contas-bancarias/${id}/`, data)
  },
  deleteContaBancaria(id) {
    return apiClient.delete(`/financeiro/contas-bancarias/${id}/`)
  },

  // Períodos
  getPeriodos(params = {}) {
    return apiClient.get("/financeiro/periodos/", { params })
  },
  getPeriodo(id) {
    return apiClient.get(`/financeiro/periodos/${id}/`)
  },
  getSindicoAtivo(condominioId) {
    return apiClient.get("/financeiro/periodos/sindico-ativo/", { params: { condominio_id: condominioId } })
  },
  getSaldosPeriodoAnterior(params = {}) {
    return apiClient.get("/financeiro/periodos/saldos-periodo-anterior/", { params })
  },
  createPeriodo(data) {
    return apiClient.post("/financeiro/periodos/", data)
  },
  updatePeriodo(id, data) {
    return apiClient.patch(`/financeiro/periodos/${id}/`, data)
  },
  deletePeriodo(id) {
    return apiClient.delete(`/financeiro/periodos/${id}/`)
  },
  gerarCotas(periodoId) {
    return apiClient.post(`/financeiro/periodos/${periodoId}/gerar-cotas/`)
  },
  gerarDespesasFixas(periodoId) {
    return apiClient.post(`/financeiro/periodos/${periodoId}/gerar-despesas-fixas/`)
  },
  fecharPeriodo(periodoId) {
    return apiClient.post(`/financeiro/periodos/${periodoId}/fechar/`)
  },
  publicarPeriodo(periodoId) {
    return apiClient.post(`/financeiro/periodos/${periodoId}/publicar/`)
  },
  reabrirPeriodo(periodoId) {
    return apiClient.post(`/financeiro/periodos/${periodoId}/reabrir/`)
  },
  getTotais(periodoId) {
    return apiClient.get(`/financeiro/periodos/${periodoId}/totais/`)
  },
  exportarPdf(periodoId) {
    return apiClient.get(`/financeiro/periodos/${periodoId}/exportar-pdf/`, {
      responseType: "blob",
    })
  },
  exportarExcel(periodoId) {
    return apiClient.get(`/financeiro/periodos/${periodoId}/exportar-excel/`, {
      responseType: "blob",
    })
  },

  // Cotas
  getCotas(params = {}) {
    return apiClient.get("/financeiro/cotas/", { params: { page_size: 500, ...params } })
  },
  updateCota(id, data) {
    return apiClient.patch(`/financeiro/cotas/${id}/`, data)
  },
  darBaixaCota(id, data = {}) {
    return apiClient.post(`/financeiro/cotas/${id}/dar-baixa/`, data)
  },
  removerBaixaCota(id) {
    return apiClient.post(`/financeiro/cotas/${id}/remover-baixa/`)
  },
  marcarCotasEmMassa(data) {
    return apiClient.post("/financeiro/cotas/marcar-em-massa/", data)
  },

  // Receitas Extras
  getReceitasExtras(params = {}) {
    return apiClient.get("/financeiro/receitas-extras/", { params: { page_size: 500, ...params } })
  },
  createReceitaExtra(data) {
    return apiClient.post("/financeiro/receitas-extras/", data)
  },
  updateReceitaExtra(id, data) {
    return apiClient.patch(`/financeiro/receitas-extras/${id}/`, data)
  },
  deleteReceitaExtra(id) {
    return apiClient.delete(`/financeiro/receitas-extras/${id}/`)
  },

  // Despesas
  getDespesas(params = {}) {
    return apiClient.get("/financeiro/despesas/", { params: { page_size: 500, ...params } })
  },
  createDespesa(formData) {
    return apiClient.post("/financeiro/despesas/", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    })
  },
  updateDespesa(id, formData) {
    return apiClient.patch(`/financeiro/despesas/${id}/`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    })
  },
  deleteDespesa(id) {
    return apiClient.delete(`/financeiro/despesas/${id}/`)
  },

  // Área do Morador
  getAreaMorador(params = {}) {
    return apiClient.get("/financeiro/morador/", { params })
  },

  // Módulo de Inadimplência e Cobrança
  getInadimplenciaGeral(params = {}) {
    return apiClient.get("/financeiro/inadimplencia/", { params })
  },
  getInadimplenciaUnidade(unidadeId, params = {}) {
    return apiClient.get(`/financeiro/inadimplencia/unidade/${unidadeId}/`, { params })
  },
  getInadimplenciaConsolidadaMorador() {
    return apiClient.get("/financeiro/inadimplencia/morador/consolidado/")
  },
  getAvisoDebitoPdf(unidadeId) {
    return apiClient.get(`/financeiro/inadimplencia/unidade/${unidadeId}/pdf/`, {
      responseType: "blob",
    })
  },
  getAvisoDebitoConsolidadoPdf() {
    return apiClient.get("/financeiro/inadimplencia/morador/consolidado/pdf/", {
      responseType: "blob",
    })
  },
  getAvisoDebitoPdfUrl(unidadeId) {
    const base = apiClient.defaults.baseURL || "/api"
    return `${base}/financeiro/inadimplencia/unidade/${unidadeId}/pdf/`
  },
  enviarEmailCobranca(unidadeId, data) {
    return apiClient.post(`/financeiro/inadimplencia/unidade/${unidadeId}/enviar-email/`, data)
  },
  getParametrosCobranca() {
    return apiClient.get("/financeiro/parametros-cobranca/atual/")
  },
  getHistoricoParametrosCobranca() {
    return apiClient.get("/financeiro/parametros-cobranca/historico/")
  },
  salvarParametrosCobranca(data) {
    return apiClient.post("/financeiro/parametros-cobranca/atual/", data)
  },
  getHistoricoCobrancas(params = {}) {
    return apiClient.get("/financeiro/historico-cobrancas/", { params })
  },

  // Declaração de Nada Consta
  emitirNadaConsta(unidadeId) {
    return apiClient.post("/financeiro/nada-consta/emitir/", { unidade_id: unidadeId })
  },
  emitirNadaConstaConsolidado() {
    return apiClient.post("/financeiro/nada-consta/morador/consolidado/")
  },
  getNadaConstaPdf(certidaoId, unidadesMulti = "") {
    const params = unidadesMulti ? { unidades_multi: unidadesMulti } : {}
    return apiClient.get(`/financeiro/nada-consta/${certidaoId}/pdf/`, {
      params,
      responseType: "blob",
    })
  },
  getNadaConstaConsolidadoPdf(ids = "") {
    const params = ids ? { ids } : {}
    return apiClient.get("/financeiro/nada-consta/morador/consolidado/pdf/", {
      params,
      responseType: "blob",
    })
  },
  getNadaConstaPdfUrl(certidaoId) {
    const base = apiClient.defaults.baseURL || "/api"
    return `${base}/financeiro/nada-consta/${certidaoId}/pdf/`
  },
}

export default financeiroApi
