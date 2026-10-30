/**
 * Utilitários de regras de negócio e cálculos do módulo de prestação de contas.
 * Garante fidelidade matemática 100% à planilha original do Condomínio Hortênias III.
 */

export function calcularJurosMulta(valorPago, cotaBase) {
  const pago = Number(valorPago) || 0
  const cota = Number(cotaBase) || 0
  if (pago > cota) {
    return Number((pago - cota).toFixed(2))
  }
  return 0
}

export function formatarObservacaoDiferenca(saldoMes, totalSaldoBancario, valorCotaPadrao, mesProx, dataProx) {
  const diff = Number((saldoMes - totalSaldoBancario).toFixed(2))
  const cotaPadrao = Number(valorCotaPadrao) || 380
  const cotas = Math.abs(diff) / cotaPadrao
  const qtdFormatada = Number.isInteger(cotas) ? cotas : Number(cotas.toFixed(2))
  const mes = mesProx || "MÊS SEGUINTE"
  const venc = dataProx || ""

  return `A diferença entre o SALDO MÊS e o TOTAL DO SALDO BANCÁRIO é de ${qtdFormatada} cota(s) referente ao mês de ${mes} com vencimento em ${venc}`
}

export function calcularTotaisPrestacao({
  cotas = [],
  receitasExtras = [],
  despesas = [],
  saldoAnteriorCC = 0,
  saldoAnteriorAplicacao = 0,
  saldoAnteriorPorquinho = 0,
  totalSaldoBancario = 0,
  valorCotaPadrao = 380,
  mesProx = "OUTUBRO",
  dataProx = "05/11/2026",
}) {
  // 1. Cotas Regulares
  const totalCotasRegulares = cotas.reduce((acc, c) => {
    if (c.data_pagamento) {
      return acc + (Number(c.cota) || Number(c.valor_titulo) || 0)
    }
    return acc
  }, 0)

  // 2. Receitas Extras
  const totalReceitasExtras = receitasExtras.reduce((acc, e) => {
    return acc + (Number(e.valor) || 0)
  }, 0)

  const totalReceitas = Number((totalCotasRegulares + totalReceitasExtras).toFixed(2))

  // 3. Despesas Fixas e Variáveis
  const totalDespesasFixas = despesas
    .filter((d) => d.tipo === "FIXA")
    .reduce((acc, d) => acc + (Number(d.valor) || 0), 0)

  const totalDespesasVariaveis = despesas
    .filter((d) => d.tipo === "VARIAVEL")
    .reduce((acc, d) => acc + (Number(d.valor) || 0), 0)

  const totalDespesas = Number((totalDespesasFixas + totalDespesasVariaveis).toFixed(2))

  // 4. Saldos Anteriores
  const cc = Number(saldoAnteriorCC) || 0
  const cdb = Number(saldoAnteriorAplicacao) || 0
  const porquinho = Number(saldoAnteriorPorquinho) || 0
  const saldoAnteriorTotal = Number((cc + cdb + porquinho).toFixed(2))

  // 5. Subtotal e Saldo Mês
  const subtotal = Number((saldoAnteriorTotal + totalReceitas).toFixed(2))
  const saldoMes = Number((subtotal - totalDespesas).toFixed(2))

  // 6. Diferença
  const saldoBancario = Number(totalSaldoBancario) || 0
  const diferencaSaldo = Number((saldoMes - saldoBancario).toFixed(2))
  const observacaoDiferenca = formatarObservacaoDiferenca(
    saldoMes,
    saldoBancario,
    valorCotaPadrao,
    mesProx,
    dataProx
  )

  return {
    totalCotasRegulares: Number(totalCotasRegulares.toFixed(2)),
    totalReceitasExtras: Number(totalReceitasExtras.toFixed(2)),
    totalReceitas,
    totalDespesasFixas: Number(totalDespesasFixas.toFixed(2)),
    totalDespesasVariaveis: Number(totalDespesasVariaveis.toFixed(2)),
    totalDespesas,
    saldoAnteriorTotal,
    subtotal,
    saldoMes,
    totalSaldoBancario: saldoBancario,
    diferencaSaldo,
    observacaoDiferenca,
  }
}
