from rest_framework import serializers
from decimal import Decimal
from django.utils import timezone
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
from .services import calcular_totais_periodo


class ContaBancariaSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source="get_tipo_conta_display", read_only=True)
    condominio_nome = serializers.CharField(source="condominio.nome", read_only=True)

    class Meta:
        model = ContaBancaria
        fields = [
            "id",
            "condominio",
            "condominio_nome",
            "banco_nome",
            "tipo_conta",
            "tipo_display",
            "descricao",
            "agencia",
            "conta",
            "ativo",
            "ordem",
            "created_at",
            "updated_at",
        ]


class PeriodoSaldoContaSerializer(serializers.ModelSerializer):
    conta_descricao = serializers.CharField(source="conta.descricao", read_only=True)
    conta_banco = serializers.CharField(source="conta.banco_nome", read_only=True)
    conta_tipo = serializers.CharField(source="conta.tipo_conta", read_only=True)
    conta_tipo_display = serializers.CharField(source="conta.get_tipo_conta_display", read_only=True)

    class Meta:
        model = PeriodoSaldoConta
        fields = [
            "id",
            "periodo",
            "conta",
            "conta_descricao",
            "conta_banco",
            "conta_tipo",
            "conta_tipo_display",
            "saldo_anterior",
            "saldo_final",
        ]


class ReceitaCotaSerializer(serializers.ModelSerializer):
    unidade_identificador = serializers.CharField(source="unidade.identificador", read_only=True)
    unidade_bloco = serializers.CharField(source="unidade.bloco_torre", read_only=True)

    class Meta:
        model = ReceitaCota
        fields = [
            "id",
            "periodo",
            "unidade",
            "unidade_identificador",
            "unidade_bloco",
            "numero_ordem",
            "isento",
            "mes_referencia",
            "data_vencimento",
            "valor_titulo",
            "data_pagamento",
            "cota",
            "valor_pago",
            "juros_multa",
            "status",
            "observacao",
            "comprovante",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        valor_titulo = attrs.get("valor_titulo", getattr(self.instance, "valor_titulo", None))
        valor_pago = attrs.get("valor_pago", getattr(self.instance, "valor_pago", None))
        data_pagamento = attrs.get("data_pagamento", getattr(self.instance, "data_pagamento", None))

        if valor_titulo is not None and valor_titulo < Decimal("0.00"):
            raise serializers.ValidationError({"valor_titulo": "O valor do título não pode ser negativo."})

        if valor_pago is not None and valor_pago < Decimal("0.00"):
            raise serializers.ValidationError({"valor_pago": "O valor pago não pode ser negativo."})

        # Validação de data de pagamento não ser futura
        if data_pagamento and data_pagamento > timezone.now().date():
            raise serializers.ValidationError({"data_pagamento": "A data de pagamento não pode ser no futuro."})

        # Cálculo automático de juros/multa se pago a maior
        cota_base = attrs.get("cota", getattr(self.instance, "cota", None))
        if valor_pago is not None and cota_base is not None:
            if valor_pago > cota_base and ("juros_multa" not in attrs or attrs.get("juros_multa") == Decimal("0.00")):
                attrs["juros_multa"] = valor_pago - cota_base

        return attrs


class ReceitaExtraSerializer(serializers.ModelSerializer):
    unidade_identificador = serializers.CharField(source="unidade.identificador", read_only=True)
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)

    class Meta:
        model = ReceitaExtra
        fields = [
            "id",
            "periodo",
            "tipo",
            "tipo_display",
            "descricao",
            "unidade",
            "unidade_identificador",
            "valor",
            "data",
            "observacao",
            "created_at",
            "updated_at",
        ]

    def validate_valor(self, value):
        if value < Decimal("0.00"):
            raise serializers.ValidationError("O valor não pode ser negativo.")
        return value


class DespesaSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)
    categoria_display = serializers.CharField(source="get_categoria_display", read_only=True)

    class Meta:
        model = Despesa
        fields = [
            "id",
            "periodo",
            "tipo",
            "tipo_display",
            "categoria",
            "categoria_display",
            "descricao",
            "fornecedor",
            "numero_documento",
            "valor",
            "data_pagamento",
            "comprovante",
            "observacoes",
            "created_at",
            "updated_at",
        ]

    def validate_valor(self, value):
        if value < Decimal("0.00"):
            raise serializers.ValidationError("O valor da despesa não pode ser negativo.")
        return value


class SaldoPeriodoSerializer(serializers.ModelSerializer):
    fechado_por_nome = serializers.CharField(source="fechado_por.get_full_name", read_only=True)

    class Meta:
        model = SaldoPeriodo
        fields = "__all__"


class PeriodoPrestacaoSerializer(serializers.ModelSerializer):
    condominio_nome = serializers.CharField(source="condominio.nome", read_only=True)
    totais = serializers.SerializerMethodField()
    snapshot = SaldoPeriodoSerializer(source="snapshot_saldo", read_only=True)
    qtd_cotas_total = serializers.SerializerMethodField()
    qtd_cotas_pagas = serializers.SerializerMethodField()
    qtd_cotas_pendentes = serializers.SerializerMethodField()
    qtd_cotas_isentas = serializers.SerializerMethodField()
    saldos_contas = PeriodoSaldoContaSerializer(many=True, required=False)

    class Meta:
        model = PeriodoPrestacao
        fields = [
            "id",
            "condominio",
            "condominio_nome",
            "mes_referencia",
            "mes_referencia_rotulo",
            "data_vencimento",
            "mes_prox_vencimento",
            "data_prox_vencimento",
            "data_inicio_prestacao",
            "data_fim_prestacao",
            "valor_cota_padrao",
            "valor_vaga_padrao",
            "saldo_anterior_cc",
            "saldo_anterior_aplicacao",
            "saldo_anterior_porquinho",
            "total_saldo_bancario",
            "data_saldo_bancario",
            "observacao_diferenca",
            "status",
            "sindico_nome",
            "sindico_cpf",
            "data_assinatura",
            "fechado_em",
            "fechado_por",
            "publicado_em",
            "totais",
            "snapshot",
            "saldos_contas",
            "qtd_cotas_total",
            "qtd_cotas_pagas",
            "qtd_cotas_pendentes",
            "qtd_cotas_isentas",
            "created_at",
            "updated_at",
        ]

    def get_totais(self, obj):
        try:
            return calcular_totais_periodo(obj)
        except Exception:
            return None

    def get_qtd_cotas_total(self, obj):
        return obj.cotas.count()

    def get_qtd_cotas_pagas(self, obj):
        return obj.cotas.filter(data_pagamento__isnull=False).count()

    def get_qtd_cotas_pendentes(self, obj):
        return obj.cotas.filter(data_pagamento__isnull=True, isento=False).count()

    def get_qtd_cotas_isentas(self, obj):
        return obj.cotas.filter(isento=True).count()

    def validate(self, attrs):
        dt_ini = attrs.get("data_inicio_prestacao", getattr(self.instance, "data_inicio_prestacao", None))
        dt_fim = attrs.get("data_fim_prestacao", getattr(self.instance, "data_fim_prestacao", None))
        dt_venc = attrs.get("data_vencimento", getattr(self.instance, "data_vencimento", None))

        if dt_ini and dt_fim and dt_fim < dt_ini:
            raise serializers.ValidationError({"data_fim_prestacao": "A data fim não pode ser menor que a data de início."})

        return attrs

    def create(self, validated_data):
        saldos_data = self.initial_data.get("saldos_contas", [])
        periodo = super().create(validated_data)
        self._sync_saldos_contas(periodo, saldos_data)
        return periodo

    def update(self, instance, validated_data):
        saldos_data = self.initial_data.get("saldos_contas", None)
        periodo = super().update(instance, validated_data)
        if saldos_data is not None:
            self._sync_saldos_contas(periodo, saldos_data)
        return periodo

    def _sync_saldos_contas(self, periodo, saldos_data):
        if not saldos_data:
            return
        total_saldo_anterior = Decimal("0.00")
        total_saldo_bancario = Decimal("0.00")
        for item in saldos_data:
            conta_id = item.get("conta") or item.get("conta_id")
            if not conta_id:
                continue
            saldo_ant = Decimal(str(item.get("saldo_anterior") or 0))
            saldo_fin = Decimal(str(item.get("saldo_final") or 0))
            PeriodoSaldoConta.objects.update_or_create(
                periodo=periodo,
                conta_id=conta_id,
                defaults={
                    "saldo_anterior": saldo_ant,
                    "saldo_final": saldo_fin,
                }
            )
            total_saldo_anterior += saldo_ant
            total_saldo_bancario += saldo_fin

        PeriodoPrestacao.objects.filter(id=periodo.id).update(
            total_saldo_bancario=total_saldo_bancario
        )


class AuditLogSerializer(serializers.ModelSerializer):
    usuario_nome = serializers.CharField(source="usuario.username", read_only=True)

    class Meta:
        model = AuditLog
        fields = "__all__"
