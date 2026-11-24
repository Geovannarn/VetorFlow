# VetorFlow

**Pipeline de ETL, qualidade de dados e gerenciamento de informações cadastrais.**

O **VetorFlow** é uma solução desenvolvida para tratar, validar, normalizar e enriquecer os dados cadastrais da Distribuidora Vetor.

O sistema recebe bases de dados em formato CSV, aplica regras de qualidade e padronização, realiza o enriquecimento de endereços por meio de serviços externos e disponibiliza os registros tratados para armazenamento em PostgreSQL.

Além do processamento de dados, o projeto disponibiliza uma API REST para gerenciamento de clientes, uma interface web para interação com as funcionalidades do sistema e um módulo de benchmark destinado à avaliação de desempenho em diferentes volumes de dados.

---

## Sumário

1. [Visão geral](#1-visão-geral)
2. [Objetivos](#2-objetivos)
3. [Tecnologias utilizadas](#3-tecnologias-utilizadas)
4. [Arquitetura do sistema](#4-arquitetura-do-sistema)
5. [Pipeline ETL](#5-pipeline-etl)
6. [Tratamento e normalização dos dados](#6-tratamento-e-normalização-dos-dados)
7. [Enriquecimento de endereços](#7-enriquecimento-de-endereços)
8. [Qualidade dos dados](#8-qualidade-dos-dados)
9. [Resolução de divergências de bairros](#9-resolução-de-divergências-de-bairros)
10. [Banco de dados](#10-banco-de-dados)
11. [API REST](#11-api-rest)
12. [Interface web](#12-interface-web)
13. [Benchmark e desempenho](#13-benchmark-e-desempenho)
14. [Auditoria e rastreabilidade](#14-auditoria-e-rastreabilidade)
15. [Testes automatizados](#15-testes-automatizados)
16. [Estrutura do projeto](#16-estrutura-do-projeto)
17. [Instalação e configuração](#17-instalação-e-configuração)
18. [Execução](#18-execução)
19. [Versionamento e organização](#19-versionamento-e-organização)
20. [Documentação complementar](#20-documentação-complementar)

---

## 1. Visão geral

O VetorFlow foi desenvolvido para solucionar problemas comuns encontrados em bases cadastrais, como:

Informações incompletas ou inválidas.
Diferentes formatos para um mesmo tipo de informação.
Registros duplicados.
Dados inconsistentes.
Divergências entre bairros informados e retornados por serviços de CEP.
Ausência de padronização e validação dos registros.

A solução organiza o processamento em módulos independentes, permitindo que cada etapa do tratamento seja executada de maneira estruturada.

O sistema também disponibiliza recursos para consulta e gerenciamento dos clientes, além de mecanismos para avaliação da qualidade dos dados e do desempenho do processamento.

## 2. Objetivos

Os principais objetivos do projeto são:

Desenvolver um pipeline ETL modular.
Padronizar informações cadastrais.
Identificar inconsistências e problemas de qualidade.
Validar informações antes da persistência.
Enriquecer endereços utilizando serviços externos.
Implementar regras para resolução de divergências entre bairros.
Armazenar os dados tratados em PostgreSQL.
Disponibilizar operações de gerenciamento por meio de uma API REST.
Desenvolver uma interface web integrada à API.
Implementar testes automatizados.
Avaliar desempenho e consumo de recursos computacionais em diferentes volumes de dados.

## 3. Tecnologias utilizadas

| Tecnologia | Aplicação |
|---|---|
| Python | Desenvolvimento e processamento |
| Pandas | Manipulação e transformação dos dados |
| Django | Estrutura da aplicação web |
| Django REST Framework | Desenvolvimento da API REST |
| PostgreSQL | Persistência dos dados |
| Psycopg | Conexão com PostgreSQL |
| Requests | Comunicação com serviços externos |
| ViaCEP | Consulta de endereços |
| BrasilAPI | Serviço alternativo de consulta de CEP |
| Pytest | Testes automatizados |
| Python-dotenv | Gerenciamento de variáveis de ambiente |
| Matplotlib | Visualização dos resultados do benchmark |
| psutil | Monitoramento de recursos computacionais |
| HTML, CSS e JavaScript | Interface web |
| Git e GitHub | Versionamento e gerenciamento do código |

## 4. Arquitetura do sistema

O VetorFlow possui uma arquitetura modular, na qual cada diretório concentra responsabilidades específicas.

Essa organização facilita a manutenção, os testes e a evolução independente dos componentes.

### Fluxo geral

```text
              ARQUIVO CSV
                   |
                   v
                EXTRACT
                   |
                   v
          Verificações de qualidade
                   |
                   v
             TRANSFORM
                   |
          +--------+--------+
          |        |        |
          v        v        v
      Normalização CEP    Bairros
          |        |        |
          |        v        |
          |    Enriquecimento
          |        |        |
          +--------+--------+
                   |
                   v
           Validação dos dados
                   |
                   v
              Resolução
             de divergências
                   |
                   v
                 LOAD
                   |
                   v
              PostgreSQL
                   |
              +----+----+
              |         |
              v         v
           API REST  Interface
                      Web
```

O sistema também possui mecanismos de auditoria, registro de rejeições, métricas e avaliação de desempenho.

## 5. Pipeline ETL

O processamento dos dados segue as três etapas fundamentais do processo ETL.

### 5.1. Extract — Extração

A extração consiste na leitura dos arquivos CSV utilizando Pandas.

Nessa etapa, os dados são carregados para estruturas de manipulação, permitindo a aplicação das regras de tratamento.

### 5.2. Transform — Transformação

A transformação concentra as regras responsáveis por melhorar a qualidade e a consistência dos registros.

São realizadas operações como:

Normalização dos campos cadastrais.
Identificação de valores ausentes.
Verificação de duplicidades.
Validação de informações.
Enriquecimento de endereços.
Normalização de bairros.
Resolução de divergências.
Identificação de registros rejeitados.

### 5.3. Load — Carga

A carga realiza a persistência dos registros tratados no PostgreSQL.

O processo utiliza a tabela `usuarios` e a instrução `ON CONFLICT (id_cliente) DO NOTHING`, evitando a inserção de registros com identificadores já existentes.

Os registros rejeitados são tratados separadamente, permitindo identificar os motivos pelos quais não foram considerados aptos para a carga.

## 6. Tratamento e normalização dos dados

O diretório `normalizers/` concentra as regras de padronização dos campos cadastrais.

| Campo | Tratamento |
|---|---|
| CNPJ | Remoção de caracteres não numéricos e validação |
| Telefone | Padronização e tratamento dos caracteres |
| E-mail | Remoção de espaços, conversão para minúsculas e tratamento de domínios internacionalizados |
| Data | Conversão para formatos reconhecidos e padronização |
| CEP | Normalização para oito dígitos |
| Texto | Padronização de espaços e caracteres |

As regras de normalização são aplicadas antes da persistência, respeitando os critérios de validação definidos para cada campo.

Informações inválidas podem resultar em valores nulos ou na rejeição do registro, conforme a regra correspondente.

## 7. Enriquecimento de endereços

O enriquecimento de endereços utiliza serviços externos para complementar as informações cadastrais.

São utilizadas duas fontes:

1. **ViaCEP:** serviço principal de consulta.
2. **BrasilAPI:** serviço alternativo utilizado quando a consulta principal não fornece uma resposta válida.

### Fluxo de consulta

```text
           CEP normalizado
                  |
                  v
              Cache local
                  |
           +------+------+
           |             |
       Encontrado      Ausente
           |             |
           v             v
         Retorno       ViaCEP
                         |
                   +-----+-----+
                   |           |
                 Sucesso      Falha
                   |           |
                   v           v
                 Cache      BrasilAPI
                               |
                         +-----+-----+
                         |           |
                       Sucesso      Falha
                         |           |
                         v           v
                       Cache    Sem retorno
```

O cache local utiliza o arquivo `data/cache/cep_cache.json`, permitindo reutilizar informações previamente consultadas e reduzir chamadas repetidas aos serviços externos.

As falhas de comunicação com os serviços de CEP são tratadas sem interromper desnecessariamente o processamento do pipeline.

## 8. Qualidade dos dados

O projeto possui verificações destinadas a identificar problemas na base de entrada.

Entre os principais critérios avaliados estão:

- Existência de colunas obrigatórias.
- Quantidade de valores nulos.
- Identificação de registros duplicados.
- Identificação de registros vazios.
- Disponibilidade de dados para processamento.

As verificações permitem gerar métricas relacionadas à qualidade da base, incluindo quantidades e percentuais de inconsistências.

Esses indicadores auxiliam na identificação dos problemas existentes e na avaliação dos resultados após o tratamento.

## 9. Resolução de divergências de bairros

Um dos componentes importantes do VetorFlow é o mecanismo de normalização e resolução de divergências entre bairros.

O sistema compara o bairro originalmente informado no cadastro com aquele retornado pelo serviço de consulta de CEP.

O processo considera diferentes situações:

| Classificação | Significado |
|---|---|
| `convergente` | As informações representam o mesmo bairro ou versões compatíveis |
| `informado` | Apenas o cadastro possui informação de bairro |
| `api` | Apenas o serviço externo possui informação de bairro |
| `divergente` | As fontes apresentam informações diferentes |
| `sem informação` | Nenhuma das fontes possui informação de bairro |

Quando existe uma divergência real, o sistema preserva o bairro informado originalmente no cadastro.

Essa decisão evita substituir automaticamente uma informação fornecida pela origem dos dados por outra retornada por um serviço externo.

O mecanismo também permite identificar e classificar as divergências para análise posterior.

## 10. Banco de dados

O armazenamento dos dados é realizado utilizando PostgreSQL.

O módulo `database/` concentra as responsabilidades relacionadas à conexão e às operações de persistência.

A tabela principal é `usuarios`, responsável por armazenar os dados cadastrais tratados.

Entre os campos utilizados estão:

| Campo | Descrição |
|---|---|
| `id_cliente` | Identificador do cliente |
| `razao_social` | Nome empresarial |
| `cnpj` | Documento cadastral |
| `telefone` | Telefone de contato |
| `email` | Endereço de e-mail |
| `bairro` | Bairro |
| `cep` | Código postal |
| `cidade` | Município |
| `uf` | Unidade federativa |
| `cadastro` | Data de cadastro |
| `responsavel` | Responsável pelo cadastro |

As configurações de conexão são realizadas por meio de variáveis de ambiente, evitando a exposição de credenciais diretamente no código-fonte.

## 11. API REST

A API foi desenvolvida utilizando Django REST Framework e disponibiliza operações de gerenciamento dos clientes.

### Endpoints

| Método HTTP | Endpoint | Operação |
|---|---|---|
| GET | `/api/clientes/` | Listar clientes |
| GET | `/api/clientes/<id_cliente>/` | Consultar cliente específico |
| POST | `/api/clientes/` | Cadastrar cliente |
| PUT | `/api/clientes/<id_cliente>/` | Atualizar cliente |
| DELETE | `/api/clientes/<id_cliente>/` | Excluir cliente |

As respostas são disponibilizadas no formato JSON.

### Validação e tratamento de erros

A API possui regras próprias de validação para cadastros e atualizações manuais.

Entre os códigos HTTP utilizados estão:

| Código | Significado |
|---|---|
| `200 OK` | Operação realizada com sucesso |
| `201 Created` | Registro criado |
| `400 Bad Request` | Dados inválidos |
| `404 Not Found` | Registro não encontrado |
| `409 Conflict` | Conflito de identificador |

As validações permitem identificar problemas nos dados enviados e retornar respostas que auxiliam na correção das informações.

## 12. Interface web

A interface foi desenvolvida utilizando HTML, CSS e JavaScript, integrando-se à API REST.

O frontend disponibiliza funcionalidades para:

Consulta e enriquecimento de CEP.
Cadastro de clientes.
Busca de registros.
Exclusão de clientes.
Importação e tratamento de arquivos CSV.
Visualização de resultados do benchmark.

A interface permite interagir com as funcionalidades do sistema sem a necessidade de acessar diretamente o banco de dados.

## 13. Benchmark e desempenho

O módulo `benchmark/` foi desenvolvido para avaliar o comportamento do VetorFlow em diferentes volumes de dados.

São utilizados conjuntos de dados sintéticos, com volumes configuráveis de 10 mil a 5 milhões de registros.

As bases geradas possuem inconsistências propositais, simulando problemas encontrados em situações reais de processamento cadastral.

### 13.1. Indicadores avaliados

Tempo de execução.
Utilização de CPU.
Consumo de memória RAM.
Quantidade de registros processados por segundo.
Taxa de erros.
Quantidade de registros rejeitados.

### 13.2. Etapas avaliadas

| Etapa | Avaliação |
|---|---|
| Geração | Criação de bases sintéticas |
| Extração | Leitura dos arquivos CSV |
| Transformação | Normalização e validação |
| Carga | Comparação de estratégias de inserção |
| Consultas | Desempenho de operações no PostgreSQL |
| API | Desempenho das operações REST |

### 13.3. Estratégias de carga

O benchmark também compara diferentes estratégias de inserção no PostgreSQL:

Inserção individual.
Inserção em lotes (*batch insert*).
COPY.

Essa comparação permite observar como diferentes abordagens influenciam o tempo de execução e o comportamento da persistência em volumes maiores de dados.

### 13.4. Execução

```bash
python -m benchmark.executar
```

Os resultados são armazenados em `data/benchmark/resultados/`, incluindo arquivos JSON, CSV, gráficos e relatórios HTML.

## 14. Auditoria e rastreabilidade

O módulo `audit/` reúne os mecanismos de registro relacionados aos acessos e às operações realizadas no sistema.

São considerados dois tipos principais de eventos:

| Tipo | Informações registradas |
|---|---|
| `ACESSO` | Data, horário, IP, método HTTP, URL e código de resposta |
| `OPERACAO` | Operações de criação, atualização e exclusão de clientes |

O registro de acessos utiliza middleware do Django.

O projeto também possui uma estrutura destinada ao armazenamento do histórico de transformações por campo, por meio da tabela `auditoria_tratamento`.

**Estado da implementação:** a gravação individual das transformações realizadas pelo pipeline ainda não está integrada. Portanto, a rastreabilidade das decisões de tratamento permanece parcial.

## 15. Testes automatizados

Os testes automatizados são executados utilizando Pytest.

A suíte contempla verificações relacionadas a:

Normalização de campos cadastrais.
Tratamento e resolução de bairros.
Integração com serviços de CEP.
Verificações de qualidade.
Processamento e carregamento dos dados.
Operações da API.

As dependências externas podem ser simuladas por meio de mocks, evitando chamadas reais aos serviços externos durante os testes correspondentes.

### Executar os testes

```bash
pytest
```

## 16. Estrutura do projeto

A organização atual do repositório está distribuída em módulos com responsabilidades específicas.

```text
VetorFlow/
│
├── api/                 # API REST e operações de clientes
├── audit/               # Auditoria e registros de operações
├── benchmark/           # Avaliação de desempenho
├── config/              # Configurações do Django
│
├── data/
│   ├── raw/             # Bases de dados originais
│   ├── processed/       # Dados processados
│   ├── cache/           # Cache de consultas de CEP
│   └── benchmark/       # Resultados de desempenho
│
├── database/            # Conexão e persistência
├── docs/                # Documentação técnica
│
├── frontend/
│   ├── static/          # Arquivos CSS e JavaScript
│   └── templates/       # Templates HTML
│
├── integrations/        # Integrações com serviços externos
├── neighborhood/        # Normalização e resolução de bairros
├── normalizers/         # Normalização de campos cadastrais
├── pipeline/            # Processamento e qualidade dos dados
├── test/                # Testes automatizados
│
├── .env.example         # Modelo de variáveis de ambiente
├── .gitignore
├── manage.py
└── README.md
```

## 17. Instalação e configuração

### Pré-requisitos

- Python.
- PostgreSQL.
- Git.

### 17.1. Clonar o repositório

```bash
git clone https://github.com/Geovannarn/VetorFlow.git
cd VetorFlow
```

### 17.2. Criar o ambiente virtual

```bash
python -m venv .venv
```

### 17.3. Ativar o ambiente virtual

**Windows PowerShell:**

```powershell
.\.venv\Scripts\Activate.ps1
```

**Linux:**

```bash
source .venv/bin/activate
```

### 17.4. Instalar as dependências

Instale as dependências utilizando o arquivo de dependências disponibilizado na raiz do projeto.

### 17.5. Configurar o banco de dados

Crie um banco de dados PostgreSQL para armazenar os registros do sistema.

### 17.6. Configurar as variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto, utilizando o `.env.example` como referência.

Exemplo de configuração:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=nome_do_banco
DB_USER=usuario
DB_PASSWORD=senha

DJANGO_SECRET_KEY=sua_chave_secreta
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
```

Ajuste os valores de acordo com a configuração do ambiente local.

**Importante:** o arquivo `.env` contém informações sensíveis e não deve ser enviado ao repositório.

## 18. Execução

### Verificar a configuração do Django

```bash
python manage.py check
```

### Iniciar a aplicação

```bash
python manage.py runserver
```

A interface web ficará disponível em:

```text
http://127.0.0.1:8000/
```

A API REST ficará disponível a partir de:

```text
http://127.0.0.1:8000/api/
```

### Executar os testes

```bash
pytest
```

### Executar o benchmark

```bash
python -m benchmark.executar
```

**Observação:** a execução do pipeline ETL e a preparação inicial do banco de dados devem seguir os procedimentos específicos documentados nos respectivos módulos.

## 19. Versionamento e organização

O desenvolvimento utiliza Git e GitHub para controle de versão e organização das alterações.

As funcionalidades foram organizadas em branches específicas, separando etapas como:

Estrutura do banco de dados.
Normalização dos campos.
Integração com serviços de CEP.
Tratamento e resolução de bairros.
Auditoria.
Pipeline e carga de dados.
Verificações de qualidade.
API REST.

O acompanhamento das atividades também utilizou Trello, com organização das tarefas em etapas de desenvolvimento e validação.

## 20. Documentação complementar

A documentação técnica complementar está organizada no diretório [`docs/`](docs/).

Seu objetivo é detalhar os componentes, as regras de negócio e as decisões técnicas do projeto, mantendo o README como ponto central de apresentação e orientação.

Entre os assuntos documentados estão:

Arquitetura do sistema.
Funcionamento do pipeline ETL.
Regras de normalização.
Estrutura do banco de dados.
Endpoints da API.
Decisões técnicas e trade-offs.
Testes automatizados.
Benchmark e análise de desempenho.



**VetorFlow**  

