from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator


# ---------------------------------------------------------------------------
# Validators reutilizáveis
# ---------------------------------------------------------------------------
cpf_validator = RegexValidator(
    regex=r"^\d{3}\.\d{3}\.\d{3}-\d{2}$",
    message="CPF deve estar no formato 000.000.000-00.",
)
cnpj_validator = RegexValidator(
    regex=r"^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$",
    message="CNPJ deve estar no formato 00.000.000/0000-00.",
)
cep_validator = RegexValidator(
    regex=r"^\d{5}-\d{3}$",
    message="CEP deve estar no formato 00000-000.",
)


# ---------------------------------------------------------------------------
# Mixin de auditoria
# ---------------------------------------------------------------------------
class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        abstract = True


# ---------------------------------------------------------------------------
# Condomínio
# ---------------------------------------------------------------------------
class Condominio(TimeStampedModel):
    nome = models.CharField(max_length=150, verbose_name="Nome do Condomínio")
    cnpj = models.CharField(
        max_length=18,
        blank=True,
        null=True,
        unique=True,
        validators=[cnpj_validator],
        verbose_name="CNPJ",
    )
    endereco = models.CharField(max_length=255, verbose_name="Endereço / Logradouro")
    numero = models.CharField(max_length=20, blank=True, verbose_name="Número")
    complemento = models.CharField(max_length=50, blank=True, verbose_name="Complemento")
    bairro = models.CharField(max_length=100, blank=True, verbose_name="Bairro")
    cidade = models.CharField(max_length=100, default="São Paulo", verbose_name="Cidade")
    uf = models.CharField(max_length=2, default="SP", verbose_name="UF")
    cep = models.CharField(
        max_length=9, blank=True, validators=[cep_validator], verbose_name="CEP"
    )
    ativo = models.BooleanField(default=True, verbose_name="Ativo")

    class Meta:
        verbose_name = "Condomínio"
        verbose_name_plural = "Condomínios"
        ordering = ["nome"]

    def __str__(self):
        return self.nome

    def save(self, *args, **kwargs):
        # Normaliza string vazia para None (evita conflito em campos unique)
        if not self.cnpj:
            self.cnpj = None
        super().save(*args, **kwargs)


# ---------------------------------------------------------------------------
# Unidade
# ---------------------------------------------------------------------------
class Unidade(TimeStampedModel):
    condominio = models.ForeignKey(
        Condominio,
        on_delete=models.CASCADE,
        related_name="unidades",
        verbose_name="Condomínio",
    )
    bloco_torre = models.CharField(max_length=30, blank=True, verbose_name="Bloco / Torre")
    identificador = models.CharField(
        max_length=50, verbose_name="Identificador (ex: Apto 101, Casa 04)"
    )
    fracao_ideal = models.DecimalField(
        max_digits=8,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name="Fração Ideal",
        help_text="Obrigatório para rateio financeiro. Deixe em branco se ainda não definido.",
    )
    area_privativa = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Área Privativa (m²)",
    )
    observacoes = models.TextField(blank=True, verbose_name="Observações")

    class Meta:
        verbose_name = "Unidade"
        verbose_name_plural = "Unidades"
        constraints = [
            models.UniqueConstraint(
                fields=["condominio", "bloco_torre", "identificador"],
                name="unique_unidade_por_condominio",
            )
        ]
        ordering = ["bloco_torre", "identificador"]

    def __str__(self):
        bloco = f" - Bloco {self.bloco_torre}" if self.bloco_torre else ""
        return f"{self.identificador}{bloco} ({self.condominio.nome})"

    def clean(self):
        # Normaliza identificador e bloco para evitar duplicidade por caixa/espaço
        if self.identificador:
            self.identificador = " ".join(self.identificador.upper().split())
        if self.bloco_torre:
            self.bloco_torre = " ".join(self.bloco_torre.upper().split())

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


# ---------------------------------------------------------------------------
# Pessoa
# ---------------------------------------------------------------------------
class Pessoa(TimeStampedModel):
    nome = models.CharField(max_length=150, verbose_name="Nome Completo")
    cpf = models.CharField(
        max_length=14,
        unique=True,
        blank=True,
        null=True,
        validators=[cpf_validator],
        verbose_name="CPF",
    )
    telefone = models.CharField(max_length=20, blank=True, verbose_name="Telefone")
    email = models.EmailField(blank=True, null=True, verbose_name="E-mail")
    data_nascimento = models.DateField(
        blank=True, null=True, verbose_name="Data de Nascimento"
    )

    class Meta:
        verbose_name = "Pessoa"
        verbose_name_plural = "Pessoas"
        ordering = ["nome"]

    def __str__(self):
        return f"{self.nome} ({self.cpf or 'Sem CPF'})"

    def save(self, *args, **kwargs):
        if not self.cpf:
            self.cpf = None
        super().save(*args, **kwargs)


# ---------------------------------------------------------------------------
# Vínculo Pessoa-Unidade
# ---------------------------------------------------------------------------
class VinculoPessoaUnidade(TimeStampedModel):
    class TipoVinculo(models.TextChoices):
        PROPRIETARIO = "PROPRIETARIO", "Proprietário"
        INQUILINO = "INQUILINO", "Inquilino"
        MORADOR = "MORADOR", "Morador / Dependente"
        OUTRO = "OUTRO", "Outro"

    pessoa = models.ForeignKey(
        Pessoa,
        on_delete=models.CASCADE,
        related_name="vinculos_unidade",
        verbose_name="Pessoa",
    )
    unidade = models.ForeignKey(
        Unidade,
        on_delete=models.CASCADE,
        related_name="vinculos",
        verbose_name="Unidade",
    )
    tipo = models.CharField(
        max_length=20,
        choices=TipoVinculo.choices,
        default=TipoVinculo.MORADOR,
        verbose_name="Tipo de Vínculo",
    )
    data_inicio = models.DateField(verbose_name="Data Início")
    data_fim = models.DateField(
        null=True, blank=True, verbose_name="Data Fim (em branco se ativo)"
    )
    responsavel = models.BooleanField(
        default=False,
        verbose_name="Responsável pela Unidade (financeiro/legal)",
    )
    descricao_outro = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Descrição (quando tipo = Outro)",
    )

    class Meta:
        verbose_name = "Vínculo Pessoa-Unidade"
        verbose_name_plural = "Vínculos Pessoa-Unidade"
        ordering = ["-data_inicio"]
        constraints = [
            # Um único responsável ativo por unidade
            models.UniqueConstraint(
                fields=["unidade"],
                condition=models.Q(responsavel=True, data_fim__isnull=True),
                name="unique_responsavel_ativo_por_unidade",
            ),
            # Evita vínculo ativo duplicado da mesma pessoa/tipo na mesma unidade
            models.UniqueConstraint(
                fields=["pessoa", "unidade", "tipo"],
                condition=models.Q(data_fim__isnull=True),
                name="unique_vinculo_ativo_pessoa_unidade_tipo",
            ),
        ]

    def __str__(self):
        status = "Ativo" if not self.data_fim else f"Até {self.data_fim}"
        return f"{self.pessoa.nome} - {self.unidade} ({self.get_tipo_display()} - {status})"

    def clean(self):
        if self.tipo == self.TipoVinculo.OUTRO and not self.descricao_outro:
            raise ValidationError(
                {"descricao_outro": "Descreva o tipo de vínculo quando selecionar 'Outro'."}
            )


# ---------------------------------------------------------------------------
# Funcionário
# ---------------------------------------------------------------------------
class Funcionario(TimeStampedModel):
    class CargoFuncionario(models.TextChoices):
        ZELADOR = "ZELADOR", "Zelador(a)"
        PORTEIRO = "PORTEIRO", "Porteiro(a)"
        SERVICOS_GERAIS = "SERVICOS_GERAIS", "Serviços Gerais / Limpeza"
        MANUTENCAO = "MANUTENCAO", "Manutenção"
        ADMINISTRATIVO = "ADMINISTRATIVO", "Administrativo"
        OUTRO = "OUTRO", "Outro"

    pessoa = models.ForeignKey(
        Pessoa,
        on_delete=models.CASCADE,
        related_name="dados_funcionario",
        verbose_name="Pessoa",
    )
    condominio = models.ForeignKey(
        Condominio,
        on_delete=models.CASCADE,
        related_name="funcionarios",
        verbose_name="Condomínio",
    )
    cargo = models.CharField(
        max_length=30, choices=CargoFuncionario.choices, verbose_name="Cargo"
    )
    endereco_proprio = models.TextField(verbose_name="Endereço Residencial do Funcionário")
    data_admissao = models.DateField(verbose_name="Data de Admissão")
    data_demissao = models.DateField(
        null=True, blank=True, verbose_name="Data de Demissão"
    )
    ativo = models.BooleanField(default=True, verbose_name="Ativo")

    class Meta:
        verbose_name = "Funcionário"
        verbose_name_plural = "Funcionários"
        ordering = ["-ativo", "pessoa__nome"]
        constraints = [
            # Evita funcionário ativo duplicado no mesmo cargo/condomínio
            models.UniqueConstraint(
                fields=["pessoa", "condominio", "cargo"],
                condition=models.Q(ativo=True),
                name="unique_funcionario_ativo_por_cargo",
            ),
        ]

    def __str__(self):
        return f"{self.pessoa.nome} - {self.get_cargo_display()} ({self.condominio.nome})"


# ---------------------------------------------------------------------------
# Cargo Condominial / Mandato
# ---------------------------------------------------------------------------
class CargoCondominial(TimeStampedModel):
    class TipoCargo(models.TextChoices):
        SINDICO = "SINDICO", "Síndico(a)"
        SUBSINDICO = "SUBSINDICO", "Subsíndico(a)"
        CONSELHEIRO_FISCAL = "CONSELHEIRO_FISCAL", "Conselheiro(a) Fiscal"
        CONSELHEIRO_CONSULTIVO = "CONSELHEIRO_CONSULTIVO", "Conselheiro(a) Consultivo"
        OUTRO = "OUTRO", "Outro"

    condominio = models.ForeignKey(
        Condominio,
        on_delete=models.CASCADE,
        related_name="mandatos",
        verbose_name="Condomínio",
    )
    pessoa = models.ForeignKey(
        Pessoa,
        on_delete=models.CASCADE,
        related_name="cargos_gestao",
        verbose_name="Pessoa",
    )
    cargo = models.CharField(
        max_length=30, choices=TipoCargo.choices, verbose_name="Cargo de Gestão"
    )
    data_inicio = models.DateField(verbose_name="Início do Mandato")
    data_fim = models.DateField(null=True, blank=True, verbose_name="Fim do Mandato")
    ativo = models.BooleanField(default=True, verbose_name="Mandato Ativo")

    class Meta:
        verbose_name = "Cargo Condominial / Mandato"
        verbose_name_plural = "Cargos Condominiais / Mandatos"
        ordering = ["-data_inicio"]
        constraints = [
            # Só um mandato ativo por cargo/condomínio
            models.UniqueConstraint(
                fields=["condominio", "cargo"],
                condition=models.Q(ativo=True, data_fim__isnull=True),
                name="unique_cargo_ativo_por_condominio",
            ),
        ]

    def __str__(self):
        return f"{self.pessoa.nome} - {self.get_cargo_display()} em {self.condominio.nome}"


# ---------------------------------------------------------------------------
# Perfil
# ---------------------------------------------------------------------------
class Perfil(models.Model):
    class CodigoPerfil(models.TextChoices):
        SINDICO = "SINDICO", "Síndico"
        SUBSINDICO = "SUBSINDICO", "Subsíndico"
        CONSELHEIRO = "CONSELHEIRO", "Conselheiro"
        CONDOMINO = "CONDOMINO", "Condômino"
        FUNCIONARIO = "FUNCIONARIO", "Funcionário"

    codigo = models.CharField(
        max_length=20,
        choices=CodigoPerfil.choices,
        unique=True,
        primary_key=True,
        verbose_name="Código do Perfil",
    )
    nome = models.CharField(max_length=50, verbose_name="Nome de Exibição")
    descricao = models.TextField(blank=True, verbose_name="Descrição do Nível de Acesso")

    class Meta:
        verbose_name = "Perfil de Acesso"
        verbose_name_plural = "Perfis de Acesso"

    def __str__(self):
        return self.nome


# ---------------------------------------------------------------------------
# Usuário
# ---------------------------------------------------------------------------
class Usuario(AbstractUser, TimeStampedModel):
    pessoa = models.OneToOneField(
        Pessoa,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="usuario",
        verbose_name="Pessoa Vinculada",
    )

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"

    def __str__(self):
        return self.username


# ---------------------------------------------------------------------------
# Vínculo Usuário-Condomínio (multi-condomínio)
# ---------------------------------------------------------------------------
class UsuarioCondominio(TimeStampedModel):
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name="condominios",
        verbose_name="Usuário",
    )
    condominio = models.ForeignKey(
        Condominio,
        on_delete=models.CASCADE,
        related_name="usuarios",
        verbose_name="Condomínio",
    )
    perfil = models.ForeignKey(
        Perfil,
        on_delete=models.PROTECT,
        related_name="vinculos",
        verbose_name="Perfil de Acesso",
    )
    ativo = models.BooleanField(default=True, verbose_name="Ativo")

    class Meta:
        verbose_name = "Vínculo Usuário-Condomínio"
        verbose_name_plural = "Vínculos Usuário-Condomínio"
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "condominio"],
                name="unique_usuario_condominio",
            )
        ]
        ordering = ["usuario__username", "condominio__nome"]

    def __str__(self):
        return f"{self.usuario.username} - {self.condominio.nome} ({self.perfil.nome})"
