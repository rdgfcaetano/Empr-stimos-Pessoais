# Sistema Web de Gestão de Empréstimos

Sistema profissional para gestão de empréstimos particulares, com backend FastAPI, frontend React + TypeScript, autenticação JWT, auditoria, notificações e controle de acesso por perfil.

## Stack

- Backend: FastAPI, SQLAlchemy 2, Pydantic, JWT, Alembic-ready
- Frontend: React, TypeScript, Vite
- Banco: SQLite no desenvolvimento; PostgreSQL via Docker Compose
- Segurança: hash de senha com bcrypt, validação de schemas, autorização no backend

## Como rodar

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

A API cria as tabelas automaticamente em desenvolvimento e cadastra um administrador:

- Email: `admin@local`
- Senha: `Admin123!`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Abra `http://localhost:5173`.

### Docker

```bash
docker compose up --build
```

## Deploy de teste

### Backend no Render

1. Suba este projeto para o GitHub.
2. No Render, crie um Blueprint apontando para o repositorio.
3. O arquivo `render.yaml` cria a API FastAPI e um banco PostgreSQL.
4. Confirme que a variavel `PYTHON_VERSION` esta como `3.12.8`.
5. Depois que o frontend tiver dominio, configure `CORS_ORIGINS` no Render:

```text
https://seu-frontend.vercel.app
```

### Frontend na Vercel

1. Importe o mesmo repositorio na Vercel.
2. Configure o diretorio raiz como `frontend`.
3. Configure a variavel de ambiente:

```text
VITE_API_URL=https://sua-api.onrender.com/api
```

4. Faca o deploy.

### Dominio

Use um subdominio para cada parte:

```text
app.seudominio.com -> frontend
api.seudominio.com -> backend
```

## Funcionalidades

- Login JWT
- Perfis administrador e sócio
- Isolamento de carteira por sócio validado no backend
- CRUD de usuários, clientes e empréstimos
- Registro de pagamentos parciais e totais
- Cálculo automático de juros, multa, atraso e total devido
- Dashboard por perfil com movimento mensal
- Logs permanentes de auditoria
- Central de notificações para administradores
- Interface responsiva com modo escuro, filtros, tabelas e confirmação de exclusão
- Testes automatizados iniciais para autorização, pagamentos e área administrativa
- Migrations Alembic versionadas

## Estrutura

```text
backend/app
  api/          rotas HTTP
  core/         config, segurança e dependências
  db/           sessão e base ORM
  models/       modelos SQLAlchemy
  schemas/      schemas Pydantic
  services/     regras de negócio, auditoria, cálculos
frontend/src
  components/   layout e UI
  pages/        telas principais
  services/     cliente HTTP e autenticação
```

## Testes

```bash
cd backend
pytest
```

## Estado Atual

O frontend compila com `npm run build`. A validação local do backend depende de Python ou Docker disponíveis na máquina.
