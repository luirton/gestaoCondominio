"""
Views da API para o Módulo de Inadimplência e Declaração de Nada Consta.
"""

import uuid
import calendar
from datetime import date
from decimal import Decimal
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action

from core.models import Unidade, Condominio, VinculoPessoaUnidade
from core.permissions import get_user_profiles
from financeiro.models import (
    ParametroCobranca,
    AcordoDescontoCota,
    CertidaoNadaConsta,
    HistoricoNotificacaoCobranca,
    ReceitaCota
)
from financeiro.serializers import (
    ParametroCobrancaSerializer,
    AcordoDescontoCotaSerializer,
    CertidaoNadaConstaSerializer,
    HistoricoNotificacaoCobrancaSerializer
)
from financeiro.cobranca_services import (
    obter_extrato_inadimplencia_unidade,
    obter_extrato_consolidado_unidades,
    obter_responsaveis_unidade,
    obter_relatorio_geral_inadimplencia,
    obter_sindico_ativo,
    obter_ultima_cota_paga
)
from financeiro.pdf_services import gerar_pdf_aviso_debito, gerar_pdf_nada_consta, gerar_pdf_nada_consta_lista
from financeiro.email_services import enviar_email_cobranca


def usuario_tem_permissao_gestao(user, request=None, condominio_id=None):
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    perfis = get_user_profiles(user, request=request, condominio_id=condominio_id)
    return any(p in ["SINDICO", "SUBSINDICO", "CONSELHEIRO"] for p in perfis)


class InadimplenciaGeralView(APIView):
    """
    Retorna o relatório geral de inadimplência do condomínio (Visão Síndico).
    GET /api/financeiro/inadimplencia/
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        condominio_id = request.headers.get("x-condominio-id") or request.query_params.get("condominio")
        if not condominio_id:
            condominio = Condominio.objects.first()
        else:
            condominio = get_object_or_404(Condominio, id=condominio_id)

        data_corte_param = request.query_params.get("data_corte")
        data_corte = None
        if data_corte_param:
            try:
                data_corte = date.fromisoformat(data_corte_param)
            except ValueError:
                pass

        relatorio = obter_relatorio_geral_inadimplencia(condominio, data_corte=data_corte)
        return Response(relatorio)


class InadimplenciaUnidadeView(APIView):
    """
    Retorna o extrato de débitos detalhado da unidade com cálculos de juros e multas.
    GET /api/financeiro/inadimplencia/unidade/<id>/
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, unidade_id):
        unidade = get_object_or_404(Unidade, id=unidade_id)
        
        # Se for morador comum (não síndico/admin), só pode ver sua própria unidade
        user = request.user
        is_admin_ou_sindico = usuario_tem_permissao_gestao(user, request=request, condominio_id=unidade.condominio_id)
        if not is_admin_ou_sindico:
            vinculos_usuario = VinculoPessoaUnidade.objects.filter(
                pessoa=user.pessoa,
                unidade=unidade,
                data_fim__isnull=True
            ) if hasattr(user, "pessoa") and user.pessoa else []
            if not vinculos_usuario:
                return Response(
                    {"detail": "Você não tem permissão para visualizar débitos desta unidade."},
                    status=status.HTTP_403_FORBIDDEN
                )

        data_corte_param = request.query_params.get("data_corte")
        data_corte = None
        if data_corte_param:
            try:
                data_corte = date.fromisoformat(data_corte_param)
            except ValueError:
                pass

        extrato = obter_extrato_inadimplencia_unidade(unidade, data_corte=data_corte)
        return Response(extrato)


class InadimplenciaConsolidadaMoradorView(APIView):
    """
    Retorna o extrato consolidado de débitos de todas as unidades vinculadas ao morador autenticado ('Tudo Junto').
    GET /api/financeiro/inadimplencia/morador/consolidado/
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        if not hasattr(user, "pessoa") or not user.pessoa:
            return Response({"detail": "Usuário não possui cadastro de pessoa vinculado."}, status=status.HTTP_400_BAD_REQUEST)

        unidades_ids = VinculoPessoaUnidade.objects.filter(
            pessoa=user.pessoa,
            data_fim__isnull=True
        ).values_list("unidade_id", flat=True)

        unidades = list(Unidade.objects.filter(id__in=unidades_ids).order_by("identificador"))
        if not unidades:
            return Response({"detail": "Nenhuma unidade vinculada encontrada."}, status=status.HTTP_404_NOT_FOUND)

        extrato_cons = obter_extrato_consolidado_unidades(unidades)
        return Response(extrato_cons)


class DownloadAvisoDebitoConsolidadoPdfView(APIView):
    """
    Download do PDF de Aviso de Débito Consolidado com todas as unidades do morador ('Tudo Junto').
    GET /api/financeiro/inadimplencia/morador/consolidado/pdf/
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        if not hasattr(user, "pessoa") or not user.pessoa:
            return Response({"detail": "Não autorizado."}, status=status.HTTP_400_BAD_REQUEST)

        unidades_ids = VinculoPessoaUnidade.objects.filter(
            pessoa=user.pessoa,
            data_fim__isnull=True
        ).values_list("unidade_id", flat=True)

        unidades = list(Unidade.objects.filter(id__in=unidades_ids).order_by("identificador"))
        extrato_cons = obter_extrato_consolidado_unidades(unidades)
        if not extrato_cons:
            return Response({"detail": "Nenhum dado encontrado."}, status=status.HTTP_404_NOT_FOUND)

        pdf_bytes = gerar_pdf_aviso_debito(extrato_cons)
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        filename = f"aviso_debito_consolidado_{user.username}.pdf"
        response["Content-Disposition"] = f'inline; filename="{filename}"'
        return response


class DownloadAvisoDebitoPdfView(APIView):
    """
    Gera e faz download do PDF de Aviso de Débito em Atraso da unidade.
    GET /api/financeiro/inadimplencia/unidade/<id>/pdf/
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, unidade_id):
        unidade = get_object_or_404(Unidade, id=unidade_id)
        
        user = request.user
        is_admin_ou_sindico = usuario_tem_permissao_gestao(user, request=request, condominio_id=unidade.condominio_id)
        if not is_admin_ou_sindico:
            vinculos_usuario = VinculoPessoaUnidade.objects.filter(
                pessoa=user.pessoa,
                unidade=unidade,
                data_fim__isnull=True
            ) if hasattr(user, "pessoa") and user.pessoa else []
            if not vinculos_usuario:
                return Response({"detail": "Não autorizado."}, status=status.HTTP_403_FORBIDDEN)

        extrato = obter_extrato_inadimplencia_unidade(unidade)
        pdf_bytes = gerar_pdf_aviso_debito(extrato)

        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        filename = f"aviso_debito_{unidade.identificador.replace(' ', '_').lower()}.pdf"
        response["Content-Disposition"] = f'inline; filename="{filename}"'
        return response


class EnviarEmailCobrancaView(APIView):
    """
    Dispara o e-mail de cobrança para os responsáveis da unidade com texto customizado e PDF anexado.
    POST /api/financeiro/inadimplencia/unidade/<id>/enviar-email/
    Body:
    {
       "destinatario_email": "morador@exemplo.com",
       "mensagem": "Texto personalizado digitado pelo síndico",
       "assunto": "Assunto opcional"
    }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, unidade_id):
        user = request.user
        is_admin_ou_sindico = usuario_tem_permissao_gestao(user, request=request, condominio_id=unidade.condominio_id)
        if not is_admin_ou_sindico:
            return Response(
                {"detail": "Apenas o síndico ou administradores podem disparar e-mails de cobrança."},
                status=status.HTTP_403_FORBIDDEN
            )

        unidade = get_object_or_404(Unidade, id=unidade_id)
        destinatario = request.data.get("destinatario_email")
        mensagem = request.data.get("mensagem")
        assunto = request.data.get("assunto")

        if not destinatario or not mensagem:
            return Response(
                {"detail": "Informe o destinatário e a mensagem do e-mail."},
                status=status.HTTP_400_BAD_REQUEST
            )

        resultado = enviar_email_cobranca(
            unidade=unidade,
            destinatario_email=destinatario,
            mensagem_corpo=mensagem,
            assunto=assunto,
            usuario=user,
        )

        if not resultado["sucesso"]:
            return Response(resultado, status=status.HTTP_400_BAD_REQUEST)

        return Response(resultado, status=status.HTTP_200_OK)


class EmitirNadaConstaView(APIView):
    """
    Valida a adimplência e emite a Declaração de Nada Consta (Quitação).
    Válida até o último dia do mês corrente.
    POST /api/financeiro/nada-consta/emitir/
    Body: { "unidade_id": 1 }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        unidade_id = request.data.get("unidade_id")
        if not unidade_id:
            return Response({"detail": "unidade_id é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)

        unidade = get_object_or_404(Unidade, id=unidade_id)
        user = request.user

        # Se for morador, só pode emitir para a sua unidade
        is_admin_ou_sindico = usuario_tem_permissao_gestao(user, request=request, condominio_id=unidade.condominio_id)
        if not is_admin_ou_sindico:
            vinculos_usuario = VinculoPessoaUnidade.objects.filter(
                pessoa=user.pessoa,
                unidade=unidade,
                data_fim__isnull=True
            ) if hasattr(user, "pessoa") and user.pessoa else []
            if not vinculos_usuario:
                return Response({"detail": "Não autorizado para emitir certidão desta unidade."}, status=status.HTTP_403_FORBIDDEN)

        # Validação de inadimplência
        extrato = obter_extrato_inadimplencia_unidade(unidade)
        if not extrato["esta_em_dia"]:
            return Response(
                {
                    "sucesso": False,
                    "detail": "Não é possível emitir a Certidão de Nada Consta pois a unidade possui títulos pendentes em atraso.",
                    "qtd_titulos": extrato["qtd_titulos"],
                    "saldo_devedor": extrato["totais"]["total_geral"],
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        hoje = date.today()
        # Calcula último dia do mês vigente
        _, ultimo_dia = calendar.monthrange(hoje.year, hoje.month)
        data_validade = date(hoje.year, hoje.month, ultimo_dia)

        # Obtém síndico em exercício
        sindico_info = obter_sindico_ativo(unidade.condominio)
        
        # Dados do proprietário
        responsavel = extrato["responsavel"]

        # Última cota paga
        ultima_cota = obter_ultima_cota_paga(unidade)
        ultima_ref = ultima_cota["referencia"] if ultima_cota else "ANTERIOR"
        ultima_venc = ultima_cota["vencimento"] if ultima_cota else None

        # Gera código único
        codigo_autenticacao = f"NC-{unidade.identificador.replace(' ', '')}-{hoje.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        certidao = CertidaoNadaConsta.objects.create(
            condominio=unidade.condominio,
            unidade=unidade,
            solicitante=user,
            codigo_autenticacao=codigo_autenticacao,
            data_validade=data_validade,
            proprietario_nome=responsavel["nome"],
            proprietario_cpf=responsavel["cpf"],
            sindico_nome=sindico_info["nome"],
            sindico_cpf=sindico_info["cpf"],
            sindico_endereco=sindico_info["endereco"],
            ultima_cota_referencia=ultima_ref,
            ultima_cota_vencimento=ultima_venc,
        )

        serializer = CertidaoNadaConstaSerializer(certidao)
        return Response({
            "sucesso": True,
            "certidao": serializer.data,
            "download_url": f"/api/financeiro/nada-consta/{certidao.id}/pdf/"
        }, status=status.HTTP_201_CREATED)


class EmitirNadaConstaConsolidadoMoradorView(APIView):
    """
    Emite a Declaração de Nada Consta individual para cada uma das unidades adimplentes do morador ('Tudo Junto').
    POST /api/financeiro/nada-consta/morador/consolidado/
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        if not hasattr(user, "pessoa") or not user.pessoa:
            return Response({"detail": "Usuário não possui cadastro de pessoa vinculado."}, status=status.HTTP_400_BAD_REQUEST)

        unidades_ids = VinculoPessoaUnidade.objects.filter(
            pessoa=user.pessoa,
            data_fim__isnull=True
        ).values_list("unidade_id", flat=True)

        unidades = list(Unidade.objects.filter(id__in=unidades_ids).order_by("identificador"))
        if not unidades:
            return Response({"detail": "Nenhuma unidade vinculada encontrada."}, status=status.HTTP_404_NOT_FOUND)

        # Filtra quais unidades estão adimplentes
        unidades_adimplentes = []
        for u in unidades:
            ext = obter_extrato_inadimplencia_unidade(u)
            if ext["esta_em_dia"]:
                unidades_adimplentes.append(u)

        if not unidades_adimplentes:
            return Response(
                {
                    "sucesso": False,
                    "detail": "Todas as suas unidades possuem pendências em aberto. Não há unidades adimplentes para emissão de Nada Consta.",
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        hoje = date.today()
        _, ultimo_dia = calendar.monthrange(hoje.year, hoje.month)
        data_validade = date(hoje.year, hoje.month, ultimo_dia)

        certidoes_emitidas = []
        for u in unidades_adimplentes:
            sindico_info = obter_sindico_ativo(u.condominio)
            responsavel = obter_responsaveis_unidade(u)
            ultima_cota = obter_ultima_cota_paga(u)
            ultima_ref = ultima_cota["referencia"] if ultima_cota else "ANTERIOR"
            ultima_venc = ultima_cota["vencimento"] if ultima_cota else None
            codigo_autenticacao = f"NC-{u.identificador.replace(' ', '')}-{hoje.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

            certidao = CertidaoNadaConsta.objects.create(
                condominio=u.condominio,
                unidade=u,
                solicitante=user,
                codigo_autenticacao=codigo_autenticacao,
                data_validade=data_validade,
                proprietario_nome=responsavel["nome"],
                proprietario_cpf=responsavel["cpf"],
                sindico_nome=sindico_info["nome"],
                sindico_cpf=sindico_info["cpf"],
                sindico_endereco=sindico_info["endereco"],
                ultima_cota_referencia=ultima_ref,
                ultima_cota_vencimento=ultima_venc,
            )
            certidoes_emitidas.append(certidao)

        nomes_concatenados = ", ".join(u.identificador for u in unidades_adimplentes)
        ids_str = ",".join(str(c.id) for c in certidoes_emitidas)

        return Response({
            "sucesso": True,
            "qtd_adimplentes": len(unidades_adimplentes),
            "unidades_adimplentes": [u.identificador for u in unidades_adimplentes],
            "unidades_concatenadas": nomes_concatenados,
            "ids": [c.id for c in certidoes_emitidas],
            "download_url": f"/api/financeiro/nada-consta/morador/consolidado/pdf/?ids={ids_str}"
        }, status=status.HTTP_201_CREATED)


class DownloadCertidaoNadaConstaConsolidadoPdfView(APIView):
    """
    Download do PDF consolidado (concatenado) com as certidões de cada unidade adimplente do morador.
    GET /api/financeiro/nada-consta/morador/consolidado/pdf/?ids=1,2,3
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        ids_param = request.query_params.get("ids")
        if ids_param:
            try:
                ids = [int(i.strip()) for i in ids_param.split(",") if i.strip()]
            except ValueError:
                ids = []
            certidoes = list(CertidaoNadaConsta.objects.filter(id__in=ids).select_related("condominio", "unidade"))
        else:
            if not hasattr(user, "pessoa") or not user.pessoa:
                return Response({"detail": "Usuário não possui pessoa associada."}, status=status.HTTP_400_BAD_REQUEST)
            unidades_ids = VinculoPessoaUnidade.objects.filter(
                pessoa=user.pessoa,
                data_fim__isnull=True
            ).values_list("unidade_id", flat=True)
            certidoes_map = {}
            for c in CertidaoNadaConsta.objects.filter(
                unidade_id__in=unidades_ids,
                data_validade__gte=date.today()
            ).order_by("-created_at").select_related("condominio", "unidade"):
                if c.unidade_id not in certidoes_map:
                    certidoes_map[c.unidade_id] = c
            certidoes = sorted(certidoes_map.values(), key=lambda x: x.unidade.identificador)

        if not certidoes:
            return Response({"detail": "Nenhuma certidão encontrada para download consolidado."}, status=status.HTTP_404_NOT_FOUND)

        for c in certidoes:
            is_admin_ou_sindico = usuario_tem_permissao_gestao(user, request=request, condominio_id=c.condominio_id)
            if not is_admin_ou_sindico:
                tem_vinculo = VinculoPessoaUnidade.objects.filter(
                    pessoa=user.pessoa,
                    unidade=c.unidade,
                    data_fim__isnull=True
                ).exists() if hasattr(user, "pessoa") and user.pessoa else False
                if not tem_vinculo:
                    return Response({"detail": f"Você não tem autorização para a certidão da {c.unidade.identificador}."}, status=status.HTTP_403_FORBIDDEN)

        pdf_bytes = gerar_pdf_nada_consta_lista(certidoes)
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        filename = f"nada_consta_consolidado_{date.today().strftime('%Y%m%d')}.pdf"
        response["Content-Disposition"] = f'inline; filename="{filename}"'
        return response


class DownloadCertidaoNadaConstaPdfView(APIView):
    """
    Download do PDF de uma Certidão de Nada Consta emitida.
    GET /api/financeiro/nada-consta/<id>/pdf/
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, certidao_id):
        certidao = get_object_or_404(CertidaoNadaConsta, id=certidao_id)
        
        user = request.user
        is_admin_ou_sindico = usuario_tem_permissao_gestao(user, request=request, condominio_id=certidao.condominio_id)
        if not is_admin_ou_sindico:
            vinculos_usuario = VinculoPessoaUnidade.objects.filter(
                pessoa=user.pessoa,
                unidade=certidao.unidade,
                data_fim__isnull=True
            ) if hasattr(user, "pessoa") and user.pessoa else []
            if not vinculos_usuario:
                return Response({"detail": "Não autorizado."}, status=status.HTTP_403_FORBIDDEN)

        unidades_multi = request.query_params.get("unidades_multi")
        pdf_bytes = gerar_pdf_nada_consta(certidao, unidades_adicionais_str=unidades_multi)
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        filename = f"nada_consta_{certidao.unidade.identificador.replace(' ', '_').lower()}_{certidao.codigo_autenticacao}.pdf"
        response["Content-Disposition"] = f'inline; filename="{filename}"'
        return response


class ParametroCobrancaViewSet(viewsets.ModelViewSet):
    """
    CRUD com histórico e vigência dos parâmetros de cobrança (juros, multas, mensagens padrão).
    """
    queryset = ParametroCobranca.objects.all().order_by("-data_inicio")
    serializer_class = ParametroCobrancaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        condominio_id = self.request.headers.get("x-condominio-id") or self.request.query_params.get("condominio")
        if condominio_id:
            return self.queryset.filter(condominio_id=condominio_id)
        return self.queryset

    def perform_create(self, serializer):
        condominio_id = self.request.headers.get("x-condominio-id") or self.request.data.get("condominio")
        if not condominio_id:
            condominio = Condominio.objects.first()
        else:
            condominio = get_object_or_404(Condominio, id=condominio_id)

        data_inicio = serializer.validated_data.get("data_inicio")

        # Regra 2: Fechamento automático da vigência anterior aberta
        if data_inicio:
            from datetime import timedelta
            vigencia_aberta = ParametroCobranca.objects.filter(
                condominio=condominio,
                data_fim__isnull=True,
                data_inicio__lt=data_inicio
            ).order_by("-data_inicio").first()

            if vigencia_aberta:
                vigencia_aberta.data_fim = data_inicio - timedelta(days=1)
                vigencia_aberta.save(update_fields=["data_fim", "updated_at"])

        serializer.save(condominio=condominio)

    @action(detail=False, methods=["get", "post"])
    def atual(self, request):
        condominio_id = request.headers.get("x-condominio-id") or request.query_params.get("condominio")
        if not condominio_id:
            condominio = Condominio.objects.first()
        else:
            condominio = get_object_or_404(Condominio, id=condominio_id)

        hoje = date.today()
        # Busca vigência ativa hoje
        param = ParametroCobranca.objects.filter(
            condominio=condominio,
            data_inicio__lte=hoje
        ).filter(
            Q(data_fim__gte=hoje) | Q(data_fim__isnull=True)
        ).order_by("-data_inicio").first()

        if not param:
            param = ParametroCobranca.objects.filter(
                condominio=condominio
            ).order_by("-data_inicio").first()

        if not param:
            param = ParametroCobranca.objects.create(
                condominio=condominio,
                data_inicio=date(2024, 1, 1),
                tipo_multa=ParametroCobranca.TipoMulta.FIXO,
                valor_multa=Decimal("10.00"),
                percentual_juros_dia=Decimal("0.0024"),
            )

        if request.method == "POST":
            # Se for cadastrada uma nova data de início para criar nova vigência
            nova_data_inicio = request.data.get("nova_data_inicio")
            if nova_data_inicio:
                dt_inicio = date.fromisoformat(nova_data_inicio)
                from datetime import timedelta
                # Fecha vigência atual
                if not param.data_fim or param.data_fim >= dt_inicio:
                    param.data_fim = dt_inicio - timedelta(days=1)
                    param.save(update_fields=["data_fim", "updated_at"])

                # Cria novo parâmetro
                novo_param = ParametroCobranca.objects.create(
                    condominio=condominio,
                    data_inicio=dt_inicio,
                    data_fim=None,
                    tipo_multa=request.data.get("tipo_multa", param.tipo_multa),
                    valor_multa=Decimal(str(request.data.get("valor_multa", param.valor_multa))),
                    percentual_juros_dia=Decimal(str(request.data.get("percentual_juros_dia", param.percentual_juros_dia))),
                    qtd_parcelas_ajuizamento=int(request.data.get("qtd_parcelas_ajuizamento", param.qtd_parcelas_ajuizamento)),
                    email_cobranca=request.data.get("email_cobranca", param.email_cobranca),
                    telefone_cobranca=request.data.get("telefone_cobranca", param.telefone_cobranca),
                    prazo_negociacao_info=request.data.get("prazo_negociacao_info", param.prazo_negociacao_info),
                    aviso_protesto_info=request.data.get("aviso_protesto_info", param.aviso_protesto_info),
                    aviso_ajuizamento_info=request.data.get("aviso_ajuizamento_info", param.aviso_ajuizamento_info),
                )
                serializer = self.get_serializer(novo_param)
                return Response(serializer.data, status=status.HTTP_201_CREATED)

            # Caso contrário, apenas atualiza a regra atual
            serializer = self.get_serializer(param, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

        serializer = self.get_serializer(param)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def historico(self, request):
        condominio_id = request.headers.get("x-condominio-id") or request.query_params.get("condominio")
        qs = self.get_queryset()
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


class AcordoDescontoCotaViewSet(viewsets.ModelViewSet):
    """
    CRUD de acordos e descontos negociados pelo síndico.
    """
    queryset = AcordoDescontoCota.objects.all()
    serializer_class = AcordoDescontoCotaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(sindico_autorizador=self.request.user)


class HistoricoNotificacaoCobrancaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Consulta do histórico de e-mails de cobrança disparados.
    """
    queryset = HistoricoNotificacaoCobranca.objects.all()
    serializer_class = HistoricoNotificacaoCobrancaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = self.queryset
        condominio_id = self.request.headers.get("x-condominio-id") or self.request.query_params.get("condominio")
        if condominio_id:
            qs = qs.filter(condominio_id=condominio_id)
        unidade_id = self.request.query_params.get("unidade")
        if unidade_id:
            qs = qs.filter(unidade_id=unidade_id)
        return qs
