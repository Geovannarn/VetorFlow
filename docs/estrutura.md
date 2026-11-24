# Estrutura do projeto

O VetorFlow está organizado em módulos independentes, cada um responsável por uma parte específica do sistema. Essa divisão facilita a manutenção, a organização das regras de negócio e a evolução das funcionalidades.

```text
VetorFlow/
├── api/
├── audit/
├── benchmark/
├── config/
├── data/
├── database/
├── docs/
├── frontend/
├── integrations/
├── neighborhood/
├── normalizers/
├── pipeline/
├── test/
├── .env
├── .env.example
├── .gitignore
└── manage.py
```

## Diretórios e suas responsabilidades

| Diretório/Arquivo | Finalidade |
|---|---|
| `api/` | Contém a implementação da API REST, incluindo modelos, rotas, visualizações, esquemas e funcionalidades relacionadas ao benchmark. |
| `audit/` | Responsável pelos mecanismos de auditoria e registro de eventos da aplicação, incluindo logger, middleware e recorder. |
| `benchmark/` | Reúne os componentes responsáveis pela execução dos benchmarks, geração de dados, medição de desempenho e elaboração de relatórios. |
| `config/` | Contém as configurações centrais do Django, incluindo configurações gerais, rotas principais e pontos de entrada WSGI e ASGI. |
| `data/` | Armazena os arquivos utilizados e gerados pelo processamento, organizados em dados originais, processados e resultados de benchmark. |
| `database/` | Reúne os arquivos responsáveis pela conexão com o PostgreSQL e pela definição da estrutura do banco de dados. |
| `docs/` | Armazena a documentação técnica do projeto, incluindo arquitetura, instalação, API, banco de dados, regras de tratamento e decisões técnicas. |
| `frontend/` | Contém a interface web da aplicação, organizada em templates HTML, arquivos CSS e scripts JavaScript. |
| `integrations/` | Implementa a comunicação com serviços externos, como ViaCEP e BrasilAPI, além do mecanismo de cache. |
| `neighborhood/` | Responsável pela normalização e resolução de nomes de bairros, tratando variações e inconsistências cadastrais. |
| `normalizers/` | Reúne as funções de padronização dos campos cadastrais, como CNPJ, datas, e-mails, CEP, telefones e textos. |
| `pipeline/` | Contém componentes do processamento ETL, incluindo verificações de qualidade, métricas e carregamento dos dados. |
| `test/` | Reúne os testes automatizados da aplicação, abrangendo API, ETL, integrações, qualidade dos dados e resolução de bairros. |

## Arquivos da raiz

| Arquivo | Finalidade |
|---|---|
| `.env` | Armazena as variáveis de ambiente e configurações locais da aplicação. Não deve ser versionado. |
| `.env.example` | Apresenta um modelo das variáveis necessárias para configurar o ambiente. |
| `.gitignore` | Define os arquivos e diretórios que devem ser ignorados pelo Git. |
| `manage.py` | Ponto de entrada para executar comandos administrativos e gerenciar a aplicação Django. |

## Organização dos dados

O diretório `data/` possui a seguinte estrutura:

```text
data/
├── benchmark/
│   ├── dados/
│   └── resultados/
│       ├── graficos/
│       ├── relatorio.html
│       ├── resultados.csv
│       └── resultados.json
├── processed/
└── raw/
    └── clientes_distribuidora_vetor.csv
```

`benchmark/dados/`: destinado aos dados utilizados nos experimentos de desempenho.
`benchmark/resultados/`: armazena os resultados dos benchmarks, incluindo relatórios e gráficos.
`processed/`: destinado aos dados após o processamento.
`raw/`: armazena os dados originais utilizados como entrada do pipeline ETL.

## Organização dos testes

O diretório `test/` está organizado da seguinte forma:

```text
test/
├── api/
├── integration/
├── test_api.py
├── test_cep.py
├── test_etl.py
├── test_neighborhood.py
└── test_quality.py
```

`api/`: destinado à organização de testes relacionados à API.
'integration/`: destinado à organização de testes de integração.
`test_api.py`: verifica funcionalidades da API.
`test_cep.py`: verifica o comportamento das consultas de CEP.
'test_etl.py`: verifica etapas do processamento ETL.
`test_neighborhood.py`: verifica a normalização e resolução de bairros.
`test_quality.py`: verifica as regras de qualidade dos dados.