# Documentação da API REST — VetorFlow

API desenvolvida com **Django REST Framework** para o gerenciamento dos clientes da Distribuidora Vetor armazenados no **PostgreSQL**. Também expõe endpoints de consulta do módulo de **benchmark**.

## Sumário

1. [Visão geral](#1-visão-geral)
2. [Como executar](#2-como-executar)
3. [Endpoints](#3-endpoints)
4. [Modelo do cliente](#4-modelo-do-cliente)
5. [Regras de validação](#5-regras-de-validação)
6. [Exemplos de uso](#6-exemplos-de-uso)
7. [Códigos de resposta e erros](#7-códigos-de-resposta-e-erros)
8. [Auditoria das operações](#8-auditoria-das-operações)
9. [Endpoints de benchmark](#9-endpoints-de-benchmark)
10. [Autenticação](#10-autenticação)
11. [Limitações conhecidas](#11-limitações-conhecidas)
12. [Testes da API](#12-testes-da-api)

## 1. Visão geral

| Item | Valor |
|---|---|
| Framework | Django REST Framework |
| Banco de dados | PostgreSQL (tabela `usuarios`) |
| Formato | JSON |
| URL base (local) | `http://127.0.0.1:8000/api/` |
| Recurso principal | `clientes` |
| Acesso ao banco | SQL direto via `database/connection.py` (função `conectar`) |

A API permite consultar, cadastrar, atualizar e excluir clientes. Os dados enviados passam pelos mesmos normalizadores usados no pipeline (`normalizers/`), garantindo que o banco mantenha o padrão definido no tratamento.

## 2. Como executar

```bash
# 1. ativar o ambiente virtual (Windows)
.\.venv\Scripts\Activate.ps1

# 2. instalar as dependências
pip install -r requirements.txt

# 3. configurar o .env com os dados do PostgreSQL (use o .env.example)

# 4. iniciar o servidor
python manage.py runserver
```

## 3. Endpoints

### Clientes

| Método | Rota | Descrição |
|:---:|---|---|
| `GET` | `/api/clientes/` | Lista todos os clientes, ordenados por `id_cliente` |
| `GET` | `/api/clientes/{id_cliente}/` | Consulta um cliente pelo código |
| `POST` | `/api/clientes/` | Cadastra um novo cliente |
| `PUT` | `/api/clientes/{id_cliente}/` | Atualiza os campos enviados de um cliente |
| `DELETE` | `/api/clientes/{id_cliente}/` | Exclui um cliente |

### Benchmark

| Método | Rota | Descrição |
|:---:|---|---|
| `GET` | `/api/benchmark/` | Resultados do benchmark em JSON |
| `GET` | `/api/benchmark/relatorio/` | Relatório comparativo em HTML |
| `GET` | `/api/benchmark/grafico/{nome}/` | Gráfico em PNG |

## 4. Modelo do cliente

Campos da tabela `usuarios`:

| Campo | Obrigatório | Descrição |
|---|:---:|---|
| `id_cliente` | Sim (no `POST`) | Código do cliente, informado por quem cadastra |
| `razao_social` | Sim | Nome do cliente |
| `cnpj` | Não | CNPJ, armazenado com 14 dígitos |
| `telefone` | Não | Telefone com 10 ou 11 dígitos, gravado com o prefixo `+55` |
| `email` | Não | E-mail em formato válido |
| `bairro` | Não | Bairro |
| `cep` | Não | CEP, armazenado com 8 dígitos |
| `cidade` | Não | Cidade |
| `uf` | Não | Sigla do estado, 2 letras maiúsculas |
| `cadastro` | Não | Data de cadastro |
| `responsavel` | Não | Vendedor responsável |

Campos enviados vazios (`""`) ou ausentes são gravados como `NULL`.

## 5. Regras de validação

Aplicadas no `POST` e no `PUT` antes de gravar no banco:

| Campo | Regra | Mensagem de erro |
|---|---|---|
| `cnpj` | Normalizado para 14 dígitos | CNPJ precisa ter 14 dígitos. |
| `telefone` | Padronizado: remove o DDI `55` se houver mais de 11 dígitos, exige 10 ou 11 dígitos e grava com `+55` | Telefone precisa ter 10 ou 11 dígitos. |
| `email` | Normalizado e validado | E-mail inválido. |
| `cep` | Normalizado para 8 dígitos | CEP precisa ter 8 dígitos. |
| `uf` | 2 letras, convertidas para maiúsculas | UF precisa ter 2 letras. |
| `cadastro` | Aceita `AAAA-MM-DD` ou `DD/MM/AAAA` | Data de cadastro inválida. Use AAAA-MM-DD ou DD/MM/AAAA. |
| `razao_social` | Não pode ser vazia | Informe a razão social do cliente. |
| `id_cliente` | Obrigatório no `POST` e único | Informe o código do cliente. |

Quando há mais de um campo inválido, as mensagens são retornadas juntas no campo `erro`.

## 6. Exemplos de uso

### Listar clientes

```http
GET /api/clientes/
```

### Consultar um cliente

```http
GET /api/clientes/1/
```

Resposta `200`: objeto com as colunas da tabela `usuarios`.

### Cadastrar cliente

```http
POST /api/clientes/
Content-Type: application/json
```

```json
{
  "id_cliente": "101",
  "razao_social": "Mercado Exemplo LTDA",
  "cnpj": "12.345.678/0001-90",
  "telefone": "(61) 99999-8888",
  "email": "contato@exemplo.com.br",
  "bairro": "Águas Claras",
  "cep": "71900-000",
  "cidade": "Brasília",
  "uf": "df",
  "cadastro": "15/01/2026",
  "responsavel": "Nome do Vendedor"
}
```

Resposta `201`:

```json
{
  "mensagem": "Cliente criado com sucesso.",
  "id_cliente": "101"
}
```

Os valores são gravados já padronizados: CNPJ com 14 dígitos, telefone com prefixo `+55` (`+5561999998888`), CEP com 8 dígitos, `uf` como `DF` e a data no formato `AAAA-MM-DD`.

### Atualizar cliente

Envie **somente os campos que deseja alterar**.

```http
PUT /api/clientes/101/
Content-Type: application/json
```

```json
{
  "telefone": "6133334444",
  "bairro": "Taguatinga"
}
```

Resposta `200`:

```json
{
  "mensagem": "Cliente atualizado com sucesso."
}
```

### Excluir cliente

```http
DELETE /api/clientes/101/
```

Resposta `200`:

```json
{
  "mensagem": "Cliente excluído com sucesso."
}
```

### Exemplo com `curl`

```bash
curl -X GET http://127.0.0.1:8000/api/clientes/
```

## 7. Códigos de resposta e erros

| Código | Significado | Quando ocorre |
|:---:|---|---|
| `200 OK` | Sucesso | Consulta, atualização ou exclusão realizada |
| `201 Created` | Criado | Cliente cadastrado |
| `400 Bad Request` | Requisição inválida | Campo inválido, código ou razão social ausente, nenhum campo enviado no `PUT`, ou dado rejeitado pelo banco |
| `404 Not Found` | Não encontrado | Cliente inexistente em `GET`, `PUT` ou `DELETE` |
| `409 Conflict` | Conflito | `id_cliente` já cadastrado |
| `500 Internal Server Error` | Erro interno | Falha inesperada do banco |

Todas as respostas de erro seguem o formato:

```json
{
  "erro": "Descrição do problema."
}
```

### Erros vindos do banco de dados

Erros do PostgreSQL das classes `22` (dado inválido) e `23` (violação de restrição) são traduzidos para mensagens legíveis e retornam `400`, com o código SQL no campo `codigo`:

| Código SQL | Mensagem |
|---|---|
| `23502` | A coluna não pode ficar vazia e não tem valor padrão |
| `23505` | Valor duplicado na restrição |
| `22001` | Texto maior que o tamanho da coluna |
| `22P02` | Valor em formato inválido para o tipo da coluna |

Exemplo:

```json
{
  "erro": "Um dos textos é maior que o tamanho da coluna. (...)",
  "codigo": "22001"
}
```

Em caso de erro, a transação sofre `rollback`, e a conexão é sempre fechada ao final da requisição.

## 8. Auditoria das operações

O módulo `audit/` grava um arquivo de log (`audit/audit.log`) com dois tipos de linha:

| Tipo | Quem registra | O que registra |
|---|---|---|
| `ACESSO` | Middleware (`AuditoriaMiddleware`) | **Toda** requisição (exceto `/static/`): método, caminho e código de resposta |
| `OPERACAO` | A view de clientes (`registrar_operacao`) | Apenas `POST`, `PUT` e `DELETE`: método, rota, `id_cliente`, resultado, IP e, no `POST` e no `PUT`, os dados gravados |

As consultas (`GET`) aparecem só como `ACESSO`, sem detalhes. Quebras de linha nos textos são removidas para manter uma linha por registro.

Exemplo:

```text
23/11/2026 14:02:10 | OPERACAO | 127.0.0.1 | POST /api/clientes/ | cliente: 101 | sucesso | dados: {...}
23/11/2026 14:02:10 | ACESSO | 127.0.0.1 | POST /api/clientes/ -> 201
```

O arquivo `audit.log` não é versionado (está no `.gitignore`).

## 9. Endpoints de benchmark

Endpoints somente de leitura, que servem os resultados gerados pelo módulo `benchmark/`.

### `GET /api/benchmark/`

Retorna os resultados em `resultados.json`.

```json
{
  "existe": true,
  "gerado_em": 1763900000.0,
  "resultados": [],
  "graficos": [
    { "nome": "exemplo", "url": "/api/benchmark/grafico/exemplo/" }
  ]
}
```

Se o benchmark ainda não foi executado, retorna `{"existe": false, "resultados": [], "graficos": []}`.

### `GET /api/benchmark/relatorio/`

Retorna o `relatorio.html` gerado. Responde `404` se o arquivo não existir.

### `GET /api/benchmark/grafico/{nome}/`

Retorna a imagem PNG do gráfico. Responde `404` se o nome não existir.

## 10. Autenticação

Nesta versão, a API **não exige autenticação**. O `REST_FRAMEWORK` (em `config/settings.py`) não define classes de permissão, então vale o padrão `AllowAny` do Django REST Framework: qualquer cliente com acesso à URL pode consultar, criar, alterar e excluir registros. O uso previsto é em ambiente acadêmico local.

Pontos relacionados à segurança já tratados:

- A chave secreta (`DJANGO_SECRET_KEY`), o modo `DEBUG` e os hosts permitidos (`DJANGO_ALLOWED_HOSTS`) são lidos do `.env`.
- As credenciais do banco ficam no `.env` (`DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`), fora do repositório.
- As consultas ao banco usam parâmetros (`%s`), o que evita injeção de SQL nos valores enviados.

Para uso em produção, seria necessário configurar autenticação (token ou sessão) e permissões por operação.

## 11. Limitações conhecidas

- **Sem autenticação** (ver seção 10). Em produção seria necessário token ou sessão, além de permissões por tipo de operação.
- **`PUT` funciona como atualização parcial**: apenas os campos enviados são alterados.
- **Sem paginação**: `GET /api/clientes/` retorna todos os registros de uma vez.
- **O bairro não passa pela resolução do pipeline**: na API ele é gravado como enviado. A normalização e a resolução com o CEP (módulo `neighborhood/`) acontecem apenas no processamento em lote. O mesmo vale para o preenchimento de cidade e UF a partir do CEP.
- **`DELETE` retorna `200` com mensagem** (e não `204`), para manter o mesmo formato JSON das demais respostas.
- **A validação ocorre antes da checagem de existência no `PUT`**: dados inválidos enviados para um cliente inexistente retornam `400`, e não `404`.
- **O log de auditoria fica fora do repositório**, então o histórico de operações não acompanha o código no GitHub.
- **A API responde sempre em JSON**: apenas o renderizador JSON está ativo, então a interface navegável do DRF fica desligada.
- **A chave secreta tem um valor padrão de desenvolvimento** no código (`django-insecure-...`), usado se `DJANGO_SECRET_KEY` não estiver no `.env`. Em produção, ela deve ser sempre definida no ambiente e `DJANGO_DEBUG` deve ser `False`.

## 12. Testes da API

Os testes automatizados estão na pasta `test/` e rodam com:

```bash
pytest
```