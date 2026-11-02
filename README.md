# CondoGestão - Sistema Integrado de Gestão Condominial

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Django 5.0](https://img.shields.io/badge/Django-5.0-success.svg)](https://www.djangoproject.com/)
[![Django REST Framework](https://img.shields.io/badge/DRF-3.15-red.svg)](https://www.django-rest-framework.org/)
[![Vue.js 3](https://img.shields.io/badge/Vue.js-3.4-brightgreen.svg)](https://vuejs.org/)
[![Vite](https://img.shields.io/badge/Vite-6.0-purple.svg)](https://vitejs.dev/)
[![Tailwind CSS](https://img.shields.io/badge/TailwindCSS-3.4-38bdf8.svg)](https://tailwindcss.com/)
[![JWT Auth](https://img.shields.io/badge/JWT-SimpleJWT-orange.svg)](https://django-rest-framework-simplejwt.readthedocs.io/)

O **CondoGestão** é uma plataforma moderna e completa para administração de condomínios residenciais e comerciais. O sistema foi desenvolvido com arquitetura desacoplada, separando claramente as entidades de pessoas civis, usuários de acesso, unidades físicas, vínculos contratuais, mandatos de governança e funcionários operacionais.

Possui controle de acesso baseado em papéis (**RBAC**), isolamento seguro de dados por condomínio (multi-tenant lógico) e interface segregada entre administração predial, auto-serviço do morador e um **Super Painel Global** para gestão de alto nível.

---

## 💼 Módulo de Gestão de Prestação de Contas

O módulo substitui integralmente planilhas manuais de condomínio (baseado no caso real do **Condomínio Hortências III**, Fortaleza/CE), sanando as fragilidades de fórmulas e garantindo rastreabilidade histórica.

### 🏛️ As 6 Telas do Módulo:
1. **Dashboard Financeiro (`/prestacao`):**
   - Cards em tempo real: Total Receitas, Total Despesas, Saldo do Mês, Saldo Bancário Final.
   - Status do período atual (ABERTO, FECHADO, PUBLICADO).
   - Alertas preventivos: inadimplência/cotas pendentes e despesas sem comprovante.
   - Gráfico de evolução de receitas vs despesas.
2. **Configuração do Período (`/prestacao/periodos`):**
   - Espelho da aba `PROPRIEDADES` com validações de datas.
   - Parâmetros: valor da cota (R$ 380,00), vaga de estacionamento (R$ 100,00), saldos anteriores (CC, CDB, Porquinho Férias/13º).
   - Botão **"Gerar Cotas"** para criação em lote para as 52 unidades.
3. **Lançamento de Pagamentos (`/prestacao/pagamentos`):**
   - Espelho da aba `PAGAMENTOS` com tabela editável de 52 unidades.
   - Baixa em lote ("Marcar selecionadas como pagas").
   - Cálculo automático de juros e multa para pagamentos a maior ou fora do prazo.
   - Seção dedicada de **Receitas Extras** (aluguel de vagas, rendimento CDB, acordos).
4. **Gestão de Despesas (`/prestacao/despesas`):**
   - Categorização pré-definida de despesas Fixas e Variáveis.
   - Upload de comprovantes fiscais (PDF e imagem).
   - Filtros dinâmicos e cards totalizadores.
5. **Prestação de Contas Balancete (`/prestacao/relatorio`):**
   - Reprodução idêntica da aba `PRESTAÇÃO` da planilha.
   - Exportação para **PDF** oficial (ReportLab) e **Excel** (.xlsx multi-aba via OpenPyXL).
   - Observação automática da diferença de cotas:
     > *"A diferença entre o SALDO MÊS e o TOTAL DO SALDO BANCÁRIO é de X cota(s) referente ao mês de [MÊS] com vencimento em [DATA]"*
   - Assinatura digital do síndico (Nome, CPF e Data).
   - Ações de **Fechar Período** (gera snapshot congelado) e **Publicar**.
6. **Área do Morador (`/prestacao/morador`):**
   - Consulta de cotas pagas/pendentes da unidade do condômino.
   - Acesso e download das prestações de contas oficiais aprovadas e publicadas.

### ⚙️ Comando de Carga & Migração da Planilha:
Para carregar os dados reais da planilha do Condomínio Hortências III (52 casas + período 09/2026 100% conferido):
```bash
python manage.py migrar_prestacao_hortencias
```

### 🧪 Execução de Testes Automatizados:
- **Backend (Regras de Negócio e Cálculos - Django Test):**
  ```bash
  python manage.py test financeiro
  ```
- **Frontend (Regras de Cálculo e Utilitários - Vitest):**
  ```bash
  cd frontend
  npm test
  ```

---

## 📑 Sumário

- [Destaques e Funcionalidades](#-destaques-e-funcionalidades)
- [Estrutura do Repositório](#-estrutura-do-repositório)
- [Perfis de Acesso e Permissões](#-perfis-de-acesso-e-permissões)
- [Contas de Teste Pré-Configuradas](#-contas-de-teste-pré-configuradas)
- [Como Rodar Localmente (Desenvolvimento)](#-como-rodar-localmente-desenvolvimento)
  - [Método Rápido via Script (Windows)](#método-rápido-via-script-windows)
  - [Execução Manual Passo a Passo](#execução-manual-passo-a-passo)
- [Como Subir em Servidor de Produção (Linux / VPS)](#-como-subir-em-servidor-de-produção-linux--vps)
  - [1. Preparação do Servidor](#1-preparação-do-servidor-ubuntu--debian)
  - [2. Configuração do Banco de Dados PostgreSQL](#2-configuração-do-banco-de-dados-postgresql)
  - [3. Deploy do Backend (Django + Gunicorn)](#3-deploy-do-backend-django--gunicorn)
  - [4. Deploy do Frontend (Vue.js + Vite)](#4-deploy-do-frontend-vuejs--vite)
  - [5. Configuração do Nginx (Reverse Proxy + SPA)](#5-configuração-do-nginx-reverse-proxy--spa)
  - [6. Certificado SSL Gratuito com Let's Encrypt](#6-certificado-ssl-gratuito-com-lets-encrypt)
- [Deploy com Docker e Docker Compose](#-deploy-alternativo-com-docker-e-docker-compose)
- [Suíte de Testes Automatizados](#-suíte-de-testes-automatizados)
- [Licença](#-licença)

---

## 🚀 Destaques e Funcionalidades

- **Autenticação JWT Segura:** Tokens de acesso e refresh via `SimpleJWT` com interceptação e renovação automática no frontend.
- **Isolamento por Condomínio:** Headers customizados (`X-Condominio-Id`) e validação rigorosa no backend garantem que síndicos e funcionários acessem exclusivamente os dados do seu condomínio ativo.
- **Super Painel Global:** Interface autônoma e leve para o administrador geral cadastrar novos condomínios e gerenciar a base sem restrições.
- **Auto-Cadastro de Morador:** Fluxo de primeiro acesso na tela de login validando o CPF diretamente contra a base de moradores pré-cadastrada pela administração predial, com disparo automático de e-mail de confirmação.
- **Preparado para o Módulo Financeiro:** Unidades com validação de responsável legal/financeiro único e entidades prontas para cobranças, boletos e rateios.
- **Módulo de Prestação de Contas (100% Integrado):** Gestão orçamentária mensal com cálculo rigoroso de balancete, fechamento imutável com snapshots, conciliação com extrato bancário, observação automática da diferença de cotas, exportação em PDF corporativo e Excel multi-aba idêntico à planilha original, além de portal de transparência para o morador.
- **Máscaras e Validações Dinâmicas:** Formatação amigável para CPF, CNPJ, Telefones e CEPs com validações preventivas contra duplicidade.

---

## 📁 Estrutura do Repositório

```text
gestaoCondominio/
│
├── backend/                              # API REST em Django + Django REST Framework
│   ├── config/                           # Configurações globais (settings, urls, wsgi, asgi)
│   │   ├── settings.py                   # Configurações com suporte a SQLite, PostgreSQL, JWT e CORS
│   │   ├── urls.py                       # Rotas principais e SimpleJWT
│   │   └── wsgi.py
│   ├── core/                             # Aplicação principal de domínio condominial
│   │   ├── management/commands/          # Comandos CLI (seed_initial_data para carga de teste)
│   │   ├── migrations/                   # Histórico de migrações do banco de dados
│   │   ├── models.py                     # Modelagem relacional do domínio condominial
│   │   ├── permissions.py                # Regras de acesso e autorização por perfil (RBAC)
│   │   ├── serializers.py                # Serializadores DRF com validações de negócio
│   │   ├── tests.py                      # Testes automatizados de API e segurança
│   │   ├── urls.py                       # Endpoints da API REST
│   │   └── views.py                      # ViewSets e endpoints de autenticação/dashboard
│   ├── .env.example                      # Exemplo de variáveis de ambiente do backend
│   ├── manage.py
│   ├── requirements.txt                  # Dependências Python (Django, DRF, Gunicorn, Psycopg2)
│   └── run_backend.bat                   # Atalho de execução local do backend no Windows
│
├── frontend/                             # Aplicação SPA moderna em Vue.js 3 + Vite
│   ├── src/
│   │   ├── api/client.js                 # Cliente Axios com interceptors JWT e auto-refresh
│   │   ├── layouts/AppLayout.vue         # Layout principal responsivo com sidebar
│   │   ├── router/index.js               # Vue Router com Navigation Guards por perfil
│   │   ├── stores/auth.js                # Pinia Store com estado de autenticação e RBAC
│   │   ├── utils/masks.js                # Utilitários de máscaras (CPF, CNPJ, telefone, CEP)
│   │   ├── views/                        # Telas da aplicação (Dashboard, Pessoas, Unidades, etc.)
│   │   ├── App.vue
│   │   ├── main.js
│   │   └── style.css                     # Tailwind CSS v3
│   ├── .env.example                      # Configuração da URL da API
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── run_frontend.bat                  # Atalho de execução local do frontend no Windows
│
├── admin-painel/                         # Super Painel Global (SPA autônomo sem dependências)
│   ├── index.html                        # Aplicação Vue 3 CDN + Tailwind (acesso global de condomínios)
│   └── run_admin.bat                     # Servidor local leve na porta 5174
│
├── .gitignore                            # Arquivos ignorados pelo controle de versão
├── start.bat                             # Inicia Backend + Frontend + Super Painel juntos
├── start_dev.bat                         # Inicia Backend + Frontend juntos
└── README.md                             # Documentação do projeto
```

---

## 👥 Perfis de Acesso e Permissões

| Perfil | Acesso no CondoGestão | Responsabilidade |
| :--- | :--- | :--- |
| **Superadmin (Root)** | Acesso total e irrestrito | Cadastra novos condomínios via Super Painel Global e gerencia o sistema. |
| **Síndico** | Acesso completo ao seu condomínio | Gerencia unidades, moradores, funcionários, mandatos e usuários da sua unidade. |
| **Subsíndico** | Acesso total (exceto exclusões críticas) | Apoia na administração diária; bloqueado para exclusão permanente de usuários. |
| **Conselheiro** | Somente Leitura | Acompanha cadastros e relatórios para fiscalização, sem permissão de alteração. |
| **Condômino** | Área do Morador (`/meu-espaco`) | Visualiza apenas suas unidades vinculadas, dados cadastrais e comunicados. |
| **Funcionário** | Operacional Restrito | Consulta registros autorizados de portaria/zeladoria, sem acesso a dados sensíveis. |

---

## 🔑 Contas de Teste Pré-Configuradas

Ao executar a carga inicial (`python manage.py seed_initial_data`), as seguintes contas estarão disponíveis:

| Perfil | Usuário | Senha | Finalidade |
| :--- | :--- | :--- | :--- |
| **Síndico (Superadmin)** | `admin` | `admin123` | Acesso total ao CondoGestão e ao Super Painel |
| **Condômina** | `mariana` | `senha123` | Teste da Área do Morador |
| **Porteiro (Funcionário)** | `jose` | `senha123` | Teste da interface operacional restrita |

---

## 💻 Como Rodar Localmente (Desenvolvimento)

### Pré-requisitos
- **Python 3.10+** instalado ([python.org](https://www.python.org/))
- **Node.js 18+** instalado ([nodejs.org](https://nodejs.org/))
- **Git** instalado ([git-scm.com](https://git-scm.com/))

### Método Rápido via Script (Windows)

1. Clone o repositório:
   ```bash
   git clone https://github.com/luirton/gestaoCondominio.git
   cd gestaoCondominio
   ```
2. Dê um duplo clique no arquivo:
   ```bat
   start.bat
   ```
   *O script iniciará automaticamente o Backend na porta `8000`, o Frontend na porta `5173` e o Super Painel na porta `5174`.*

---

### Execução Manual Passo a Passo

#### 1. Backend (Django)
```bash
cd backend

# Crie o ambiente virtual
python -m venv venv

# Ative o ambiente virtual
# No Windows (PowerShell/CMD):
venv\Scripts\activate
# No Linux/Mac:
source venv/bin/activate

# Instale as dependências
pip install -r requirements.txt

# Crie o arquivo de configuração baseado no exemplo
copy .env.example .env    # Windows
# cp .env.example .env    # Linux/Mac

# Execute as migrações do banco de dados
python manage.py migrate

# Carregue os dados de teste (perfis, condomínio demo e usuários)
python manage.py seed_initial_data

# Inicie o servidor do backend
python manage.py runserver 127.0.0.1:8000
```
O backend estará acessível em: `http://127.0.0.1:8000/api/`

#### 2. Frontend (Vue.js)
Abra outro terminal:
```bash
cd frontend

# Instale as dependências do Node.js
npm install

# Inicie o servidor de desenvolvimento Vite
npm run dev
```
O frontend estará acessível em: `http://localhost:5173/`

#### 3. Super Painel Global
Abra um terceiro terminal:
```bash
cd admin-painel
python -m http.server 5174
```
O Super Painel estará acessível em: `http://localhost:5174/`

---

## 🌐 Como Subir em Servidor de Produção (Linux / VPS)

Este guia cobre o deploy profissional em um servidor **Ubuntu 22.04 / 24.04 LTS** utilizando **PostgreSQL**, **Gunicorn**, **Nginx** e **Certbot (SSL)**.

### 1. Preparação do Servidor (Ubuntu / Debian)

Conecte-se ao seu servidor via SSH:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv python3-dev libpq-dev postgresql postgresql-contrib nginx curl git
```

Instale o **Node.js (versão 20 LTS)**:
```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
```

---

### 2. Configuração do Banco de Dados PostgreSQL

Acesse o prompt do PostgreSQL:
```bash
sudo -u postgres psql
```

Crie o banco de dados e o usuário da aplicação:
```sql
CREATE DATABASE condominio_db;
CREATE USER condominio_user WITH PASSWORD 'DefinaUmaSenhaForteAqui123!';
ALTER ROLE condominio_user SET client_encoding TO 'utf8';
ALTER ROLE condominio_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE condominio_user SET timezone TO 'America/Sao_Paulo';
GRANT ALL PRIVILEGES ON DATABASE condominio_db TO condominio_user;
\q
```

---

### 3. Deploy do Backend (Django + Gunicorn)

Clone o projeto no diretório `/var/www/`:
```bash
cd /var/www/
sudo git clone https://github.com/luirton/gestaoCondominio.git
sudo chown -R $USER:$USER /var/www/gestaoCondominio
cd /var/www/gestaoCondominio/backend
```

Configure o ambiente virtual e as dependências:
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Crie e configure o arquivo `.env` de produção:
```bash
nano .env
```
Preencha com suas configurações de produção:
```env
DEBUG=False
SECRET_KEY=gere-uma-chave-longa-e-aleatoria-aqui
ALLOWED_HOSTS=api.seudominio.com.br,seudominio.com.br,127.0.0.1

DB_ENGINE=postgresql
DB_NAME=condominio_db
DB_USER=condominio_user
DB_PASSWORD=DefinaUmaSenhaForteAqui123!
DB_HOST=127.0.0.1
DB_PORT=5432

# E-mail em produção (ex: Gmail ou SMTP corporativo)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
DEFAULT_FROM_EMAIL=CondoGestão <notificacoes@seudominio.com.br>
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=seu-email@seudominio.com.br
EMAIL_HOST_PASSWORD=sua-senha-de-app

JWT_ACCESS_MINUTES=120
JWT_REFRESH_DAYS=7
```

Execute as migrações e colete os arquivos estáticos:
```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py seed_initial_data   # Ou python manage.py createsuperuser
```

#### Criar o Serviço Systemd para o Gunicorn
Crie o arquivo de serviço:
```bash
sudo nano /etc/systemd/system/condogestao.service
```

Cole o conteúdo abaixo (ajuste o usuário se necessário):
```ini
[Unit]
Description=Gunicorn daemon para CondoGestao Backend
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/gestaoCondominio/backend
ExecStart=/var/www/gestaoCondominio/backend/venv/bin/gunicorn \
          --access-logfile - \
          --workers 3 \
          --bind unix:/run/condogestao.sock \
          config.wsgi:application

[Install]
WantedBy=multi-user.target
```

Ajuste permissões, inicie e habilite o serviço:
```bash
sudo chown -R www-data:www-data /var/www/gestaoCondominio/backend
sudo systemctl start condogestao
sudo systemctl enable condogestao
sudo systemctl status condogestao
```

---

### 4. Deploy do Frontend (Vue.js + Vite)

Navegue até a pasta do frontend:
```bash
cd /var/www/gestaoCondominio/frontend
```

Crie o arquivo `.env.production`:
```bash
nano .env.production
```
Defina a URL de produção da sua API:
```env
VITE_API_URL=https://seudominio.com.br/api
```

Instale os pacotes e gere a compilação estática otimizada:
```bash
npm install
npm run build
```
Os arquivos otimizados serão gerados na pasta `/var/www/gestaoCondominio/frontend/dist/`.

---

### 5. Configuração do Nginx (Reverse Proxy + SPA)

Crie o arquivo de configuração do site no Nginx:
```bash
sudo nano /etc/nginx/sites-available/condogestao
```

Cole a configuração abaixo substituindo `seudominio.com.br` pelo seu domínio ou IP:
```nginx
server {
    listen 80;
    server_name seudominio.com.br www.seudominio.com.br;

    # Frontend Vue.js (SPA)
    location / {
        root /var/www/gestaoCondominio/frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # Backend Django REST API
    location /api/ {
        include proxy_params;
        proxy_pass http://unix:/run/condogestao.sock;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Arquivos Estáticos do Django Admin / DRF
    location /static/ {
        alias /var/www/gestaoCondominio/backend/staticfiles/;
    }

    # Uploads de Mídia
    location /media/ {
        alias /var/www/gestaoCondominio/backend/media/;
    }

    # Super Painel Global (Opcional - via subcaminho /super-admin/)
    location /super-admin/ {
        alias /var/www/gestaoCondominio/admin-painel/;
        index index.html;
        try_files $uri $uri/ /super-admin/index.html;
    }

    # Configurações de segurança e tamanho de upload
    client_max_body_size 20M;
}
```

Ative o site e reinicie o Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/condogestao /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

### 6. Certificado SSL Gratuito com Let's Encrypt

Para habilitar HTTPS gratuitamente com renovação automática:
```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d seudominio.com.br -d www.seudominio.com.br
```
O Certbot configurará automaticamente o redirecionamento HTTP para HTTPS e cuidará da renovação.

---

## 🐳 Deploy Alternativo com Docker e Docker Compose

Se preferir rodar toda a stack com contêineres Docker, crie um arquivo `docker-compose.yml` na raiz:

```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    restart: always
    environment:
      POSTGRES_DB: condominio_db
      POSTGRES_USER: condominio_user
      POSTGRES_PASSWORD: senha_segura_aqui
    volumes:
      - postgres_data:/var/lib/postgresql/data

  backend:
    build: ./backend
    restart: always
    command: gunicorn --bind 0.0.0.0:8000 config.wsgi:application
    environment:
      - DEBUG=False
      - DB_ENGINE=postgresql
      - DB_NAME=condominio_db
      - DB_USER=condominio_user
      - DB_PASSWORD=senha_segura_aqui
      - DB_HOST=db
      - DB_PORT=5432
    depends_on:
      - db

  frontend:
    build: ./frontend
    restart: always
    ports:
      - "80:80"
    depends_on:
      - backend

volumes:
  postgres_data:
```

Execute para subir:
```bash
docker-compose up -d --build
```

---

## 🧪 Suíte de Testes Automatizados

O sistema conta com testes automatizados cobrindo autenticação, autorização por perfil, isolamento por condomínio e auto-cadastro de moradores.

Para rodar os testes:
```bash
cd backend
python manage.py test core
```

Exemplo de saída esperada:
```text
Creating test database for alias 'default'...
......
----------------------------------------------------------------------
Ran 6 tests in 5.351s

OK
Destroying test database for alias 'default'...
```

---

## 📄 Licença

Este projeto é desenvolvido para fins de gestão condominial sob os termos de uso estabelecidos pela administração do condomínio.
