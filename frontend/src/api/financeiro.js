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
  getAreaMorador() {
    return apiClient.get("/financeiro/morador/")
  },
}

export default financeiroApi
