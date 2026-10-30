from rest_framework import permissions


def get_user_profiles(user, condominio_id=None):
    """
    Retorna uma lista dos códigos de perfil que o usuário possui.
    Se condominio_id for passado, filtra pelos vínculos com aquele condomínio.
    """
    if not user or not user.is_authenticated:
        return []
    
    if user.is_superuser:
        return ["SINDICO", "SUBSINDICO", "CONSELHEIRO", "CONDOMINO", "FUNCIONARIO"]

    vinculos = user.condominios.filter(ativo=True)
    if condominio_id:
        vinculos = vinculos.filter(condominio_id=condominio_id)
        
    return list(vinculos.values_list("perfil__codigo", flat=True))


class IsSuperUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_superuser)


class CondominioGlobalPermission(permissions.BasePermission):
    """
    Condomínios só podem ser criados, editados ou excluídos pelo Superusuário (Super Painel).
    Usuários comuns (Síndico, etc.) só podem visualizar (SAFE_METHODS).
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user.is_superuser)


class IsSindico(permissions.BasePermission):
    """
    Permissão exclusiva para Síndicos (ou superusuário).
    Acesso total a todas as operações, inclusive exclusão e configurações críticas.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        profiles = get_user_profiles(request.user)
        return "SINDICO" in profiles


class IsSindicoOrSubSindico(permissions.BasePermission):
    """
    Síndico e Subsíndico têm acesso de leitura, criação e edição.
    Exclusão (DELETE) é restrita apenas ao Síndico (ou superuser).
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True

        profiles = get_user_profiles(request.user)
        if "SINDICO" in profiles:
            return True
        if "SUBSINDICO" in profiles:
            # Subsíndico não pode excluir (DELETE)
            if request.method == "DELETE":
                return False
            return True
        return False


class CondominioModulePermission(permissions.BasePermission):
    """
    Regra geral para os módulos do condomínio:
    - SAFE_METHODS (GET, HEAD, OPTIONS):
      - Síndico, Subsíndico, Conselheiro e Funcionário podem visualizar.
      - Condômino pode visualizar unidades/pessoas de forma restrita (suas próprias).
    - Métodos de Escrita (POST, PUT, PATCH):
      - Síndico e Subsíndico têm permissão.
    - Método DELETE:
      - Apenas Síndico (ou superusuário).
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True

        profiles = get_user_profiles(request.user)

        # Se for método de leitura
        if request.method in permissions.SAFE_METHODS:
            return len(profiles) > 0

        # Subsíndico pode criar e atualizar, mas não deletar
        if request.method == "DELETE":
            return "SINDICO" in profiles

        return ("SINDICO" in profiles) or ("SUBSINDICO" in profiles)


class UserManagementPermission(permissions.BasePermission):
    """
    Gerenciamento de Usuários e Perfis:
    - Criação/Edição: Síndico e Subsíndico.
    - Exclusão: Apenas Síndico.
    - O próprio usuário pode ler seus dados (/api/auth/me/).
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True

        profiles = get_user_profiles(request.user)
        
        if request.method in permissions.SAFE_METHODS:
            return ("SINDICO" in profiles) or ("SUBSINDICO" in profiles)
        
        if request.method == "DELETE":
            return "SINDICO" in profiles

        return ("SINDICO" in profiles) or ("SUBSINDICO" in profiles)
