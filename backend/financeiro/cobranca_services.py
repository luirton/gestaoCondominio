"""
Serviços de cálculo de encargos de inadimplência (multa e juros)
e consolidação de débitos por unidade condominial.
"""

from decimal import Decimal, ROUND_HALF_UP
from datetime import date
from django.db import transaction
from django.db.models import Q
from django.core.exceptions import ValidationError
from financeiro.models import (
    ReceitaCota,
    ParametroCobranca,
    ReceitaExtra,
    PeriodoPrestacao,
    AuditLog
)
from core.models import Unidade, Condominio, VinculoPessoaUnidade, CargoCondominial


def obter_parametro_para_vencimento(condominio, data_vencimento):
    """
    Busca o parâmetro de cobrança que estava em vigor na data de vencimento informada (Opção A).
    Critério: data_inicio <= data_vencimento AND (data_fim >= data_vencimento OR data_fim IS NULL).
    Caso não exista parâmetro específico para a data, busca o mais antigo ou mais recente, ou cria padrão.
    """
    # 1. Tenta vigência exata
    param = ParametroCobranca.objects.filter(
        condominio=condominio,
        data_inicio__lte=data_vencimento
    ).filter(
        Q(data_fim__gte=data_vencimento) | Q(data_fim__isnull=True)
    ).order_by("-data_inicio").first()

    if param:
        return param

    # 2. Se a data for mais antiga que a primeira vigência cadastrada, pega a mais antiga
    param_antigo = ParametroCobranca.objects.filter(
        condominio=condominio
    ).order_by("data_inicio").first()

    if param_antigo:
        return param_antigo

    # 3. Fallback: cria o primeiro parâmetro padrão
    param_padrao, _ = ParametroCobranca.objects.get_or_create(
        condominio=condominio,
        data_inicio=date(2024, 1, 1),
        defaults={
            "tipo_multa": ParametroCobranca.TipoMulta.FIXO,
            "valor_multa": Decimal("10.00"),
            "percentual_juros_dia": Decimal("0.0024"),
        }
    )
    return param_padrao


def calcular_encargos_cota(cota, data_corte=None, parametro=None):
    """
    Calcula multa e juros atualizados para uma ReceitaCota até a data_corte.
    Utiliza o parâmetro em vigor na DATA DE VENCIMENTO da cota (Opção A).
    Retorna um dicionário com os detalhes calculados.
    """
    if data_corte is None:
        data_corte = date.today()

    vencimento = cota.periodo.data_vencimento
    dias_atraso = (data_corte - vencimento).days

    if dias_atraso <= 0:
        return {
            "cota_id": cota.id,
            "periodo_rotulo": cota.periodo.mes_referencia_rotulo,
            "vencimento": vencimento,
            "data_atualizacao": data_corte,
            "dias_atraso": 0,
            "taxa": cota.valor_titulo,
            "multa": Decimal("0.00"),
            "juros": Decimal("0.00"),
            "total": cota.valor_titulo,
            "tem_acordo": False,
            "valor_acordo": None,
            "observacao": cota.observacao or "",
        }

    condominio = cota.periodo.condominio
    if parametro is None:
        parametro = obter_parametro_para_vencimento(condominio, vencimento)

    # Verifica se há acordo pendente ou quitado
    acordo_ativo = cota.acordos.exclude(status="CANCELADO").order_by("-created_at").first()

    taxa = cota.valor_titulo

    # Multa baseada no parâmetro histórico da cota
    if parametro.tipo_multa == ParametroCobranca.TipoMulta.FIXO:
        multa = parametro.valor_multa
    else:
        multa = (taxa * (parametro.valor_multa / Decimal("100.00"))).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

    # Juros pro-rata die: taxa * (fator_dia * dias)
    fator_juros = parametro.percentual_juros_dia * Decimal(str(dias_atraso))
    juros = (taxa * fator_juros).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    total_calculado = taxa + multa + juros

    obs = cota.observacao or ""
    if acordo_ativo:
        total_a_pagar = acordo_ativo.valor_acordado
        obs_acordo = f"Acordo #{acordo_ativo.id}: R$ {acordo_ativo.valor_acordado} ({acordo_ativo.get_status_display()})"
        obs = f"{obs} | {obs_acordo}" if obs else obs_acordo
    else:
        total_a_pagar = total_calculado

    return {
        "cota_id": cota.id,
        "periodo_rotulo": cota.periodo.mes_referencia_rotulo,
        "vencimento": vencimento,
        "data_atualizacao": data_corte,
        "dias_atraso": dias_atraso,
        "taxa": taxa,
        "multa": multa,
        "juros": juros,
        "total_calculado": total_calculado,
        "total": total_a_pagar,
        "tem_acordo": bool(acordo_ativo),
        "valor_acordo": acordo_ativo.valor_acordado if acordo_ativo else None,
        "observacao": obs,
        "parametro_utilizado": {
            "id": parametro.id,
            "data_inicio": parametro.data_inicio,
            "data_fim": parametro.data_fim,
            "tipo_multa": parametro.tipo_multa,
            "valor_multa": parametro.valor_multa,
            "percentual_juros_dia": parametro.percentual_juros_dia,
        }
    }


def obter_responsaveis_unidade(unidade):
    """
    Retorna o nome, CPF e e-mail dos responsáveis/proprietários da unidade.
    """
    vinculos = VinculoPessoaUnidade.objects.filter(
        unidade=unidade,
        data_fim__isnull=True
    ).select_related("pessoa").order_by("-responsavel", "tipo")

    if not vinculos.exists():
        return {
            "nome": f"Proprietário da {unidade.identificador}",
            "cpf": "",
            "email": "",
            "telefone": "",
            "vinculos": [],
        }

    # Prioriza o responsável financeiro ou proprietário
    principal = vinculos.filter(responsavel=True).first() or vinculos.filter(tipo="PROPRIETARIO").first() or vinculos.first()
    pessoa = principal.pessoa

    emails = [v.pessoa.email for v in vinculos if v.pessoa.email]
    
    return {
        "nome": pessoa.nome,
        "cpf": pessoa.cpf or "",
        "email": pessoa.email or (emails[0] if emails else ""),
        "emails_todos": list(set(emails)),
        "telefone": pessoa.telefone or "",
        "vinculos": [
            {
                "nome": v.pessoa.nome,
                "cpf": v.pessoa.cpf or "",
                "email": v.pessoa.email or "",
                "tipo": v.get_tipo_display(),
                "responsavel": v.responsavel,
            }
            for v in vinculos
        ],
    }


def obter_extrato_inadimplencia_unidade(unidade, data_corte=None):
    """
    Gera o extrato de débitos vencidos de uma unidade até a data_corte.
    """
    if data_corte is None:
        data_corte = date.today()

    # Busca parâmetro de comunicação vigente atual para textos padrão
    parametro_atual = ParametroCobranca.objects.filter(
        condominio=unidade.condominio,
        data_inicio__lte=data_corte
    ).filter(
        Q(data_fim__gte=data_corte) | Q(data_fim__isnull=True)
    ).order_by("-data_inicio").first()

    if not parametro_atual:
        parametro_atual = ParametroCobranca.objects.filter(
            condominio=unidade.condominio
        ).order_by("-data_inicio").first()

    # Busca cotas PENDENTES cujo vencimento seja menor ou igual a hoje
    cotas_pendentes = ReceitaCota.objects.filter(
        unidade=unidade,
        status="PENDENTE",
        isento=False,
        periodo__data_vencimento__lt=data_corte
    ).select_related("periodo").order_by("periodo__data_vencimento")

    itens = []
    total_taxa = Decimal("0.00")
    total_multa = Decimal("0.00")
    total_juros = Decimal("0.00")
    total_geral = Decimal("0.00")

    for i, cota in enumerate(cotas_pendentes, start=1):
        # Cada cota calcula encargos com base no parâmetro histórico do seu vencimento
        detalhe = calcular_encargos_cota(cota, data_corte=data_corte)
        detalhe["item"] = i
        itens.append(detalhe)

        total_taxa += detalhe["taxa"]
        total_multa += detalhe["multa"]
        total_juros += detalhe["juros"]
        total_geral += detalhe["total"]

    responsavel = obter_responsaveis_unidade(unidade)
    esta_em_dia = len(itens) == 0
    limite_aj = parametro_atual.qtd_parcelas_ajuizamento if parametro_atual else 6

    return {
        "condominio": {
            "id": unidade.condominio.id,
            "nome": unidade.condominio.nome,
            "cnpj": unidade.condominio.cnpj or "",
            "endereco": f"{unidade.condominio.endereco}, {unidade.condominio.numero}".strip(", "),
        },
        "unidade": {
            "id": unidade.id,
            "identificador": unidade.identificador,
            "bloco_torre": unidade.bloco_torre or "",
        },
        "responsavel": responsavel,
        "data_atualizacao": data_corte,
        "esta_em_dia": esta_em_dia,
        "qtd_titulos": len(itens),
        "sujeito_ajuizamento": len(itens) >= limite_aj,
        "itens": itens,
        "totais": {
            "taxa": total_taxa,
            "multa": total_multa,
            "juros": total_juros,
            "total_geral": total_geral,
        },
        "parametro": {
            "prazo_negociacao_info": parametro_atual.prazo_negociacao_info if parametro_atual else "",
            "aviso_protesto_info": parametro_atual.aviso_protesto_info if parametro_atual else "",
            "aviso_ajuizamento_info": parametro_atual.aviso_ajuizamento_info if parametro_atual else "",
            "email_cobranca": parametro_atual.email_cobranca if parametro_atual else "condominiohortenciasiii@gmail.com",
            "telefone_cobranca": parametro_atual.telefone_cobranca if parametro_atual else "",
            "mensagem_email_padrao": parametro_atual.mensagem_email_padrao if parametro_atual else "",
        }
    }


def obter_extrato_consolidado_unidades(unidades, data_corte=None):
    """
    Gera o extrato de débitos consolidado ('Tudo Junto') para um conjunto de unidades de um mesmo morador.
    """
    if data_corte is None:
        data_corte = date.today()

    if not unidades:
        return None

    primeira_unidade = unidades[0]
    condominio = primeira_unidade.condominio
    responsavel = obter_responsaveis_unidade(primeira_unidade)

    # Busca parâmetro de comunicação vigente atual
    parametro_atual = ParametroCobranca.objects.filter(
        condominio=condominio,
        data_inicio__lte=data_corte
    ).filter(
        Q(data_fim__gte=data_corte) | Q(data_fim__isnull=True)
    ).order_by("-data_inicio").first()

    itens_consolidados = []
    total_taxa = Decimal("0.00")
    total_multa = Decimal("0.00")
    total_juros = Decimal("0.00")
    total_geral = Decimal("0.00")
    item_idx = 1

    unidades_com_debito = []
    unidades_em_dia = []

    for u in unidades:
        extrato_u = obter_extrato_inadimplencia_unidade(u, data_corte=data_corte)
        if extrato_u["esta_em_dia"]:
            unidades_em_dia.append(u)
        else:
            unidades_com_debito.append(u)
            for it in extrato_u["itens"]:
                it_copia = dict(it)
                it_copia["item"] = item_idx
                it_copia["observacao"] = f"{u.identificador} | {it.get('observacao') or ''}".strip(" |")
                itens_consolidados.append(it_copia)
                item_idx += 1

                total_taxa += it_copia["taxa"]
                total_multa += it_copia["multa"]
                total_juros += it_copia["juros"]
                total_geral += it_copia["total"]

    nomes_todas_unidades = ", ".join(u.identificador for u in unidades)
    nomes_devedoras = ", ".join(u.identificador for u in unidades_com_debito) if unidades_com_debito else "Nenhuma"
    nomes_em_dia = ", ".join(u.identificador for u in unidades_em_dia) if unidades_em_dia else "Nenhuma"

    limite_aj = parametro_atual.qtd_parcelas_ajuizamento if parametro_atual else 6

    return {
        "condominio": {
            "id": condominio.id,
            "nome": condominio.nome,
            "cnpj": condominio.cnpj or "",
            "endereco": f"{condominio.endereco}, {condominio.numero}".strip(", "),
        },
        "unidade": {
            "id": None,
            "identificador": nomes_todas_unidades,
            "bloco_torre": "",
        },
        "multi_unidades": True,
        "unidades_com_debito_nomes": nomes_devedoras,
        "unidades_em_dia_nomes": nomes_em_dia,
        "qtd_unidades_total": len(unidades),
        "qtd_unidades_com_debito": len(unidades_com_debito),
        "qtd_unidades_em_dia": len(unidades_em_dia),
        "responsavel": responsavel,
        "data_atualizacao": data_corte,
        "esta_em_dia": len(itens_consolidados) == 0,
        "qtd_titulos": len(itens_consolidados),
        "sujeito_ajuizamento": len(itens_consolidados) >= limite_aj,
        "itens": itens_consolidados,
        "totais": {
            "taxa": total_taxa,
            "multa": total_multa,
            "juros": total_juros,
            "total_geral": total_geral,
        },
        "parametro": {
            "prazo_negociacao_info": parametro_atual.prazo_negociacao_info if parametro_atual else "",
            "aviso_protesto_info": parametro_atual.aviso_protesto_info if parametro_atual else "",
            "aviso_ajuizamento_info": parametro_atual.aviso_ajuizamento_info if parametro_atual else "",
            "email_cobranca": parametro_atual.email_cobranca if parametro_atual else "condominiohortenciasiii@gmail.com",
            "telefone_cobranca": parametro_atual.telefone_cobranca if parametro_atual else "",
            "mensagem_email_padrao": parametro_atual.mensagem_email_padrao if parametro_atual else "",
        }
    }


def obter_relatorio_geral_inadimplencia(condominio, data_corte=None):
    """
    Gera o relatório de inadimplência de todo o condomínio com resumo por unidade.
    """
    if data_corte is None:
        data_corte = date.today()

    unidades = Unidade.objects.filter(condominio=condominio).order_by("identificador")
    
    devedores = []
    total_geral_taxas = Decimal("0.00")
    total_geral_multas = Decimal("0.00")
    total_geral_juros = Decimal("0.00")
    total_geral_saldo = Decimal("0.00")
    total_titulos_geral = 0

    for unidade in unidades:
        extrato = obter_extrato_inadimplencia_unidade(unidade, data_corte=data_corte)
        if not extrato["esta_em_dia"]:
            devedores.append(extrato)
            total_geral_taxas += extrato["totais"]["taxa"]
            total_geral_multas += extrato["totais"]["multa"]
            total_geral_juros += extrato["totais"]["juros"]
            total_geral_saldo += extrato["totais"]["total_geral"]
            total_titulos_geral += extrato["qtd_titulos"]

    return {
        "condominio": {
            "id": condominio.id,
            "nome": condominio.nome,
            "cnpj": condominio.cnpj or "",
        },
        "data_atualizacao": data_corte,
        "total_unidades": unidades.count(),
        "total_inadimplentes": len(devedores),
        "taxa_inadimplencia_percentual": (
            round((len(devedores) / unidades.count()) * 100, 2) if unidades.count() > 0 else 0
        ),
        "devedores": devedores,
        "totais_consolidados": {
            "total_taxas": total_geral_taxas,
            "total_multas": total_geral_multas,
            "total_juros": total_geral_juros,
            "total_saldo_devedor": total_geral_saldo,
            "total_titulos": total_titulos_geral,
        }
    }


def obter_sindico_ativo(condominio):
    """
    Retorna os dados do síndico ativo para a assinatura e emissão da certidão.
    """
    cargo = CargoCondominial.objects.filter(
        condominio=condominio,
        cargo=CargoCondominial.TipoCargo.SINDICO,
        ativo=True,
        data_fim__isnull=True
    ).select_related("pessoa").first()

    if not cargo:
        return {
            "nome": "ADMINISTRAÇÃO DO CONDOMÍNIO",
            "cpf": "",
            "endereco": f"{condominio.endereco}, {condominio.numero}",
        }

    pessoa = cargo.pessoa
    # Tenta descobrir a unidade onde o síndico mora
    vinculo = VinculoPessoaUnidade.objects.filter(
        pessoa=pessoa,
        unidade__condominio=condominio,
        data_fim__isnull=True
    ).select_related("unidade").first()

    casa_info = f", {vinculo.unidade.identificador}" if vinculo else ""
    endereco_sindico = f"{condominio.endereco}, {condominio.numero}{casa_info}"

    return {
        "nome": pessoa.nome,
        "cpf": pessoa.cpf or "",
        "endereco": endereco_sindico,
    }


def obter_ultima_cota_paga(unidade):
    """
    Busca a última cota condominial paga da unidade para constar no Nada Consta.
    """
    cota_paga = ReceitaCota.objects.filter(
        unidade=unidade,
        status="PAGO",
        data_pagamento__isnull=False
    ).select_related("periodo").order_by("-periodo__data_vencimento").first()

    if cota_paga:
        return {
            "referencia": cota_paga.periodo.mes_referencia_rotulo,
            "vencimento": cota_paga.periodo.data_vencimento,
            "data_pagamento": cota_paga.data_pagamento,
            "valor": cota_paga.valor_pago or cota_paga.valor_titulo,
        }
    return None


def obter_periodo_para_data(condominio, data_alvo):
    """
    Localiza o período de prestação de contas do condomínio correspondente à data informada (regime de caixa).
    Critérios de busca:
    1. Intervalo do período: data_inicio_prestacao <= data_alvo <= data_fim_prestacao.
    2. Pelo mês e ano de mes_referencia (ex: se mes_referencia for novembro/2026 e data_alvo for 14/11/2026).
    3. Período com status ABERTO mais recente.
    4. Período mais recente existente no condomínio.
    """
    p = PeriodoPrestacao.objects.filter(
        condominio=condominio,
        data_inicio_prestacao__lte=data_alvo,
        data_fim_prestacao__gte=data_alvo
    ).order_by("-mes_referencia").first()
    if p:
        return p

    p = PeriodoPrestacao.objects.filter(
        condominio=condominio,
        mes_referencia__year=data_alvo.year,
        mes_referencia__month=data_alvo.month
    ).order_by("-mes_referencia").first()
    if p:
        return p

    p = PeriodoPrestacao.objects.filter(
        condominio=condominio,
        status=PeriodoPrestacao.StatusPeriodo.ABERTO
    ).order_by("-mes_referencia").first()
    if p:
        return p

    return PeriodoPrestacao.objects.filter(
        condominio=condominio
    ).order_by("-mes_referencia").first()


@transaction.atomic
def executar_baixa_cota_atrasada(
    cota: ReceitaCota,
    data_pagamento: date,
    valor_pago: Decimal,
    cota_val: Decimal = None,
    juros_multa_val: Decimal = None,
    observacao: str = "",
    comprovante_file=None,
    usuario=None
):
    """
    Executa a baixa de uma cota condominial em atraso aplicando a Abordagem A:
    1. Marca a cota original como PAGO para efeito cadastral e liberação de Nada Consta.
    2. Localiza o período de prestação correspondente ao mês da DATA DE PAGAMENTO (regime de caixa).
    3. Se a cota for de período diferente daquele onde o dinheiro entra (meses anteriores,
       fechados, publicados ou históricos), lança automaticamente em ReceitaExtra (COTA_ATRASADA
       para o principal e JUROS_MULTA para os encargos).
    4. Registra log de auditoria.
    """
    if cota.isento:
        raise ValidationError("Cota isenta não permite baixa de pagamento.")

    # Se cota_val (principal) não foi especificado, usa o valor original do título
    if cota_val is None:
        cota_val = cota.valor_titulo

    cota_val = Decimal(str(cota_val))
    valor_pago = Decimal(str(valor_pago))

    # Se juros_multa_val não foi informado, calcula a diferença ou 0
    if juros_multa_val is None:
        if valor_pago > cota_val:
            juros_multa_val = valor_pago - cota_val
        else:
            juros_multa_val = Decimal("0.00")
    else:
        juros_multa_val = Decimal(str(juros_multa_val))

    receitas_extras_criadas = []

    # Localiza o período da prestação de contas correspondente ao mês da DATA DE PAGAMENTO
    periodo_destino = obter_periodo_para_data(cota.periodo.condominio, data_pagamento)

    if periodo_destino:
        obs_extra = f"Baixa cota atrasada #{cota.id}. {observacao}".strip()

        # Caso 1: Cota é de um período diferente daquele em que o pagamento foi realizado
        # (ex: cota de Setembro ou Outubro recebida em Novembro)
        if cota.periodo_id != periodo_destino.id:
            # 1.1 Principal em ReceitaExtra COTA_ATRASADA
            descricao_principal = f"Recuperação Cota Atrasada - {cota.unidade.identificador} - Ref. {cota.periodo.mes_referencia_rotulo}"
            re_cota = ReceitaExtra.objects.create(
                periodo=periodo_destino,
                tipo=ReceitaExtra.TipoReceitaExtra.COTA_ATRASADA,
                descricao=descricao_principal,
                unidade=cota.unidade,
                valor=cota_val,
                data=data_pagamento,
                observacao=obs_extra
            )
            receitas_extras_criadas.append(re_cota)

            # 1.2 Encargos (Multa/Juros) em ReceitaExtra JUROS_MULTA
            if juros_multa_val > Decimal("0.00"):
                descricao_encargos = f"Encargos/Juros/Multa Cota - {cota.unidade.identificador} - Ref. {cota.periodo.mes_referencia_rotulo}"
                re_encargos = ReceitaExtra.objects.create(
                    periodo=periodo_destino,
                    tipo=ReceitaExtra.TipoReceitaExtra.JUROS_MULTA,
                    descricao=descricao_encargos,
                    unidade=cota.unidade,
                    valor=juros_multa_val,
                    data=data_pagamento,
                    observacao=obs_extra
                )
                receitas_extras_criadas.append(re_encargos)
        else:
            # Caso 2: Cota é do PRÓPRIO período da data de pagamento, mas foi paga com juros/multa de atraso
            if juros_multa_val > Decimal("0.00"):
                descricao_encargos = f"Multa/Juros Cota - {cota.unidade.identificador} - Ref. {cota.periodo.mes_referencia_rotulo}"
                re_encargos = ReceitaExtra.objects.create(
                    periodo=periodo_destino,
                    tipo=ReceitaExtra.TipoReceitaExtra.JUROS_MULTA,
                    descricao=descricao_encargos,
                    unidade=cota.unidade,
                    valor=juros_multa_val,
                    data=data_pagamento,
                    observacao=obs_extra
                )
                receitas_extras_criadas.append(re_encargos)

    # Atualiza a cota original
    cota.data_pagamento = data_pagamento
    cota.cota = cota_val
    cota.juros_multa = juros_multa_val
    cota.valor_pago = valor_pago
    cota.status = ReceitaCota.StatusCota.PAGO

    if observacao:
        if cota.observacao and cota.observacao != observacao:
            cota.observacao = f"{cota.observacao} | {observacao}"
        else:
            cota.observacao = observacao

    if comprovante_file:
        cota.comprovante = comprovante_file

    cota.save()

    # Log de Auditoria
    if usuario and usuario.is_authenticated:
        AuditLog.objects.create(
            usuario=usuario,
            condominio=cota.periodo.condominio,
            entidade="ReceitaCota",
            registro_id=str(cota.id),
            acao=AuditLog.AcaoAudit.UPDATE,
            dados_novos={
                "acao": "BAIXA_COTA_ATRASADA",
                "cota_id": cota.id,
                "unidade": cota.unidade.identificador,
                "valor_pago": str(valor_pago),
                "principal": str(cota_val),
                "juros_multa": str(juros_multa_val),
                "data_pagamento": str(data_pagamento),
                "periodo_origem_id": cota.periodo_id,
                "periodo_destino_id": periodo_destino.id if periodo_destino else None,
                "observacao": observacao,
            }
        )

    return {
        "cota": cota,
        "receitas_extras": receitas_extras_criadas,
        "periodo_destino_id": periodo_destino.id if periodo_destino else None
    }

