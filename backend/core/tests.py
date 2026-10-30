from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
from datetime import date

from .models import (
    Perfil,
    Condominio,
    Unidade,
    Pessoa,
    VinculoPessoaUnidade,
    UsuarioCondominio,
)

Usuario = get_user_model()


class CondominioAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Cria Perfis
        self.perfil_sindico = Perfil.objects.create(
            codigo=Perfil.CodigoPerfil.SINDICO,
            nome="Síndico",
            descricao="Acesso total"
        )
        self.perfil_condomino = Perfil.objects.create(
            codigo=Perfil.CodigoPerfil.CONDOMINO,
            nome="Condômino",
            descricao="Acesso condômino"
        )

        # Cria Condomínio
        self.condominio = Condominio.objects.create(
            nome="Condomínio Teste",
            cnpj="11.222.333/0001-44",
            endereco="Rua dos Testes",
            numero="100",
            cidade="São Paulo",
            uf="SP",
            cep="01001-000",
        )

        # Cria Unidade
        self.unidade = Unidade.objects.create(
            condominio=self.condominio,
            bloco_torre="A",
            identificador="101",
            fracao_ideal=Decimal("0.050000"),
            area_privativa=Decimal("70.00"),
        )

        # Cria Usuário Síndico
        self.user_sindico = Usuario.objects.create_superuser(
            username="sindico_test",
            email="sindico@teste.com",
            password="password123"
        )
        UsuarioCondominio.objects.create(
            usuario=self.user_sindico,
            condominio=self.condominio,
            perfil=self.perfil_sindico,
        )

    def test_jwt_login(self):
        response = self.client.post("/api/token/", {
            "username": "sindico_test",
            "password": "password123"
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["user"]["perfil_principal"], "SINDICO")

    def test_current_user_endpoint(self):
        self.client.force_authenticate(user=self.user_sindico)
        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "sindico_test")
        self.assertEqual(response.data["perfil_principal"], "SINDICO")

    def test_crud_condominio(self):
        self.client.force_authenticate(user=self.user_sindico)
        response = self.client.get("/api/condominios/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_condominio_isolation(self):
        # Cria um segundo condomínio e uma unidade nele
        condo2 = Condominio.objects.create(
            nome="Condomínio Isolado 2",
            cnpj="99.888.777/0001-66",
            endereco="Rua Isolada",
            cidade="Campinas",
            uf="SP"
        )
        u2 = Unidade.objects.create(
            condominio=condo2,
            identificador="Apto 999",
            fracao_ideal=Decimal("0.010000")
        )

        # Cria um usuário não-superuser vinculado apenas ao Condomínio 1
        user_c1 = Usuario.objects.create_user(
            username="sindico_c1",
            email="c1@teste.com",
            password="password123"
        )
        UsuarioCondominio.objects.create(
            usuario=user_c1,
            condominio=self.condominio,
            perfil=self.perfil_sindico
        )

        self.client.force_authenticate(user=user_c1)
        
        # O usuário c1 só deve ver o Condomínio 1
        resp_condos = self.client.get("/api/condominios/")
        self.assertEqual(len(resp_condos.data["results"]), 1)
        self.assertEqual(resp_condos.data["results"][0]["id"], self.condominio.id)

        # O usuário c1 só deve ver as unidades do Condomínio 1 (não vê Apto 999 do condo2)
        resp_unidades = self.client.get("/api/unidades/")
        self.assertEqual(len(resp_unidades.data["results"]), 1)
        self.assertEqual(resp_unidades.data["results"][0]["identificador"], "101")

    def test_crud_pessoa_and_vinculo(self):
        self.client.force_authenticate(user=self.user_sindico)
        
        # Cria pessoa com unidade_id obrigatório
        resp_pessoa = self.client.post("/api/pessoas/", {
            "nome": "João Morador",
            "cpf": "999.888.777-66",
            "telefone": "(11) 99999-8888",
            "email": "joao@teste.com",
            "unidade_id": self.unidade.id,
            "tipo_vinculo": "MORADOR",
            "responsavel": True,
        })
        self.assertEqual(resp_pessoa.status_code, status.HTTP_201_CREATED)
        pessoa_id = resp_pessoa.data["id"]

        # Tentativa de criar outro responsável ativo para a mesma unidade deve falhar
        resp_pessoa2 = self.client.post("/api/pessoas/", {
            "nome": "Maria Moradora",
            "cpf": "888.777.666-55",
            "telefone": "(11) 99999-7777",
            "email": "maria@teste.com",
            "unidade_id": self.unidade.id,
            "tipo_vinculo": "MORADOR",
            "responsavel": True,
        })
        self.assertEqual(resp_pessoa2.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_condomino_and_email(self):
        from django.core import mail

        # 1. Cria uma pessoa pré-cadastrada pelo síndico
        pessoa = Pessoa.objects.create(
            nome="Carlos Condômino",
            cpf="123.456.789-00",
            email="carlos@email.com"
        )
        VinculoPessoaUnidade.objects.create(
            pessoa=pessoa,
            unidade=self.unidade,
            tipo=VinculoPessoaUnidade.TipoVinculo.MORADOR,
            data_inicio=date.today()
        )

        # 2. Cadastro sem CPF pré-existente falha
        resp_fail = self.client.post("/api/auth/register-condomino/", {
            "cpf": "000.000.000-99",
            "username": "carlos",
            "email": "carlos@email.com",
            "password": "senha123password"
        })
        self.assertEqual(resp_fail.status_code, status.HTTP_404_NOT_FOUND)

        # 3. Cadastro com CPF existente tem sucesso e envia e-mail
        resp_success = self.client.post("/api/auth/register-condomino/", {
            "cpf": "123.456.789-00",
            "username": "carlos_login",
            "email": "carlos@email.com",
            "password": "senha123password"
        })
        self.assertEqual(resp_success.status_code, status.HTTP_201_CREATED)
        self.assertIn("carlos_login", resp_success.data["username"])

        # Verifica se o e-mail foi disparado para a outbox
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Confirmação de Cadastro", mail.outbox[0].subject)
        self.assertIn("carlos@email.com", mail.outbox[0].to)

        # 4. Novo cadastro com o mesmo CPF agora deve ser bloqueado
        resp_dup = self.client.post("/api/auth/register-condomino/", {
            "cpf": "123.456.789-00",
            "username": "carlos_outro",
            "email": "carlos@email.com",
            "password": "senha123password"
        })
        self.assertEqual(resp_dup.status_code, status.HTTP_400_BAD_REQUEST)
