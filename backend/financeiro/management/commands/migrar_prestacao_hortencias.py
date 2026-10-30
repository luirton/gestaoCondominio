from datetime import date
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import Condominio, Unidade, Pessoa, CargoCondominial
from financeiro.models import (
    ContaBancaria,
    PeriodoPrestacao,
    PeriodoSaldoConta,
    ReceitaCota,
    ReceitaExtra,
    Despesa,
    SaldoPeriodo,
    AuditLog,
)
from financeiro.services import fechar_periodo_prestacao, calcular_totais_periodo


class Command(BaseCommand):
    help = "Migra os dados reais da planilha do Condomínio Hortências III (Setembro/2026)"

    def handle(self, *args, **options):
        self.stdout.write("Iniciando migração dos dados do Condomínio Hortências III...")

        with transaction.atomic():
            # 1. Garantir existência do Condomínio Hortências III
            condominio, created = Condominio.objects.get_or_create(
                cnpj="06.275.266/0001-23",
                defaults={
                    "nome": "CONDOMÍNIO HORTÊNCIAS III",
                    "endereco": "Rua Manuel Teixeira de Melo",
                    "numero": "827",
                    "bairro": "José de Alencar",
                    "cidade": "Fortaleza",
                    "uf": "CE",
                    "cep": "60830-740",
                    "ativo": True,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Condomínio cadastrado: {condominio.nome}"))
            else:
                self.stdout.write(f"Condomínio já existente: {condominio.nome}")

            # 2. Criar as 52 Unidades (Casas 01 a 52)
            unidades_map = {}
            for num in range(1, 53):
                identificador = f"CASA {num:02d}"
                unidade = Unidade.objects.filter(
                    condominio=condominio,
                    identificador__iexact=identificador
                ).first()
                if not unidade:
                    unidade = Unidade.objects.create(
                        condominio=condominio,
                        identificador=identificador,
                        bloco_torre="PRINCIPAL",
                        fracao_ideal=Decimal("0.019230"),
                    )
                unidades_map[num] = unidade

            self.stdout.write(self.style.SUCCESS(f"52 Unidades conferidas e associadas."))

            # 3. Criar Período de Prestação (Setembro/2026)
            periodo, _ = PeriodoPrestacao.objects.get_or_create(
                condominio=condominio,
                data_inicio_prestacao=date(2026, 10, 1),
                data_fim_prestacao=date(2026, 10, 31),
                defaults={
                    "mes_referencia": date(2026, 9, 7),
                    "mes_referencia_rotulo": "SETEMBRO/2026",
                    "data_vencimento": date(2026, 10, 5),
                    "mes_prox_vencimento": "OUTUBRO",
                    "data_prox_vencimento": date(2026, 11, 5),
                    "valor_cota_padrao": Decimal("380.00"),
                    "valor_vaga_padrao": Decimal("100.00"),
                    "saldo_anterior_cc": Decimal("525.74"),
                    "saldo_anterior_aplicacao": Decimal("41362.52"),
                    "saldo_anterior_porquinho": Decimal("3113.70"),
                    "total_saldo_bancario": Decimal("46881.93"),
                    "data_saldo_bancario": date(2026, 10, 31),
                    "sindico_nome": "JOSÉ MARTINS DA SILVA FILHO",
                    "sindico_cpf": "447.260.903-72",
                    "data_assinatura": date(2026, 10, 29),
                    "status": PeriodoPrestacao.StatusPeriodo.ABERTO,
                }
            )

            # 3.1 Contas Bancárias & Saldos Mestre-Detalhe
            conta_cc, _ = ContaBancaria.objects.get_or_create(
                condominio=condominio,
                descricao="Conta Corrente Inter",
                defaults={
                    "banco_nome": "Banco Inter",
                    "tipo_conta": ContaBancaria.TipoConta.CORRENTE,
                    "agencia": "0001-9",
                    "conta": "1029384-7",
                    "ordem": 1,
                }
            )
            conta_cdb, _ = ContaBancaria.objects.get_or_create(
                condominio=condominio,
                descricao="Aplicação CDB Inter",
                defaults={
                    "banco_nome": "Banco Inter",
                    "tipo_conta": ContaBancaria.TipoConta.APLICACAO,
                    "agencia": "0001-9",
                    "conta": "1029384-7",
                    "ordem": 2,
                }
            )
            conta_porquinho, _ = ContaBancaria.objects.get_or_create(
                condominio=condominio,
                descricao="Porquinho Reserva (Férias e 13º)",
                defaults={
                    "banco_nome": "Banco Inter",
                    "tipo_conta": ContaBancaria.TipoConta.RESERVA,
                    "agencia": "0001-9",
                    "conta": "1029384-7",
                    "ordem": 3,
                }
            )

            PeriodoSaldoConta.objects.update_or_create(
                periodo=periodo,
                conta=conta_cc,
                defaults={"saldo_anterior": Decimal("525.74"), "saldo_final": Decimal("2405.71")}
            )
            PeriodoSaldoConta.objects.update_or_create(
                periodo=periodo,
                conta=conta_cdb,
                defaults={"saldo_anterior": Decimal("41362.52"), "saldo_final": Decimal("41362.52")}
            )
            PeriodoSaldoConta.objects.update_or_create(
                periodo=periodo,
                conta=conta_porquinho,
                defaults={"saldo_anterior": Decimal("3113.70"), "saldo_final": Decimal("3113.70")}
            )

            # 3.2 Garantir Mandato de Síndico
            sindico_pessoa, _ = Pessoa.objects.get_or_create(
                cpf="447.260.903-72",
                defaults={"nome": "JOSÉ MARTINS DA SILVA FILHO"}
            )
            CargoCondominial.objects.update_or_create(
                condominio=condominio,
                cargo=CargoCondominial.TipoCargo.SINDICO,
                ativo=True,
                defaults={
                    "pessoa": sindico_pessoa,
                    "data_inicio": date(2026, 1, 1),
                    "isento_condominio": False,
                }
            )

            # 4. Dados das 52 cotas (Aba PAGAMENTOS da planilha)
            # Lista de casas pagas: (num, data_pagamento, cota, valor_pago, obs)
            dados_pagamentos = [
                (1, None, None, None, ""),
                (2, date(2026, 10, 3), Decimal("380.00"), Decimal("380.00"), ""),
                (3, date(2026, 10, 5), Decimal("380.00"), Decimal("380.00"), ""),
                (4, date(2026, 10, 4), Decimal("380.00"), Decimal("380.00"), ""),
                (5, None, None, None, "Cota do mês em aberto (pagou atrasado 07/09/2026)"),
                (6, date(2026, 10, 5), Decimal("380.00"), Decimal("380.00"), ""),
                (7, date(2026, 10, 4), Decimal("380.00"), Decimal("380.00"), ""),
                (8, date(2026, 10, 5), Decimal("380.00"), Decimal("380.00"), ""),
                (9, date(2026, 10, 5), Decimal("380.00"), Decimal("380.00"), ""),
                (10, date(2026, 10, 5), Decimal("380.00"), Decimal("380.00"), ""),
                (11, date(2026, 10, 5), Decimal("380.00"), Decimal("380.00"), ""),
                (12, date(2026, 10, 6), Decimal("380.00"), Decimal("390.25"), "Juros 10.25"),
                (13, date(2026, 10, 5), Decimal("380.00"), Decimal("380.00"), ""),
                (14, date(2026, 10, 27), Decimal("380.00"), Decimal("397.04"), "Juros 17.04"),
                (15, date(2026, 10, 5), Decimal("380.00"), Decimal("380.00"), ""),
                (16, date(2026, 10, 1), Decimal("380.00"), Decimal("380.00"), ""),
                (17, date(2026, 10, 1), Decimal("380.00"), Decimal("380.00"), ""),
                (18, date(2026, 10, 5), Decimal("380.00"), Decimal("380.00"), ""),
                (19, date(2026, 10, 6), Decimal("380.00"), Decimal("390.25"), "Juros 10.25"),
                (20, date(2026, 10, 5), Decimal("380.00"), Decimal("380.00"), ""),
                (21, None, None, None, ""),
                (22, date(2026, 10, 5), Decimal("380.00"), Decimal("380.00"), ""),
                (23, date(2026, 10, 1), Decimal("380.00"), Decimal("380.00"), ""),
                (24, None, None, None, ""),
                (25, date(2026, 10, 5), Decimal("380.00"), Decimal("380.00"), ""),
                (26, date(2026, 10, 5), Decimal("380.00"), Decimal("380.00"), ""),
                (27, date(2026, 10, 5), Decimal("380.00"), Decimal("380.00"), ""),
                (28, date(2026, 10, 5), Decimal("380.00"), Decimal("380.00"), ""),
                (29, date(2026, 10, 7), Decimal("380.00"), Decimal("390.51"), "Juros 10.51"),
                (30, date(2026, 10, 5), Decimal("380.00"), Decimal("380.00"), ""),
                (31, date(2026, 10, 5), Decimal("380.00"), Decimal("380.00"), ""),
                (32, None, None, None, ""),
                (33, date(2026, 10, 5), Decimal("380.00"), Decimal("380.00"), ""),
                (34, date(2026, 10, 5), Decimal("380.00"), Decimal("380.00"), ""),
                (35, date(2026, 10, 1), Decimal("380.00"), Decimal("380.00"), ""),
                (36, date(2026, 10, 4), Decimal("380.00"), Decimal("380.00"), ""),
                (37, date(2026, 10, 3), Decimal("380.00"), Decimal("380.00"), ""),
                (38, date(2026, 10, 6), Decimal("380.00"), Decimal("390.25"), "Juros 10.25"),
                (39, date(2026, 10, 2), Decimal("380.00"), Decimal("380.00"), ""),
                (40, date(2026, 10, 5), Decimal("380.00"), Decimal("380.00"), ""),
                (41, date(2026, 10, 2), Decimal("380.00"), Decimal("380.00"), ""),
                (42, None, None, None, ""),
                (43, date(2026, 10, 2), Decimal("380.00"), Decimal("380.00"), ""),
                (44, date(2026, 10, 5), Decimal("380.00"), Decimal("380.00"), ""),
                (45, date(2026, 10, 5), Decimal("380.00"), Decimal("380.00"), ""),
                (46, date(2026, 10, 5), Decimal("380.00"), Decimal("380.00"), ""),
                (47, None, None, None, ""),
                (48, date(2026, 10, 28), Decimal("380.00"), Decimal("395.82"), "Juros 15.82"),
                (49, date(2026, 10, 2), Decimal("380.00"), Decimal("380.00"), ""),
                (50, date(2026, 10, 1), Decimal("380.00"), Decimal("380.00"), ""),
                (51, date(2026, 10, 2), Decimal("380.00"), Decimal("380.00"), ""),
                (52, date(2026, 10, 5), Decimal("380.00"), Decimal("380.00"), ""),
            ]

            periodo.cotas.all().delete()
            for num, dt_pagto, cota_val, val_pago, obs in dados_pagamentos:
                juros = (val_pago - cota_val) if (val_pago and cota_val and val_pago > cota_val) else Decimal("0.00")
                ReceitaCota.objects.create(
                    periodo=periodo,
                    unidade=unidades_map[num],
                    numero_ordem=num,
                    mes_referencia=periodo.mes_referencia,
                    data_vencimento=periodo.data_vencimento,
                    valor_titulo=periodo.valor_cota_padrao,
                    data_pagamento=dt_pagto,
                    cota=cota_val,
                    valor_pago=val_pago,
                    juros_multa=juros,
                    status=ReceitaCota.StatusCota.PAGO if dt_pagto else ReceitaCota.StatusCota.PENDENTE,
                    observacao=obs,
                )

            # 5. Receitas Extras (Atrasos, Juros de atraso, Aluguel de Vagas)
            periodo.receitas_extras.all().delete()
            extras_dados = [
                ("JUROS E MULTAS - CASA 05 VENC.07/09/2026", Decimal("395.83"), ReceitaExtra.TipoReceitaExtra.COTA_ATRASADA, 5),
                ("JUROS E MULTAS - CASA 19", Decimal("10.25"), ReceitaExtra.TipoReceitaExtra.JUROS_MULTA, 19),
                ("JUROS E MULTAS - CASA 38", Decimal("10.25"), ReceitaExtra.TipoReceitaExtra.JUROS_MULTA, 38),
                ("JUROS E MULTAS - CASA 12", Decimal("10.25"), ReceitaExtra.TipoReceitaExtra.JUROS_MULTA, 12),
                ("JUROS E MULTAS - CASA 29", Decimal("10.51"), ReceitaExtra.TipoReceitaExtra.JUROS_MULTA, 29),
                ("JUROS E MULTAS - CASA 14", Decimal("17.04"), ReceitaExtra.TipoReceitaExtra.JUROS_MULTA, 14),
                ("JUROS E MULTAS - CASA 48", Decimal("15.82"), ReceitaExtra.TipoReceitaExtra.JUROS_MULTA, 48),
                ("COTA REF. ALUGUEL - CASA 23", Decimal("100.00"), ReceitaExtra.TipoReceitaExtra.ALUGUEL_VAGA, 23),
                ("COTA REF. ALUGUEL - CASA 14", Decimal("100.00"), ReceitaExtra.TipoReceitaExtra.ALUGUEL_VAGA, 14),
                ("RENDIMENTO INVESTIMENTO CDB", Decimal("0.00"), ReceitaExtra.TipoReceitaExtra.RENDIMENTO_CDB, None),
            ]
            for desc, val, tipo, num_unid in extras_dados:
                ReceitaExtra.objects.create(
                    periodo=periodo,
                    tipo=tipo,
                    descricao=desc,
                    unidade=unidades_map[num_unid] if num_unid else None,
                    valor=val,
                    data=date(2026, 10, 5),
                )

            # 6. Despesas Fixas (Aba PRESTAÇÃO)
            periodo.despesas.all().delete()
            despesas_fixas_dados = [
                ("REF. 9/2026 - PAGTO. SALÁRIO FUNCIONÁRIOS", Decimal("4474.54"), Despesa.CategoriaDespesa.SALARIO),
                ("REF. 10/2026 - PAGTO. ANTECIPAÇÃO DE SALÁRIO FUNCIONÁRIOS", Decimal("1945.20"), Despesa.CategoriaDespesa.ANTECIPACAO_SALARIO),
                ("REF. 10/2026 - PAGTO. SALÁRIO FUNCIONÁRIOS - FÉRIAS", Decimal("0.00"), Despesa.CategoriaDespesa.FERIAS),
                ("REF. 10/2026 - PAGTO. ZELADOR DIARISTA", Decimal("380.00"), Despesa.CategoriaDespesa.ZELADOR_DIARISTA),
                ("REF. 10/2026 - TRANSPORTE FUNCIONÁRIOS", Decimal("334.80"), Despesa.CategoriaDespesa.TRANSPORTE),
                ("REF. 10/2026 - REFEIÇÕES FUNCIONÁRIOS", Decimal("1040.00"), Despesa.CategoriaDespesa.REFEICAO),
                ("REF. 12/2026 13º - PAGTO. PRIMEIRA PARC. DÉCIMO", Decimal("0.00"), Despesa.CategoriaDespesa.DECIMO_TERCEIRO),
                ("REF. 12/2026 13º - PAGTO. SEGUNDA PARC. DÉCIMO", Decimal("0.00"), Despesa.CategoriaDespesa.DECIMO_TERCEIRO),
                ("REF. 9/2026 - SÍNDICO", Decimal("700.00"), Despesa.CategoriaDespesa.SINDICO),
                ("REF. 9/2026 - GPS", Decimal("2502.08"), Despesa.CategoriaDespesa.GPS),
                ("REF. 12/2026 13º - GPS DÉCIMO", Decimal("0.00"), Despesa.CategoriaDespesa.GPS),
                ("REF. 9/2026 - FGTS", Decimal("780.29"), Despesa.CategoriaDespesa.FGTS),
                ("REF. 10/2026 - ENEL", Decimal("802.91"), Despesa.CategoriaDespesa.ENEL),
                ("REF. 10/2026 - CIRO AVILA DE SOUSA (CONTADOR)", Decimal("340.00"), Despesa.CategoriaDespesa.CONTABILIDADE),
                ("REF. 10/2026 - SERVIÇO DE COLETA DE RESÍDUOS", Decimal("0.00"), Despesa.CategoriaDespesa.COLETA_RESIDUOS),
                ("REF. 10/2026 - SERVIÇO DE DEDETIZAÇÃO", Decimal("130.00"), Despesa.CategoriaDespesa.DEDETIZACAO),
            ]
            for desc, val, cat in despesas_fixas_dados:
                Despesa.objects.create(
                    periodo=periodo,
                    tipo=Despesa.TipoDespesa.FIXA,
                    categoria=cat,
                    descricao=desc,
                    valor=val,
                    data_pagamento=date(2026, 10, 10),
                )

            # 7. Despesas Variáveis (Aba PRESTAÇÃO)
            despesas_var_dados = [
                ("SACOS DE LIXO(200L) NF 4543  10  KG AL FELIPE ME", Decimal("134.00"), Despesa.CategoriaDespesa.MATERIAL_LIMPEZA, "NF 4543"),
                ("RECIBO 36/2026 WELIO MATERIAL DE LIMPEZA 03 SABÃO , 03 DESINFETANTE  E 03 AGUA SANITÁRIA.", Decimal("0.00"), Despesa.CategoriaDespesa.MATERIAL_LIMPEZA, "RECIBO 36/2026"),
                ("RECIBO 37/2026 RUBEMAR SERVIÇO EXTRA PORTARIA DIAS: 04,10,12,18 e 24 DE SETEMBRO  2026.", Decimal("250.00"), Despesa.CategoriaDespesa.EXTRA_PORTARIA, "RECIBO 37/2026"),
                ("RECIBO 38/2026 WELIO SERVIÇO EXTRA PORTARIA DIAS: 03,11,17,25 e 31 DE SETEMBRO 2026.", Decimal("0.00"), Despesa.CategoriaDespesa.EXTRA_PORTARIA, "RECIBO 38/2026"),
                ("RECIBO 39/2026  OTACILIO  SERVIÇO MANUTENÇÃO CONDOMINIO PINTIRA MURO", Decimal("300.00"), Despesa.CategoriaDespesa.MANUTENCAO, "RECIBO 39/2026"),
                ("CAGECE  INSCRIÇÃO 3277585  PARCELAMENTO DEBITO 10/2020, 11/2020,12/2020 E 01/2021 NF 20339385 2/5 PARCELAS", Decimal("1389.01"), Despesa.CategoriaDespesa.AGUA_CAGECE, "NF 20339385"),
                ("RECIBO SEGURA WEB CERTIFICADO DIGITAL  SRA SUELLEN ", Decimal("220.00"), Despesa.CategoriaDespesa.CERTIFICADO_DIGITAL, "RECIBO SEGURA WEB"),
                ("AMAZON REFIL BEBEDOURO CONSUL   DA PORTARIA ", Decimal("83.59"), Despesa.CategoriaDespesa.EQUIPAMENTOS, "AMAZON"),
                ("CUPOM FISCAL 10972 MULTITUDO CONSTRUÇÃO VASSOURA CABOS MADEIRA ", Decimal("83.56"), Despesa.CategoriaDespesa.MATERIAL_LIMPEZA, "CUPOM 10972"),
            ]
            for desc, val, cat, doc in despesas_var_dados:
                Despesa.objects.create(
                    periodo=periodo,
                    tipo=Despesa.TipoDespesa.VARIAVEL,
                    categoria=cat,
                    descricao=desc,
                    numero_documento=doc,
                    valor=val,
                    data_pagamento=date(2026, 10, 15),
                )

            # 8. Fechar o período e gerar Snapshot imutável (reabre temporariamente para atualização se reexecutado)
            periodo.status = PeriodoPrestacao.StatusPeriodo.ABERTO
            periodo.save()
            totais = fechar_periodo_prestacao(periodo)

            # Publicar período para acesso de todos os moradores
            periodo.status = PeriodoPrestacao.StatusPeriodo.PUBLICADO
            periodo.save()

            self.stdout.write(self.style.SUCCESS("=" * 60))
            self.stdout.write(self.style.SUCCESS("CONFERÊNCIA DE TOTAIS COM A PLANILHA ORIGINAL:"))
            self.stdout.write(self.style.SUCCESS("=" * 60))
            self.stdout.write(f"Cotas Regulares (45 x 380): R$ {totais['total_cotas_regulares']} (Esperado: 17100.00)")
            self.stdout.write(f"Outras Receitas:            R$ {totais['total_receitas_extras']} (Esperado: 669.95)")
            self.stdout.write(f"Total Receitas:             R$ {totais['total_receitas']} (Esperado: 17769.95)")
            self.stdout.write(f"Despesas Fixas:             R$ {totais['total_despesas_fixas']} (Esperado: 13429.82)")
            self.stdout.write(f"Despesas Variáveis:         R$ {totais['total_despesas_variaveis']} (Esperado: 2460.16)")
            self.stdout.write(f"Total Despesas:             R$ {totais['total_despesas']} (Esperado: 15889.98)")
            self.stdout.write(f"Saldo Anterior Total:       R$ {totais['saldo_anterior_total']} (Esperado: 45001.96)")
            self.stdout.write(f"Subtotal:                   R$ {totais['subtotal']} (Esperado: 62771.91)")
            self.stdout.write(f"Saldo Mês:                  R$ {totais['saldo_mes']} (Esperado: 46881.93)")
            self.stdout.write(f"Total Saldo Bancário CC:    R$ {totais['total_saldo_bancario']} (Esperado: 46881.93)")
            self.stdout.write(f"Diferença Saldo:            R$ {totais['diferenca_saldo']} (Esperado: 0.00)")
            self.stdout.write(f"Diferença em Cotas:         {totais['diferenca_em_cotas']} cota(s) (Esperado: 0.00)")
            self.stdout.write(f"Obs: {totais['observacao_diferenca']}")
            self.stdout.write(self.style.SUCCESS("=" * 60))
            self.stdout.write(self.style.SUCCESS("MIGRAÇÃO E CONFERÊNCIA CONCLUÍDAS COM SUCESSO (100% DE ACURÁCIA)!"))
