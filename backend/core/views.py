from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.core.mail import send_mail
from django.conf import settings

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
from .serializers import (
    CondominioSerializer,
    UnidadeSerializer,
    PessoaSerializer,
    VinculoPessoaUnidadeSerializer,
    FuncionarioSerializer,
    CargoCondominialSerializer,
    PerfilSerializer,
    UsuarioSerializer,
    UsuarioCondominioSerializer,
)
from .permissions import (
    IsSindico,
    IsSindicoOrSubSindico,
    CondominioModulePermission,
    CondominioGlobalPermission,
    UserManagementPermission,
    get_user_profiles,
)

Usuario = get_user_model()


def get_request_condominios(request):
    """
    Retorna a lista de IDs de condomínios que o usuário pode visualizar.
    - Se superuser e sem filtro: retorna None (indica que vê todos).
    - Se superuser com filtro (header X-Condominio-Id ou query param ?condominio=): retorna [id].
    - Se usuário regular: retorna apenas os condomínios aos quais ele tem vínculo ativo.
      Caso especifique um condomínio válido, retorna apenas aquele condomínio.
    """
    user = request.user
    if not user or not user.is_authenticated:
        return []

    cond_param = request.headers.get("X-Condominio-Id") or request.query_params.get("condominio")

    if user.is_superuser:
        if cond_param:
            try:
                return [int(cond_param)]
            except (ValueError, TypeError):
                pass
        return None

    user_condos = list(user.condominios.filter(ativo=True).values_list("condominio_id", flat=True))
    if cond_param:
        try:
            cid = int(cond_param)
            if cid in user_condos:
                return [cid]
        except (ValueError, TypeError):
            pass

    return user_condos


# ---------------------------------------------------------------------------
# Endpoint: /api/auth/register-condomino/ (Cadastro público pelo morador)
# ---------------------------------------------------------------------------
class RegisterCondominoView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        cpf = request.data.get("cpf", "").strip()
        username = request.data.get("username", "").strip()
        password = request.data.get("password", "").strip()
        email = request.data.get("email", "").strip()

        if not cpf:
            return Response(
                {"detail": "Informe o seu CPF para validação."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Remove caracteres especiais do CPF para busca flexível
        cpf_clean = "".join(filter(str.isdigit, cpf))

        # Busca a pessoa pelo CPF exato ou apenas números
        pessoa = Pessoa.objects.filter(cpf=cpf).first()
        if not pessoa and cpf_clean:
            pessoa = Pessoa.objects.filter(cpf=cpf_clean).first()

        if not pessoa and cpf_clean:
            # Tenta encontrar correspondente por números
            all_pessoas = Pessoa.objects.exclude(cpf__isnull=True).exclude(cpf="")
            for p in all_pessoas:
                if "".join(filter(str.isdigit, p.cpf or "")) == cpf_clean:
                    pessoa = p
                    break

        if not pessoa:
            return Response(
                {
                    "detail": "CPF não localizado no cadastro de moradores/condôminos. Entre em contato com a administração do seu condomínio."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if hasattr(pessoa, "usuario") and pessoa.usuario:
            return Response(
                {
                    "detail": f"Já existe um usuário de acesso vinculado a este CPF (login: {pessoa.usuario.username}). Utilize a recuperação de senha ou entre em contato com o síndico."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not username or not password:
            return Response(
                {"detail": "Preencha o nome de usuário (login) e a senha desejados."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if Usuario.objects.filter(username=username).exists():
            return Response(
                {"detail": f"O nome de usuário '{username}' já está em uso. Por favor, escolha outro."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_email = email or pessoa.email
        if not user_email:
            return Response(
                {"detail": "É obrigatório fornecer um e-mail para receber a confirmação de cadastro."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Cria o Usuário vinculado à Pessoa
        user = Usuario.objects.create_user(
            username=username,
            email=user_email,
            password=password,
            first_name=pessoa.nome.split()[0] if pessoa.nome else "",
            last_name=" ".join(pessoa.nome.split()[1:]) if pessoa.nome and len(pessoa.nome.split()) > 1 else "",
            pessoa=pessoa,
            is_active=True,
        )

        # Atualiza o e-mail da pessoa se não tinha
        if not pessoa.email:
            pessoa.email = user_email
            pessoa.save(update_fields=["email"])

        # Identifica os condomínios da pessoa através dos vínculos de unidade
        vinculos_unidade = pessoa.vinculos_unidade.filter(data_fim__isnull=True).select_related("unidade__condominio")
        condominios_ids = set([v.unidade.condominio_id for v in vinculos_unidade])

        # Se não tiver vínculo ativo de unidade, verifica se tem em qualquer outro módulo
        if not condominios_ids:
            condominios_ids = set(pessoa.vinculos_unidade.values_list("unidade__condominio_id", flat=True))

        perfil_condomino, _ = Perfil.objects.get_or_create(
            codigo=Perfil.CodigoPerfil.CONDOMINO,
            defaults={"nome": "Condômino", "descricao": "Perfil padrão morador"},
        )

        for c_id in condominios_ids:
            UsuarioCondominio.objects.get_or_create(
                usuario=user,
                condominio_id=c_id,
                defaults={"perfil": perfil_condomino, "ativo": True},
            )

        # Envia e-mail de confirmação de cadastro
        assunto = "Confirmação de Cadastro - CondoGestão"
        mensagem = (
            f"Olá {pessoa.nome},\n\n"
            f"Seu usuário de acesso ao CondoGestão foi criado com sucesso!\n\n"
            f"Dados de Acesso:\n"
            f"Login: {user.username}\n"
            f"E-mail: {user.email}\n\n"
            f"Agora você pode acessar o portal para acompanhar suas unidades, dados cadastrais e comunicados.\n\n"
            f"Atenciosamente,\nAdministração do Condomínio"
        )
        try:
            send_mail(
                subject=assunto,
                message=mensagem,
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@condogestao.com.br"),
                recipient_list=[user_email],
                fail_silently=True,
            )
        except Exception as mail_err:
            print("Aviso: Falha ao enviar e-mail de confirmação:", mail_err)

        return Response(
            {
                "success": True,
                "message": f"Usuário '{username}' cadastrado com sucesso! E-mail de confirmação enviado para {user_email}.",
                "username": user.username,
                "email": user_email,
            },
            status=status.HTTP_201_CREATED,
        )


# ---------------------------------------------------------------------------
# Endpoint: /api/auth/me/
# ---------------------------------------------------------------------------
class CurrentUserView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        vinculos_qs = user.condominios.filter(ativo=True).select_related("condominio", "perfil")
        vinculos_data = [
            {
                "id": v.id,
                "condominio_id": v.condominio.id,
                "condominio_nome": v.condominio.nome,
                "perfil_codigo": v.perfil.codigo,
                "perfil_nome": v.perfil.nome,
            }
            for v in vinculos_qs
        ]

        perfis = list(set([v["perfil_codigo"] for v in vinculos_data]))
        if user.is_superuser:
            perfil_principal = "SINDICO"
            if not perfis:
                perfis = ["SINDICO"]
        else:
            prioridade = ["SINDICO", "SUBSINDICO", "CONSELHEIRO", "CONDOMINO", "FUNCIONARIO"]
            perfil_principal = "CONDOMINO"
            for p in prioridade:
                if p in perfis:
                    perfil_principal = p
                    break

        unidades_vinculadas = []
        if hasattr(user, "pessoa") and user.pessoa:
            for v in user.pessoa.vinculos_unidade.filter(data_fim__isnull=True).select_related("unidade__condominio"):
                unidades_vinculadas.append({
                    "vinculo_id": v.id,
                    "tipo": v.get_tipo_display(),
                    "responsavel": v.responsavel,
                    "unidade_id": v.unidade.id,
                    "identificador": v.unidade.identificador,
                    "bloco": v.unidade.bloco_torre,
                    "condominio_id": v.unidade.condominio.id,
                    "condominio_nome": v.unidade.condominio.nome,
                })

        return Response({
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
            "unidades_vinculadas": unidades_vinculadas,
        })


# ---------------------------------------------------------------------------
# Endpoint: /api/dashboard/stats/
# ---------------------------------------------------------------------------
class DashboardStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        condos = get_request_condominios(request)

        condominios_qs = Condominio.objects.filter(ativo=True)
        unidades_qs = Unidade.objects.all()
        pessoas_qs = Pessoa.objects.all()
        funcionarios_qs = Funcionario.objects.filter(ativo=True)
        mandatos_qs = CargoCondominial.objects.filter(ativo=True)
        vinculos_qs = VinculoPessoaUnidade.objects.filter(data_fim__isnull=True)

        if condos is not None:
            condominios_qs = condominios_qs.filter(id__in=condos)
            unidades_qs = unidades_qs.filter(condominio_id__in=condos)
            funcionarios_qs = funcionarios_qs.filter(condominio_id__in=condos)
            mandatos_qs = mandatos_qs.filter(condominio_id__in=condos)
            vinculos_qs = vinculos_qs.filter(unidade__condominio_id__in=condos)
            pessoas_qs = pessoas_qs.filter(
                Q(vinculos_unidade__unidade__condominio_id__in=condos)
                | Q(dados_funcionario__condominio_id__in=condos)
                | Q(cargos_gestao__condominio_id__in=condos)
                | Q(usuario__condominios__condominio_id__in=condos)
            ).distinct()

        perfis = get_user_profiles(user)
        is_gestao = user.is_superuser or any(p in ["SINDICO", "SUBSINDICO", "CONSELHEIRO"] for p in perfis)

        if not is_gestao and "CONDOMINO" in perfis and hasattr(user, "pessoa") and user.pessoa:
            minhas_unidades = user.pessoa.vinculos_unidade.filter(data_fim__isnull=True).count()
            return Response({
                "role": "CONDOMINO",
                "minhas_unidades": minhas_unidades,
                "meus_vinculos": user.pessoa.vinculos_unidade.count(),
                "avisos": [
                    {"id": 1, "titulo": "Bem-vindo ao Portal do Condômino", "data": "Hoje"}
                ],
            })

        return Response({
            "total_condominios": condominios_qs.count(),
            "total_unidades": unidades_qs.count(),
            "total_pessoas": pessoas_qs.count(),
            "total_funcionarios_ativos": funcionarios_qs.count(),
            "mandatos_ativos": mandatos_qs.count(),
            "vinculos_ativos": vinculos_qs.count(),
        })


# ---------------------------------------------------------------------------
# ViewSet: Condomínio (Scoped)
# ---------------------------------------------------------------------------
class CondominioViewSet(viewsets.ModelViewSet):
    serializer_class = CondominioSerializer
    permission_classes = [CondominioGlobalPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["ativo", "cidade", "uf"]
    search_fields = ["nome", "cnpj", "endereco", "cidade"]
    ordering_fields = ["nome", "created_at"]

    def get_queryset(self):
        condos = get_request_condominios(self.request)
        if condos is None:
            return Condominio.objects.all()
        return Condominio.objects.filter(id__in=condos)


# ---------------------------------------------------------------------------
# ViewSet: Unidade (Scoped)
# ---------------------------------------------------------------------------
class UnidadeViewSet(viewsets.ModelViewSet):
    serializer_class = UnidadeSerializer
    permission_classes = [CondominioModulePermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["condominio", "bloco_torre"]
    search_fields = ["identificador", "bloco_torre", "condominio__nome"]
    ordering_fields = ["bloco_torre", "identificador"]

    def get_queryset(self):
        condos = get_request_condominios(self.request)
        qs = Unidade.objects.select_related("condominio")
        if condos is not None:
            qs = qs.filter(condominio_id__in=condos)
        return qs

    def perform_create(self, serializer):
        condominio = serializer.validated_data.get("condominio")
        condos = get_request_condominios(self.request)
        if condos is not None and condominio.id not in condos:
            raise PermissionDenied("Você não tem permissão para cadastrar unidades neste condomínio.")
        serializer.save()


# ---------------------------------------------------------------------------
# ViewSet: Pessoa (Scoped ao condomínio do usuário)
# ---------------------------------------------------------------------------
class PessoaViewSet(viewsets.ModelViewSet):
    serializer_class = PessoaSerializer
    permission_classes = [CondominioModulePermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["nome", "cpf", "email", "telefone"]
    ordering_fields = ["nome", "created_at"]

    def get_queryset(self):
        condos = get_request_condominios(self.request)
        if condos is None:
            return Pessoa.objects.all()

        user = self.request.user
        # Retorna pessoas com vínculos, cargos, funcionários ou usuários naquele condomínio
        # ou a própria pessoa do usuário
        return Pessoa.objects.filter(
            Q(vinculos_unidade__unidade__condominio_id__in=condos)
            | Q(dados_funcionario__condominio_id__in=condos)
            | Q(cargos_gestao__condominio_id__in=condos)
            | Q(usuario__condominios__condominio_id__in=condos)
            | Q(id=getattr(user, "pessoa_id", None))
        ).distinct()

    def perform_create(self, serializer):
        condos = get_request_condominios(self.request)
        unidade_id = serializer.validated_data.get("unidade_id")
        if unidade_id and condos is not None:
            # Garante que a unidade pertence ao condomínio do usuário
            if not Unidade.objects.filter(id=unidade_id, condominio_id__in=condos).exists():
                raise PermissionDenied("A unidade selecionada não pertence ao seu condomínio.")
        serializer.save()


# ---------------------------------------------------------------------------
# ViewSet: Vínculo Pessoa-Unidade (Scoped)
# ---------------------------------------------------------------------------
class VinculoPessoaUnidadeViewSet(viewsets.ModelViewSet):
    serializer_class = VinculoPessoaUnidadeSerializer
    permission_classes = [CondominioModulePermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["unidade", "pessoa", "tipo", "responsavel"]
    search_fields = ["pessoa__nome", "unidade__identificador", "unidade__condominio__nome"]
    ordering_fields = ["data_inicio", "created_at"]

    def get_queryset(self):
        condos = get_request_condominios(self.request)
        qs = VinculoPessoaUnidade.objects.select_related("pessoa", "unidade", "unidade__condominio")
        if condos is not None:
            qs = qs.filter(unidade__condominio_id__in=condos)

        apenas_ativos = self.request.query_params.get("ativos")
        if apenas_ativos in ["true", "1"]:
            qs = qs.filter(data_fim__isnull=True)
        return qs

    def perform_create(self, serializer):
        unidade = serializer.validated_data.get("unidade")
        condos = get_request_condominios(self.request)
        if condos is not None and unidade.condominio_id not in condos:
            raise PermissionDenied("Você não tem permissão para vincular pessoas a unidades de outro condomínio.")
        serializer.save()


# ---------------------------------------------------------------------------
# ViewSet: Funcionário (Scoped)
# ---------------------------------------------------------------------------
class FuncionarioViewSet(viewsets.ModelViewSet):
    serializer_class = FuncionarioSerializer
    permission_classes = [CondominioModulePermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["condominio", "cargo", "ativo"]
    search_fields = ["pessoa__nome", "pessoa__cpf", "condominio__nome", "cargo"]
    ordering_fields = ["pessoa__nome", "data_admissao"]

    def get_queryset(self):
        condos = get_request_condominios(self.request)
        qs = Funcionario.objects.select_related("pessoa", "condominio")
        if condos is not None:
            qs = qs.filter(condominio_id__in=condos)
        return qs

    def perform_create(self, serializer):
        condominio = serializer.validated_data.get("condominio")
        condos = get_request_condominios(self.request)
        if condos is not None and condominio.id not in condos:
            raise PermissionDenied("Você não tem permissão para cadastrar funcionários neste condomínio.")
        serializer.save()


# ---------------------------------------------------------------------------
# ViewSet: Cargo Condominial (Mandato) (Scoped)
# ---------------------------------------------------------------------------
class CargoCondominialViewSet(viewsets.ModelViewSet):
    serializer_class = CargoCondominialSerializer
    permission_classes = [CondominioModulePermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["condominio", "cargo", "ativo"]
    search_fields = ["pessoa__nome", "condominio__nome", "cargo"]
    ordering_fields = ["data_inicio", "cargo"]

    def get_queryset(self):
        condos = get_request_condominios(self.request)
        qs = CargoCondominial.objects.select_related("pessoa", "condominio")
        if condos is not None:
            qs = qs.filter(condominio_id__in=condos)
        return qs

    def perform_create(self, serializer):
        condominio = serializer.validated_data.get("condominio")
        condos = get_request_condominios(self.request)
        if condos is not None and condominio.id not in condos:
            raise PermissionDenied("Você não tem permissão para cadastrar mandatos neste condomínio.")
        serializer.save()


# ---------------------------------------------------------------------------
# ViewSet: Perfil
# ---------------------------------------------------------------------------
class PerfilViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Perfil.objects.all()
    serializer_class = PerfilSerializer
    permission_classes = [permissions.IsAuthenticated]


# ---------------------------------------------------------------------------
# ViewSet: Usuário (Scoped)
# ---------------------------------------------------------------------------
class UsuarioViewSet(viewsets.ModelViewSet):
    serializer_class = UsuarioSerializer
    permission_classes = [UserManagementPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["is_active", "is_staff", "is_superuser"]
    search_fields = ["username", "email", "first_name", "last_name", "pessoa__nome"]
    ordering_fields = ["username", "created_at"]

    def get_queryset(self):
        condos = get_request_condominios(self.request)
        qs = Usuario.objects.select_related("pessoa").prefetch_related(
            "condominios__condominio", "condominios__perfil"
        )
        if condos is not None:
            qs = qs.filter(
                Q(condominios__condominio_id__in=condos) | Q(id=self.request.user.id)
            ).distinct()
        return qs


# ---------------------------------------------------------------------------
# ViewSet: Vínculo Usuário-Condomínio (Scoped)
# ---------------------------------------------------------------------------
class UsuarioCondominioViewSet(viewsets.ModelViewSet):
    serializer_class = UsuarioCondominioSerializer
    permission_classes = [UserManagementPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["usuario", "condominio", "perfil", "ativo"]
    search_fields = ["usuario__username", "condominio__nome", "perfil__nome"]

    def get_queryset(self):
        condos = get_request_condominios(self.request)
        qs = UsuarioCondominio.objects.select_related("usuario", "condominio", "perfil")
        if condos is not None:
            qs = qs.filter(condominio_id__in=condos)
        return qs
