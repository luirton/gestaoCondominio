"""
Serviço de envio de e-mail de cobrança com PDF anexado.
Permite edição livre do corpo da mensagem pelo síndico.
"""

import logging
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from financeiro.models import HistoricoNotificacaoCobranca
from financeiro.pdf_services import gerar_pdf_aviso_debito
from financeiro.cobranca_services import obter_extrato_inadimplencia_unidade

logger = logging.getLogger(__name__)


def enviar_email_cobranca(unidade, destinatario_email, mensagem_corpo, assunto=None, usuario=None, data_corte=None):
    """
    Gera o PDF de cobrança da unidade e envia por e-mail para o destinatário informado.
    Registra a notificação em HistoricoNotificacaoCobranca.
    """
    extrato = obter_extrato_inadimplencia_unidade(unidade, data_corte=data_corte)
    
    if extrato["esta_em_dia"]:
        return {
            "sucesso": False,
            "erro": f"A unidade {unidade.identificador} não possui débitos pendentes em atraso."
        }

    condominio = unidade.condominio
    nome_destinatario = extrato["responsavel"]["nome"]
    valor_total = extrato["totais"]["total_geral"]
    qtd_titulos = extrato["qtd_titulos"]

    if not assunto:
        assunto = f"[{condominio.nome}] Aviso de Débito em Atraso - {unidade.identificador}"

    # Gera o PDF
    try:
        pdf_bytes = gerar_pdf_aviso_debito(extrato)
    except Exception as e:
        logger.exception("Erro ao gerar PDF de cobrança")
        return {
            "sucesso": False,
            "erro": f"Erro na geração do PDF de cobrança: {str(e)}"
        }

    # Prepara o envio de e-mail
    remetente = getattr(settings, "DEFAULT_FROM_EMAIL", None) or f"{condominio.nome} <noreply@condogestao.com.br>"
    
    lista_destinatarios = [e.strip() for e in destinatario_email.split(",") if e.strip()]
    if not lista_destinatarios:
        return {
            "sucesso": False,
            "erro": "Nenhum endereço de e-mail destinatário foi fornecido."
        }

    status_envio = "ENVIADO"
    erro_detalhe = ""

    # Corpo em HTML simples convertendo quebras de linha
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
        <div style="max-width: 650px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 8px;">
            <h3 style="color: #2b6cb0; margin-top: 0;">{condominio.nome}</h3>
            <div style="background-color: #f7fafc; padding: 15px; border-left: 4px solid #c53030; margin-bottom: 20px;">
                <strong>Aviso de Cobrança Condominial</strong><br/>
                Unidade: <strong>{unidade.identificador}</strong><br/>
                Títulos em Atraso: <strong>{qtd_titulos}</strong> | Total Atualizado: <strong>R$ {valor_total:,.2f}</strong>
            </div>
            <div style="white-space: pre-wrap; font-size: 14px; margin-bottom: 25px;">
{mensagem_corpo}
            </div>
            <p style="font-size: 12px; color: #718096; border-top: 1px solid #e2e8f0; padding-top: 12px;">
                O espelho detalhado com o cálculo de multas e juros por vencimento está anexado em formato PDF.<br/>
                Para dúvidas ou negociações, responda a este e-mail ou entre em contato com a administração.
            </p>
        </div>
    </body>
    </html>
    """

    try:
        email = EmailMultiAlternatives(
            subject=assunto,
            body=mensagem_corpo,
            from_email=remetente,
            to=lista_destinatarios,
        )
        email.attach_alternative(html_content, "text/html")
        nome_arquivo = f"aviso_debito_{unidade.identificador.replace(' ', '_').lower()}.pdf"
        email.attach(nome_arquivo, pdf_bytes, "application/pdf")
        email.send(fail_silently=False)

    except Exception as e:
        logger.exception("Falha ao enviar e-mail de cobrança")
        status_envio = "FALHA"
        erro_detalhe = str(e)

    # Grava no histórico
    historico = HistoricoNotificacaoCobranca.objects.create(
        condominio=condominio,
        unidade=unidade,
        enviado_por=usuario,
        destinatario_nome=nome_destinatario,
        destinatario_email=", ".join(lista_destinatarios),
        assunto=assunto,
        mensagem_enviada=mensagem_corpo,
        valor_total_devedor=valor_total,
        qtd_titulos=qtd_titulos,
        status_envio=status_envio,
        erro_detalhe=erro_detalhe,
    )

    return {
        "sucesso": status_envio == "ENVIADO",
        "historico_id": historico.id,
        "status_envio": status_envio,
        "erro": erro_detalhe if status_envio == "FALHA" else None,
    }
