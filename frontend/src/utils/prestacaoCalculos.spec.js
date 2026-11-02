import { describe, it, expect } from "vitest"
import {
  calcularJurosMulta,
  formatarObservacaoDiferenca,
  calcularTotaisPrestacao,
} from "./prestacaoCalculos"

describe("Cálculos e Regras de Negócio da Prestação de Contas", () => {
  it("deve calcular juros e multa quando o valor pago for maior que a cota", () => {
    expect(calcularJurosMulta(390.25, 380)).toBe(10.25)
    expect(calcularJurosMulta(397.04, 380)).toBe(17.04)
    expect(calcularJurosMulta(380, 380)).toBe(0)
    expect(calcularJurosMulta(350, 380)).toBe(0)
  })

  it("deve formatar a observação da diferença de cotas com 0 cotas", () => {
    const obs = formatarObservacaoDiferenca(46881.93, 46881.93, 380, "OUTUBRO", "05/11/2026")
    expect(obs).toBe(
      "A diferença entre o SALDO MÊS e o TOTAL DO SALDO BANCÁRIO é de 0 cota(s) referente ao mês de OUTUBRO com vencimento em 05/11/2026"
    )
  })

  it("deve calcular com precisão de 100% o cenário real de Setembro/2026 da planilha", () => {
    // 45 cotas pagas a 380
    const cotas = Array.from({ length: 45 }, (_, i) => ({
      data_pagamento: "2026-10-05",
      cota: 380,
      valor_titulo: 380,
    }))
    // 7 cotas pendentes
    for (let i = 0; i < 7; i++) {
      cotas.push({ data_pagamento: null, cota: null, valor_titulo: 380 })
    }

    const receitasExtras = [
      { valor: 395.83 }, // casa 05
      { valor: 10.25 },  // casa 19
      { valor: 10.25 },  // casa 38
      { valor: 10.25 },  // casa 12
      { valor: 10.51 },  // casa 29
      { valor: 17.04 },  // casa 14
      { valor: 15.82 },  // casa 48
      { valor: 100.0 },  // vaga 23
      { valor: 100.0 },  // vaga 14
      { valor: 0.0 },    // CDB
    ]

    const despesas = [
      // Fixas (total 13429.82)
      { tipo: "FIXA", valor: 4474.54 },
      { tipo: "FIXA", valor: 1945.20 },
      { tipo: "FIXA", valor: 380.00 },
      { tipo: "FIXA", valor: 334.80 },
      { tipo: "FIXA", valor: 1040.00 },
      { tipo: "FIXA", valor: 700.00 },
      { tipo: "FIXA", valor: 2502.08 },
      { tipo: "FIXA", valor: 780.29 },
      { tipo: "FIXA", valor: 802.91 },
      { tipo: "FIXA", valor: 340.00 },
      { tipo: "FIXA", valor: 130.00 },

      // Variáveis (total 2460.16)
      { tipo: "VARIAVEL", valor: 134.00 },
      { tipo: "VARIAVEL", valor: 250.00 },
      { tipo: "VARIAVEL", valor: 300.00 },
      { tipo: "VARIAVEL", valor: 1389.01 },
      { tipo: "VARIAVEL", valor: 220.00 },
      { tipo: "VARIAVEL", valor: 83.59 },
      { tipo: "VARIAVEL", valor: 83.56 },
    ]

    const resultado = calcularTotaisPrestacao({
      cotas,
      receitasExtras,
      despesas,
      saldoAnteriorCC: 525.74,
      saldoAnteriorAplicacao: 41362.52,
      saldoAnteriorPorquinho: 3113.70,
      totalSaldoBancario: 46881.93,
      valorCotaPadrao: 380,
      mesProx: "OUTUBRO",
      dataProx: "05/11/2026",
    })

    expect(resultado.totalCotasRegulares).toBe(17100.00)
    expect(resultado.totalReceitasExtras).toBe(669.95)
    expect(resultado.totalReceitas).toBe(17769.95)
    expect(resultado.totalDespesasFixas).toBe(13429.82)
    expect(resultado.totalDespesasVariaveis).toBe(2460.16)
    expect(resultado.totalDespesas).toBe(15889.98)
    expect(resultado.saldoAnteriorTotal).toBe(45001.96)
    expect(resultado.subtotal).toBe(62771.91)
    expect(resultado.saldoMes).toBe(46881.93)
    expect(resultado.diferencaSaldo).toBe(0.00)
    expect(resultado.observacaoDiferenca).toContain("0 cota(s)")
  })
})
