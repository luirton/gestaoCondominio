from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from decimal import Decimal
import datetime


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        abstract = True


class ContaBancaria(TimeStampedModel):
    class TipoConta(models.TextChoices):
        CORRENTE = "CORRENTE", "Conta Corrente"
        APLICACAO = "APLICACAO", "Aplicação Financeira / CDB"
        POUPANCA = "POUPANCA", "Conta Poupança"
        RESERVA = "RESERVA", "Reserva / Férias e 13º"
        OUTRO = "OUTRO", "Outra Conta"

    condominio = models.ForeignKey(
        "core.Condominio",
        on_delete=models.CASCADE,
        related_name="contas_bancarias",
        verbose_name="Condomínio",
    )
    banco_nome = models.CharField(max_length=100, verbose_name="Banco / Instituição", default="Banco Inter")
    tipo_conta = models.CharField(max_length=30, choices=TipoConta.choices, default=TipoConta.CORRENTE, verbose_name="Tipo de Conta")
    descricao = models.CharField(max_length=150, verbose_name="Descrição / Identificação da Conta")
    agencia = models.CharField(max_length=20, blank=True, verbose_name="Agência")
    conta = models.CharField(max_length=30, blank=True, verbose_name="Número da Conta")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    ordem = models.IntegerField(default=1, verbose_name="Ordem de Exibição")

    class Meta:
        verbose_name = "Conta Bancária do Condomínio"
        verbose_name_plural = "Contas Bancárias do Condomínio"
        ordering = ["ordem", "banco_nome", "descricao"]

    def __str__(self):
        return f"{self.banco_nome} - {self.descricao} ({self.get_tipo_conta_display()})"


class PeriodoPrestacao(TimeStampedModel):
    class StatusPeriodo(models.TextChoices):
        ABERTO = "ABERTO", "Aberto"
        FECHADO = "FECHADO", "Fechado"
        PUBLICADO = "PUBLICADO", "Publicado"

    condominio = models.ForeignKey(
        "core.Condominio",
        on_delete=models.CASCADE,
        related_name="periodos_prestacao",
        verbose_name="Condomínio",
    )
    # Informações de Referência e Datas (conforme aba PROPRIEDADES)
    mes_referencia = models.DateField(
        verbose_name="Mês de Referência",
        help_text="Data inicial ou representativa do mês de referência das cotas (ex: 2026-09-07)"
    )
    mes_referencia_rotulo = models.CharField(
        max_length=50,
        default="SETEMBRO/2026",
        verbose_name="Rótulo do Mês de Referência"
    )
    data_vencimento = models.DateField(
        verbose_name="Data de Vencimento das Cotas",
        help_text="Ex: 2026-10-05"
    )
    mes_prox_vencimento = models.CharField(
        max_length=50,
        blank=True,
        default="OUTUBRO",
        verbose_name="Mês Próx. Vencimento"
    )
    data_prox_vencimento = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data Próx. Vencimento",
        help_text="Ex: 2026-11-05"
    )
    data_inicio_prestacao = models.DateField(
        verbose_name="Início da Prestação de Contas",
        help_text="Ex: 2026-10-01"
    )
    data_fim_prestacao = models.DateField(
        verbose_name="Fim da Prestação de Contas",
        help_text="Ex: 2026-10-31"
    )

    # Valores Parametrizados
    valor_cota_padrao = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=Decimal("380.00"),
        verbose_name="Valor Padrão da Cota (R$)"
    )
    cota_extra = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        null=True,
        blank=True,
        default=None,
        verbose_name="Cota Extra (R$)",
        help_text="Valor da cota extra (opcional). Caso preenchido, soma com o valor da cota condominial."
    )

    @property
    def valor_cota_total(self):
        cota = self.valor_cota_padrao or Decimal("0.00")
        if self.cota_extra:
            return cota + self.cota_extra
        return cota

    # Saldos Anteriores (aba PRESTAÇÃO / RESULTADO CONTA CORRENTE)
    saldo_anterior_cc = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Saldo Anterior Inter (Conta Corrente)"
    )
    saldo_anterior_aplicacao = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Saldo Anterior Inter (Aplicação / CDB)"
    )
    saldo_anterior_porquinho = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Saldo Porquinho (Férias/13º)"
    )

    # Fechamento e Saldo Bancário
    total_saldo_bancario = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Total do Saldo Bancário Final (R$)"
    )
    data_saldo_bancario = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data do Saldo Bancário"
    )
    observacao_diferenca = models.TextField(
        blank=True,
        verbose_name="Observação Automática da Diferença de Cotas"
    )

    # Controle e Assinatura
    status = models.CharField(
        max_length=20,
        choices=StatusPeriodo.choices,
        default=StatusPeriodo.ABERTO,
        verbose_name="Status"
    )
    sindico_nome = models.CharField(
        max_length=150,
        default="JOSÉ MARTINS DA SILVA FILHO",
        verbose_name="Nome do Síndico"
    )
    sindico_cpf = models.CharField(
        max_length=18,
        default="447.260.903-72",
        verbose_name="CPF do Síndico"
    )
    data_assinatura = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data da Assinatura"
    )
    fechado_em = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fechado em"
    )
    fechado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="periodos_fechados",
        verbose_name="Fechado por"
    )
    publicado_em = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Publicado em"
    )

    class Meta:
        verbose_name = "Período de Prestação de Contas"
        verbose_name_plural = "Períodos de Prestação de Contas"
        ordering = ["-data_inicio_prestacao"]

    def __str__(self):
        return f"{self.mes_referencia_rotulo} ({self.data_inicio_prestacao.strftime('%d/%m/%Y')} a {self.data_fim_prestacao.strftime('%d/%m/%Y')}) - {self.condominio.nome}"

    def clean(self):
        if self.data_fim_prestacao and self.data_inicio_prestacao:
            if self.data_fim_prestacao < self.data_inicio_prestacao:
                raise ValidationError({"data_fim_prestacao": "A data final da prestação não pode ser anterior à data inicial."})
        if self.valor_cota_padrao < Decimal("0.00"):
            raise ValidationError({"valor_cota_padrao": "O valor padrão da cota não pode ser negativo."})

    def save(self, *args, **kwargs):
        if self.mes_referencia and not self.data_assinatura:
            import calendar
            from datetime import date
            ano = self.mes_referencia.year
            mes = self.mes_referencia.month
            ultimo_dia = calendar.monthrange(ano, mes)[1]
            self.data_assinatura = date(ano, mes, ultimo_dia)
        super().save(*args, **kwargs)


class PeriodoSaldoConta(TimeStampedModel):
    """
    Relação Mestre-Detalhe dos Saldos Anteriores e Bancários do Período por Conta Bancária.
    """
    periodo = models.ForeignKey(
        PeriodoPrestacao,
        on_delete=models.CASCADE,
        related_name="saldos_contas",
        verbose_name="Período de Prestação",
    )
    conta = models.ForeignKey(
        ContaBancaria,
        on_delete=models.CASCADE,
        related_name="saldos_periodo",
        verbose_name="Conta Bancária",
    )
    saldo_anterior = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Saldo Anterior (R$)"
    )
    saldo_final = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Saldo Final Bancário (R$)"
    )

    class Meta:
        verbose_name = "Saldo de Conta no Período"
        verbose_name_plural = "Saldos de Contas no Período"
        constraints = [
            models.UniqueConstraint(
                fields=["periodo", "conta"],
                name="unique_saldo_conta_por_periodo"
            )
        ]

    def __str__(self):
        return f"{self.conta.descricao} - Ant: R$ {self.saldo_anterior} | Final: R$ {self.saldo_final}"


class ReceitaCota(TimeStampedModel):
    class StatusCota(models.TextChoices):
        PENDENTE = "PENDENTE", "Pendente"
        PAGO = "PAGO", "Pago"
        ATRASADO = "ATRASADO", "Em Atraso"
        ACORDO = "ACORDO", "Acordo"
        ISENTO = "ISENTO", "Isento de Condomínio"

    periodo = models.ForeignKey(
        PeriodoPrestacao,
        on_delete=models.CASCADE,
        related_name="cotas",
        verbose_name="Período de Prestação"
    )
    unidade = models.ForeignKey(
        "core.Unidade",
        on_delete=models.CASCADE,
        related_name="receitas_cotas",
        verbose_name="Unidade"
    )
    numero_ordem = models.IntegerField(
        verbose_name="Nº Ordem",
        default=1,
        help_text="Nº da casa/unidade na ordenação da planilha"
    )
    isento = models.BooleanField(
        default=False,
        verbose_name="Isento de Condomínio",
        help_text="Indica se o titular é isento pelo mandato (síndico/subsíndico)."
    )
    mes_referencia = models.DateField(
        verbose_name="Mês de Referência"
    )
    data_vencimento = models.DateField(
        verbose_name="Data de Vencimento"
    )
    valor_titulo = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("380.00"),
        verbose_name="Valor do Título (R$)"
    )
    data_pagamento = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data de Pagamento"
    )
    cota = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Cota Regular (R$)",
        help_text="Valor base de cota computado para as receitas regulares (ex: 380.00)"
    )
    valor_pago = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Valor Pago Efetivo (R$)"
    )
    juros_multa = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Juros e Multa (R$)"
    )
    status = models.CharField(
        max_length=20,
        choices=StatusCota.choices,
        default=StatusCota.PENDENTE,
        verbose_name="Status"
    )
    observacao = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Observação"
    )
    comprovante = models.FileField(
        upload_to="comprovantes/cotas/",
        null=True,
        blank=True,
        verbose_name="Comprovante"
    )

    class Meta:
        verbose_name = "Receita de Cota Condominial"
        verbose_name_plural = "Receitas de Cotas Condominiais"
        ordering = ["numero_ordem", "unidade__identificador"]
        constraints = [
            models.UniqueConstraint(
                fields=["periodo", "unidade"],
                name="unique_cota_por_periodo_unidade"
            )
        ]

    def __str__(self):
        return f"{self.unidade.identificador} - {self.periodo.mes_referencia_rotulo} (R$ {self.valor_pago or self.valor_titulo})"

    def clean(self):
        if self.valor_titulo < Decimal("0.00"):
            raise ValidationError({"valor_titulo": "O valor do título não pode ser negativo."})
        if self.valor_pago is not None and self.valor_pago < Decimal("0.00"):
            raise ValidationError({"valor_pago": "O valor pago não pode ser negativo."})
        if self.isento:
            self.status = self.StatusCota.ISENTO

    def save(self, *args, **kwargs):
        if self.isento:
            self.status = self.StatusCota.ISENTO
            if not self.observacao:
                self.observacao = "Isento de taxa de condomínio (Mandato de Gestão)"
        elif self.status == self.StatusCota.ISENTO and not self.isento:
            self.status = self.StatusCota.PAGO if self.data_pagamento else self.StatusCota.PENDENTE
        super().save(*args, **kwargs)


class ReceitaExtra(TimeStampedModel):
    class TipoReceitaExtra(models.TextChoices):
        JUROS_MULTA = "JUROS_MULTA", "Juros e Multas de Atraso"
        ALUGUEL_VAGA = "ALUGUEL_VAGA", "Aluguel de Vaga"
        RENDIMENTO_CDB = "RENDIMENTO_CDB", "Rendimento Investimento CDB"
        COTA_ATRASADA = "COTA_ATRASADA", "Cota em Atraso / Acordo"
        OUTRO = "OUTRO", "Outra Receita"

    periodo = models.ForeignKey(
        PeriodoPrestacao,
        on_delete=models.CASCADE,
        related_name="receitas_extras",
        verbose_name="Período de Prestação"
    )
    tipo = models.CharField(
        max_length=30,
        choices=TipoReceitaExtra.choices,
        default=TipoReceitaExtra.OUTRO,
        verbose_name="Tipo de Receita Extra"
    )
    descricao = models.CharField(
        max_length=255,
        verbose_name="Descrição"
    )
    unidade = models.ForeignKey(
        "core.Unidade",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="receitas_extras",
        verbose_name="Unidade Relacionada"
    )
    valor = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        verbose_name="Valor (R$)"
    )
    data = models.DateField(
        verbose_name="Data da Entrada"
    )
    observacao = models.TextField(
        blank=True,
        verbose_name="Observações"
    )

    class Meta:
        verbose_name = "Receita Extra / Outras Receitas"
        verbose_name_plural = "Receitas Extras / Outras Receitas"
        ordering = ["data", "descricao"]

    def __str__(self):
        return f"{self.descricao} - R$ {self.valor}"

    def clean(self):
        if self.valor < Decimal("0.00"):
            raise ValidationError({"valor": "O valor da receita não pode ser negativo."})


class Despesa(TimeStampedModel):
    class TipoDespesa(models.TextChoices):
        FIXA = "FIXA", "Despesa Fixa"
        VARIAVEL = "VARIAVEL", "Despesa Variável"

    class CategoriaDespesa(models.TextChoices):
        SALARIO = "SALARIO", "Salário Funcionários"
        ANTECIPACAO_SALARIO = "ANTECIPACAO_SALARIO", "Antecipação de Salário"
        FERIAS = "FERIAS", "Salário / Férias"
        DECIMO_TERCEIRO = "DECIMO_TERCEIRO", "13º Salário (1ª/2ª Parcela)"
        GPS = "GPS", "GPS / Previdência"
        FGTS = "FGTS", "FGTS"
        ZELADOR_DIARISTA = "ZELADOR_DIARISTA", "Zelador Diarista"
        TRANSPORTE = "TRANSPORTE", "Transporte Funcionários"
        REFEICAO = "REFEICAO", "Refeições Funcionários"
        SINDICO = "SINDICO", "Pró-Labore Síndico"
        ENEL = "ENEL", "Energia Elétrica (Enel)"
        AGUA_CAGECE = "AGUA_CAGECE", "Água / Cagece"
        CONTABILIDADE = "CONTABILIDADE", "Contador / Assessoria"
        DEDETIZACAO = "DEDETIZACAO", "Serviço de Dedetização"
        COLETA_RESIDUOS = "COLETA_RESIDUOS", "Coleta de Resíduos"
        MATERIAL_LIMPEZA = "MATERIAL_LIMPEZA", "Material de Limpeza"
        MANUTENCAO = "MANUTENCAO", "Manutenção e Obras"
        EXTRA_PORTARIA = "EXTRA_PORTARIA", "Serviço Extra Portaria"
        CERTIFICADO_DIGITAL = "CERTIFICADO_DIGITAL", "Certificado Digital"
        EQUIPAMENTOS = "EQUIPAMENTOS", "Equipamentos / Insumos"
        OUTRO = "OUTRO", "Outros"

    periodo = models.ForeignKey(
        PeriodoPrestacao,
        on_delete=models.CASCADE,
        related_name="despesas",
        verbose_name="Período de Prestação"
    )
    tipo = models.CharField(
        max_length=20,
        choices=TipoDespesa.choices,
        verbose_name="Tipo de Despesa"
    )
    categoria = models.CharField(
        max_length=40,
        choices=CategoriaDespesa.choices,
        default=CategoriaDespesa.OUTRO,
        verbose_name="Categoria"
    )
    descricao = models.CharField(
        max_length=255,
        verbose_name="Descrição da Despesa"
    )
    fornecedor = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Fornecedor / Beneficiário"
    )
    numero_documento = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Nº Documento / NF / Recibo"
    )
    valor = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        verbose_name="Valor (R$)"
    )
    data_pagamento = models.DateField(
        verbose_name="Data de Pagamento"
    )
    comprovante = models.FileField(
        upload_to="comprovantes/despesas/",
        null=True,
        blank=True,
        verbose_name="Comprovante (PDF/Imagem)"
    )
    observacoes = models.TextField(
        blank=True,
        verbose_name="Observações"
    )

    class Meta:
        verbose_name = "Despesa"
        verbose_name_plural = "Despesas"
        ordering = ["tipo", "data_pagamento", "descricao"]

    def __str__(self):
        return f"[{self.get_tipo_display()}] {self.descricao} - R$ {self.valor}"

    def clean(self):
        if self.valor < Decimal("0.00"):
            raise ValidationError({"valor": "O valor da despesa não pode ser negativo."})


class SaldoPeriodo(TimeStampedModel):
    """
    Snapshot congelado no momento do fechamento do período.
    Preserva a fórmula original e integridade histórica total.
    """
    periodo = models.OneToOneField(
        PeriodoPrestacao,
        on_delete=models.CASCADE,
        related_name="snapshot_saldo",
        verbose_name="Período de Prestação"
    )
    saldo_anterior_cc = models.DecimalField(
        max_digits=18, decimal_places=2, verbose_name="Saldo Anterior CC"
    )
    saldo_anterior_aplicacao = models.DecimalField(
        max_digits=18, decimal_places=2, verbose_name="Saldo Anterior Aplicação"
    )
    saldo_anterior_porquinho = models.DecimalField(
        max_digits=18, decimal_places=2, verbose_name="Saldo Anterior Porquinho"
    )
    saldo_anterior_total = models.DecimalField(
        max_digits=18, decimal_places=2, verbose_name="Saldo Anterior Total"
    )
    total_cotas_regulares = models.DecimalField(
        max_digits=18, decimal_places=2, verbose_name="Total Cotas Regulares"
    )
    total_receitas_extras = models.DecimalField(
        max_digits=18, decimal_places=2, verbose_name="Total Receitas Extras / Outras"
    )
    total_receitas = models.DecimalField(
        max_digits=18, decimal_places=2, verbose_name="Total das Receitas"
    )
    subtotal = models.DecimalField(
        max_digits=18, decimal_places=2, verbose_name="Subtotal (Saldo Anterior + Receitas)"
    )
    total_despesas_fixas = models.DecimalField(
        max_digits=18, decimal_places=2, verbose_name="Total Despesas Fixas"
    )
    total_despesas_variaveis = models.DecimalField(
        max_digits=18, decimal_places=2, verbose_name="Total Despesas Variáveis"
    )
    total_despesas = models.DecimalField(
        max_digits=18, decimal_places=2, verbose_name="Total das Despesas"
    )
    saldo_mes = models.DecimalField(
        max_digits=18, decimal_places=2, verbose_name="Saldo Mês (Subtotal - Despesas)"
    )
    total_saldo_bancario = models.DecimalField(
        max_digits=18, decimal_places=2, verbose_name="Total do Saldo Bancário"
    )
    diferenca_saldo = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal("0.00"), verbose_name="Diferença de Saldo"
    )
    diferenca_em_cotas = models.DecimalField(
        max_digits=8, decimal_places=2, default=Decimal("0.00"), verbose_name="Diferença em Cotas"
    )
    observacao_diferenca = models.TextField(
        blank=True, verbose_name="Texto Explicativo da Diferença"
    )
    fechado_em = models.DateTimeField(
        verbose_name="Data/Hora do Fechamento"
    )
    fechado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Usuário Responsável pelo Fechamento"
    )

    class Meta:
        verbose_name = "Snapshot de Saldo do Período"
        verbose_name_plural = "Snapshots de Saldo dos Períodos"

    def __str__(self):
        return f"Snapshot {self.periodo.mes_referencia_rotulo} - Saldo Mês: R$ {self.saldo_mes}"


class AuditLog(TimeStampedModel):
    class AcaoAudit(models.TextChoices):
        CREATE = "CREATE", "Criação"
        UPDATE = "UPDATE", "Atualização"
        DELETE = "DELETE", "Exclusão"
        FECHAR = "FECHAR", "Fechamento de Período"
        PUBLICAR = "PUBLICAR", "Publicação de Período"
        REABRIR = "REABRIR", "Reabertura de Período"

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="logs_auditoria_financeira",
        verbose_name="Usuário"
    )
    condominio = models.ForeignKey(
        "core.Condominio",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="logs_auditoria_financeira",
        verbose_name="Condomínio"
    )
    entidade = models.CharField(max_length=60, verbose_name="Entidade")
    registro_id = models.CharField(max_length=60, verbose_name="ID do Registro")
    acao = models.CharField(max_length=20, choices=AcaoAudit.choices, verbose_name="Ação")
    dados_anteriores = models.JSONField(null=True, blank=True, encoder=DjangoJSONEncoder, verbose_name="Dados Anteriores")
    dados_novos = models.JSONField(null=True, blank=True, encoder=DjangoJSONEncoder, verbose_name="Dados Novos")
    detalhes = models.TextField(blank=True, verbose_name="Detalhes Adicionais")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="Endereço IP")

    class Meta:
        verbose_name = "Log de Auditoria Financeira"
        verbose_name_plural = "Logs de Auditoria Financeira"
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.acao}] {self.entidade} #{self.registro_id} por {self.usuario}"


# ---------------------------------------------------------------------------
# Módulo de Inadimplência, Cobrança e Nada Consta
# ---------------------------------------------------------------------------
class ParametroCobranca(TimeStampedModel):
    class TipoMulta(models.TextChoices):
        FIXO = "FIXO", "Valor Fixo (R$)"
        PERCENTUAL = "PERCENTUAL", "Percentual (%)"

    condominio = models.ForeignKey(
        "core.Condominio",
        on_delete=models.CASCADE,
        related_name="parametros_cobranca",
        verbose_name="Condomínio",
    )
    data_inicio = models.DateField(
        default=datetime.date(2024, 1, 1),
        verbose_name="Data Início da Vigência",
        help_text="Data inicial em que esta regra passa a vigorar (ex: 2024-01-01)",
    )
    data_fim = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data Fim da Vigência",
        help_text="Data final da vigência. Se em branco, é a regra atual ativa.",
    )
    tipo_multa = models.CharField(
        max_length=20,
        choices=TipoMulta.choices,
        default=TipoMulta.FIXO,
        verbose_name="Tipo de Multa",
    )
    valor_multa = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal("10.00"),
        verbose_name="Valor / Percentual da Multa",
        help_text="Se Fixo: R$ 10.00; Se Percentual: 2.00 para 2%",
    )
    percentual_juros_dia = models.DecimalField(
        max_digits=6,
        decimal_places=4,
        default=Decimal("0.0024"),
        verbose_name="Juros por Dia (Fator)",
        help_text="Ex: 0.0024 representa 0,24% ao dia (aproximadamente 2% ao mês em juros pro-rata)",
    )
    prazo_negociacao_info = models.CharField(
        max_length=255,
        default="O PRAZO PARA NEGOCIAÇÃO OU RENEGOCIAÇÃO DE DÍVIDAS ENCERRA-SE NO FINAL DESTE MÊS.",
        verbose_name="Texto: Prazo de Negociação",
    )
    aviso_protesto_info = models.CharField(
        max_length=255,
        default="OS TÍTULOS VENCIDOS E NÃO PAGOS SERÃO PROTESTADOS.",
        verbose_name="Texto: Aviso de Protesto",
    )
    aviso_ajuizamento_info = models.CharField(
        max_length=255,
        default="DÉBITOS COM 6 (SEIS) OU MAIS PARCELAS EM ATRASO ESTÃO SUJEITOS A AJUIZAMENTO.",
        verbose_name="Texto: Aviso de Ajuizamento",
    )
    qtd_parcelas_ajuizamento = models.IntegerField(
        default=6,
        verbose_name="Qtd. Mínima de Parcelas para Ajuizamento",
    )
    email_cobranca = models.EmailField(
        default="condominiohortenciasiii@gmail.com",
        verbose_name="E-mail de Contato para Cobrança",
    )
    telefone_cobranca = models.CharField(
        max_length=30,
        blank=True,
        default="",
        verbose_name="Telefone / WhatsApp de Contato",
    )
    mensagem_email_padrao = models.TextField(
        blank=True,
        default=(
            "Prezado(a) condômino(a),\n\n"
            "Constatamos em nosso sistema títulos pendentes referentes à sua unidade no Condomínio Hortências III.\n"
            "Em anexo enviamos o demonstrativo atualizado de débitos com os cálculos de encargos.\n\n"
            "Caso já tenha realizado o pagamento ou identifique alguma inconsistência, por favor nos responda com os devidos comprovantes para atualização cadastral.\n\n"
            "Estamos à disposição para esclarecimentos e propostas de negociação.\n\n"
            "Atenciosamente,\nAdministração do Condomínio"
        ),
        verbose_name="Mensagem Padrão do E-mail de Cobrança",
    )

    class Meta:
        verbose_name = "Parâmetro de Cobrança do Condomínio"
        verbose_name_plural = "Parâmetros de Cobrança do Condomínio"
        ordering = ["-data_inicio"]

    def __str__(self):
        status_vig = "Ativa" if not self.data_fim else f"Até {self.data_fim}"
        return f"Parâmetro Cobrança ({self.data_inicio} - {status_vig}) - {self.condominio.nome}"

    def __str__(self):
        return f"Parâmetros de Cobrança - {self.condominio.nome}"


class AcordoDescontoCota(TimeStampedModel):
    class StatusAcordo(models.TextChoices):
        PENDENTE = "PENDENTE", "Pendente"
        PAGO = "PAGO", "Quitado / Pago"
        CANCELADO = "CANCELADO", "Cancelado"

    cota = models.ForeignKey(
        ReceitaCota,
        on_delete=models.CASCADE,
        related_name="acordos",
        verbose_name="Cota em Cobrança",
    )
    sindico_autorizador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="acordos_autorizados",
        verbose_name="Síndico / Usuário que Autorizou",
    )
    valor_acordado = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Valor Acordado (R$)",
        help_text="Valor final a pagar acordado (ex: apenas a cota original sem juros/multa)",
    )
    desconto_juros_multa = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Desconto Concedido em Encargos (R$)",
    )
    data_limite_pagamento = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data Limite para Quitação do Acordo",
    )
    data_pagamento = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data Efetiva de Pagamento",
    )
    status = models.CharField(
        max_length=20,
        choices=StatusAcordo.choices,
        default=StatusAcordo.PENDENTE,
        verbose_name="Status do Acordo",
    )
    justificativa_observacao = models.TextField(
        blank=True,
        verbose_name="Justificativa / Anotação da Negociação",
    )

    class Meta:
        verbose_name = "Acordo / Desconto em Cota"
        verbose_name_plural = "Acordos / Descontos em Cotas"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Acordo Cota {self.cota.unidade.identificador} - R$ {self.valor_acordado} ({self.get_status_display()})"


class CertidaoNadaConsta(TimeStampedModel):
    condominio = models.ForeignKey(
        "core.Condominio",
        on_delete=models.CASCADE,
        related_name="certidoes_nada_consta",
        verbose_name="Condomínio",
    )
    unidade = models.ForeignKey(
        "core.Unidade",
        on_delete=models.CASCADE,
        related_name="certidoes_nada_consta",
        verbose_name="Unidade",
    )
    solicitante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="certidoes_emitidas",
        verbose_name="Emitido por (Usuário)",
    )
    codigo_autenticacao = models.CharField(
        max_length=64,
        unique=True,
        verbose_name="Código de Autenticação",
        help_text="Código único para validação de veracidade da certidão",
    )
    data_emissao = models.DateField(
        auto_now_add=True,
        verbose_name="Data de Emissão",
    )
    data_validade = models.DateField(
        verbose_name="Data de Validade (Fim do Mês)",
    )
    # Dados congelados no momento da emissão
    proprietario_nome = models.CharField(max_length=150, verbose_name="Nome do Proprietário")
    proprietario_cpf = models.CharField(max_length=20, blank=True, verbose_name="CPF do Proprietário")
    sindico_nome = models.CharField(max_length=150, verbose_name="Nome do Síndico")
    sindico_cpf = models.CharField(max_length=20, blank=True, verbose_name="CPF do Síndico")
    sindico_endereco = models.CharField(max_length=255, blank=True, verbose_name="Endereço/Unidade do Síndico")
    
    ultima_cota_referencia = models.CharField(
        max_length=60,
        blank=True,
        verbose_name="Mês/Ano da Última Cota Paga",
        help_text="Ex: JULHO/2024",
    )
    ultima_cota_vencimento = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data de Vencimento da Última Cota",
    )
    arquivo_pdf = models.FileField(
        upload_to="certidoes_nada_consta/%Y/%m/",
        null=True,
        blank=True,
        verbose_name="Arquivo PDF Gerado",
    )

    class Meta:
        verbose_name = "Declaração de Nada Consta"
        verbose_name_plural = "Declarações de Nada Consta"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Nada Consta - {self.unidade.identificador} ({self.codigo_autenticacao[:8]}...)"


class HistoricoNotificacaoCobranca(TimeStampedModel):
    condominio = models.ForeignKey(
        "core.Condominio",
        on_delete=models.CASCADE,
        related_name="notificacoes_cobranca",
        verbose_name="Condomínio",
    )
    unidade = models.ForeignKey(
        "core.Unidade",
        on_delete=models.CASCADE,
        related_name="notificacoes_cobranca",
        verbose_name="Unidade",
    )
    enviado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cobrancas_enviadas",
        verbose_name="Enviado por",
    )
    destinatario_nome = models.CharField(max_length=150, verbose_name="Nome Destinatário")
    destinatario_email = models.CharField(max_length=255, verbose_name="E-mails Destinatários")
    assunto = models.CharField(max_length=255, verbose_name="Assunto")
    mensagem_enviada = models.TextField(verbose_name="Mensagem Enviada (Corpo do E-mail)")
    valor_total_devedor = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Valor Total Devedor Notificado",
    )
    qtd_titulos = models.IntegerField(default=1, verbose_name="Quantidade de Títulos em Atraso")
    status_envio = models.CharField(
        max_length=30,
        default="ENVIADO",
        verbose_name="Status do Envio",
    )
    erro_detalhe = models.TextField(blank=True, verbose_name="Detalhes de Erro (se houver)")
    arquivo_pdf = models.FileField(
        upload_to="cobrancas_enviadas/%Y/%m/",
        null=True,
        blank=True,
        verbose_name="PDF Anexado ao Envio",
    )

    class Meta:
        verbose_name = "Histórico de Notificação de Cobrança"
        verbose_name_plural = "Históricos de Notificações de Cobrança"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Notificação {self.unidade.identificador} em {self.created_at.strftime('%d/%m/%Y %H:%M')}"

