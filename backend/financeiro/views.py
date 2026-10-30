from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.http import HttpResponse
from django.utils import timezone
from decimal import Decimal

from core.views import get_request_condominios
from core.permissions import IsSindico, IsSindicoOrSubSindico, get_user_profiles
from .models import PeriodoPrestacao, ReceitaCota, ReceitaExtra, Despesa, SaldoPeriodo, AuditLog
from .serializers import (
    PeriodoPrestacaoSerializer,
    ReceitaCotaSerializer,
    ReceitaExtraSerializer,
    DespesaSerializer,
    SaldoPeriodoSerializer,
    AuditLogSerializer,
)
from .services import (
    calcular_totais_periodo,
    fechar_periodo_prestacao,
    gerar_cotas_iniciais,
    exportar_relatorio_pdf,
    exportar_relatorio_excel,
)


class PeriodoPrestacaoViewSet(viewsets.ModelViewSet):
    serializer_class = PeriodoPrestacaoSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["condominio", "status"]
    search_fields = ["mes_referencia_rotulo", "sindico_nome"]
    ordering_fields = ["data_inicio_prestacao", "data_vencimento", "created_at"]
    ordering = ["-data_inicio_prestacao"]

    def get_queryset(self):
        conds = get_request_condominios(self.request)
        qs = PeriodoPrestacao.objects.select_related("condominio", "snapshot_saldo").all()
        if conds is not None:
            qs = qs.filter(condominio_id__in=conds)
        return qs

    def perform_create(self, serializer):
        user_profiles = get_user_profiles(self.request.user)
        if not self.request.user.is_superuser and "SINDICO" not in user_profiles and "SUBSINDICO" not in user_profiles:
            raise PermissionDenied("Apenas síndicos ou subsíndicos podem criar novos períodos de prestação.")
        periodo = serializer.save()
        AuditLog.objects.create(
            usuario=self.request.user,
            condominio=periodo.condominio,
            entidade="PeriodoPrestacao",
            registro_id=str(periodo.id),
            acao=AuditLog.AcaoAudit.CREATE,
            dados_novos=serializer.data,
            detalhes=f"Período {periodo.mes_referencia_rotulo} criado."
        )

    def perform_update(self, serializer):
        instance = self.get_object()
        if instance.status in [PeriodoPrestacao.StatusPeriodo.FECHADO, PeriodoPrestacao.StatusPeriodo.PUBLICADO]:
            # Permite reabrir ou alterar somente se for superuser ou explicitamente reaberto
            if not self.request.user.is_superuser and not self.request.data.get("allow_locked_edit"):
                raise ValidationError("Período fechado ou publicado não pode ser editado. Reabra-o primeiro.")
        periodo = serializer.save()
        AuditLog.objects.create(
            usuario=self.request.user,
            condominio=periodo.condominio,
            entidade="PeriodoPrestacao",
            registro_id=str(periodo.id),
            acao=AuditLog.AcaoAudit.UPDATE,
            dados_novos=serializer.data,
            detalhes=f"Período {periodo.mes_referencia_rotulo} atualizado."
        )

    @action(detail=True, methods=["post"], url_path="gerar-cotas")
    def gerar_cotas(self, request, pk=None):
        periodo = self.get_object()
        if periodo.status != PeriodoPrestacao.StatusPeriodo.ABERTO:
            return Response({"error": "Só é possível gerar cotas para períodos com status ABERTO."}, status=status.HTTP_400_BAD_REQUEST)
        criadas = gerar_cotas_iniciais(periodo)
        return Response({"message": f"{criadas} cotas geradas com sucesso para as unidades do condomínio.", "total_cotas": periodo.cotas.count()})

    @action(detail=True, methods=["post"], url_path="fechar")
    def fechar(self, request, pk=None):
        periodo = self.get_object()
        user_profiles = get_user_profiles(request.user)
        if not request.user.is_superuser and "SINDICO" not in user_profiles:
            raise PermissionDenied("Apenas o Síndico ou Super Administrador pode fechar a prestação de contas.")
        try:
            totais = fechar_periodo_prestacao(periodo, request.user)
            return Response({"message": "Período fechado com sucesso e snapshot congelado.", "totais": totais})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"], url_path="publicar")
    def publicar(self, request, pk=None):
        periodo = self.get_object()
        user_profiles = get_user_profiles(request.user)
        if not request.user.is_superuser and "SINDICO" not in user_profiles:
            raise PermissionDenied("Apenas o Síndico pode publicar a prestação de contas.")
        
        if periodo.status == PeriodoPrestacao.StatusPeriodo.ABERTO:
            fechar_periodo_prestacao(periodo, request.user)

        periodo.status = PeriodoPrestacao.StatusPeriodo.PUBLICADO
        periodo.publicado_em = timezone.now()
        periodo.save()

        AuditLog.objects.create(
            usuario=request.user,
            condominio=periodo.condominio,
            entidade="PeriodoPrestacao",
            registro_id=str(periodo.id),
            acao=AuditLog.AcaoAudit.PUBLICAR,
            detalhes=f"Período {periodo.mes_referencia_rotulo} publicado para os moradores."
        )
        return Response({"message": "Período publicado com sucesso. Disponível para todos os moradores."})

    @action(detail=True, methods=["post"], url_path="reabrir")
    def reabrir(self, request, pk=None):
        periodo = self.get_object()
        if not request.user.is_superuser:
            user_profiles = get_user_profiles(request.user)
            if "SINDICO" not in user_profiles:
                raise PermissionDenied("Apenas o Síndico pode reabrir um período já fechado.")
        
        periodo.status = PeriodoPrestacao.StatusPeriodo.ABERTO
        periodo.save()

        AuditLog.objects.create(
            usuario=request.user,
            condominio=periodo.condominio,
            entidade="PeriodoPrestacao",
            registro_id=str(periodo.id),
            acao=AuditLog.AcaoAudit.REABRIR,
            detalhes=f"Período {periodo.mes_referencia_rotulo} foi reaberto para edição."
        )
        return Response({"message": "Período reaberto com sucesso."})

    @action(detail=True, methods=["get"], url_path="totais")
    def totais(self, request, pk=None):
        periodo = self.get_object()
        totais = calcular_totais_periodo(periodo)
        return Response(totais)

    @action(detail=True, methods=["get"], url_path="exportar-pdf")
    def exportar_pdf(self, request, pk=None):
        periodo = self.get_object()
        pdf_buffer = exportar_relatorio_pdf(periodo)
        nome_arquivo = f"Prestacao_Contas_{periodo.mes_referencia_rotulo.replace('/', '_')}.pdf"
        response = HttpResponse(pdf_buffer.getvalue(), content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{nome_arquivo}"'
        return response

    @action(detail=True, methods=["get"], url_path="exportar-excel")
    def exportar_excel(self, request, pk=None):
        periodo = self.get_object()
        excel_buffer = exportar_relatorio_excel(periodo)
        nome_arquivo = f"Prestacao_Contas_{periodo.mes_referencia_rotulo.replace('/', '_')}.xlsx"
        response = HttpResponse(
            excel_buffer.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = f'attachment; filename="{nome_arquivo}"'
        return response


class ReceitaCotaViewSet(viewsets.ModelViewSet):
    serializer_class = ReceitaCotaSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["periodo", "unidade", "status"]
    search_fields = ["unidade__identificador", "observacao"]
    ordering_fields = ["numero_ordem", "data_pagamento", "valor_pago"]
    ordering = ["numero_ordem"]

    def get_queryset(self):
        conds = get_request_condominios(self.request)
        qs = ReceitaCota.objects.select_related("periodo", "unidade").all()
        if conds is not None:
            qs = qs.filter(periodo__condominio_id__in=conds)
        return qs

    def perform_update(self, serializer):
        cota = self.get_object()
        if cota.periodo.status == PeriodoPrestacao.StatusPeriodo.FECHADO and not self.request.user.is_superuser:
            raise ValidationError("Não é possível alterar cotas de um período já fechado.")
        serializer.save()

    @action(detail=False, methods=["post"], url_path="marcar-em-massa")
    def marcar_em_massa(self, request):
        """
        Marca múltiplas cotas como pagas de uma vez só.
        Aceita: { cota_ids: [1, 2, ...], data_pagamento: "2026-10-05" }
        """
        cota_ids = request.data.get("cota_ids", [])
        data_pagamento = request.data.get("data_pagamento") or timezone.now().date()

        if not cota_ids:
            return Response({"error": "Nenhuma cota informada."}, status=status.HTTP_400_BAD_REQUEST)

        cotas = ReceitaCota.objects.filter(id__in=cota_ids)
        atualizadas = 0
        for c in cotas:
            if c.periodo.status == PeriodoPrestacao.StatusPeriodo.FECHADO and not request.user.is_superuser:
                continue
            c.data_pagamento = data_pagamento
            c.cota = c.valor_titulo
            c.valor_pago = c.valor_titulo
            c.status = ReceitaCota.StatusCota.PAGO
            c.save()
            atualizadas += 1

        return Response({"message": f"{atualizadas} cotas marcadas como pagas com sucesso."})


class ReceitaExtraViewSet(viewsets.ModelViewSet):
    serializer_class = ReceitaExtraSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["periodo", "tipo"]
    search_fields = ["descricao", "observacao"]
    ordering_fields = ["data", "valor"]
    ordering = ["data"]

    def get_queryset(self):
        conds = get_request_condominios(self.request)
        qs = ReceitaExtra.objects.select_related("periodo", "unidade").all()
        if conds is not None:
            qs = qs.filter(periodo__condominio_id__in=conds)
        return qs


class DespesaViewSet(viewsets.ModelViewSet):
    serializer_class = DespesaSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["periodo", "tipo", "categoria"]
    search_fields = ["descricao", "fornecedor", "numero_documento"]
    ordering_fields = ["data_pagamento", "valor", "tipo"]
    ordering = ["tipo", "data_pagamento"]

    def get_queryset(self):
        conds = get_request_condominios(self.request)
        qs = Despesa.objects.select_related("periodo").all()
        if conds is not None:
            qs = qs.filter(periodo__condominio_id__in=conds)
        return qs


class DashboardFinanceiroView(APIView):
    def get(self, request):
        conds = get_request_condominios(request)
        periodos_qs = PeriodoPrestacao.objects.all()
        if conds is not None:
            periodos_qs = periodos_qs.filter(condominio_id__in=conds)

        ultimo_periodo = periodos_qs.order_by("-data_inicio_prestacao").first()

        metricas_atual = None
        if ultimo_periodo:
            metricas_atual = {
                "periodo_id": ultimo_periodo.id,
                "rotulo": ultimo_periodo.mes_referencia_rotulo,
                "status": ultimo_periodo.status,
                "totais": calcular_totais_periodo(ultimo_periodo),
                "cotas_pendentes": ultimo_periodo.cotas.filter(data_pagamento__isnull=True).count(),
                "cotas_pagas": ultimo_periodo.cotas.filter(data_pagamento__isnull=False).count(),
                "despesas_sem_comprovante": ultimo_periodo.despesas.filter(comprovante="").count()
            }

        # Histórico dos últimos 6 períodos para gráficos
        historico = []
        for p in periodos_qs.order_by("-data_inicio_prestacao")[:6]:
            t = calcular_totais_periodo(p)
            historico.append({
                "periodo_id": p.id,
                "rotulo": p.mes_referencia_rotulo,
                "receitas": float(t["total_receitas"]),
                "despesas": float(t["total_despesas"]),
                "saldo_mes": float(t["saldo_mes"]),
                "status": p.status,
            })
        historico.reverse()

        return Response({
            "periodo_atual": metricas_atual,
            "historico_grafico": historico,
            "total_periodos": periodos_qs.count()
        })


class AreaMoradorPrestacaoView(APIView):
    """
    Endpoint específico para condôminos:
    - Retorna prestações publicadas do condomínio do morador
    - Retorna histórico das cotas da(s) unidade(s) vinculada(s) ao morador logado
    """
    def get(self, request):
        user = request.user
        if not user.is_authenticated:
            return Response({"error": "Não autenticado"}, status=status.HTTP_401_UNAUTHORIZED)

        # Encontra as unidades da pessoa logada
        unidades_ids = []
        if hasattr(user, "pessoa") and user.pessoa:
            unidades_ids = list(
                user.pessoa.vinculos_unidade.filter(data_fim__isnull=True).values_list("unidade_id", flat=True)
            )

        conds = get_request_condominios(request)
        periodos_publicados = PeriodoPrestacao.objects.filter(
            status=PeriodoPrestacao.StatusPeriodo.PUBLICADO
        )
        if conds is not None:
            periodos_publicados = periodos_publicados.filter(condominio_id__in=conds)

        lista_prestas = []
        for p in periodos_publicados.order_by("-data_inicio_prestacao"):
            t = calcular_totais_periodo(p)
            lista_prestas.append({
                "id": p.id,
                "mes_referencia_rotulo": p.mes_referencia_rotulo,
                "data_inicio": p.data_inicio_prestacao,
                "data_fim": p.data_fim_prestacao,
                "total_receitas": t["total_receitas"],
                "total_despesas": t["total_despesas"],
                "saldo_mes": t["saldo_mes"],
                "data_publicacao": p.publicado_em,
                "sindico_nome": p.sindico_nome,
            })

        # Cotas do morador
        minhas_cotas = []
        if unidades_ids:
            cotas_qs = ReceitaCota.objects.filter(
                unidade_id__in=unidades_ids
            ).select_related("periodo", "unidade").order_by("-periodo__data_inicio_prestacao")

            for c in cotas_qs:
                minhas_cotas.append({
                    "id": c.id,
                    "unidade": c.unidade.identificador,
                    "periodo_rotulo": c.periodo.mes_referencia_rotulo,
                    "data_vencimento": c.data_vencimento,
                    "valor_titulo": c.valor_titulo,
                    "data_pagamento": c.data_pagamento,
                    "valor_pago": c.valor_pago,
                    "status": "PAGO" if c.data_pagamento else "PENDENTE",
                    "observacao": c.observacao,
                })

        return Response({
            "prestacoes_publicadas": lista_prestas,
            "minhas_cotas": minhas_cotas
        })
