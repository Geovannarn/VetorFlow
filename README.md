# VetorFlow

Sistema para tratamento, validação, enriquecimento e armazenamento de dados cadastrais da Distribuidora Vetor.

A partir de uma base CSV, o VetorFlow normaliza os campos, valida a qualidade dos dados, consulta APIs de CEP, resolve divergências de bairro e grava os registros em PostgreSQL. O projeto também oferece uma API REST para gerenciar os clientes, uma interface web e um módulo de benchmark que mede o desempenho do sistema com milhares ou milhões de registros.

## Sumário

- [Objetivo](#objetivo)
- [Tecnologias](#tecnologias)
- [Arquitetura do fluxo](#arquitetura-do-fluxo)
- [Processamento dos dados](#processamento-dos-dados)
- [Tratamento de bairros](#tratamento-de-bairros)
- [Qualidade dos dados](#qualidade-dos-dados)
- [Auditoria](#auditoria)
- [Banco de dados](#banco-de-dados)
- [API REST](#api-rest)
- [Frontend](#frontend)
- [Benchmark](#benchmark)
- [Testes automatizados](#testes-automatizados)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Configuração](#configuração)
- [Versionamento](#versionamento)
- [Organização do desenvolvimento](#organização-do-desenvolvimento)
- [Documentação](#documentação)
- [Próximos passos](#próximos-passos)

  ## Objetivo

Estruturar um processo de tratamento de dados capaz de lidar com as inconsistências da base original, mantendo critérios definidos para normalização, validação, enriquecimento e resolução de divergências.

O projeto cobre a entrada dos dados, o armazenamento no PostgreSQL e a disponibilização por meio de uma API REST e de uma interface web.

## Tecnologias

- **Python**: processamento e regras de tratamento.
- **Pandas**: leitura e processamento dos dados.
- **Django**: estrutura da aplicação.
- **Django REST Framework**: API REST.
- **PostgreSQL** (com **psycopg**): armazenamento dos dados.
- **Requests**: consultas às APIs de CEP e testes da API no benchmark.
- **Pytest**: testes automatizados.
- **psutil e Matplotlib**: medição de recursos e gráficos do benchmark.
- **HTML, CSS e JavaScript**: interface web.
- **Git / GitHub**: versionamento.

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

Cada etapa é um módulo independente, descrito nas seções abaixo.

## Processamento dos dados

### Normalização

Há normalizadores para os principais campos da base:

- CNPJ
- Data
- E-mail
- Telefone
- Texto
- CEP

O objetivo é reduzir as diferenças de formatação e estabelecer um padrão para os dados antes das etapas seguintes.

O CNPJ é validado pelos dígitos verificadores, além do tamanho e da rejeição de sequências repetidas.

### CEP

O tratamento do CEP aceita valores com e sem hífen, valida o tamanho e normaliza para oito dígitos. Valores vazios ou inválidos são tratados como tal.

### Integrações externas

O enriquecimento dos dados de CEP usa:

- **ViaCEP**: fonte principal de consulta.
- **BrasilAPI**: alternativa quando o ViaCEP não responde.

Um cache local evita consultas repetidas para CEPs já processados.

## Tratamento de bairros

O tratamento dos bairros fica em `neighborhood/`, em duas etapas: normalização e resolução.

### Normalização

A normalização padroniza o nome do bairro para permitir comparações entre representações diferentes do mesmo lugar. Ela remove acentos, converte para minúsculas, tira pontuação e espaços repetidos, remove a UF no final (como ` - DF` e `/DF`) e, quando o nome vem com parênteses, usa o texto de dentro deles.

| O que veio | O que ficou |
|---|---|
| `Águas Claras` | `aguas claras` |
| `AGUAS CLARAS` | `aguas claras` |
| `Aguas claras` | `aguas claras` |
| `Aguas Claras - DF` | `aguas claras` |
| `Águas Claras/DF` | `aguas claras` |
| `Taguatinga - DF` | `taguatinga` |
| `guara - df` | `guara` |
| `Sul (Águas Claras)` | `aguas claras` |
| `Norte (Aguas Claras)` | `aguas claras` |
| `Guará II` | `guara ii` |
| `   Vicente   Pires  ` | `vicente pires` |
| `V. Pires` | `v pires` |
| (vazio) | sem valor |

Abreviações como `V. Pires` e `Vte Pires` não são ampliadas na normalização. Elas são unificadas com `Vicente Pires` na etapa de resolução.

### Resolução

Na resolução, o bairro informado no cadastro é comparado com o bairro retornado pela API de CEP. Os dois passam pela normalização antes da comparação. O resultado traz o bairro final e a classificação.

| Informado no cadastro | Retornado pela API | Bairro final | Classificação |
|---|---|---|---|
| `Sul (Águas Claras)` | `Águas Claras` | `aguas claras` | `convergente` |
| `V. Pires` | `Vicente Pires` | `vicente pires` | `convergente` |
| `Vte Pires` | `Vicente Pires` | `vicente pires` | `convergente` |
| `Águas Claras Norte` | `Águas Claras` | `aguas claras norte` | `convergente` |
| `Guará` | `Guará II` | `guara ii` | `convergente` |
| `Taguatinga - DF` | `Ceilândia` | `taguatinga` | `divergente` |
| (vazio) | `Guará` | `guara` | `api` |
| `Taguatinga` | (sem retorno) | `taguatinga` | `informado` |
| (vazio) | (sem retorno) | sem valor | `sem informação` |

As classificações significam:

| Classificação | Significado |
|---|---|
| `convergente` | Os dois bairros são o mesmo, ou um é a versão mais completa do outro. Nesse caso fica o nome mais específico |
| `informado` | Só existe o bairro do cadastro, e ele é mantido |
| `api` | Só existe o bairro devolvido pela API, e ele é usado |
| `divergente` | Os dois existem e são diferentes |
| `sem informação` | Nenhum dos dois existe |

Quando há divergência, o critério adotado é manter o bairro informado no cadastro (`taguatinga` no exemplo acima), em vez de substituí-lo automaticamente pelo da API.

## Qualidade dos dados

Os checks em `pipeline/checks.py` avaliam a base processada:

- colunas obrigatórias ausentes;
- valores nulos e campos vazios;
- registros duplicados;
- existência de registros.

A partir deles, `pipeline/metrics.py` calcula:

- total de registros;
- total de nulos e percentual de nulos;
- total de duplicados e percentual de duplicados;
- percentual de nulos por coluna.

## Auditoria

O módulo `audit/` grava o arquivo `audit/audit.log` com dois tipos de linha:

| Tipo | O que registra |
|---|---|
| `ACESSO` | Data e hora, IP, método, URL acessada e código de resposta de cada requisição |
| `OPERACAO` | Criação, alteração e exclusão de clientes: qual cliente, o resultado e os dados enviados |

O registro de acessos é feito por um middleware do Django (`audit/middleware.py`). O arquivo de log contém dados de clientes e não deve ser versionado.

## Banco de dados

O PostgreSQL guarda os dados processados. A conexão fica centralizada em:

```text
database/
└── connection.py
```

As credenciais vêm de variáveis de ambiente, definidas no arquivo `.env`:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=nome_do_banco
DB_USER=usuario
DB_PASSWORD=senha
```

Opcionalmente, também são lidas as variáveis `DJANGO_SECRET_KEY`, `DJANGO_DEBUG` e `DJANGO_ALLOWED_HOSTS`.

O `.env` não deve ser versionado. O `.env.example` serve de modelo.

Os clientes ficam na tabela `usuarios`, com as colunas `id_cliente`, `razao_social`, `cnpj`, `telefone`, `email`, `bairro`, `cep`, `cidade`, `uf`, `cadastro` e `responsavel`.

## API REST

A API usa Django REST Framework e gerencia os clientes da tabela `usuarios`.

| Método | Rota | Operação |
|:---:|---|---|
| `GET` | `/api/clientes/` | Lista os clientes |
| `GET` | `/api/clientes/<id_cliente>/` | Consulta um cliente |
| `POST` | `/api/clientes/` | Cadastra um cliente |
| `PUT` | `/api/clientes/<id_cliente>/` | Atualiza um cliente |
| `DELETE` | `/api/clientes/<id_cliente>/` | Exclui um cliente |
| `GET` | `/api/benchmark/` | Resultados do último benchmark (JSON) |
| `GET` | `/api/benchmark/relatorio/` | Relatório HTML do benchmark |
| `GET` | `/api/benchmark/grafico/<nome>/` | Gráfico do benchmark (PNG) |

## Frontend

A interface web fica em `frontend/` e tem quatro áreas:

- **Consulta de CEP**: ViaCEP com BrasilAPI de reserva e cache no navegador.
- **Clientes**: cadastro, busca e exclusão de clientes, usando a API REST.
- **Importação**: envio de um CSV com limpeza de CNPJ, telefone, CEP e data, e download dos registros limpos e dos registros com erro.
- **Benchmark**: tabelas, gráficos e link para o relatório completo do último benchmark.

Regras de limpeza da importação:

| Campo | Regra |
|---|---|
| CNPJ | 14 dígitos; rejeita sequências repetidas |
| Telefone | 10 ou 11 dígitos; remove o 55 e padroniza para `+55` |
| CEP | 8 dígitos, formatado como `00000-000` |
| Data | `AAAA-MM-DD`, `DD/MM/AAAA`, `DD-MM-AAAA` ou `Mês DD, AAAA` |

## Benchmark

O módulo `benchmark/` mede o desempenho do VetorFlow com dados sintéticos de 10 mil a 5 milhões de registros (clientes com nome, CPF/CNPJ fictício, CEP, endereço, região administrativa e identificador). Os dados já saem com defeitos propositais (documentos inválidos, CEPs ruins, campos vazios e ids repetidos) para testar a qualidade.

### O que é medido

| Etapa | O que mede |
|---|---|
| Geração | Tempo para gerar a base sintética |
| Extração | Leitura do CSV em partes e de uma vez só |
| Transformação | Normalização e validação de CPF/CNPJ, validação de CEP, duplicados, vazios, correções e preparo para carga, cada uma com seu tempo |
| Carga | Gravação no PostgreSQL de quatro jeitos: um a um com commit em cada linha, um a um com um commit só, em lotes e com `COPY` |
| Consultas no banco | Contagem, busca por id, leitura de 100 mil linhas e filtro por região com e sem índice |
| API | Listagem, busca por id e operações de criar, consultar, atualizar e excluir |

Em cada etapa são registrados tempo, uso de CPU, memória RAM, registros por segundo, taxa de erros e registros rejeitados.

### Preparação

Instale as bibliotecas extras:

```bash
pip install psutil matplotlib
```

Crie, uma vez, a tabela usada pelo teste de carga (ela é separada da tabela `usuarios`):

```sql
CREATE TABLE benchmark_clientes (
    id_cliente TEXT PRIMARY KEY,
    nome TEXT,
    documento TEXT,
    cep TEXT,
    endereco TEXT,
    regiao_administrativa TEXT
);
```

### Execução

Na pasta principal do projeto:

```bash
python -m benchmark.executar
```

As opções ficam no começo do arquivo `benchmark/executar.py`:

| Opção | Função |
|---|---|
| `VOLUMES` | Volumes testados. `config.PERFIS["rapido"]` usa 10 mil e 100 mil; `"completo"` vai de 10 mil a 5 milhões |
| `TESTAR_BANCO` | Liga ou desliga os testes de gravação no PostgreSQL |
| `TESTAR_API` | Liga ou desliga os testes da API (o servidor precisa estar rodando) |
| `APAGAR_ARQUIVOS_NO_FINAL` | Apaga os CSVs gerados ao terminar |

Para testar a API, em outro terminal:

```bash
python manage.py runserver --noreload
```

### Resultados

Tudo é gravado em `data/benchmark/resultados/`:

- `relatorio.html`: relatório com conclusões, tabelas, gráficos e estimativas de escalabilidade;
- `resultados.csv` e `resultados.json`: todos os números medidos;
- `graficos/`: gráficos em PNG.

Os mesmos resultados aparecem na seção **Benchmark** da interface web.

### Cuidados

- O teste de carga só usa a tabela `benchmark_clientes`. A tabela `usuarios` não é alterada pela carga.
- A tabela `benchmark_clientes` é esvaziada a cada teste.
- Antes de medir, o benchmark confere se as regras de CPF e CNPJ aceitam documentos válidos conhecidos. Se não aceitarem, ele para e avisa.
- A pasta `data/benchmark/` não é versionada.

## Testes automatizados

Os testes usam **Pytest**:

```bash
pytest
```

Eles cobrem:

- API;
- normalização e integração de CEP;
- carregamento dos dados;
- verificações de qualidade.

## Estrutura do projeto

```text
VetorFlow/
├── api/                  # endpoints da API REST (clientes e benchmark)
├── audit/                # auditoria: logger e middleware
├── benchmark/            # módulo de benchmark
├── config/               # configurações do Django
├── data/
│   ├── raw/              # CSV de origem
│   ├── processed/        # saída do processamento
│   └── benchmark/        # dados e resultados do benchmark (não versionado)
├── database/             # conexão com o PostgreSQL
├── docs/                 # documentação técnica complementar
├── frontend/
│   ├── static/           # CSS e JavaScript
│   └── templates/        # index.html
├── integrations/         # ViaCEP, BrasilAPI e cache
├── neighborhood/         # normalização e resolução de bairros
├── normalizers/          # normalização dos campos cadastrais
├── pipeline/             # carregamento, checks e métricas
├── test/                 # testes automatizados
├── .env.example
├── .gitignore
├── manage.py
├── pytest.ini
├── README.md
├── Relatório_tradeoffs.md
└── requirements.txt
```

### Responsabilidades

| Diretório/arquivo | Responsabilidade |
|---|---|
| `api/` | Endpoints e componentes da API REST |
| `audit/` | Registro de acessos e operações |
| `benchmark/` | Testes de desempenho, gráficos e relatório |
| `config/` | Configurações do projeto Django |
| `data/` | Arquivos de entrada, saída e resultados do benchmark |
| `database/` | Conexão com o PostgreSQL |
| `docs/` | Documentação técnica complementar |
| `frontend/` | Interface web |
| `integrations/` | Integrações externas e cache de CEP |
| `neighborhood/` | Normalização e resolução de bairros |
| `normalizers/` | Normalização dos campos cadastrais |
| `pipeline/` | Carregamento, qualidade e métricas |
| `test/` | Testes automatizados |
| `manage.py` | Comandos administrativos do Django |
| `pytest.ini` | Configuração do Pytest |
| `requirements.txt` | Dependências do projeto |
| `.env.example` | Modelo das variáveis de ambiente |
| `Relatório_tradeoffs.md` | Decisões e trade-offs do projeto |

## Configuração

### 1. Clonar o repositório

```bash
git clone https://github.com/Geovannarn/VetorFlow.git
cd VetorFlow
```

### 2. Criar o ambiente virtual

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

Crie o arquivo `.env` na raiz do projeto com os dados de conexão do PostgreSQL, usando o `.env.example` como referência.

### 6. Verificar a configuração do Django

```bash
python manage.py check
```

### 7. Executar os testes

```bash
pytest
```

### 8. Iniciar o servidor

```bash
python manage.py runserver
```

A interface fica em `http://127.0.0.1:8000/`.

## Versionamento

O desenvolvimento usa Git e GitHub. As funcionalidades foram separadas em branches por responsabilidade:

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

Depois de desenvolvidas e validadas, as alterações foram incorporadas à branch `main`.

## Organização do desenvolvimento

O acompanhamento das atividades foi feito no Trello, com práticas de Agile e Scrum. As tarefas passaram por estas etapas:

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

Essa organização permitiu acompanhar o andamento, visualizar as tarefas pendentes e controlar a evolução das funcionalidades.

## Documentação

O arquivo `Relatório_tradeoffs.md`, na raiz do projeto, apresenta as principais decisões tomadas, os critérios usados e os pontos considerados na implementação. O diretório `docs/` é destinado à documentação técnica complementar.

## Próximos passos

- Integrar ao `pipeline/loaders.py` os normalizadores, o enriquecimento por CEP e a resolução de bairros, para que o carregamento passe por todas as etapas do fluxo.
- Adicionar filtros e paginação à API de clientes, para suportar bases grandes.

---

**VetorFlow**