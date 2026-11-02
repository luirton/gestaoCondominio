from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ContaBancariaViewSet,
    PeriodoPrestacaoViewSet,
    ReceitaCotaViewSet,
    ReceitaExtraViewSet,
    DespesaViewSet,
    DashboardFinanceiroView,
    AreaMoradorPrestacaoView,
)

router = DefaultRouter()
router.register(r"contas-bancarias", ContaBancariaViewSet, basename="conta-bancaria")
router.register(r"periodos", PeriodoPrestacaoViewSet, basename="periodo-prestacao")
router.register(r"cotas", ReceitaCotaViewSet, basename="receita-cota")
router.register(r"receitas-extras", ReceitaExtraViewSet, basename="receita-extra")
router.register(r"despesas", DespesaViewSet, basename="despesa")

urlpatterns = [
    path("dashboard/", DashboardFinanceiroView.as_view(), name="financeiro-dashboard"),
    path("morador/", AreaMoradorPrestacaoView.as_view(), name="financeiro-morador"),
    path("", include(router.urls)),
]
