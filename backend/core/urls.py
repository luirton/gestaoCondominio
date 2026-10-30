from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    CurrentUserView,
    RegisterCondominoView,
    DashboardStatsView,
    CondominioViewSet,
    UnidadeViewSet,
    PessoaViewSet,
    VinculoPessoaUnidadeViewSet,
    FuncionarioViewSet,
    CargoCondominialViewSet,
    PerfilViewSet,
    UsuarioViewSet,
    UsuarioCondominioViewSet,
)

router = DefaultRouter()
router.register(r"condominios", CondominioViewSet, basename="condominio")
router.register(r"unidades", UnidadeViewSet, basename="unidade")
router.register(r"pessoas", PessoaViewSet, basename="pessoa")
router.register(r"vinculos-unidade", VinculoPessoaUnidadeViewSet, basename="vinculo-unidade")
router.register(r"funcionarios", FuncionarioViewSet, basename="funcionario")
router.register(r"cargos-condominiais", CargoCondominialViewSet, basename="cargo-condominial")
router.register(r"perfis", PerfilViewSet, basename="perfil")
router.register(r"usuarios", UsuarioViewSet, basename="usuario")
router.register(r"usuarios-condominios", UsuarioCondominioViewSet, basename="usuario-condominio")

urlpatterns = [
    path("auth/me/", CurrentUserView.as_view(), name="auth-me"),
    path("auth/register-condomino/", RegisterCondominoView.as_view(), name="auth-register-condomino"),
    path("dashboard/stats/", DashboardStatsView.as_view(), name="dashboard-stats"),
    path("", include(router.urls)),
]
