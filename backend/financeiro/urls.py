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
from .cobranca_views import (
    InadimplenciaGeralView,
    InadimplenciaUnidadeView,
    InadimplenciaConsolidadaMoradorView,
    DownloadAvisoDebitoPdfView,
    DownloadAvisoDebitoConsolidadoPdfView,
    EnviarEmailCobrancaView,
    EmitirNadaConstaView,
    EmitirNadaConstaConsolidadoMoradorView,
    DownloadCertidaoNadaConstaPdfView,
    DownloadCertidaoNadaConstaConsolidadoPdfView,
    ParametroCobrancaViewSet,
    AcordoDescontoCotaViewSet,
    HistoricoNotificacaoCobrancaViewSet,
    BaixaCotaAtrasadaView,
    BaixaCotasAtrasadasLoteView,
)

router = DefaultRouter()
router.register(r"contas-bancarias", ContaBancariaViewSet, basename="conta-bancaria")
router.register(r"periodos", PeriodoPrestacaoViewSet, basename="periodo-prestacao")
router.register(r"cotas", ReceitaCotaViewSet, basename="receita-cota")
router.register(r"receitas-extras", ReceitaExtraViewSet, basename="receita-extra")
router.register(r"despesas", DespesaViewSet, basename="despesa")

# Roteadores de Inadimplência e Cobrança
router.register(r"parametros-cobranca", ParametroCobrancaViewSet, basename="parametro-cobranca")
router.register(r"acordos-cota", AcordoDescontoCotaViewSet, basename="acordo-cota")
router.register(r"historico-cobrancas", HistoricoNotificacaoCobrancaViewSet, basename="historico-cobranca")

urlpatterns = [
    path("dashboard/", DashboardFinanceiroView.as_view(), name="financeiro-dashboard"),
    path("morador/", AreaMoradorPrestacaoView.as_view(), name="financeiro-morador"),
    
    # Endpoints de Inadimplência e Declaração de Nada Consta
    path("inadimplencia/", InadimplenciaGeralView.as_view(), name="inadimplencia-geral"),
    path("inadimplencia/morador/consolidado/", InadimplenciaConsolidadaMoradorView.as_view(), name="inadimplencia-consolidada-morador"),
    path("inadimplencia/morador/consolidado/pdf/", DownloadAvisoDebitoConsolidadoPdfView.as_view(), name="inadimplencia-consolidada-pdf"),
    path("inadimplencia/unidade/<int:unidade_id>/", InadimplenciaUnidadeView.as_view(), name="inadimplencia-unidade"),
    path("inadimplencia/unidade/<int:unidade_id>/pdf/", DownloadAvisoDebitoPdfView.as_view(), name="inadimplencia-unidade-pdf"),
    path("inadimplencia/unidade/<int:unidade_id>/enviar-email/", EnviarEmailCobrancaView.as_view(), name="inadimplencia-enviar-email"),
    path("nada-consta/emitir/", EmitirNadaConstaView.as_view(), name="nada-consta-emitir"),
    path("nada-consta/morador/consolidado/", EmitirNadaConstaConsolidadoMoradorView.as_view(), name="nada-consta-consolidado-morador"),
    path("nada-consta/morador/consolidado/pdf/", DownloadCertidaoNadaConstaConsolidadoPdfView.as_view(), name="nada-consta-consolidado-pdf"),
    path("nada-consta/<int:certidao_id>/pdf/", DownloadCertidaoNadaConstaPdfView.as_view(), name="nada-consta-pdf"),

    # Baixa de Cotas em Atraso (Abordagem A - Regime de Caixa)
    path("cotas/<int:cota_id>/dar-baixa-atrasada/", BaixaCotaAtrasadaView.as_view(), name="cota-dar-baixa-atrasada"),
    path("cotas/dar-baixa-atrasadas-lote/", BaixaCotasAtrasadasLoteView.as_view(), name="cotas-dar-baixa-atrasadas-lote"),

    path("", include(router.urls)),
]
