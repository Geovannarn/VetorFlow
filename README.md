# VetorFlow

Sistema desenvolvido para tratamento, validação, enriquecimento e armazenamento de dados cadastrais da Distribuidora Vetor.

O VetorFlow implementa um fluxo de processamento de dados a partir de uma base CSV, realizando normalização de campos, validações de qualidade, enriquecimento por meio de APIs externas, tratamento de inconsistências e persistência dos dados em PostgreSQL.

O projeto também disponibiliza uma API REST para gerenciamento dos registros de clientes e uma interface web para interação com o sistema.

## Objetivo

O projeto tem como objetivo estruturar um processo de tratamento de dados capaz de lidar com inconsistências presentes na base original, mantendo critérios definidos para normalização, validação, enriquecimento e resolução de divergências.

O fluxo desenvolvido contempla desde a entrada dos dados até seu armazenamento e disponibilização por meio da API REST.

## Tecnologias

**Python** — desenvolvimento do processamento e das regras de tratamento.

**Pandas** — leitura e processamento dos dados.

**Django** — estrutura da aplicação.

**Django REST Framework** — desenvolvimento da API REST.

**PostgreSQL** — armazenamento dos dados.

**Pytest** — testes automatizados.

**HTML, CSS e JavaScript** — desenvolvimento da interface web.

**Git / GitHub** — versionamento do projeto.

## Arquitetura do fluxo

```text
                   ┌─────────────────┐
                   │       CSV       │
                   └────────┬────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │  Normalização   │
                   └────────┬────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │    Validação    │
                   │   e Qualidade   │
                   └────────┬────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │ Enriquecimento  │
                   │     por CEP     │
                   └────────┬────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │    Bairros      │
                   │ Normalização /  │
                   │    Resolução    │
                   └────────┬────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │    Auditoria    │
                   └────────┬────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │   PostgreSQL    │
                   └────────┬────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │    API REST     │
                   └────────┬────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │    Frontend     │
                   └─────────────────┘
```

## Processamento dos dados

O processamento é organizado em etapas específicas para cada responsabilidade.

### Normalização

Foram implementados normalizadores para diferentes campos da base:

CNPJ;
Data;
E-mail;
Telefone;
Texto;
CEP.

O objetivo é reduzir diferenças de formatação e estabelecer um padrão para os dados antes das etapas seguintes.

### CEP

O tratamento do CEP considera diferentes formatos de entrada, incluindo valores com e sem hífen.

Os valores são validados e normalizados para um padrão de oito dígitos, considerando também situações de valores vazios ou inválidos.

### Integrações externas

O enriquecimento dos dados de CEP utiliza:

**ViaCEP:** utilizada como fonte principal de consulta.
**BrasilAPI:** utilizada como alternativa.

O projeto também possui um mecanismo de cache local para evitar consultas repetidas para CEPs já processados.

## Tratamento de bairros

O tratamento dos bairros está separado no diretório `neighborhood/`.

A etapa de normalização padroniza os nomes para permitir comparações entre diferentes representações do mesmo bairro.

Na etapa de resolução, o bairro informado no cadastro é comparado com o bairro retornado pela API.

Os resultados podem ser classificados como:

`convergente`
`informado`
`api`
`divergente`
`sem informação`

Quando existe divergência entre as informações disponíveis, o critério adotado é manter o bairro informado no cadastro em vez de substituí-lo automaticamente.

## Qualidade dos dados

O projeto possui verificações específicas para avaliar a qualidade da base processada.

Entre os checks implementados estão:

Identificação de colunas obrigatórias ausentes;
Identificação de valores nulos;
Identificação de registros duplicados;
Verificação da existência de registros.

A partir dos resultados dos checks, são calculadas métricas como:

Total de registros;
Total de valores nulos;
Total de registros duplicados;
Percentual de nulos;
Percentual de duplicados.

## Auditoria

O projeto possui um módulo de auditoria, localizado em `audit/`, destinado ao registro das operações realizadas durante o processamento dos dados.

Esse módulo permite manter registros relacionados às alterações e ao tratamento das informações, contribuindo para o acompanhamento do processamento.

## Banco de dados

O PostgreSQL é utilizado para persistência dos dados processados.

A conexão com o banco está centralizada em:

```text
database/
└── connection.py
```

As credenciais são obtidas por meio de variáveis de ambiente configuradas no arquivo `.env`.

Exemplo:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=nome_do_banco
DB_USER=usuario
DB_PASSWORD=senha
```

O arquivo `.env` não deve ser versionado. O projeto disponibiliza um `.env.example` como referência para configuração das variáveis necessárias.

## API REST

A API foi desenvolvida utilizando Django REST Framework e permite o gerenciamento dos clientes armazenados no PostgreSQL.

### Operações

| Método | Operação |
|:---:|---|
| `GET` | Consulta de clientes |
| `POST` | Cadastro de cliente |
| `PUT` | Atualização de cliente |
| `DELETE` | Exclusão de cliente |

A API utiliza a conexão com o PostgreSQL para realizar as operações sobre os registros.

## Frontend

O projeto possui uma interface web localizada no diretório `frontend/`.

A interface permite a interação com as funcionalidades disponibilizadas pelo sistema, integrando a apresentação das informações com os recursos de processamento e gerenciamento de clientes.

## Testes automatizados

Os testes automatizados são executados utilizando **Pytest**.

Para executar a suíte de testes:

```bash
pytest
```

Os testes abrangem diferentes partes do projeto, incluindo:

API;
Integração de CEP;
Carregamento dos dados;
Verificações de qualidade.

## Estrutura do projeto

```text
VetorFlow/
├── .idea/
├── .pytest_cache/
├── .venv/
├── api/
├── audit/
├── config/
├── data/
├── database/
├── docs/
├── frontend/
├── integrations/
├── neighborhood/
├── normalizers/
├── pipeline/
├── src/
├── test/
├── .env
├── .env.example
├── .gitignore
├── db.sqlite3
├── exceptions.py
├── logging_config.py
├── Makefile
├── manage.py
├── pytest.ini
├── README.md
├── Relatório_tradeoffs.md
├── requirements.txt
└── settings.py
```

### Responsabilidades dos diretórios e arquivos

| Diretório/arquivo | Responsabilidade |
|---|---|
| `api/` | Endpoints e componentes da API REST |
| `audit/` | Registros de auditoria |
| `config/` | Configurações do projeto Django |
| `data/` | Arquivos utilizados no processamento |
| `database/` | Conexão e acesso ao PostgreSQL |
| `docs/` | Documentação técnica complementar |
| `frontend/` | Arquivos da interface web |
| `integrations/` | Integrações externas e mecanismo de cache |
| `neighborhood/` | Normalização e resolução de bairros |
| `normalizers/` | Normalização dos campos cadastrais |
| `pipeline/` | Processamento, carregamento e qualidade dos dados |
| `src/` | Organização do código-fonte |
| `test/` | Testes automatizados |
| `manage.py` | Ponto de entrada para comandos administrativos do Django |
| `pytest.ini` | Configurações do Pytest |
| `requirements.txt` | Dependências do projeto |
| `.env` | Variáveis de ambiente locais |
| `.env.example` | Modelo de configuração das variáveis de ambiente |
| `Relatório_tradeoffs.md` | Documentação das decisões e dos trade-offs do projeto |

## Configuração

### 1. Clonar o repositório

```bash
git clone https://github.com/Geovannarn/VetorFlow.git
cd VetorFlow
```

### 2. Criar o ambiente virtual

No Windows:

```powershell
python -m venv .venv
```

### 3. Ativar o ambiente virtual

```powershell
.\.venv\Scripts\Activate.ps1
```

### 4. Instalar as dependências

```bash
pip install -r requirements.txt
```

### 5. Configurar as variáveis de ambiente

Crie o arquivo `.env` na raiz do projeto e configure os dados de conexão com o PostgreSQL, utilizando o `.env.example` como referência.

### 6. Verificar a configuração do Django

```bash
python manage.py check
```

### 7. Executar os testes

```bash
pytest
```

## Versionamento

O desenvolvimento foi organizado utilizando Git e GitHub.

As funcionalidades foram separadas em branches de acordo com suas responsabilidades, como:

```text
feature/database-schema
feature/field-normalizers
feature/postal-code-enrichment
feature/neighborhood-normalization
feature/neighborhood-resolver
feature/audit-trail
feature/pipeline-and-load
feature/data-quality
feature/rest-api
```

Após o desenvolvimento e a validação das funcionalidades, as alterações foram incorporadas à branch `main`.

## Organização do desenvolvimento

O acompanhamento das atividades foi realizado utilizando Trello, seguindo uma organização baseada em práticas de Agile e SCRUM.

As tarefas foram organizadas em etapas de:

```text
Backlog
   ↓
Fazer
   ↓
Desenvolvimento
   ↓
Em Testes
   ↓
Concluído
```

Essa organização permitiu acompanhar o andamento das atividades, visualizar as tarefas pendentes e controlar a evolução das funcionalidades durante o desenvolvimento.

## Documentação

A documentação complementar está organizada no diretório `docs/`.

O projeto também possui o arquivo `Relatório_tradeoffs.md`, que apresenta as principais decisões tomadas durante o desenvolvimento, os critérios utilizados e os pontos considerados na implementação das soluções.

---

**VetorFlow**
