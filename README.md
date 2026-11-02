# VetorFlow

Sistema desenvolvido para tratamento, validação, enriquecimento e armazenamento de dados cadastrais da Distribuidora Vetor.

O VetorFlow implementa um fluxo de processamento de dados a partir de uma base CSV, realizando normalização de campos, validações de qualidade, enriquecimento por meio de APIs externas, tratamento de inconsistências e persistência dos dados em PostgreSQL.

O projeto também disponibiliza uma API REST para gerenciamento dos registros de clientes.

## Objetivo

O projeto tem como objetivo estruturar um processo de tratamento de dados capaz de lidar com inconsistências presentes na base original, mantendo critérios definidos para normalização, validação, enriquecimento e resolução de divergências.

O fluxo desenvolvido contempla desde a entrada dos dados até seu armazenamento e disponibilização por meio da API.

## Tecnologias

**Python** — desenvolvimento do processamento e das regras de tratamento

**Pandas** — leitura e processamento dos dados

**Django** — estrutura da aplicação

**Django REST Framework** — desenvolvimento da API REST

**PostgreSQL** — armazenamento dos dados

**Pytest** — testes automatizados

**Git / GitHub** — versionamento do projeto

## Arquitetura do fluxo

```text
                    ┌─────────────────┐
                    │     CSV         │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   Normalização  │
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
                    │  Enriquecimento │
                    │    por CEP      │
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
                    └─────────────────┘
```

## Processamento dos dados

O processamento é organizado em etapas específicas para cada responsabilidade.

### Normalização

Foram implementados normalizadores para diferentes campos da base:

CNPJ
Data
E-mail
Telefone
Texto
CEP

O objetivo é reduzir diferenças de formatação e estabelecer um padrão para os dados antes das etapas seguintes.

### CEP

O tratamento do CEP considera diferentes formatos de entrada, incluindo valores com e sem hífen.

Os valores são validados e normalizados para um padrão de oito dígitos, considerando também situações de valores vazios ou inválidos.

### Integrações externas

O enriquecimento dos dados de CEP utiliza:

**ViaCEP**
**BrasilAPI**

A ViaCEP é utilizada como fonte principal e a BrasilAPI como alternativa.

O projeto também possui um mecanismo de cache local para evitar consultas repetidas para CEPs já processados.

## Tratamento de bairros

O tratamento dos bairros está separado no diretório `neighborhood`.

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

identificação de colunas obrigatórias ausentes;
identificação de valores nulos;
identificação de registros duplicados;
verificação da existência de registros.

A partir dos resultados dos checks, são calculadas métricas como:

total de registros;
total de valores nulos;
total de registros duplicados;
percentual de nulos;
percentual de duplicados.

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

O arquivo `.env` não deve ser versionado.

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

## Testes automatizados

Os testes automatizados são executados utilizando **Pytest**.

Para executar a suíte de testes:

```bash
pytest
```

Os testes abrangem diferentes partes do projeto, incluindo:

API;
integração de CEP;
carregamento dos dados;
verificações de qualidade.

## Estrutura do projeto

```text
VetorFlow/
├── api/
├── audit/
├── config/
├── data/
├── database/
├── docs/
├── integrations/
├── neighborhood/
├── normalizers/
├── pipeline/
├── test/
├── .env
├── .env.example
├── .gitignore
├── manage.py
├── Makefile
├── pytest.ini
├── README.md
└── requirements.txt
```

### Responsabilidades dos diretórios

| Diretório | Responsabilidade |
|---|---|
| `api/` | Endpoints e componentes da API REST |
| `audit/` | Registros de auditoria |
| `config/` | Configurações do Django |
| `data/` | Dados utilizados no processamento |
| `database/` | Conexão e acesso ao PostgreSQL |
| `docs/` | Documentação complementar |
| `integrations/` | Integrações externas e cache |
| `neighborhood/` | Normalização e resolução de bairros |
| `normalizers/` | Normalização dos campos |
| `pipeline/` | Processamento, carregamento e qualidade dos dados |
| `test/` | Testes automatizados |

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

Ativação:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Instalar as dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar as variáveis de ambiente

Crie o arquivo `.env` na raiz do projeto e configure os dados de conexão com o PostgreSQL.

### 5. Verificar a configuração do Django

```bash
python manage.py check
```

### 6. Executar os testes

```bash
pytest
```

## Versionamento

O desenvolvimento foi organizado utilizando Git e GitHub.

As funcionalidades foram separadas em branches de acordo com suas responsabilidades, como:

```text
feature/database-integration
feature/field-normalizers
feature/data-quality
feature/neighborhood-normalization
feature/neighborhood-resolver
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

## Documentação

A documentação complementar do projeto está disponível na raiz. O  relatório de trade-offs,  apresenta as principais decisões tomadas durante o desenvolvimento, os critérios utilizados e os pontos considerados na implementação das soluções.

---

**VetorFlow**  
Projeto acadêmico
