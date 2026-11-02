from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.http import HttpResponse
from django.utils import timezone
import datetime
from decimal import Decimal

from core.models import CargoCondominial
from core.views import get_request_condominios
from core.permissions import IsSindico, IsSindicoOrSubSindico, ContaBancariaPermission, get_user_profiles
from .models import (
    ContaBancaria,
    PeriodoPrestacao,
    PeriodoSaldoConta,
    ReceitaCota,
    ReceitaExtra,
    Despesa,
    SaldoPeriodo,
    AuditLog,
)
from .serializers import (
    ContaBancariaSerializer,
    PeriodoSaldoContaSerializer,
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


class ContaBancariaViewSet(viewsets.ModelViewSet):
    serializer_class = ContaBancariaSerializer
    permission_classes = [ContaBancariaPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["condominio", "tipo_conta", "ativo"]
    search_fields = ["banco_nome", "descricao", "conta"]
    ordering_fields = ["ordem", "banco_nome", "id"]
    ordering = ["ordem", "banco_nome"]

    def get_queryset(self):
        conds = get_request_condominios(self.request)
        qs = ContaBancaria.objects.select_related("condominio").all()
        if conds is not None:
            qs = qs.filter(condominio_id__in=conds)
        return qs


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

        # Gestores (Síndico e Subsíndico) têm acesso a todos os períodos (inclusive abertos e em fechamento)
        active_role = self.request.headers.get("X-Active-Role") or self.request.query_params.get("active_role")
        if active_role:
            if active_role not in ["SINDICO", "SUBSINDICO"]:
                qs = qs.filter(status=PeriodoPrestacao.StatusPeriodo.PUBLICADO)
        else:
            user_profiles = get_user_profiles(self.request.user, request=self.request)
            if not self.request.user.is_superuser and "SINDICO" not in user_profiles and "SUBSINDICO" not in user_profiles:
                qs = qs.filter(status=PeriodoPrestacao.StatusPeriodo.PUBLICADO)

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

    def perform_destroy(self, instance):
        user_profiles = get_user_profiles(self.request.user)
        if not self.request.user.is_superuser and "SINDICO" not in user_profiles:
            raise PermissionDenied("Apenas o Síndico ou Administrador pode excluir um período de prestação.")
        if instance.status == PeriodoPrestacao.StatusPeriodo.PUBLICADO and not self.request.user.is_superuser:
            raise ValidationError("Período publicado não pode ser excluído diretamente. Reabra-o primeiro.")

        rotulo = instance.mes_referencia_rotulo
        condominio = instance.condominio
        periodo_id = str(instance.id)
        instance.delete()
        AuditLog.objects.create(
            usuario=self.request.user,
            condominio=condominio,
            entidade="PeriodoPrestacao",
            registro_id=periodo_id,
            acao=AuditLog.AcaoAudit.DELETE,
            detalhes=f"Período {rotulo} excluído com sucesso."
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
        if not request.user.is_superuser and "SINDICO" not in user_profiles and "SUBSINDICO" not in user_profiles:
            raise PermissionDenied("Apenas o Síndico ou Subsíndico pode fechar a prestação de contas.")
        try:
            totais = fechar_periodo_prestacao(periodo, request.user)
            return Response({"message": "Período fechado com sucesso e snapshot congelado.", "totais": totais})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"], url_path="publicar")
    def publicar(self, request, pk=None):
        periodo = self.get_object()
        user_profiles = get_user_profiles(request.user)
        if not request.user.is_superuser and "SINDICO" not in user_profiles and "SUBSINDICO" not in user_profiles:
            raise PermissionDenied("Apenas o Síndico ou Subsíndico pode publicar a prestação de contas.")
        
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
            if "SINDICO" not in user_profiles and "SUBSINDICO" not in user_profiles:
                raise PermissionDenied("Apenas o Síndico ou Subsíndico pode reabrir um período já fechado.")
        
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

    @action(detail=False, methods=["get"], url_path="sindico-ativo")
    def sindico_ativo(self, request):
        """
        Retorna os dados do síndico ativo para o condomínio informado.
        """
        condominio_id = request.query_params.get("condominio_id") or request.query_params.get("condominio")
        if not condominio_id:
            conds = get_request_condominios(request)
            if conds:
                condominio_id = conds[0]

        if not condominio_id:
            return Response({"nome": "", "cpf": "", "cargo": ""})

        cargo = CargoCondominial.objects.filter(
            condominio_id=condominio_id,
            cargo=CargoCondominial.TipoCargo.SINDICO,
            ativo=True,
        ).select_related("pessoa").first()

        if cargo and cargo.pessoa:
            return Response({
                "nome": cargo.pessoa.nome,
                "cpf": cargo.pessoa.cpf or "",
                "cargo": cargo.get_cargo_display(),
            })
        return Response({"nome": "", "cpf": "", "cargo": ""})

    @action(detail=True, methods=["post"], url_path="gerar-despesas-fixas")
    def gerar_despesas_fixas(self, request, pk=None):
        periodo = self.get_object()
        if periodo.status != PeriodoPrestacao.StatusPeriodo.ABERTO:
            return Response(
                {"error": "Só é possível gerar despesas para períodos com status ABERTO."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        dt_ref = periodo.mes_referencia or periodo.data_inicio_prestacao
        mes_ref_str = dt_ref.strftime("%m/%Y")

        primeiro_dia_mes_ref = dt_ref.replace(day=1)
        ultimo_dia_mes_ant = primeiro_dia_mes_ref - datetime.timedelta(days=1)
        mes_ant_str = ultimo_dia_mes_ant.strftime("%m/%Y")

        ult_mes_ano_str = f"12/{dt_ref.year}"

        despesas_config = [
            ("PAGTO. SALÁRIO FUNCIONÁRIOS", f"REF. {mes_ant_str} - PAGTO. SALÁRIO FUNCIONÁRIOS", Despesa.CategoriaDespesa.SALARIO),
            ("PAGTO. ANTECIPAÇÃO DE SALÁRIO FUNCIONÁRIOS", f"REF. {mes_ref_str} - PAGTO. ANTECIPAÇÃO DE SALÁRIO FUNCIONÁRIOS", Despesa.CategoriaDespesa.ANTECIPACAO_SALARIO),
            ("PAGTO. SALÁRIO FUNCIONÁRIOS - FÉRIAS", f"REF. {mes_ref_str} - PAGTO. SALÁRIO FUNCIONÁRIOS - FÉRIAS", Despesa.CategoriaDespesa.FERIAS),
            ("PAGTO. ZELADOR DIARISTA", f"REF. {mes_ref_str} - PAGTO. ZELADOR DIARISTA", Despesa.CategoriaDespesa.ZELADOR_DIARISTA),
            ("TRANSPORTE FUNCIONÁRIOS", f"REF. {mes_ref_str} - TRANSPORTE FUNCIONÁRIOS", Despesa.CategoriaDespesa.TRANSPORTE),
            ("REFEIÇÕES FUNCIONÁRIOS", f"REF. {mes_ref_str} - REFEIÇÕES FUNCIONÁRIOS", Despesa.CategoriaDespesa.REFEICAO),
            ("PAGTO. PRIMEIRA PARC. DÉCIMO", f"REF. {ult_mes_ano_str} 13º - PAGTO. PRIMEIRA PARC. DÉCIMO", Despesa.CategoriaDespesa.DECIMO_TERCEIRO),
            ("PAGTO. SEGUNDA PARC. DÉCIMO", f"REF. {ult_mes_ano_str} 13º - PAGTO. SEGUNDA PARC. DÉCIMO", Despesa.CategoriaDespesa.DECIMO_TERCEIRO),
            ("SÍNDICO", f"REF. {mes_ant_str} - SÍNDICO", Despesa.CategoriaDespesa.SINDICO),
            ("GPS", f"REF. {mes_ant_str} - GPS", Despesa.CategoriaDespesa.GPS),
            ("GPS DÉCIMO", f"REF. {ult_mes_ano_str} 13º - GPS DÉCIMO", Despesa.CategoriaDespesa.GPS),
            ("FGTS", f"REF. {mes_ant_str} - FGTS", Despesa.CategoriaDespesa.FGTS),
            ("ENEL", f"REF. {mes_ref_str} - ENEL", Despesa.CategoriaDespesa.ENEL),
            ("CIRO AVILA DE SOUSA (CONTADOR)", f"REF. {mes_ref_str} - CIRO AVILA DE SOUSA (CONTADOR)", Despesa.CategoriaDespesa.CONTABILIDADE),
            ("SERVIÇO DE COLETA DE RESÍDUOS", f"REF. {mes_ref_str} - SERVIÇO DE COLETA DE RESÍDUOS", Despesa.CategoriaDespesa.COLETA_RESIDUOS),
            ("SERVIÇO DE DEDETIZAÇÃO", f"REF. {mes_ref_str} - SERVIÇO DE DEDETIZAÇÃO", Despesa.CategoriaDespesa.DEDETIZACAO),
        ]

        fornecedores_padrao = {
            "ENEL": "Enel Ceará",
            "CIRO AVILA DE SOUSA (CONTADOR)": "Ciro Avila de Sousa",
            "GPS": "Receita Federal",
            "GPS DÉCIMO": "Receita Federal",
            "FGTS": "Caixa Econômica Federal",
            "SÍNDICO": periodo.sindico_nome or "Síndico",
        }

        dt_pagto = periodo.data_inicio_prestacao or timezone.now().date()
        criadas = 0

        for chave, descricao_formatada, categoria in despesas_config:
            fornecedor = fornecedores_padrao.get(chave, "")
            obj, created = Despesa.objects.get_or_create(
                periodo=periodo,
                descricao=descricao_formatada,
                defaults={
                    "tipo": Despesa.TipoDespesa.FIXA,
                    "categoria": categoria,
                    "fornecedor": fornecedor,
                    "valor": Decimal("0.00"),
                    "data_pagamento": dt_pagto,
                },
            )
            if created:
                criadas += 1

        return Response({
            "message": f"{criadas} despesas fixas geradas com sucesso para {periodo.mes_referencia_rotulo}.",
            "criadas": criadas,
            "total_fixas": periodo.despesas.filter(tipo=Despesa.TipoDespesa.FIXA).count(),
        })

    @action(detail=False, methods=["get"], url_path="saldos-periodo-anterior")
    def saldos_periodo_anterior(self, request):
        """
        Retorna os saldos finais da prestação anterior ao mês de referência informado para o condomínio.
        """
        condominio_id = request.query_params.get("condominio") or request.query_params.get("condominio_id")
        data_ref_str = request.query_params.get("mes_referencia") or request.query_params.get("data_inicio")

        if not condominio_id:
            conds = get_request_condominios(request)
            if conds:
                condominio_id = conds[0]

        if not condominio_id:
            return Response({"error": "Condomínio não informado."}, status=status.HTTP_400_BAD_REQUEST)

        qs = PeriodoPrestacao.objects.filter(condominio_id=condominio_id)
        if data_ref_str:
            try:
                if len(data_ref_str) == 7:
                    ano, mes = map(int, data_ref_str.split("-"))
                    dt_limite = datetime.date(ano, mes, 1)
                else:
                    dt_limite = datetime.date.fromisoformat(data_ref_str)
                qs = qs.filter(data_inicio_prestacao__lt=dt_limite)
            except Exception:
                pass

        periodo_ant = qs.order_by("-data_inicio_prestacao", "-id").first()
        if not periodo_ant:
            return Response({
                "encontrado": False,
                "mensagem": "Nenhuma prestação anterior encontrada.",
                "saldos_contas": [],
            })

        saldos_contas = []
        for sc in periodo_ant.saldos_contas.select_related("conta").all():
            saldos_contas.append({
                "conta": sc.conta_id,
                "conta_id": sc.conta_id,
                "banco_nome": sc.conta.banco_nome,
                "descricao": sc.conta.descricao,
                "tipo_display": sc.conta.get_tipo_conta_display(),
                "agencia": sc.conta.agencia,
                "conta_num": sc.conta.conta,
                "saldo_anterior": sc.saldo_anterior,
                "saldo_final": sc.saldo_final,
            })

        return Response({
            "encontrado": True,
            "periodo_anterior_id": periodo_ant.id,
            "periodo_anterior_rotulo": periodo_ant.mes_referencia_rotulo,
            "saldo_anterior_cc": periodo_ant.saldo_anterior_cc,
            "saldo_anterior_aplicacao": periodo_ant.saldo_anterior_aplicacao,
            "saldo_anterior_porquinho": periodo_ant.saldo_anterior_porquinho,
            "total_saldo_bancario": periodo_ant.total_saldo_bancario,
            "saldos_contas": saldos_contas,
        })


class ReceitaCotaViewSet(viewsets.ModelViewSet):
    serializer_class = ReceitaCotaSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["periodo", "unidade", "status", "isento"]
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

    @action(detail=True, methods=["post"], url_path="dar-baixa")
    def dar_baixa(self, request, pk=None):
        """
        Dá baixa no pagamento de uma cota individual.
        """
        cota = self.get_object()
        if cota.periodo.status == PeriodoPrestacao.StatusPeriodo.FECHADO and not request.user.is_superuser:
            return Response({"error": "Período fechado não permite baixa."}, status=status.HTTP_400_BAD_REQUEST)
        if cota.isento:
            return Response({"error": "Cota isenta não permite baixa de pagamento."}, status=status.HTTP_400_BAD_REQUEST)

        data_pgto = request.data.get("data_pagamento") or timezone.now().date()
        cota_val = request.data.get("cota") if request.data.get("cota") is not None else cota.valor_titulo
        valor_pg = request.data.get("valor_pago") if request.data.get("valor_pago") is not None else cota_val

        cota.data_pagamento = data_pgto
        cota.cota = Decimal(str(cota_val))
        cota.valor_pago = Decimal(str(valor_pg))
        if cota.valor_pago > cota.cota:
            cota.juros_multa = cota.valor_pago - cota.cota
        else:
            cota.juros_multa = Decimal("0.00")
        cota.status = ReceitaCota.StatusCota.PAGO
        if "observacao" in request.data:
            cota.observacao = request.data.get("observacao")
        cota.save()

        return Response(self.get_serializer(cota).data)

    @action(detail=True, methods=["post"], url_path="remover-baixa")
    def remover_baixa(self, request, pk=None):
        """
        Remove / estorna a baixa de uma cota individual.
        """
        cota = self.get_object()
        if cota.periodo.status == PeriodoPrestacao.StatusPeriodo.FECHADO and not request.user.is_superuser:
            return Response({"error": "Período fechado não permite remoção de baixa."}, status=status.HTTP_400_BAD_REQUEST)

        cota.data_pagamento = None
        cota.cota = None
        cota.valor_pago = None
        cota.juros_multa = Decimal("0.00")
        cota.status = ReceitaCota.StatusCota.ISENTO if cota.isento else ReceitaCota.StatusCota.PENDENTE
        cota.save()

        return Response(self.get_serializer(cota).data)

    @action(detail=False, methods=["post"], url_path="marcar-em-massa")
    def marcar_em_massa(self, request):
        """
        Marca múltiplas cotas como pagas ou remove baixa em massa.
        Aceita: { cota_ids: [1, 2, ...], data_pagamento: "2026-10-05", acao: "BAIXAR" | "REMOVER_BAIXA" }
        """
        cota_ids = request.data.get("cota_ids", [])
        acao = request.data.get("acao", "BAIXAR")
        data_pagamento = request.data.get("data_pagamento") or timezone.now().date()

        if not cota_ids:
            return Response({"error": "Nenhuma cota informada."}, status=status.HTTP_400_BAD_REQUEST)

        cotas = ReceitaCota.objects.filter(id__in=cota_ids)
        atualizadas = 0
        for c in cotas:
            if c.periodo.status == PeriodoPrestacao.StatusPeriodo.FECHADO and not request.user.is_superuser:
                continue
            if c.isento:
                continue

            if acao == "REMOVER_BAIXA":
                c.data_pagamento = None
                c.cota = None
                c.valor_pago = None
                c.juros_multa = Decimal("0.00")
                c.status = ReceitaCota.StatusCota.PENDENTE
            else:
                c.data_pagamento = data_pagamento
                c.cota = c.valor_titulo
                c.valor_pago = c.valor_titulo
                c.juros_multa = Decimal("0.00")
                c.status = ReceitaCota.StatusCota.PAGO
            c.save()
            atualizadas += 1

        msg = f"{atualizadas} cotas baixadas com sucesso." if acao != "REMOVER_BAIXA" else f"Baixa removida de {atualizadas} cotas."
        return Response({"message": msg})


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

        # Se não for síndico, despesas só podem ser consultadas se o período for PUBLICADO
        active_role = self.request.headers.get("X-Active-Role") or self.request.query_params.get("active_role")
        if active_role:
            if active_role != "SINDICO":
                qs = qs.filter(periodo__status=PeriodoPrestacao.StatusPeriodo.PUBLICADO)
        elif not self.request.user.is_superuser and "SINDICO" not in get_user_profiles(self.request.user, request=self.request):
            qs = qs.filter(periodo__status=PeriodoPrestacao.StatusPeriodo.PUBLICADO)

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
                "cotas_pendentes": ultimo_periodo.cotas.filter(data_pagamento__isnull=True, isento=False).count(),
                "cotas_pagas": ultimo_periodo.cotas.filter(data_pagamento__isnull=False, isento=False).count(),
                "cotas_isentas": ultimo_periodo.cotas.filter(isento=True).count(),
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
        cond_param = request.headers.get("X-Condominio-Id") or request.query_params.get("condominio")

        periodos_publicados = PeriodoPrestacao.objects.filter(
            status=PeriodoPrestacao.StatusPeriodo.PUBLICADO
        ).select_related("condominio")

        if cond_param:
            try:
                cid = int(cond_param)
                if user.is_superuser or conds is None or cid in conds:
                    periodos_publicados = periodos_publicados.filter(condominio_id=cid)
                elif conds is not None:
                    periodos_publicados = periodos_publicados.filter(condominio_id__in=conds)
            except (ValueError, TypeError):
                if conds is not None:
                    periodos_publicados = periodos_publicados.filter(condominio_id__in=conds)
        elif conds is not None:
            periodos_publicados = periodos_publicados.filter(condominio_id__in=conds)

        lista_prestas = []
        for p in periodos_publicados.order_by("-data_inicio_prestacao"):
            t = calcular_totais_periodo(p)
            lista_prestas.append({
                "id": p.id,
                "condominio_id": p.condominio.id,
                "condominio_nome": p.condominio.nome,
                "mes_referencia_rotulo": p.mes_referencia_rotulo,
                "status": p.status,
                "data_inicio": p.data_inicio_prestacao,
                "data_fim": p.data_fim_prestacao,
                "data_vencimento": p.data_vencimento,
                "data_publicacao": p.publicado_em,
                "sindico_nome": p.sindico_nome,
                "valor_cota_padrao": float(p.valor_cota_padrao),
                "cota_extra": float(p.cota_extra) if p.cota_extra else None,
                "valor_cota_total": float(p.valor_cota_total),
                "total_receitas": float(t["total_receitas"]),
                "total_cotas_regulares": float(t["total_cotas_regulares"]),
                "total_receitas_extras": float(t["total_receitas_extras"]),
                "total_despesas": float(t["total_despesas"]),
                "total_despesas_fixas": float(t["total_despesas_fixas"]),
                "total_despesas_variaveis": float(t["total_despesas_variaveis"]),
                "saldo_mes": float(t["saldo_mes"]),
                "total_saldo_bancario": float(t["total_saldo_bancario"]),
                "diferenca_saldo": float(t["diferenca_saldo"]),
                "cotas_pagas": p.cotas.filter(data_pagamento__isnull=False, isento=False).count(),
                "cotas_total": p.cotas.count(),
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
