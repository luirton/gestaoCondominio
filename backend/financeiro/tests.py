from decimal import Decimal
from datetime import date
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from core.models import Condominio, Unidade, Pessoa, VinculoPessoaUnidade, CargoCondominial
from financeiro.models import (
    ContaBancaria,
    PeriodoPrestacao,
    PeriodoSaldoConta,
    ReceitaCota,
    ReceitaExtra,
    Despesa,
    SaldoPeriodo,
)
from financeiro.services import (
    calcular_totais_periodo,
    fechar_periodo_prestacao,
    gerar_cotas_iniciais,
    exportar_relatorio_pdf,
    exportar_relatorio_excel,
)

Usuario = get_user_model()


class FinanceiroCalculosTestCase(TestCase):
    def setUp(self):
        self.condominio = Condominio.objects.create(
            nome="CONDOMÍNIO HORTÊNCIAS III",
            cnpj="06.275.266/0001-23",
            endereco="Rua Manuel Teixeira de Melo",
            numero="827",
            cidade="Fortaleza",
            uf="CE"
        )
        self.unidade1 = Unidade.objects.create(
            condominio=self.condominio,
            identificador="Casa 01",
            bloco_torre="1"
        )
        self.unidade2 = Unidade.objects.create(
            condominio=self.condominio,
            identificador="Casa 02",
            bloco_torre="1"
        )

        self.periodo = PeriodoPrestacao.objects.create(
            condominio=self.condominio,
            mes_referencia=date(2026, 9, 7),
            mes_referencia_rotulo="SETEMBRO/2026",
            data_vencimento=date(2026, 10, 5),
            mes_prox_vencimento="OUTUBRO",
            data_prox_vencimento=date(2026, 11, 5),
            data_inicio_prestacao=date(2026, 10, 1),
            data_fim_prestacao=date(2026, 10, 31),
            valor_cota_padrao=Decimal("380.00"),
            cota_extra=Decimal("50.00"),
            saldo_anterior_cc=Decimal("500.00"),
            saldo_anterior_aplicacao=Decimal("1000.00"),
            saldo_anterior_porquinho=Decimal("200.00"),
            total_saldo_bancario=Decimal("2080.00"),
        )

    def test_gerar_cotas_automaticas(self):
        criadas = gerar_cotas_iniciais(self.periodo)
        self.assertEqual(criadas, 2)
        self.assertEqual(self.periodo.cotas.count(), 2)

    def test_calculo_receitas_despesas_e_saldo(self):
        # Cria cotas
        ReceitaCota.objects.create(
            periodo=self.periodo,
            unidade=self.unidade1,
            mes_referencia=date(2026, 9, 7),
            data_vencimento=date(2026, 10, 5),
            valor_titulo=Decimal("380.00"),
            data_pagamento=date(2026, 10, 5),
            cota=Decimal("380.00"),
            valor_pago=Decimal("380.00"),
        )
        # Cota com juros
        ReceitaCota.objects.create(
            periodo=self.periodo,
            unidade=self.unidade2,
            mes_referencia=date(2026, 9, 7),
            data_vencimento=date(2026, 10, 5),
            valor_titulo=Decimal("380.00"),
            data_pagamento=date(2026, 10, 6),
            cota=Decimal("380.00"),
            valor_pago=Decimal("390.00"),
            juros_multa=Decimal("10.00"),
        )
        # Receita extra
        ReceitaExtra.objects.create(
            periodo=self.periodo,
            tipo=ReceitaExtra.TipoReceitaExtra.ALUGUEL_VAGA,
            descricao="Aluguel de vaga 01",
            valor=Decimal("100.00"),
            data=date(2026, 10, 5),
        )

        # Despesas Fixas e Variáveis
        Despesa.objects.create(
            periodo=self.periodo,
            tipo=Despesa.TipoDespesa.FIXA,
            categoria=Despesa.CategoriaDespesa.SALARIO,
            descricao="Salário Zelador",
            valor=Decimal("400.00"),
            data_pagamento=date(2026, 10, 5),
        )
        Despesa.objects.create(
            periodo=self.periodo,
            tipo=Despesa.TipoDespesa.VARIAVEL,
            categoria=Despesa.CategoriaDespesa.MATERIAL_LIMPEZA,
            descricao="Sacos de Lixo",
            valor=Decimal("80.00"),
            data_pagamento=date(2026, 10, 10),
        )

        totais = calcular_totais_periodo(self.periodo)

        # Asserções
        # Cotas regulares: 380 + 380 = 760.00
        self.assertEqual(totais["total_cotas_regulares"], Decimal("760.00"))
        # Extra: 100.00
        self.assertEqual(totais["total_receitas_extras"], Decimal("100.00"))
        # Total receitas = 860.00
        self.assertEqual(totais["total_receitas"], Decimal("860.00"))
        # Despesas Fixas = 400.00, Variáveis = 80.00, Total = 480.00
        self.assertEqual(totais["total_despesas_fixas"], Decimal("400.00"))
        self.assertEqual(totais["total_despesas_variaveis"], Decimal("80.00"))
        self.assertEqual(totais["total_despesas"], Decimal("480.00"))
        # Saldo anterior total = 500 + 1000 + 200 = 1700.00
        self.assertEqual(totais["saldo_anterior_total"], Decimal("1700.00"))
        # Subtotal = 1700 + 860 = 2560.00
        self.assertEqual(totais["subtotal"], Decimal("2560.00"))
        # Saldo Mês = 2560 - 480 = 2080.00
        self.assertEqual(totais["saldo_mes"], Decimal("2080.00"))
        # Diferença com saldo bancário (2080.00) = 0.00
        self.assertEqual(totais["diferenca_saldo"], Decimal("0.00"))
        self.assertEqual(totais["diferenca_em_cotas"], Decimal("0.00"))
        self.assertIn("0 cota(s)", totais["observacao_diferenca"])

    def test_fechamento_congelado_e_snapshot(self):
        usuario = Usuario.objects.create_user(username="sindico_teste", password="123")
        totais = fechar_periodo_prestacao(self.periodo, usuario)

        self.assertEqual(self.periodo.status, PeriodoPrestacao.StatusPeriodo.FECHADO)
        snapshot = SaldoPeriodo.objects.get(periodo=self.periodo)
        self.assertEqual(snapshot.saldo_anterior_total, totais["saldo_anterior_total"])
        self.assertEqual(snapshot.fechado_por, usuario)

        # Não deve permitir fechar novamente um período fechado
        with self.assertRaises(ValidationError):
            fechar_periodo_prestacao(self.periodo, usuario)

    def test_exportacao_pdf_e_excel(self):
        pdf_buf = exportar_relatorio_pdf(self.periodo)
        self.assertGreater(len(pdf_buf.getvalue()), 1000)

        excel_buf = exportar_relatorio_excel(self.periodo)
        self.assertGreater(len(excel_buf.getvalue()), 1000)

    def test_validacao_valores_negativos(self):
        despesa_invalida = Despesa(
            periodo=self.periodo,
            tipo=Despesa.TipoDespesa.FIXA,
            categoria=Despesa.CategoriaDespesa.OUTRO,
            descricao="Negativa",
            valor=Decimal("-50.00"),
            data_pagamento=date(2026, 10, 5)
        )
        with self.assertRaises(ValidationError):
            despesa_invalida.clean()

    def test_isencao_mandato_sindico_na_geracao_de_cotas(self):
        # 1. Cria pessoa e vinculo de responsavel com a unidade 1
        sindico_pessoa = Pessoa.objects.create(
            nome="Síndico Isento de Teste",
            cpf="111.222.333-44",
        )
        VinculoPessoaUnidade.objects.create(
            pessoa=sindico_pessoa,
            unidade=self.unidade1,
            tipo=VinculoPessoaUnidade.TipoVinculo.PROPRIETARIO,
            data_inicio=date(2026, 1, 1),
            responsavel=True,
        )
        # 2. Cria mandato de sindico com isenção
        CargoCondominial.objects.create(
            condominio=self.condominio,
            pessoa=sindico_pessoa,
            cargo=CargoCondominial.TipoCargo.SINDICO,
            data_inicio=date(2026, 1, 1),
            ativo=True,
            isento_condominio=True,
        )

        # 3. Gera cotas para o período
        gerar_cotas_iniciais(self.periodo)

        cota_unid1 = ReceitaCota.objects.get(periodo=self.periodo, unidade=self.unidade1)
        cota_unid2 = ReceitaCota.objects.get(periodo=self.periodo, unidade=self.unidade2)

        # Unidade 1 deve nascer como ISENTO
        self.assertTrue(cota_unid1.isento)
        self.assertEqual(cota_unid1.status, ReceitaCota.StatusCota.ISENTO)
        self.assertEqual(cota_unid1.cota, Decimal("0.00"))

        # Unidade 2 permanece regular pendente
        self.assertFalse(cota_unid2.isento)
        self.assertEqual(cota_unid2.status, ReceitaCota.StatusCota.PENDENTE)

        # Totais: cota isenta não entra em receitas
        totais = calcular_totais_periodo(self.periodo)
        self.assertEqual(totais["total_cotas_regulares"], Decimal("0.00"))

    def test_saldos_contas_mestre_detalhe(self):
        conta1 = ContaBancaria.objects.create(
            condominio=self.condominio,
            banco_nome="Banco Inter",
            tipo_conta=ContaBancaria.TipoConta.CORRENTE,
            descricao="Inter CC",
            ordem=1
        )
        conta2 = ContaBancaria.objects.create(
            condominio=self.condominio,
            banco_nome="Caixa",
            tipo_conta=ContaBancaria.TipoConta.POUPANCA,
            descricao="Poupança Reserva",
            ordem=2
        )

        PeriodoSaldoConta.objects.create(
            periodo=self.periodo,
            conta=conta1,
            saldo_anterior=Decimal("300.00"),
            saldo_final=Decimal("700.00")
        )
        PeriodoSaldoConta.objects.create(
            periodo=self.periodo,
            conta=conta2,
            saldo_anterior=Decimal("200.00"),
            saldo_final=Decimal("500.00")
        )

        totais = calcular_totais_periodo(self.periodo)
        self.assertEqual(totais["saldo_anterior_total"], Decimal("500.00"))
        self.assertEqual(totais["total_saldo_bancario"], Decimal("1200.00"))

    def test_serializer_criar_periodo_com_saldos_contas_e_zeros(self):
        from financeiro.serializers import PeriodoPrestacaoSerializer
        conta = ContaBancaria.objects.create(
            condominio=self.condominio,
            banco_nome="Banco Inter",
            tipo_conta=ContaBancaria.TipoConta.CORRENTE,
            descricao="Inter CC Teste",
        )
        data = {
            "condominio": self.condominio.id,
            "mes_referencia": "2026-11-30",
            "mes_referencia_rotulo": "NOVEMBRO/2026",
            "data_vencimento": "2026-12-05",
            "data_inicio_prestacao": "2026-11-01",
            "data_fim_prestacao": "2026-11-30",
            "valor_cota_padrao": "380.00",
            "cota_extra": "50.00",
            "saldos_contas": [
                {
                    "conta": conta.id,
                    "saldo_anterior": 0,
                    "saldo_final": 0,
                }
            ]
        }
        serializer = PeriodoPrestacaoSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        periodo = serializer.save()
        self.assertEqual(periodo.saldos_contas.count(), 1)
        saldo_conta = periodo.saldos_contas.first()
        self.assertEqual(saldo_conta.saldo_anterior, Decimal("0.00"))
        self.assertEqual(saldo_conta.saldo_final, Decimal("0.00"))
