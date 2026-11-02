from rest_framework.pagination import PageNumberPagination


class StandardFlexiblePagination(PageNumberPagination):
    """
    Paginação padrão flexível para o sistema CondoGestão.
    - page_size padrão: 500 (garante que condomínios com 52, 100 ou 200 unidades carreguem por completo)
    - Suporta customização via query param: ?page_size=1000
    - Suporta desativação de paginação quando necessário (combos/dropdowns): ?no_page=true ou ?page_size=all
    """
    page_size = 500
    page_size_query_param = "page_size"
    max_page_size = 5000

    def paginate_queryset(self, queryset, request, view=None):
        no_page = request.query_params.get("no_page")
        page_size_param = request.query_params.get("page_size")

        if no_page in ("true", "1", "yes") or page_size_param in ("all", "0"):
            return None

        return super().paginate_queryset(queryset, request, view)
