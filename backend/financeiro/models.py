from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from decimal import Decimal


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
