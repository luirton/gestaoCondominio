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


def parse_decimal_safe(val, default=Decimal("0.00")):
    if val is None or val == "" or val == "null":
        return default
    if isinstance(val, (int, float)):
        return Decimal(f"{val:.2f}")
    if isinstance(val, Decimal):
        return val
    if isinstance(val, str):
        clean_str = val.replace("R$", "").strip()
        if not clean_str:
            return default
        if "," in clean_str and "." in clean_str:
            clean_str = clean_str.replace(".", "").replace(",", ".")
        elif "," in clean_str:
            clean_str = clean_str.replace(",", ".")
        try:
            return Decimal(clean_str).quantize(Decimal("0.01"))
        except Exception:
            return default
    return default


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
    periodo = serializers.PrimaryKeyRelatedField(read_only=True)
    saldo_anterior = serializers.DecimalField(
        max_digits=18, decimal_places=2, required=False, default=Decimal("0.00"), allow_null=True
    )
    saldo_final = serializers.DecimalField(
        max_digits=18, decimal_places=2, required=False, default=Decimal("0.00"), allow_null=True
    )
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

    def to_internal_value(self, data):
        data_copy = data.copy() if hasattr(data, "copy") else dict(data)
        for field in ["saldo_anterior", "saldo_final"]:
            if field in data_copy:
                data_copy[field] = parse_decimal_safe(data_copy.get(field), Decimal("0.00"))
        return super().to_internal_value(data_copy)


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
    valor = serializers.DecimalField(max_digits=18, decimal_places=2, required=True)

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

    def to_internal_value(self, data):
        data_copy = data.copy() if hasattr(data, "copy") else dict(data)
        if "valor" in data_copy:
            data_copy["valor"] = parse_decimal_safe(data_copy["valor"], Decimal("0.00"))
        return super().to_internal_value(data_copy)

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
    total_saldo_bancario = serializers.DecimalField(
        max_digits=18, decimal_places=2, required=False, allow_null=True
    )
    valor_cota_total = serializers.DecimalField(
        max_digits=18, decimal_places=2, read_only=True
    )

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
            "cota_extra",
            "valor_cota_total",
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

    def to_internal_value(self, data):
        data_copy = data.copy() if hasattr(data, "copy") else dict(data)
        decimal_fields = [
            "total_saldo_bancario",
            "saldo_anterior_cc",
            "saldo_anterior_aplicacao",
            "saldo_anterior_porquinho",
            "valor_cota_padrao",
        ]
        for f in decimal_fields:
            if f in data_copy:
                data_copy[f] = parse_decimal_safe(data_copy[f], Decimal("0.00"))

        if "cota_extra" in data_copy:
            val = data_copy["cota_extra"]
            if val is None or val == "" or val == "null":
                data_copy["cota_extra"] = None
            else:
                data_copy["cota_extra"] = parse_decimal_safe(val, None)

        return super().to_internal_value(data_copy)

    def validate(self, attrs):
        dt_ini = attrs.get("data_inicio_prestacao", getattr(self.instance, "data_inicio_prestacao", None))
        dt_fim = attrs.get("data_fim_prestacao", getattr(self.instance, "data_fim_prestacao", None))
        dt_venc = attrs.get("data_vencimento", getattr(self.instance, "data_vencimento", None))

        if dt_ini and dt_fim and dt_fim < dt_ini:
            raise serializers.ValidationError({"data_fim_prestacao": "A data fim não pode ser menor que a data de início."})

        return attrs

    def create(self, validated_data):
        saldos_data = validated_data.pop("saldos_contas", None)
        if saldos_data is None and "saldos_contas" in self.initial_data:
            saldos_data = self.initial_data.get("saldos_contas", [])
        periodo = super().create(validated_data)
        self._sync_saldos_contas(periodo, saldos_data)
        return periodo

    def update(self, instance, validated_data):
        saldos_data = validated_data.pop("saldos_contas", None)
        if saldos_data is None and "saldos_contas" in self.initial_data:
            saldos_data = self.initial_data.get("saldos_contas")
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
            if hasattr(item, "get"):
                conta_val = item.get("conta") or item.get("conta_id")
                conta_id = getattr(conta_val, "id", conta_val)
                raw_ant = item.get("saldo_anterior")
                raw_fin = item.get("saldo_final")
                saldo_ant = Decimal(str(raw_ant if raw_ant not in [None, ""] else 0))
                saldo_fin = Decimal(str(raw_fin if raw_fin not in [None, ""] else 0))
            else:
                continue

            if not conta_id:
                continue

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
