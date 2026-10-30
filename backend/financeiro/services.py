import io
from decimal import Decimal
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from .models import PeriodoPrestacao, ReceitaCota, ReceitaExtra, Despesa, SaldoPeriodo, AuditLog


def calcular_totais_periodo(periodo: PeriodoPrestacao):
    """
    Executa o cálculo preciso e reproduzível das regras da planilha.
    Retorna um dicionário com todos os valores totalizados.
    """
    # 1. Cotas Regulares: soma das cotas pagas no período
    cotas_pagas = periodo.cotas.filter(data_pagamento__isnull=False)
    total_cotas_regulares = Decimal("0.00")
    for c in cotas_pagas:
        if c.cota is not None:
            total_cotas_regulares += Decimal(str(c.cota))
        elif c.valor_titulo is not None:
            total_cotas_regulares += Decimal(str(c.valor_titulo))

    # 2. Receitas Extras (Juros/Multas, Aluguel Vaga, CDB, Atrasos)
    total_receitas_extras = Decimal("0.00")
    for extra in periodo.receitas_extras.all():
        total_receitas_extras += Decimal(str(extra.valor))

    total_receitas = total_cotas_regulares + total_receitas_extras

    # 3. Despesas Fixas e Variáveis
    despesas_fixas = periodo.despesas.filter(tipo=Despesa.TipoDespesa.FIXA)
    total_despesas_fixas = sum((Decimal(str(d.valor)) for d in despesas_fixas), Decimal("0.00"))

    despesas_var = periodo.despesas.filter(tipo=Despesa.TipoDespesa.VARIAVEL)
    total_despesas_variaveis = sum((Decimal(str(d.valor)) for d in despesas_var), Decimal("0.00"))

    total_despesas = total_despesas_fixas + total_despesas_variaveis

    # 4. Saldos Anteriores
    saldo_anterior_cc = Decimal(str(periodo.saldo_anterior_cc))
    saldo_anterior_aplicacao = Decimal(str(periodo.saldo_anterior_aplicacao))
    saldo_anterior_porquinho = Decimal(str(periodo.saldo_anterior_porquinho))
    saldo_anterior_total = saldo_anterior_cc + saldo_anterior_aplicacao + saldo_anterior_porquinho

    # 5. Subtotal e Saldo Mês
    subtotal = saldo_anterior_total + total_receitas
    saldo_mes = subtotal - total_despesas

    # 6. Conferência de Saldo Bancário e Diferença
    total_saldo_bancario = Decimal(str(periodo.total_saldo_bancario))
    diferenca_saldo = saldo_mes - total_saldo_bancario

    cota_padrao = Decimal(str(periodo.valor_cota_padrao))
    if cota_padrao > Decimal("0.00"):
        diferenca_em_cotas = round(abs(diferenca_saldo) / cota_padrao, 2)
    else:
        diferenca_em_cotas = Decimal("0.00")

    prox_venc = periodo.data_prox_vencimento.strftime("%d/%m/%Y") if periodo.data_prox_vencimento else ""
    rotulo_prox = periodo.mes_prox_vencimento or "MÊS SEGUINTE"

    qtd_formatada = int(diferenca_em_cotas) if diferenca_em_cotas == int(diferenca_em_cotas) else diferenca_em_cotas

    observacao_diferenca = (
        f"A diferença entre o SALDO MÊS e o TOTAL DO SALDO BANCÁRIO é de {qtd_formatada} cota(s) "
        f"referente ao mês de {rotulo_prox} com vencimento em {prox_venc}"
    )

    return {
        "total_cotas_regulares": total_cotas_regulares.quantize(Decimal("0.01")),
        "total_receitas_extras": total_receitas_extras.quantize(Decimal("0.01")),
        "total_receitas": total_receitas.quantize(Decimal("0.01")),
        "total_despesas_fixas": total_despesas_fixas.quantize(Decimal("0.01")),
        "total_despesas_variaveis": total_despesas_variaveis.quantize(Decimal("0.01")),
        "total_despesas": total_despesas.quantize(Decimal("0.01")),
        "saldo_anterior_cc": saldo_anterior_cc.quantize(Decimal("0.01")),
        "saldo_anterior_aplicacao": saldo_anterior_aplicacao.quantize(Decimal("0.01")),
        "saldo_anterior_porquinho": saldo_anterior_porquinho.quantize(Decimal("0.01")),
        "saldo_anterior_total": saldo_anterior_total.quantize(Decimal("0.01")),
        "subtotal": subtotal.quantize(Decimal("0.01")),
        "saldo_mes": saldo_mes.quantize(Decimal("0.01")),
        "total_saldo_bancario": total_saldo_bancario.quantize(Decimal("0.01")),
        "diferenca_saldo": diferenca_saldo.quantize(Decimal("0.01")),
        "diferenca_em_cotas": Decimal(str(diferenca_em_cotas)).quantize(Decimal("0.01")),
        "observacao_diferenca": observacao_diferenca,
    }


@transaction.atomic
def fechar_periodo_prestacao(periodo: PeriodoPrestacao, usuario=None):
    """
    Fecha o período de prestação, gerando o snapshot imutável.
    """
    if periodo.status in [PeriodoPrestacao.StatusPeriodo.FECHADO, PeriodoPrestacao.StatusPeriodo.PUBLICADO]:
        raise ValidationError("Este período já se encontra fechado ou publicado.")

    totais = calcular_totais_periodo(periodo)
    agora = timezone.now()

    periodo.observacao_diferenca = totais["observacao_diferenca"]
    periodo.status = PeriodoPrestacao.StatusPeriodo.FECHADO
    periodo.fechado_em = agora
    periodo.fechado_por = usuario
    periodo.save()

    # Cria ou atualiza snapshot congelado
    SaldoPeriodo.objects.update_or_create(
        periodo=periodo,
        defaults={
            "saldo_anterior_cc": totais["saldo_anterior_cc"],
            "saldo_anterior_aplicacao": totais["saldo_anterior_aplicacao"],
            "saldo_anterior_porquinho": totais["saldo_anterior_porquinho"],
            "saldo_anterior_total": totais["saldo_anterior_total"],
            "total_cotas_regulares": totais["total_cotas_regulares"],
            "total_receitas_extras": totais["total_receitas_extras"],
            "total_receitas": totais["total_receitas"],
            "subtotal": totais["subtotal"],
            "total_despesas_fixas": totais["total_despesas_fixas"],
            "total_despesas_variaveis": totais["total_despesas_variaveis"],
            "total_despesas": totais["total_despesas"],
            "saldo_mes": totais["saldo_mes"],
            "total_saldo_bancario": totais["total_saldo_bancario"],
            "diferenca_saldo": totais["diferenca_saldo"],
            "diferenca_em_cotas": totais["diferenca_em_cotas"],
            "observacao_diferenca": totais["observacao_diferenca"],
            "fechado_em": agora,
            "fechado_por": usuario,
        }
    )

    # Log de auditoria
    AuditLog.objects.create(
        usuario=usuario,
        condominio=periodo.condominio,
        entidade="PeriodoPrestacao",
        registro_id=str(periodo.id),
        acao=AuditLog.AcaoAudit.FECHAR,
        dados_novos={k: str(v) for k, v in totais.items()},
        detalhes=f"Período {periodo.mes_referencia_rotulo} fechado com sucesso."
    )

    return totais


@transaction.atomic
def gerar_cotas_iniciais(periodo: PeriodoPrestacao):
    """
    Gera as cotas para todas as unidades ativas do condomínio para o período.
    """
    unidades = periodo.condominio.unidades.all().order_by("bloco_torre", "identificador")
    criadas = 0

    for idx, unidade in enumerate(unidades, start=1):
        cota, created = ReceitaCota.objects.get_or_create(
            periodo=periodo,
            unidade=unidade,
            defaults={
                "numero_ordem": idx,
                "mes_referencia": periodo.mes_referencia,
                "data_vencimento": periodo.data_vencimento,
                "valor_titulo": periodo.valor_cota_padrao,
                "cota": None,
                "valor_pago": None,
                "juros_multa": Decimal("0.00"),
                "status": ReceitaCota.StatusCota.PENDENTE,
            }
        )
        if created:
            criadas += 1

    return criadas


# ---------------------------------------------------------------------------
# GERAÇÃO DE EXCEL (.xlsx)
# ---------------------------------------------------------------------------
def exportar_relatorio_excel(periodo: PeriodoPrestacao) -> io.BytesIO:
    """
    Exporta a prestação de contas no formato Excel (.xlsx),
    reproduzindo as abas e estrutura da planilha original do condomínio.
    """
    wb = Workbook()
    
    # Cores e estilos
    fill_header = PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")
    fill_sub_blue = PatternFill(start_color="DCE6F1", end_color="DCE6F1", fill_type="solid")
    fill_sub_gray = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
    font_header = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    font_bold = Font(name="Calibri", size=10, bold=True)
    font_normal = Font(name="Calibri", size=10)
    thin_border = Border(
        left=Side(style='thin', color='BFBFBF'),
        right=Side(style='thin', color='BFBFBF'),
        top=Side(style='thin', color='BFBFBF'),
        bottom=Side(style='thin', color='BFBFBF')
    )

    totais = calcular_totais_periodo(periodo)

    # ------------------ ABA 1: PRESTAÇÃO ------------------
    ws_prestacao = wb.active
    ws_prestacao.title = "PRESTAÇÃO"

    ws_prestacao.append([periodo.condominio.nome.upper()])
    ws_prestacao.append([f"{periodo.condominio.endereco}, nº {periodo.condominio.numero} - {periodo.condominio.bairro} - {periodo.condominio.cidade}/{periodo.condominio.uf}"])
    ws_prestacao.append([f"CNPJ: {periodo.condominio.cnpj or '06.275.266/0001-23'}"])
    ws_prestacao.append([])
    ws_prestacao.append([f"PRESTAÇÃO DE CONTAS DO PERÍODO DE {periodo.data_inicio_prestacao.strftime('%d/%m/%Y')} A {periodo.data_fim_prestacao.strftime('%d/%m/%Y')}"])
    ws_prestacao.append([])

    # Receitas
    ws_prestacao.append(["RECEITAS", "VALOR (R$)"])
    ws_prestacao.append([f"COTAS – REFERENTES AO MÊS DE {periodo.mes_referencia_rotulo} COM VENC. EM {periodo.data_vencimento.strftime('%d/%m/%Y')}", float(totais["total_cotas_regulares"])])
    
    # Extras agrupados
    extras_atraso = periodo.receitas_extras.filter(tipo__in=[ReceitaExtra.TipoReceitaExtra.JUROS_MULTA, ReceitaExtra.TipoReceitaExtra.COTA_ATRASADA, ReceitaExtra.TipoReceitaExtra.ALUGUEL_VAGA, ReceitaExtra.TipoReceitaExtra.OUTRO])
    val_extras_atraso = sum((e.valor for e in extras_atraso), Decimal("0.00"))
    ws_prestacao.append(["COTAS – (RECEBIMENTO EM ATRASO / ACORDO / ANTECIPAÇÃO / OUTROS)", float(val_extras_atraso)])

    cdb_extras = periodo.receitas_extras.filter(tipo=ReceitaExtra.TipoReceitaExtra.RENDIMENTO_CDB)
    val_cdb = sum((e.valor for e in cdb_extras), Decimal("0.00"))
    ws_prestacao.append(["RENDIMENTO INVESTIMENTO CDB", float(val_cdb)])

    ws_prestacao.append(["TOTAL DAS RECEITAS", float(totais["total_receitas"])])
    ws_prestacao.append([])

    # Despesas Fixas
    ws_prestacao.append(["DESPESAS FIXAS", "VALOR (R$)"])
    for d in periodo.despesas.filter(tipo=Despesa.TipoDespesa.FIXA):
        ws_prestacao.append([d.descricao, float(d.valor)])
    ws_prestacao.append(["TOTAL DAS DESPESAS FIXAS", float(totais["total_despesas_fixas"])])
    ws_prestacao.append([])

    # Despesas Variáveis
    ws_prestacao.append(["DESPESAS VARIÁVEIS", "VALOR (R$)"])
    for d in periodo.despesas.filter(tipo=Despesa.TipoDespesa.VARIAVEL):
        ws_prestacao.append([d.descricao, float(d.valor)])
    ws_prestacao.append(["TOTAL DAS DESPESAS VARIÁVEIS", float(totais["total_despesas_variaveis"])])
    ws_prestacao.append([])

    # Resultado Conta Corrente
    ws_prestacao.append(["RESULTADO CONTA CORRENTE", "VALOR (R$)"])
    ws_prestacao.append(["SALDO ANTERIOR INTER (CC)", float(totais["saldo_anterior_cc"])])
    ws_prestacao.append(["SALDO ANTERIOR INTER (APLICAÇÃO)", float(totais["saldo_anterior_aplicacao"])])
    ws_prestacao.append(["SALDO PORQUINHO (FÉRIAS/DÉCIMO)", float(totais["saldo_anterior_porquinho"])])
    ws_prestacao.append(["SALDO ANTERIOR TOTAL", float(totais["saldo_anterior_total"])])
    ws_prestacao.append(["RECEITAS", float(totais["total_receitas"])])
    ws_prestacao.append(["SUB TOTAL", float(totais["subtotal"])])
    ws_prestacao.append(["TOTAL DAS DESPESAS DO MÊS", float(totais["total_despesas"])])
    ws_prestacao.append(["SALDO MÊS", float(totais["saldo_mes"])])
    data_saldo_str = periodo.data_saldo_bancario.strftime('%d/%m/%Y') if periodo.data_saldo_bancario else periodo.data_fim_prestacao.strftime('%d/%m/%Y')
    ws_prestacao.append([f"TOTAL DO SALDO BANCÁRIO (INTER CONTA CORRENTE) {data_saldo_str}", float(totais["total_saldo_bancario"])])
    ws_prestacao.append([])
    ws_prestacao.append([f"OBS: {totais['observacao_diferenca']}"])
    ws_prestacao.append([])
    ws_prestacao.append([f"Data: {timezone.now().strftime('%d/%m/%Y')}"])
    ws_prestacao.append(["____________________________________________________________"])
    ws_prestacao.append(["Síndico"])
    ws_prestacao.append([periodo.sindico_nome])
    ws_prestacao.append([periodo.sindico_cpf])

    ws_prestacao.column_dimensions['A'].width = 85
    ws_prestacao.column_dimensions['B'].width = 20

    # ------------------ ABA 2: PAGAMENTOS ------------------
    ws_pagamentos = wb.create_sheet(title="PAGAMENTOS")
    ws_pagamentos.append([periodo.condominio.nome.upper()])
    ws_pagamentos.append([f"COTAS – REFERENTES AO MÊS DE {periodo.mes_referencia_rotulo} COM VENC. EM {periodo.data_vencimento.strftime('%d/%m/%Y')}"])
    ws_pagamentos.append([])
    ws_pagamentos.append([
        "Nº", "MÊS DE REFERÊNCIA", "DATA DE VENCIMENTO", "VALOR DO TÍTULO (R$)",
        "DATA DE PAGAMENTO", "COTA (R$)", "VL. PAGAMENTO TÍTULO (R$)", "OBSERVAÇÃO"
    ])

    for row_idx, col_name in enumerate(["A", "B", "C", "D", "E", "F", "G", "H"], 1):
        cell = ws_pagamentos[f"{col_name}4"]
        cell.fill = fill_header
        cell.font = font_header
        cell.alignment = Alignment(horizontal="center", vertical="center")

    for cota in periodo.cotas.all().order_by("numero_ordem"):
        ws_pagamentos.append([
            cota.numero_ordem,
            cota.mes_referencia.strftime('%d/%m/%Y') if cota.mes_referencia else '',
            cota.data_vencimento.strftime('%d/%m/%Y') if cota.data_vencimento else '',
            float(cota.valor_titulo),
            cota.data_pagamento.strftime('%d/%m/%Y') if cota.data_pagamento else '',
            float(cota.cota) if cota.cota is not None else '',
            float(cota.valor_pago) if cota.valor_pago is not None else '',
            cota.observacao
        ])

    ws_pagamentos.append([])
    ws_pagamentos.append(["TOTAL RECEITA", "", "", "", "", float(totais["total_cotas_regulares"])])
    ws_pagamentos.append([])

    # Receitas extras no final da aba pagamentos
    for extra in periodo.receitas_extras.all():
        ws_pagamentos.append([extra.descricao, "", "", "", "", float(extra.valor)])
    ws_pagamentos.append(["TOTAL OUTRAS RECEITAS", "", "", "", "", float(totais["total_receitas_extras"])])

    ws_pagamentos.column_dimensions['A'].width = 8
    ws_pagamentos.column_dimensions['B'].width = 20
    ws_pagamentos.column_dimensions['C'].width = 20
    ws_pagamentos.column_dimensions['D'].width = 22
    ws_pagamentos.column_dimensions['E'].width = 20
    ws_pagamentos.column_dimensions['F'].width = 15
    ws_pagamentos.column_dimensions['G'].width = 26
    ws_pagamentos.column_dimensions['H'].width = 30

    # ------------------ ABA 3: PROPRIEDADES ------------------
    ws_prop = wb.create_sheet(title="PROPRIEDADES")
    ws_prop.append(["TABELA DE DATAS E PARÂMETROS"])
    ws_prop.append([])
    ws_prop.append(["MÊS DATA DE VENCIMENTO", periodo.data_vencimento.strftime('%Y-%m-%d')])
    ws_prop.append(["MÊS DE REFERÊNCIA", periodo.mes_referencia.strftime('%Y-%m-%d')])
    ws_prop.append(["MÊS PRÓX. VENCIMENTO", periodo.mes_prox_vencimento])
    ws_prop.append(["DATA PRÓX. VENCIMENTO", periodo.data_prox_vencimento.strftime('%Y-%m-%d')])
    ws_prop.append(["DATAS PRESTAÇÃO INÍCIO MÊS", periodo.data_inicio_prestacao.strftime('%Y-%m-%d')])
    ws_prop.append(["DATAS PRESTAÇÃO FINAL DO MÊS", periodo.data_fim_prestacao.strftime('%Y-%m-%d')])
    ws_prop.append(["VALOR CONDOMINIO", float(periodo.valor_cota_padrao)])
    ws_prop.append(["VALOR VAGA ESTACIONAMENTO", float(periodo.valor_vaga_padrao)])
    ws_prop.append(["VALOR RENDIMENTO LÍQUIDO (APLICAÇÃO)", float(periodo.saldo_anterior_aplicacao)])
    ws_prop.append(["PORQUINHO INTER (FÉRIAS/DÉCIMO)", float(periodo.saldo_anterior_porquinho)])

    ws_prop.column_dimensions['A'].width = 40
    ws_prop.column_dimensions['B'].width = 25

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer


# ---------------------------------------------------------------------------
# GERAÇÃO DE PDF PROFISSIONAL (ReportLab)
# ---------------------------------------------------------------------------
def exportar_relatorio_pdf(periodo: PeriodoPrestacao) -> io.BytesIO:
    """
    Gera o relatório em PDF com alta fidelidade visual à aba PRESTAÇÃO.
    Design elegante, profissional, pronto para assinatura e auditoria.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    totais = calcular_totais_periodo(periodo)
    styles = getSampleStyleSheet()

    # Estilos customizados
    style_title = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        alignment=1, # Centralizado
        textColor=colors.HexColor('#0F172A')
    )
    style_sub = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        alignment=1,
        textColor=colors.HexColor('#475569')
    )
    style_period = ParagraphStyle(
        'DocPeriod',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        alignment=1,
        textColor=colors.HexColor('#1E3A8A'),
        spaceAfter=10
    )
    style_section = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.white
    )
    style_item = ParagraphStyle(
        'ItemText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#1E293B')
    )
    style_item_bold = ParagraphStyle(
        'ItemTextBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#0F172A')
    )
    style_val = ParagraphStyle(
        'ValText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        alignment=2, # Direita
        textColor=colors.HexColor('#1E293B')
    )
    style_val_bold = ParagraphStyle(
        'ValTextBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        alignment=2,
        textColor=colors.HexColor('#0F172A')
    )

    def f_curr(val):
        return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    elements = []

    # Cabeçalho
    elements.append(Paragraph(periodo.condominio.nome.upper(), style_title))
    elements.append(Spacer(1, 2))
    endereco_str = f"{periodo.condominio.endereco}, {periodo.condominio.numero} – {periodo.condominio.bairro} - {periodo.condominio.cidade}/{periodo.condominio.uf}"
    elements.append(Paragraph(endereco_str, style_sub))
    elements.append(Paragraph(f"CNPJ: {periodo.condominio.cnpj or '06.275.266/0001-23'}", style_sub))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(f"PRESTAÇÃO DE CONTAS DO PERÍODO DE {periodo.data_inicio_prestacao.strftime('%d/%m/%Y')} A {periodo.data_fim_prestacao.strftime('%d/%m/%Y')}", style_period))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E1'), spaceAfter=8))

    # Helper para montar tabelas padronizadas
    def criar_bloco(titulo, itens, cor_fundo='#1E3A8A'):
        data = [[Paragraph(titulo, style_section), Paragraph("VALOR", ParagraphStyle('HVal', parent=style_section, alignment=2))]]
        for rotulo, valor, is_bold in itens:
            st_r = style_item_bold if is_bold else style_item
            st_v = style_val_bold if is_bold else style_val
            data.append([Paragraph(rotulo, st_r), Paragraph(f_curr(Decimal(str(valor))), st_v)])
        
        t = Table(data, colWidths=[420, 102])
        t_style = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(cor_fundo)),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('LINEBELOW', (0, 1), (-1, -2), 0.5, colors.HexColor('#E2E8F0')),
            ('LINEBELOW', (0, -1), (-1, -1), 1, colors.HexColor('#94A3B8')),
        ]
        t.setStyle(TableStyle(t_style))
        return t

    # 1. RECEITAS
    itens_receitas = [
        (f"COTAS – REFERENTES AO MÊS DE {periodo.mes_referencia_rotulo} COM VENC. EM {periodo.data_vencimento.strftime('%d/%m/%Y')}", totais["total_cotas_regulares"], False),
    ]
    extras_atraso = periodo.receitas_extras.filter(tipo__in=[ReceitaExtra.TipoReceitaExtra.JUROS_MULTA, ReceitaExtra.TipoReceitaExtra.COTA_ATRASADA, ReceitaExtra.TipoReceitaExtra.ALUGUEL_VAGA, ReceitaExtra.TipoReceitaExtra.OUTRO])
    val_extras_atraso = sum((e.valor for e in extras_atraso), Decimal("0.00"))
    itens_receitas.append(("COTAS – (RECEBIMENTO EM ATRASO / ACORDO / ANTECIPAÇÃO / OUTROS)", val_extras_atraso, False))

    cdb_extras = periodo.receitas_extras.filter(tipo=ReceitaExtra.TipoReceitaExtra.RENDIMENTO_CDB)
    val_cdb = sum((e.valor for e in cdb_extras), Decimal("0.00"))
    itens_receitas.append(("RENDIMENTO INVESTIMENTO CDB", val_cdb, False))
    itens_receitas.append(("TOTAL DAS RECEITAS", totais["total_receitas"], True))

    elements.append(criar_bloco("RECEITAS", itens_receitas, cor_fundo='#0F766E'))
    elements.append(Spacer(1, 8))

    # 2. DESPESAS FIXAS
    itens_fixas = []
    for d in periodo.despesas.filter(tipo=Despesa.TipoDespesa.FIXA):
        itens_fixas.append((d.descricao, d.valor, False))
    itens_fixas.append(("TOTAL DAS DESPESAS FIXAS", totais["total_despesas_fixas"], True))
    elements.append(criar_bloco("DESPESAS FIXAS", itens_fixas, cor_fundo='#1E3A8A'))
    elements.append(Spacer(1, 8))

    # 3. DESPESAS VARIÁVEIS
    itens_var = []
    for d in periodo.despesas.filter(tipo=Despesa.TipoDespesa.VARIAVEL):
        itens_var.append((d.descricao, d.valor, False))
    itens_var.append(("TOTAL DAS DESPESAS VARIÁVEIS", totais["total_despesas_variaveis"], True))
    elements.append(criar_bloco("DESPESAS VARIÁVEIS", itens_var, cor_fundo='#475569'))
    elements.append(Spacer(1, 8))

    # 4. RESULTADO CONTA CORRENTE
    itens_res = [
        ("SALDO ANTERIOR INTER (CONTA CORRENTE)", totais["saldo_anterior_cc"], False),
        ("SALDO ANTERIOR INTER (APLICAÇÃO CDB)", totais["saldo_anterior_aplicacao"], False),
        ("SALDO PORQUINHO (FÉRIAS/13º)", totais["saldo_anterior_porquinho"], False),
        ("SALDO ANTERIOR TOTAL", totais["saldo_anterior_total"], True),
        ("RECEITAS DO MÊS", totais["total_receitas"], False),
        ("SUB TOTAL", totais["subtotal"], True),
        ("TOTAL DAS DESPESAS DO MÊS", totais["total_despesas"], False),
        ("SALDO MÊS", totais["saldo_mes"], True),
        (f"TOTAL DO SALDO BANCÁRIO (INTER CC) EM {periodo.data_saldo_bancario.strftime('%d/%m/%Y') if periodo.data_saldo_bancario else periodo.data_fim_prestacao.strftime('%d/%m/%Y')}", totais["total_saldo_bancario"], True),
    ]
    elements.append(criar_bloco("RESULTADO CONTA CORRENTE", itens_res, cor_fundo='#1E293B'))
    elements.append(Spacer(1, 10))

    # Observação e Assinatura
    obs_style = ParagraphStyle(
        'ObsStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#334155')
    )
    elements.append(Paragraph(f"<b>OBS:</b> {totais['observacao_diferenca']}", obs_style))
    elements.append(Spacer(1, 16))

    # Bloco de Assinatura
    assinatura_data = [
        ["", f"Fortaleza/CE, {periodo.data_assinatura.strftime('%d/%m/%Y') if periodo.data_assinatura else timezone.now().strftime('%d/%m/%Y')}"],
        ["", ""],
        ["", "____________________________________________________________"],
        ["", "Síndico"],
        ["", periodo.sindico_nome],
        ["", f"CPF: {periodo.sindico_cpf}"],
    ]
    t_ass = Table(assinatura_data, colWidths=[200, 322])
    t_ass.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (1, 0), (1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
    ]))
    elements.append(KeepTogether(t_ass))

    doc.build(elements)
    buffer.seek(0)
    return buffer
