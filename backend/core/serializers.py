from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from django.db import transaction

from .models import (
    Condominio,
    Unidade,
    Pessoa,
    VinculoPessoaUnidade,
    Funcionario,
    CargoCondominial,
    Perfil,
    UsuarioCondominio,
)

Usuario = get_user_model()


# ---------------------------------------------------------------------------
# Serializer de Autenticação JWT Customizado
# ---------------------------------------------------------------------------
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["username"] = user.username
        token["email"] = user.email
        token["is_superuser"] = user.is_superuser
        
        # Pega os perfis ativos do usuário
        vinculos = user.condominios.filter(ativo=True).select_related("perfil", "condominio")
        perfis = list(set([v.perfil.codigo for v in vinculos]))
        token["perfis"] = perfis
        
        # Define perfil prioritário para o token
        prioridade = ["SINDICO", "SUBSINDICO", "CONSELHEIRO", "CONDOMINO", "FUNCIONARIO"]
        perfil_principal = "CONDOMINO"
        for p in prioridade:
            if p in perfis:
                perfil_principal = p
                break
        if user.is_superuser:
            perfil_principal = "SINDICO"
            
        token["perfil_principal"] = perfil_principal
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user

        vinculos_qs = user.condominios.filter(ativo=True).select_related("condominio", "perfil")
        vinculos_data = [
            {
                "condominio_id": v.condominio.id,
                "condominio_nome": v.condominio.nome,
                "perfil_codigo": v.perfil.codigo,
                "perfil_nome": v.perfil.nome,
            }
            for v in vinculos_qs
        ]

        perfis = list(set([v["perfil_codigo"] for v in vinculos_data]))
        prioridade = ["SINDICO", "SUBSINDICO", "CONSELHEIRO", "CONDOMINO", "FUNCIONARIO"]
        perfil_principal = "CONDOMINO"
        for p in prioridade:
            if p in perfis:
                perfil_principal = p
                break
        if user.is_superuser:
            perfil_principal = "SINDICO"
            if not perfis:
                perfis = ["SINDICO"]

        data["user"] = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_superuser": user.is_superuser,
            "pessoa_id": user.pessoa_id if hasattr(user, "pessoa") and user.pessoa else None,
            "pessoa_nome": user.pessoa.nome if hasattr(user, "pessoa") and user.pessoa else None,
            "perfis": perfis,
            "perfil_principal": perfil_principal,
            "vinculos_condominios": vinculos_data,
        }
        return data


# ---------------------------------------------------------------------------
# Perfil Serializer
# ---------------------------------------------------------------------------
class PerfilSerializer(serializers.ModelSerializer):
    class Meta:
        model = Perfil
        fields = ["codigo", "nome", "descricao"]


# ---------------------------------------------------------------------------
# Condomínio Serializer
# ---------------------------------------------------------------------------
class CondominioSerializer(serializers.ModelSerializer):
    total_unidades = serializers.SerializerMethodField()
    total_funcionarios = serializers.SerializerMethodField()

    class Meta:
        model = Condominio
        fields = [
            "id",
            "nome",
            "cnpj",
            "endereco",
            "numero",
            "complemento",
            "bairro",
            "cidade",
            "uf",
            "cep",
            "ativo",
            "total_unidades",
            "total_funcionarios",
            "created_at",
            "updated_at",
        ]

    def get_total_unidades(self, obj):
        return obj.unidades.count()

    def get_total_funcionarios(self, obj):
        return obj.funcionarios.filter(ativo=True).count()


# ---------------------------------------------------------------------------
# Pessoa Serializer
# ---------------------------------------------------------------------------
class PessoaSerializer(serializers.ModelSerializer):
    tem_usuario = serializers.SerializerMethodField()
    usuario_id = serializers.SerializerMethodField()
    condominio_id = serializers.SerializerMethodField()
    condominio_nome = serializers.SerializerMethodField()
    unidade_identificador = serializers.SerializerMethodField()
    unidades_vinculadas = serializers.SerializerMethodField()

    # Campos de escrita para vincular pessoa a condomínio/unidade
    unidade_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    tipo_vinculo = serializers.CharField(write_only=True, required=False, default="MORADOR")
    responsavel = serializers.BooleanField(write_only=True, required=False, default=False)
    data_inicio_vinculo = serializers.DateField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Pessoa
        fields = [
            "id",
            "nome",
            "cpf",
            "telefone",
            "email",
            "data_nascimento",
            "tem_usuario",
            "usuario_id",
            "condominio_id",
            "condominio_nome",
            "unidade_identificador",
            "unidades_vinculadas",
            "unidade_id",
            "tipo_vinculo",
            "responsavel",
            "data_inicio_vinculo",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        user = self.context.get("request").user if self.context.get("request") else None
        is_superuser = user and user.is_superuser

        unidade_id = attrs.get("unidade_id")
        responsavel = attrs.get("responsavel", False)

        # Na criação, unidade_id é obrigatório para usuários comuns
        if not self.instance and not is_superuser and not unidade_id:
            raise serializers.ValidationError({
                "unidade_id": "O vínculo com a unidade do condomínio é obrigatório no cadastro da pessoa."
            })

        # Se for informado que é responsável, valida duplicidade de responsável ativo
        if unidade_id and responsavel:
            qs = VinculoPessoaUnidade.objects.filter(
                unidade_id=unidade_id, responsavel=True, data_fim__isnull=True
            )
            if self.instance:
                qs = qs.exclude(pessoa=self.instance)
            if qs.exists():
                raise serializers.ValidationError({
                    "responsavel": "Esta unidade já possui um responsável ativo cadastrado. Desmarque ou altere o anterior."
                })

        return attrs

    def get_tem_usuario(self, obj):
        return hasattr(obj, "usuario") and obj.usuario is not None

    def get_usuario_id(self, obj):
        return obj.usuario.id if hasattr(obj, "usuario") and obj.usuario else None

    def get_condominio_id(self, obj):
        v = obj.vinculos_unidade.filter(data_fim__isnull=True).select_related("unidade__condominio").first()
        if v and v.unidade and v.unidade.condominio:
            return v.unidade.condominio.id
        f = getattr(obj, "dados_funcionario", None)
        if f and hasattr(f, "first") and f.filter(ativo=True).exists():
            return f.filter(ativo=True).first().condominio_id
        return None

    def get_condominio_nome(self, obj):
        v = obj.vinculos_unidade.filter(data_fim__isnull=True).select_related("unidade__condominio").first()
        if v and v.unidade and v.unidade.condominio:
            return v.unidade.condominio.nome
        f = getattr(obj, "dados_funcionario", None)
        if f and hasattr(f, "first") and f.filter(ativo=True).exists():
            return f.filter(ativo=True).first().condominio.nome
        return None

    def get_unidade_identificador(self, obj):
        v = obj.vinculos_unidade.filter(data_fim__isnull=True).select_related("unidade").first()
        return v.unidade.identificador if v and v.unidade else None

    def get_unidades_vinculadas(self, obj):
        vinculos = obj.vinculos_unidade.filter(data_fim__isnull=True).select_related("unidade__condominio")
        return [
            {
                "vinculo_id": v.id,
                "unidade_id": v.unidade.id,
                "unidade_identificador": v.unidade.identificador,
                "condominio_id": v.unidade.condominio.id,
                "condominio_nome": v.unidade.condominio.nome,
                "tipo": v.tipo,
                "responsavel": v.responsavel,
            }
            for v in vinculos
        ]

    def create(self, validated_data):
        unidade_id = validated_data.pop("unidade_id", None)
        tipo_vinculo = validated_data.pop("tipo_vinculo", "MORADOR")
        responsavel = validated_data.pop("responsavel", False)
        data_inicio = validated_data.pop("data_inicio_vinculo", None)

        pessoa = super().create(validated_data)

        # Se unidade_id foi informada, cria automaticamente o vínculo da pessoa com a unidade
        if unidade_id:
            from datetime import date
            VinculoPessoaUnidade.objects.create(
                pessoa=pessoa,
                unidade_id=unidade_id,
                tipo=tipo_vinculo,
                responsavel=responsavel,
                data_inicio=data_inicio or date.today()
            )

        return pessoa

    def update(self, instance, validated_data):
        unidade_id = validated_data.pop("unidade_id", None)
        tipo_vinculo = validated_data.pop("tipo_vinculo", None)
        responsavel = validated_data.pop("responsavel", None)
        data_inicio = validated_data.pop("data_inicio_vinculo", None)

        pessoa = super().update(instance, validated_data)

        if unidade_id:
            from datetime import date
            # Procura vínculo ativo
            vinculo = VinculoPessoaUnidade.objects.filter(pessoa=pessoa, data_fim__isnull=True).first()
            if vinculo:
                vinculo.unidade_id = unidade_id
                if tipo_vinculo:
                    vinculo.tipo = tipo_vinculo
                if responsavel is not None:
                    vinculo.responsavel = responsavel
                vinculo.save()
            else:
                VinculoPessoaUnidade.objects.create(
                    pessoa=pessoa,
                    unidade_id=unidade_id,
                    tipo=tipo_vinculo or "MORADOR",
                    responsavel=responsavel if responsavel is not None else False,
                    data_inicio=data_inicio or date.today()
                )

        return pessoa


# ---------------------------------------------------------------------------
# Vínculo Pessoa-Unidade Serializer
# ---------------------------------------------------------------------------
class VinculoPessoaUnidadeSerializer(serializers.ModelSerializer):
    pessoa_nome = serializers.CharField(source="pessoa.nome", read_only=True)
    pessoa_cpf = serializers.CharField(source="pessoa.cpf", read_only=True)
    unidade_identificador = serializers.CharField(source="unidade.identificador", read_only=True)
    unidade_bloco = serializers.CharField(source="unidade.bloco_torre", read_only=True)
    condominio_id = serializers.IntegerField(source="unidade.condominio.id", read_only=True)
    condominio_nome = serializers.CharField(source="unidade.condominio.nome", read_only=True)
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)

    class Meta:
        model = VinculoPessoaUnidade
        fields = [
            "id",
            "pessoa",
            "pessoa_nome",
            "pessoa_cpf",
            "unidade",
            "unidade_identificador",
            "unidade_bloco",
            "condominio_id",
            "condominio_nome",
            "tipo",
            "tipo_display",
            "data_inicio",
            "data_fim",
            "responsavel",
            "descricao_outro",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        tipo = attrs.get("tipo", getattr(self.instance, "tipo", None))
        descricao_outro = attrs.get("descricao_outro", getattr(self.instance, "descricao_outro", ""))
        if tipo == VinculoPessoaUnidade.TipoVinculo.OUTRO and not descricao_outro:
            raise serializers.ValidationError(
                {"descricao_outro": "Descreva o tipo de vínculo quando selecionar 'Outro'."}
            )

        # Checar se já existe responsável ativo para a unidade
        responsavel = attrs.get("responsavel", getattr(self.instance, "responsavel", False))
        data_fim = attrs.get("data_fim", getattr(self.instance, "data_fim", None))
        unidade = attrs.get("unidade", getattr(self.instance, "unidade", None))

        if responsavel and not data_fim and unidade:
            qs = VinculoPessoaUnidade.objects.filter(
                unidade=unidade, responsavel=True, data_fim__isnull=True
            )
            if self.instance:
                qs = qs.exclude(id=self.instance.id)
            if qs.exists():
                raise serializers.ValidationError(
                    {"responsavel": f"A unidade já possui um responsável ativo ({qs.first().pessoa.nome}). Desative o anterior primeiro."}
                )

        return attrs


# ---------------------------------------------------------------------------
# Unidade Serializer
# ---------------------------------------------------------------------------
class UnidadeSerializer(serializers.ModelSerializer):
    condominio_nome = serializers.CharField(source="condominio.nome", read_only=True)
    moradores_ativos = serializers.SerializerMethodField()

    class Meta:
        model = Unidade
        fields = [
            "id",
            "condominio",
            "condominio_nome",
            "bloco_torre",
            "identificador",
            "fracao_ideal",
            "area_privativa",
            "observacoes",
            "moradores_ativos",
            "created_at",
            "updated_at",
        ]

    def get_moradores_ativos(self, obj):
        vinculos = obj.vinculos.filter(data_fim__isnull=True).select_related("pessoa")
        return [
            {
                "id": v.id,
                "pessoa_id": v.pessoa.id,
                "pessoa_nome": v.pessoa.nome,
                "tipo": v.get_tipo_display(),
                "responsavel": v.responsavel,
            }
            for v in vinculos
        ]


# ---------------------------------------------------------------------------
# Funcionário Serializer
# ---------------------------------------------------------------------------
class FuncionarioSerializer(serializers.ModelSerializer):
    pessoa_nome = serializers.CharField(source="pessoa.nome", read_only=True)
    pessoa_cpf = serializers.CharField(source="pessoa.cpf", read_only=True)
    condominio_nome = serializers.CharField(source="condominio.nome", read_only=True)
    cargo_display = serializers.CharField(source="get_cargo_display", read_only=True)

    class Meta:
        model = Funcionario
        fields = [
            "id",
            "pessoa",
            "pessoa_nome",
            "pessoa_cpf",
            "condominio",
            "condominio_nome",
            "cargo",
            "cargo_display",
            "endereco_proprio",
            "data_admissao",
            "data_demissao",
            "ativo",
            "created_at",
            "updated_at",
        ]


# ---------------------------------------------------------------------------
# Cargo Condominial (Mandato) Serializer
# ---------------------------------------------------------------------------
class CargoCondominialSerializer(serializers.ModelSerializer):
    pessoa_nome = serializers.CharField(source="pessoa.nome", read_only=True)
    pessoa_cpf = serializers.CharField(source="pessoa.cpf", read_only=True)
    condominio_nome = serializers.CharField(source="condominio.nome", read_only=True)
    cargo_display = serializers.CharField(source="get_cargo_display", read_only=True)

    class Meta:
        model = CargoCondominial
        fields = [
            "id",
            "condominio",
            "condominio_nome",
            "pessoa",
            "pessoa_nome",
            "pessoa_cpf",
            "cargo",
            "cargo_display",
            "data_inicio",
            "data_fim",
            "ativo",
            "created_at",
            "updated_at",
        ]


# ---------------------------------------------------------------------------
# Vínculo Usuário-Condomínio Serializer
# ---------------------------------------------------------------------------
class UsuarioCondominioSerializer(serializers.ModelSerializer):
    usuario_username = serializers.CharField(source="usuario.username", read_only=True)
    condominio_nome = serializers.CharField(source="condominio.nome", read_only=True)
    perfil_nome = serializers.CharField(source="perfil.nome", read_only=True)

    class Meta:
        model = UsuarioCondominio
        fields = [
            "id",
            "usuario",
            "usuario_username",
            "condominio",
            "condominio_nome",
            "perfil",
            "perfil_nome",
            "ativo",
            "created_at",
            "updated_at",
        ]


# ---------------------------------------------------------------------------
# Usuário Serializer (Cadastro / Edição / Listagem)
# ---------------------------------------------------------------------------
class UsuarioSerializer(serializers.ModelSerializer):
    pessoa_nome = serializers.CharField(source="pessoa.nome", read_only=True)
    password = serializers.CharField(write_only=True, required=False)
    vinculos_condominios = UsuarioCondominioSerializer(source="condominios", many=True, read_only=True)

    class Meta:
        model = Usuario
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "pessoa",
            "pessoa_nome",
            "is_active",
            "is_staff",
            "is_superuser",
            "password",
            "vinculos_condominios",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user = Usuario(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance
