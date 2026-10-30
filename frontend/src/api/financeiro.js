import apiClient from "./client"

export const financeiroApi = {
  // Dashboard
  getDashboard() {
    return apiClient.get("/financeiro/dashboard/")
  },

  // Períodos
  getPeriodos(params = {}) {
    return apiClient.get("/financeiro/periodos/", { params })
  },
  getPeriodo(id) {
    return apiClient.get(`/financeiro/periodos/${id}/`)
  },
  createPeriodo(data) {
    return apiClient.post("/financeiro/periodos/", data)
  },
  updatePeriodo(id, data) {
    return apiClient.patch(`/financeiro/periodos/${id}/`, data)
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
    return apiClient.get("/financeiro/cotas/", { params })
  },
  updateCota(id, data) {
    return apiClient.patch(`/financeiro/cotas/${id}/`, data)
  },
  marcarCotasEmMassa(data) {
    return apiClient.post("/financeiro/cotas/marcar-em-massa/", data)
  },

  // Receitas Extras
  getReceitasExtras(params = {}) {
    return apiClient.get("/financeiro/receitas-extras/", { params })
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
    return apiClient.get("/financeiro/despesas/", { params })
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
