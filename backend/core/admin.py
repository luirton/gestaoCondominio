from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    Condominio,
    Unidade,
    Pessoa,
    VinculoPessoaUnidade,
    Funcionario,
    CargoCondominial,
    Perfil,
    Usuario,
    UsuarioCondominio,
)


@admin.register(Condominio)
class CondominioAdmin(admin.ModelAdmin):
    list_display = ["nome", "cnpj", "cidade", "uf", "ativo", "created_at"]
    search_fields = ["nome", "cnpj", "cidade"]
    list_filter = ["ativo", "uf"]


@admin.register(Unidade)
class UnidadeAdmin(admin.ModelAdmin):
    list_display = ["identificador", "bloco_torre", "condominio", "fracao_ideal", "area_privativa"]
    search_fields = ["identificador", "bloco_torre", "condominio__nome"]
    list_filter = ["condominio"]


@admin.register(Pessoa)
class PessoaAdmin(admin.ModelAdmin):
    list_display = ["nome", "cpf", "telefone", "email", "created_at"]
    search_fields = ["nome", "cpf", "email"]


@admin.register(VinculoPessoaUnidade)
class VinculoPessoaUnidadeAdmin(admin.ModelAdmin):
    list_display = ["pessoa", "unidade", "tipo", "data_inicio", "data_fim", "responsavel"]
    search_fields = ["pessoa__nome", "unidade__identificador", "unidade__condominio__nome"]
    list_filter = ["tipo", "responsavel"]


@admin.register(Funcionario)
class FuncionarioAdmin(admin.ModelAdmin):
    list_display = ["pessoa", "condominio", "cargo", "data_admissao", "ativo"]
    search_fields = ["pessoa__nome", "condominio__nome", "cargo"]
    list_filter = ["cargo", "ativo", "condominio"]


@admin.register(CargoCondominial)
class CargoCondominialAdmin(admin.ModelAdmin):
    list_display = ["pessoa", "condominio", "cargo", "data_inicio", "data_fim", "ativo"]
    search_fields = ["pessoa__nome", "condominio__nome"]
    list_filter = ["cargo", "ativo", "condominio"]


@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ["codigo", "nome", "descricao"]


class UsuarioCondominioInline(admin.TabularInline):
    model = UsuarioCondominio
    extra = 1


@admin.register(Usuario)
class CustomUserAdmin(UserAdmin):
    list_display = ["username", "email", "pessoa", "is_staff", "is_superuser", "is_active"]
    search_fields = ["username", "email", "pessoa__nome"]
    fieldsets = UserAdmin.fieldsets + (
        ("Vínculo Condominial", {"fields": ("pessoa",)}),
    )
    inlines = [UsuarioCondominioInline]


@admin.register(UsuarioCondominio)
class UsuarioCondominioAdmin(admin.ModelAdmin):
    list_display = ["usuario", "condominio", "perfil", "ativo"]
    search_fields = ["usuario__username", "condominio__nome", "perfil__nome"]
    list_filter = ["perfil", "ativo", "condominio"]
