from datetime import date
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import (
    Perfil,
    Condominio,
    Unidade,
    Pessoa,
    VinculoPessoaUnidade,
    Funcionario,
    CargoCondominial,
    UsuarioCondominio,
)

Usuario = get_user_model()


class Command(BaseCommand):
    help = "Popula o banco com os perfis padrão e dados iniciais de demonstração"

    def handle(self, *args, **options):
        self.stdout.write("Inicializando perfis de acesso...")

        perfis_data = [
            {
                "codigo": Perfil.CodigoPerfil.SINDICO,
                "nome": "Síndico",
                "descricao": "Acesso total ao sistema, relatórios, cadastros e parametrizações.",
            },
            {
                "codigo": Perfil.CodigoPerfil.SUBSINDICO,
                "nome": "Subsíndico",
                "descricao": "Acesso total operacional, exceto exclusão de usuários e configurações críticas.",
            },
            {
                "codigo": Perfil.CodigoPerfil.CONSELHEIRO,
                "nome": "Conselheiro",
                "descricao": "Visualiza relatórios e prestação de contas, sem permissão de edição.",
            },
            {
                "codigo": Perfil.CodigoPerfil.CONDOMINO,
                "nome": "Condômino",
                "descricao": "Vê apenas seus dados, suas unidades, seus boletos e comunicados.",
            },
            {
                "codigo": Perfil.CodigoPerfil.FUNCIONARIO,
                "nome": "Funcionário",
                "descricao": "Acesso operacional restrito, sem acesso ao módulo financeiro.",
            },
        ]

        perfis_objs = {}
        for item in perfis_data:
            obj, created = Perfil.objects.get_or_create(
                codigo=item["codigo"],
                defaults={"nome": item["nome"], "descricao": item["descricao"]},
            )
            perfis_objs[item["codigo"]] = obj
            status = "criado" if created else "já existente"
            self.stdout.write(f"- Perfil {item['nome']} ({status})")

        # 1. Condomínio Exemplo
        condominio, created = Condominio.objects.get_or_create(
            nome="Condomínio Residencial Jardins",
            defaults={
                "cnpj": "12.345.678/0001-90",
                "endereco": "Av. Paulista",
                "numero": "1500",
                "complemento": "Torre A e B",
                "bairro": "Bela Vista",
                "cidade": "São Paulo",
                "uf": "SP",
                "cep": "01310-200",
                "ativo": True,
            },
        )
        self.stdout.write(f"- Condomínio: {condominio.nome}")

        # 2. Pessoas e Usuários de teste
        # Síndico
        p_sindico, _ = Pessoa.objects.get_or_create(
            cpf="111.222.333-44",
            defaults={
                "nome": "Carlos Eduardo Síndico",
                "telefone": "(11) 98888-1111",
                "email": "sindico@condominio.com.br",
                "data_nascimento": date(1980, 5, 15),
            },
        )

        user_admin, created = Usuario.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@condominio.com.br",
                "first_name": "Carlos",
                "last_name": "Síndico",
                "is_staff": True,
                "is_superuser": True,
                "pessoa": p_sindico,
            },
        )
        if created:
            user_admin.set_password("admin123")
            user_admin.save()
            self.stdout.write("- Superusuário admin criado (senha: admin123)")

        UsuarioCondominio.objects.get_or_create(
            usuario=user_admin,
            condominio=condominio,
            defaults={"perfil": perfis_objs[Perfil.CodigoPerfil.SINDICO], "ativo": True},
        )

        # Mandato do Síndico
        CargoCondominial.objects.get_or_create(
            condominio=condominio,
            cargo=CargoCondominial.TipoCargo.SINDICO,
            data_inicio=date(2025, 1, 1),
            defaults={
                "pessoa": p_sindico,
                "data_fim": date(2027, 1, 1),
                "ativo": True,
            },
        )

        # 3. Unidades de Exemplo
        u101, _ = Unidade.objects.get_or_create(
            condominio=condominio,
            bloco_torre="A",
            identificador="101",
            defaults={
                "fracao_ideal": Decimal("0.025000"),
                "area_privativa": Decimal("85.50"),
                "observacoes": "Sol da manhã, 2 vagas de garagem",
            },
        )
        u102, _ = Unidade.objects.get_or_create(
            condominio=condominio,
            bloco_torre="A",
            identificador="102",
            defaults={
                "fracao_ideal": Decimal("0.025000"),
                "area_privativa": Decimal("85.50"),
                "observacoes": "Sol da tarde",
            },
        )
        u201, _ = Unidade.objects.get_or_create(
            condominio=condominio,
            bloco_torre="B",
            identificador="201",
            defaults={
                "fracao_ideal": Decimal("0.035000"),
                "area_privativa": Decimal("110.00"),
                "observacoes": "Cobertura duplex",
            },
        )

        # 4. Condômino morador
        p_morador, _ = Pessoa.objects.get_or_create(
            cpf="222.333.444-55",
            defaults={
                "nome": "Mariana Souza Moradora",
                "telefone": "(11) 97777-2222",
                "email": "mariana@condominio.com.br",
                "data_nascimento": date(1992, 8, 20),
            },
        )
        VinculoPessoaUnidade.objects.get_or_create(
            pessoa=p_morador,
            unidade=u101,
            tipo=VinculoPessoaUnidade.TipoVinculo.PROPRIETARIO,
            defaults={
                "data_inicio": date(2024, 3, 1),
                "responsavel": True,
            },
        )

        user_condomino, created = Usuario.objects.get_or_create(
            username="mariana",
            defaults={
                "email": "mariana@condominio.com.br",
                "first_name": "Mariana",
                "last_name": "Souza",
                "pessoa": p_morador,
            },
        )
        if created:
            user_condomino.set_password("senha123")
            user_condomino.save()
            UsuarioCondominio.objects.get_or_create(
                usuario=user_condomino,
                condominio=condominio,
                defaults={"perfil": perfis_objs[Perfil.CodigoPerfil.CONDOMINO], "ativo": True},
            )
            self.stdout.write("- Usuário condômino 'mariana' criado (senha: senha123)")

        # 5. Funcionário (Porteiro)
        p_porteiro, _ = Pessoa.objects.get_or_create(
            cpf="333.444.555-66",
            defaults={
                "nome": "José da Silva Porteiro",
                "telefone": "(11) 96666-3333",
                "email": "jose@condominio.com.br",
                "data_nascimento": date(1985, 2, 10),
            },
        )
        Funcionario.objects.get_or_create(
            pessoa=p_porteiro,
            condominio=condominio,
            cargo=Funcionario.CargoFuncionario.PORTEIRO,
            defaults={
                "endereco_proprio": "Rua das Laranjeiras, 45 - Bairro Santana",
                "data_admissao": date(2023, 6, 1),
                "ativo": True,
            },
        )

        user_func, created = Usuario.objects.get_or_create(
            username="jose",
            defaults={
                "email": "jose@condominio.com.br",
                "first_name": "José",
                "last_name": "Portaria",
                "pessoa": p_porteiro,
            },
        )
        if created:
            user_func.set_password("senha123")
            user_func.save()
            UsuarioCondominio.objects.get_or_create(
                usuario=user_func,
                condominio=condominio,
                defaults={"perfil": perfis_objs[Perfil.CodigoPerfil.FUNCIONARIO], "ativo": True},
            )
            self.stdout.write("- Usuário funcionário 'jose' criado (senha: senha123)")

        self.stdout.write(self.style.SUCCESS("Dados iniciais semeados com sucesso!"))
