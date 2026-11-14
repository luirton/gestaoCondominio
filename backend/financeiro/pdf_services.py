"""
Geração de PDFs para o Módulo de Inadimplência:
1. Aviso de Débito em Atraso (Layout oficial da planilha)
2. Declaração de Nada Consta (Layout idêntico ao modelo físico fornecido)
"""

import io
import calendar
from datetime import date
from decimal import Decimal

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether, PageBreak
)
from reportlab.pdfgen import canvas


MESES_PT_BR = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}


def format_moeda(valor):
    if valor is None:
        return "R$ 0,00"
    v = Decimal(str(valor))
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_data(d):
    if not d:
        return ""
    if isinstance(d, str):
        return d
    return d.strftime("%d/%m/%Y")


def gerar_pdf_aviso_debito(dados_extrato):
    """
    Gera o PDF de 'AVISO DE DÉBITO EM ATRASO' fiel à planilha do condomínio.
    Retorna os bytes do PDF gerado.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )

    styles = getSampleStyleSheet()
    
    style_header_title = ParagraphStyle(
        "HeaderTitle",
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#1A202C")
    )
    style_header_sub = ParagraphStyle(
        "HeaderSub",
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#4A5568")
    )
    style_title = ParagraphStyle(
        "DocTitle",
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        alignment=1, # Centralizado
        textColor=colors.HexColor("#9B2C2C") # Tom de alerta / vinho
    )
    style_body = ParagraphStyle(
        "BodyTextCustom",
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#2D3748")
    )
    style_table_cell = ParagraphStyle(
        "TableCell",
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        alignment=1,
    )
    style_table_header = ParagraphStyle(
        "TableHeader",
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        alignment=1,
        textColor=colors.white,
    )
    style_obs = ParagraphStyle(
        "ObsStyle",
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#742A2A")
    )

    story = []

    # Cabeçalho Institucional
    condominio = dados_extrato["condominio"]
    responsavel = dados_extrato["responsavel"]
    unidade = dados_extrato["unidade"]
    data_atual = dados_extrato["data_atualizacao"]

    story.append(Paragraph(f"<b>{condominio['nome'].upper()}</b>", style_header_title))
    if condominio.get("endereco"):
        story.append(Paragraph(condominio["endereco"], style_header_sub))
    if condominio.get("cnpj"):
        story.append(Paragraph(f"CNPJ: {condominio['cnpj']}", style_header_sub))

    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E0"), spaceAfter=10))

    # Data de Atualização alinhada à direita
    data_str = format_data(data_atual)
    story.append(Paragraph(f"<para align='right'><b>Data de Atualização:</b> {data_str}</para>", style_body))
    story.append(Spacer(1, 12))

    # Título do Documento
    story.append(Paragraph("AVISO DE DÉBITO EM ATRASO", style_title))
    story.append(Spacer(1, 14))

    # Saudação e Texto explicativo
    nome_proprietario = responsavel["nome"].upper()
    identificador_unidade = unidade["identificador"]
    
    if dados_extrato.get("multi_unidades"):
        saudacao = f"Prezado(a) Sr(a). <b>{nome_proprietario}</b>, proprietário(a) das unidades <b>{identificador_unidade}</b>."
    else:
        saudacao = f"Prezado(a) Sr(a). <b>{nome_proprietario}</b>, proprietário(a) da <b>{identificador_unidade}</b>."
    story.append(Paragraph(saudacao, style_body))
    story.append(Spacer(1, 8))

    texto_aviso = (
        "Com base nas informações sobre títulos em aberto coletadas no sistema de cobrança e "
        "também fornecidas pela administração, encaminhamos abaixo a planilha com os cálculos atualizados dos débitos pendentes.<br/>"
        "Caso identifique alguma inconsistência ou débito que já tenha sido quitado, solicitamos que entre em contato "
        "com a administração do condomínio e/ou envie os comprovantes para que possamos realizar as devidas correções."
    )
    story.append(Paragraph(texto_aviso, style_body))
    story.append(Spacer(1, 14))

    # Tabela de Débitos
    story.append(Paragraph("<b>DÉBITOS</b>", ParagraphStyle("DebitosHeader", fontName="Helvetica-Bold", fontSize=10, textColor=colors.HexColor("#1A202C"))))
    story.append(Spacer(1, 6))

    # Colunas: ITEM | ATUALIZAÇÃO ATÉ | VENCIMENTO | DIAS VENCIDO | TAXA | MULTA | JUROS | TOTAL A PAGAR | OBS
    table_data = [
        [
            Paragraph("Item", style_table_header),
            Paragraph("Atualização Até", style_table_header),
            Paragraph("Vencimento", style_table_header),
            Paragraph("Dias Venc.", style_table_header),
            Paragraph("Taxa", style_table_header),
            Paragraph("Multa", style_table_header),
            Paragraph("Juros", style_table_header),
            Paragraph("Total a Pagar", style_table_header),
            Paragraph("Observações", style_table_header),
        ]
    ]

    for item in dados_extrato["itens"]:
        table_data.append([
            Paragraph(str(item["item"]), style_table_cell),
            Paragraph(format_data(item["data_atualizacao"]), style_table_cell),
            Paragraph(format_data(item["vencimento"]), style_table_cell),
            Paragraph(str(item["dias_atraso"]), style_table_cell),
            Paragraph(format_moeda(item["taxa"]), style_table_cell),
            Paragraph(format_moeda(item["multa"]), style_table_cell),
            Paragraph(format_moeda(item["juros"]), style_table_cell),
            Paragraph(f"<b>{format_moeda(item['total'])}</b>", style_table_cell),
            Paragraph(item["observacao"] or "-", style_table_cell),
        ])

    # Linha de Totais (Saldo Devedor)
    totais = dados_extrato["totais"]
    table_data.append([
        Paragraph("<b>SALDO DEVEDOR</b>", style_table_header),
        "", "", "",
        Paragraph(f"<b>{format_moeda(totais['taxa'])}</b>", style_table_header),
        Paragraph(f"<b>{format_moeda(totais['multa'])}</b>", style_table_header),
        Paragraph(f"<b>{format_moeda(totais['juros'])}</b>", style_table_header),
        Paragraph(f"<b>{format_moeda(totais['total_geral'])}</b>", style_table_header),
        "",
    ])

    col_widths = [1.0 * cm, 2.3 * cm, 2.1 * cm, 1.8 * cm, 2.2 * cm, 1.8 * cm, 1.8 * cm, 2.4 * cm, 2.6 * cm]
    t = Table(table_data, colWidths=col_widths, repeatRows=1)
    
    t_style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2B6CB0")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#F7FAFC")]),
        # Estilo para linha final de saldo devedor
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#C53030")), # Vermelho forte
        ("SPAN", (0, -1), (3, -1)),
    ]
    t.setStyle(TableStyle(t_style))
    story.append(t)
    story.append(Spacer(1, 14))

    # Bloco de Rodapé / Observações Legais
    param = dados_extrato.get("parametro", {})
    obs_lines = []
    if param.get("prazo_negociacao_info"):
        obs_lines.append(f"OBS.: {param['prazo_negociacao_info']}")
    if param.get("aviso_protesto_info"):
        obs_lines.append(f"OBS.: {param['aviso_protesto_info']}")
    if param.get("aviso_ajuizamento_info"):
        obs_lines.append(f"OBS.: {param['aviso_ajuizamento_info']}")

    obs_box = [
        Paragraph("Estamos à disposição para qualquer esclarecimento que se faça necessário.", style_body),
        Spacer(1, 8),
    ]
    for line in obs_lines:
        obs_box.append(Paragraph(line, style_obs))
        obs_box.append(Spacer(1, 3))

    if param.get("email_cobranca"):
        obs_box.append(Spacer(1, 6))
        contato = f"<b>CONTATOS:</b> {param['email_cobranca']}"
        if param.get("telefone_cobranca"):
            contato += f" | Tel/WhatsApp: {param['telefone_cobranca']}"
        obs_box.append(Paragraph(contato, style_body))

    story.append(KeepTogether(obs_box))

    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


def _obter_estilos_nada_consta():
    return {
        "header_title": ParagraphStyle(
            "NCHeaderTitle",
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            textColor=colors.HexColor("#1A202C")
        ),
        "header_sub": ParagraphStyle(
            "NCHeaderSub",
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            alignment=2,
            textColor=colors.HexColor("#4A5568")
        ),
        "data_top": ParagraphStyle(
            "NCDataTop",
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            alignment=2,
        ),
        "title": ParagraphStyle(
            "NCTitle",
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            alignment=1,
            textColor=colors.black,
        ),
        "body": ParagraphStyle(
            "NCBody",
            fontName="Helvetica",
            fontSize=11,
            leading=22,
            alignment=4,
            textColor=colors.black,
        ),
        "validade": ParagraphStyle(
            "NCValidade",
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=15,
            alignment=2,
        ),
        "signature": ParagraphStyle(
            "NCSignature",
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=15,
            alignment=1,
        ),
        "signature_sub": ParagraphStyle(
            "NCSignatureSub",
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            alignment=1,
        ),
        "autenticacao": ParagraphStyle(
            "NCAuth",
            fontName="Helvetica",
            fontSize=7.5,
            leading=10,
            alignment=1,
            textColor=colors.HexColor("#718096")
        ),
    }


def _montar_pagina_nada_consta(certidao, unidades_adicionais_str=None, styles=None):
    if styles is None:
        styles = _obter_estilos_nada_consta()

    elementos = []
    condominio = certidao.condominio

    # Topo institucional
    elementos.append(Paragraph(f"<b>{condominio.nome.upper()}</b>", styles["header_title"]))
    
    end_text = f"{condominio.endereco}, nº {condominio.numero}"
    if condominio.bairro:
        end_text += f" – {condominio.bairro}"
    uf_str = getattr(condominio, "uf", "")
    if condominio.cidade and uf_str:
        end_text += f" - {condominio.cidade}/{uf_str}"
    elif condominio.cidade:
        end_text += f" - {condominio.cidade}"
    if condominio.cnpj:
        end_text += f"<br/>CNPJ: {condominio.cnpj}"

    elementos.append(Paragraph(end_text, styles["header_sub"]))
    elementos.append(Spacer(1, 4))
    elementos.append(HRFlowable(width="100%", thickness=1.5, color=colors.black, spaceAfter=20))

    # Data da emissão: Exemplo: Fortaleza, 05 de Agosto de 2024.
    data_emissao = certidao.data_emissao
    dia_str = f"{data_emissao.day:02d}"
    mes_str = MESES_PT_BR.get(data_emissao.month, "")
    ano_str = str(data_emissao.year)
    cidade_str = condominio.cidade or "Fortaleza"
    
    data_formatada_topo = f"{cidade_str}, {dia_str} de {mes_str} de {ano_str}."
    elementos.append(Paragraph(data_formatada_topo, styles["data_top"]))
    elementos.append(Spacer(1, 40))

    # Título Central
    elementos.append(Paragraph("DECLARAÇÃO DE NADA CONSTA", styles["title"]))
    elementos.append(Spacer(1, 45))

    sindico_nome = certidao.sindico_nome.upper()
    sindico_cpf = certidao.sindico_cpf or "---"
    sindico_end = certidao.sindico_endereco or f"{condominio.endereco}, {condominio.numero}"

    prop_nome = certidao.proprietario_nome.upper()
    prop_cpf = certidao.proprietario_cpf or "---"
    
    if unidades_adicionais_str:
        unidade_ident = unidades_adicionais_str
        prop_label = "proprietário(a) das unidades"
    else:
        unidade_ident = certidao.unidade.identificador
        prop_label = f"proprietário(a) da {unidade_ident}"

    cota_ref = certidao.ultima_cota_referencia or "MÊS ANTERIOR"
    cota_venc = format_data(certidao.ultima_cota_vencimento) if certidao.ultima_cota_vencimento else "---"

    if unidades_adicionais_str:
        texto_declaracao = (
            f"Eu, <b>{sindico_nome}</b>, residente em {sindico_end}, CPF <b>{sindico_cpf}</b>, "
            f"Síndico do {condominio.nome} na presente data, declaro para os devidos fins que a "
            f"Sr(a). <b>{prop_nome}</b>, CPF <b>{prop_cpf}</b>, {prop_label} <b>{unidade_ident}</b> do {condominio.nome}, "
            f"situado na {condominio.endereco}, nº {condominio.numero}, <b>não consta nenhuma pendência financeira com o condomínio para as referidas unidades</b>. "
            f"Consta como último pagamento a cota condominial referente ao mês de <b>{cota_ref}</b>, com vencimento em <b>{cota_venc}</b>."
        )
    else:
        texto_declaracao = (
            f"Eu, <b>{sindico_nome}</b>, residente em {sindico_end}, CPF <b>{sindico_cpf}</b>, "
            f"Síndico do {condominio.nome} na presente data, declaro para os devidos fins que a "
            f"Sr(a). <b>{prop_nome}</b>, CPF <b>{prop_cpf}</b>, {prop_label} do {condominio.nome}, "
            f"situado na {condominio.endereco}, nº {condominio.numero}, <b>não consta nenhuma pendência financeira com o condomínio</b>. "
            f"Consta como último pagamento a cota condominial referente ao mês de <b>{cota_ref}</b>, com vencimento em <b>{cota_venc}</b>."
        )

    elementos.append(Paragraph(texto_declaracao, styles["body"]))
    elementos.append(Spacer(1, 45))

    # Validade: "Declaração válida até 31/08/2024"
    validade_str = format_data(certidao.data_validade)
    elementos.append(Paragraph(f"<i>Declaração válida até <b>{validade_str}</b></i>", styles["validade"]))
    elementos.append(Spacer(1, 65))

    # Assinatura
    assinatura_box = [
        HRFlowable(width="60%", thickness=1, color=colors.black, hAlign="CENTER", spaceAfter=8),
        Paragraph(f"{sindico_nome}", styles["signature"]),
        Paragraph(f"{sindico_cpf}", styles["signature_sub"]),
        Paragraph("Síndico", styles["signature_sub"]),
        Spacer(1, 30),
        Paragraph(f"Código de Autenticação Digital: {certidao.codigo_autenticacao}", styles["autenticacao"]),
        Paragraph(f"Emitido eletronicamente em {format_data(certidao.data_emissao)} pelo Sistema CondoGestão", styles["autenticacao"]),
    ]
    elementos.append(KeepTogether(assinatura_box))
    return elementos


def gerar_pdf_nada_consta(certidao, unidades_adicionais_str=None):
    """
    Gera o PDF de 'DECLARAÇÃO DE NADA CONSTA' estritamente conforme o modelo oficial.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2.0 * cm,
        rightMargin=2.0 * cm,
        topMargin=2.0 * cm,
        bottomMargin=2.0 * cm,
    )

    styles = _obter_estilos_nada_consta()
    story = _montar_pagina_nada_consta(certidao, unidades_adicionais_str, styles=styles)
    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


def gerar_pdf_nada_consta_lista(certidoes_list):
    """
    Gera um único PDF concatenando as declarações de Nada Consta de cada unidade adimplente (1 página por unidade).
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2.0 * cm,
        rightMargin=2.0 * cm,
        topMargin=2.0 * cm,
        bottomMargin=2.0 * cm,
    )

    styles = _obter_estilos_nada_consta()
    story = []
    for idx, cert in enumerate(certidoes_list):
        story.extend(_montar_pagina_nada_consta(cert, styles=styles))
        if idx < len(certidoes_list) - 1:
            story.append(PageBreak())

    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
