# VetorFlow

### Engenharia de dados, qualidade cadastral e processamento inteligente de informações.

O **VetorFlow** é uma solução desenvolvida em Python para tratamento, validação, normalização, enriquecimento e gerenciamento de dados cadastrais da Distribuidora Vetor.

O projeto implementa um pipeline de ETL (*Extract, Transform, Load*) capaz de transformar uma base CSV originalmente inconsistente em dados estruturados e padronizados, aplicando regras determinísticas de tratamento, verificações de qualidade e integração com serviços externos.

Além do processamento em lote, o sistema disponibiliza uma API REST para operações CRUD, uma interface web para interação com os dados, mecanismos de auditoria e um módulo de benchmark para avaliação de desempenho em diferentes volumes de registros.

O desenvolvimento prioriza modularidade, separação de responsabilidades, integridade dos dados, reprodutibilidade dos testes e rastreabilidade das decisões de tratamento.

---

## Sumário

1. [Visão geral](#1-visão-geral)
2. [Problema e proposta de solução](#2-problema-e-proposta-de-solução)
3. [Objetivos](#3-objetivos)
4. [Tecnologias e ferramentas](#4-tecnologias-e-ferramentas)
5. [Arquitetura do sistema](#5-arquitetura-do-sistema)
6. [Pipeline de ETL](#6-pipeline-de-etl)
7. [Tratamento e normalização dos dados](#7-tratamento-e-normalização-dos-dados)
8. [Normalização e resolução de bairros](#8-normalização-e-resolução-de-bairros)
9. [Enriquecimento de endereços](#9-enriquecimento-de-endereços)
10. [Qualidade e validação dos dados](#10-qualidade-e-validação-dos-dados)
11. [Persistência e banco de dados](#11-persistência-e-banco-de-dados)
12. [API REST](#12-api-rest)
13. [Interface web](#13-interface-web)
14. [Auditoria e rastreabilidade](#14-auditoria-e-rastreabilidade)
15. [Benchmark e análise de desempenho](#15-benchmark-e-análise-de-desempenho)
16. [Testes automatizados](#16-testes-automatizados)
17. [Estrutura do projeto](#17-estrutura-do-projeto)
18. [Instalação e configuração](#18-instalação-e-configuração)
19. [Execução](#19-execução)
20. [Decisões técnicas e limitações](#20-decisões-técnicas-e-limitações)
21. [Documentação complementar](#21-documentação-complementar)

---

## 1. Visão geral

O VetorFlow foi desenvolvido para centralizar o tratamento e a organização de informações cadastrais, reduzindo inconsistências que comprometem a confiabilidade de uma base de dados.

A solução recebe arquivos CSV e executa um conjunto de procedimentos para identificar problemas, padronizar campos, consultar informações externas e armazenar os registros tratados em um banco de dados relacional.

O sistema é composto por módulos independentes que trabalham de forma integrada:

| Componente | Responsabilidade |
|---|---|
| `pipeline/` | Orquestração do processamento ETL |
| `normalizers/` | Padronização dos campos cadastrais |
| `neighborhood/` | Normalização e resolução de bairros |
| `integrations/` | Comunicação com serviços externos |
| `database/` | Conexão e persistência dos dados |
| `api/` | Operações de gerenciamento de clientes |
| `audit/` | Registro de acessos e operações |
| `benchmark/` | Avaliação de desempenho |
| `frontend/` | Interface de interação com o sistema |
| `test/` | Testes automatizados |

Essa organização permite desenvolver, testar e manter cada responsabilidade sem concentrar toda a lógica em um único módulo.

## 2. Problema e proposta de solução

Bases cadastrais podem apresentar inconsistências que dificultam consultas, análises e utilização posterior dos dados.

No contexto da Distribuidora Vetor, foram consideradas situações como:

CNPJ, telefone e CEP registrados com diferentes formatos.
E-mails com espaços e variações de capitalização.
Datas representadas em formatos distintos.
Informações cadastrais ausentes ou inválidas.
Registros duplicados.
Bairros com abreviações, acentos e subdivisões.
Divergências entre o endereço informado e o retornado por serviços de CEP.

A proposta do VetorFlow é tratar essas inconsistências por meio de regras explícitas e documentadas, evitando alterações arbitrárias ou descarte desnecessário de informações.

O enriquecimento por CEP complementa os dados disponíveis, enquanto a resolução de bairros estabelece critérios para lidar com informações provenientes de fontes diferentes.

O resultado é uma base mais consistente, acompanhada de métricas que permitem observar os problemas identificados durante o processamento.

## 3. Objetivos

### Objetivo geral

Desenvolver uma solução modular de engenharia de dados para tratamento, enriquecimento, armazenamento e gerenciamento de informações cadastrais.

### Objetivos específicos

Implementar um pipeline de ETL dividido em etapas independentes.
Desenvolver normalizadores reutilizáveis para campos cadastrais.
Identificar registros incompletos, duplicados e inconsistentes.
Aplicar regras determinísticas de comparação e resolução de bairros.
Integrar serviços externos para enriquecimento de endereços.
Implementar cache local para reduzir consultas repetidas.
Armazenar os dados tratados em PostgreSQL.
Disponibilizar operações de gerenciamento por meio de uma API REST.
Implementar registros de auditoria das operações da API.
Desenvolver testes automatizados com dependências externas simuladas.
Avaliar o desempenho do processamento e das operações do sistema.

## 4. Tecnologias e ferramentas

As tecnologias foram selecionadas de acordo com as responsabilidades de processamento, persistência, integração, exposição dos dados e avaliação de desempenho.

| Tecnologia | Aplicação no projeto |
|---|---|
| **Python** | Linguagem principal de desenvolvimento |
| **Pandas** | Leitura, manipulação e transformação de dados tabulares |
| **Django** | Estrutura da aplicação web |
| **Django REST Framework** | Implementação da API REST |
| **PostgreSQL** | Banco de dados relacional |
| **Psycopg** | Comunicação com o PostgreSQL |
| **Requests** | Requisições HTTP para serviços externos |
| **ViaCEP** | Consulta de informações de endereço |
| **BrasilAPI** | Fonte alternativa para consulta de CEP |
| **Pytest** | Execução de testes automatizados |
| **Python-dotenv** | Leitura de variáveis de ambiente |
| **Matplotlib** | Geração de visualizações do benchmark |
| **psutil** | Monitoramento de recursos computacionais |
| **HTML** | Estrutura da interface |
| **CSS** | Estilização da interface |
| **JavaScript** | Interatividade e comunicação com a API |
| **Git** | Controle de versão |
| **GitHub** | Hospedagem e gerenciamento do código |
| **Trello** | Organização e acompanhamento das atividades |

## 5. Arquitetura do sistema

A arquitetura do VetorFlow utiliza separação de responsabilidades para organizar as etapas de processamento e os componentes da aplicação.

O pipeline é responsável pelo processamento em lote, enquanto os módulos de normalização, resolução de bairros e integração fornecem funcionalidades específicas reutilizadas durante o tratamento.

A API REST utiliza as regras de normalização para manter um padrão consistente entre os dados processados em lote e os cadastros realizados manualmente.

### 5.1. Fluxo de processamento

```text
                 ARQUIVO CSV
                 data/raw/
                     |
                     v
             EXTRAÇÃO DOS DADOS
                     |
                     v
              CHECKS INICIAIS
              Qualidade da base
                     |
                     v
           ENRIQUECIMENTO POR CEP
                     |
             Cache / ViaCEP /
                BrasilAPI
                     |
                     v
             TRANSFORMAÇÃO
                     |
              +------+------+
              |             |
              v             v
         NORMALIZERS    NEIGHBORHOOD
              |             |
              +------+------+
                     |
                     v
             VALIDAÇÃO FINAL
                     |
              +------+------+
              |             |
              v             v
          REJEITADOS     TRATADOS
                            |
                            v
                       POSTGRESQL
                            |
                   +--------+--------+
                   |                 |
                   v                 v
                API REST          FRONTEND
```

### 5.2. Separação de responsabilidades

A arquitetura evita concentrar operações de leitura, tratamento, integração e persistência em uma única implementação.

Essa separação oferece algumas vantagens:

Possibilidade de testar funções individualmente.
Reutilização de normalizadores.
Isolamento de dependências externas.
Facilidade para identificar falhas.
Maior clareza na manutenção.
Possibilidade de executar o pipeline sem consultar APIs ou gravar no banco.

### 5.3. Reutilização das regras

Os normalizadores são compartilhados entre o pipeline e a API REST.

Isso evita manter duas implementações diferentes para a mesma regra de padronização e reduz o risco de divergência entre os dados processados em lote e os cadastrados manualmente.

## 6. Pipeline de ETL

O pipeline constitui o núcleo de processamento do VetorFlow.

Sua responsabilidade é receber os dados originais, aplicar as regras de tratamento e disponibilizar os registros resultantes para persistência.

A implementação é dividida em etapas com responsabilidades específicas.

### 6.1. Extract — Extração

A extração realiza a leitura do arquivo CSV utilizando Pandas.

Durante essa etapa, a estrutura da base é verificada antes do processamento.

São considerados:

Existência de dados.
Presença das colunas esperadas.
Valores ausentes.
Registros duplicados.
Registros completamente vazios.

A ausência de uma coluna obrigatória impede a continuidade do processamento, pois compromete a aplicação das regras esperadas.

### 6.2. Transform — Transformação

A transformação concentra as regras de qualidade e padronização.

As principais operações são:

1. Normalização dos campos cadastrais.
2. Identificação de informações inválidas.
3. Consulta e enriquecimento de endereços.
4. Normalização textual dos bairros.
5. Comparação entre bairro informado e bairro retornado pela API.
6. Classificação dos critérios de resolução.
7. Separação entre registros tratados e rejeitados.
8. Cálculo das métricas de processamento.

As operações são realizadas de maneira controlada, preservando informações válidas sempre que possível.

### 6.3. Load — Carga

A carga é responsável por inserir os dados tratados na tabela `usuarios`, utilizando PostgreSQL.

A operação utiliza:

```sql
INSERT ... ON CONFLICT (id_cliente) DO NOTHING;
```

Essa estratégia impede que registros com identificadores já existentes sejam inseridos novamente.

A persistência utiliza transações, com execução de `rollback` em caso de falha e fechamento da conexão ao final da operação.

### 6.4. Execução controlada

A orquestração do pipeline é realizada pela função `processar_csv`.

Ela aceita dois parâmetros importantes:

| Parâmetro | Comportamento |
|---|---|
| `consultar_api` | Controla a consulta aos serviços externos |
| `gravar` | Controla a gravação dos registros no banco |

Com ambos desabilitados, é possível executar o processamento sem internet e sem persistência no PostgreSQL.

Isso facilita testes, demonstrações e verificações das regras de transformação.

## 7. Tratamento e normalização dos dados

A normalização busca transformar informações representadas de maneiras diferentes em formatos consistentes.

O módulo `normalizers/` centraliza as regras aplicadas aos campos cadastrais.

### 7.1. Regras por campo

| Campo | Regra aplicada |
|---|---|
| CNPJ | Remoção de caracteres não numéricos e exigência de 14 dígitos |
| Telefone | Remoção de caracteres especiais, tratamento do DDI e exigência de 10 ou 11 dígitos nacionais |
| E-mail | Remoção de espaços, conversão para minúsculas e validação por expressão regular |
| Data | Reconhecimento dos formatos aceitos e conversão para ISO |
| CEP | Normalização para oito dígitos |
| UF | Conversão para maiúsculas e preenchimento pela API quando disponível |
| Cidade | Preenchimento pela API quando não informada |

### 7.2. Tratamento do CNPJ

O CNPJ passa por uma normalização que remove caracteres não numéricos.

O formato exige 14 dígitos.

O sistema também calcula os dígitos verificadores, mas não rejeita o registro quando o cálculo identifica uma inconsistência.

Essa decisão foi adotada porque os CNPJs da base do desafio são fictícios. Os casos com dígitos inválidos são contabilizados separadamente, preservando os registros.

### 7.3. Tratamento de telefone

O telefone passa por:

Remoção de caracteres não numéricos.
Remoção do DDI `55` quando aplicável.
Verificação da quantidade de dígitos nacionais.
Padronização com o prefixo `+55`.

Valores que não atendem às regras são convertidos para `NULL`.

### 7.4. Tratamento de e-mail

Os e-mails recebem remoção de espaços nas extremidades e conversão para letras minúsculas.

Uma expressão regular é utilizada para verificar o formato.

Endereços inválidos são anulados, sem necessidade de rejeitar todo o cadastro.

### 7.5. Tratamento de datas

O normalizador reconhece os seguintes formatos:

`DD/MM/AAAA`
`AAAA-MM-DD`
`DD-MM-AAAA`
`Mês DD, AAAA`, com meses abreviados em inglês.

As datas válidas são convertidas para o formato ISO.

Datas inválidas resultam em `NULL`.

### 7.6. Estratégia para dados inválidos

O VetorFlow diferencia problemas que comprometem a identificação do registro daqueles que afetam somente campos individuais.

São rejeitados:

Registros com `id_cliente` vazio.
Registros com `razao_social` vazia.
Registros com `id_cliente` duplicado no arquivo, mantendo a primeira ocorrência.

Outras inconsistências cadastrais são tratadas individualmente, com anulação do campo e contabilização quando aplicável.

Essa estratégia reduz a perda de registros que continuam sendo relevantes para o negócio.

## 8. Normalização e resolução de bairros

O tratamento de bairros é uma das partes centrais do VetorFlow, pois envolve informações que podem apresentar variações textuais e divergências entre fontes.

O módulo `neighborhood/` foi desenvolvido para tratar essas situações sem depender exclusivamente de correspondências exatas ou de consultas externas.

### 8.1. Normalização determinística

A normalização aplica uma sequência fixa de regras:

1. Remoção de espaços nas extremidades.
2. Normalização Unicode em NFC.
3. Tratamento de conteúdos entre parênteses.
4. Remoção de sufixos de UF válidos.
5. Substituição de pontuação por espaços.
6. Colapso de espaços repetidos.
7. Geração de uma chave de comparação sem acentos e em minúsculas.
8. Geração de um nome de exibição com capitalização padronizada.

Exemplo:

| Entrada | Chave de comparação |
|---|---|
| `Águas Claras` | `aguas claras` |
| `AGUAS CLARAS` | `aguas claras` |
| `aguas claras` | `aguas claras` |

A chave de comparação é utilizada nas regras de resolução, enquanto o nome de exibição é utilizado para gravação.

Essa separação permite comparar informações sem perder a grafia acentuada.

### 8.2. Tratamento de subdivisões

Quando existem parênteses, o sistema utiliza o conteúdo interno como referência.

Exemplo:

```text
Norte (Águas Claras)
          |
          v
    Águas Claras
```

A regra foi adotada para tratar registros em que a subdivisão aparece acompanhada de uma região ou denominação mais ampla.

### 8.3. Comparação entre bairros

A função `resolver_bairro(bairro_informado, bairro_api)` compara as informações normalizadas e determina o valor final e o critério utilizado.

| Situação | Resultado |
|---|---|
| Ambos ausentes | `NULL` |
| Apenas a API possui valor | Bairro da API |
| Apenas o cadastro possui valor | Bairro informado |
| Chaves equivalentes | Bairro da API |
| Contenção compatível | Nome mais completo |
| Divergência real | Bairro informado |

A contenção é realizada por conjunto de palavras, com tratamento especial para termos direcionais como norte, sul, leste, oeste e centro.

Esses termos isoladamente não são suficientes para estabelecer convergência.

### 8.4. Prevalência da informação original

Em caso de divergência real, prevalece o bairro informado pelo cliente ou vendedor.

Essa decisão considera que o CEP pode ser genérico ou não representar corretamente o bairro cadastrado.

Em vez de substituir automaticamente a informação original, o sistema mantém o dado e classifica o registro como `divergente`.

### 8.5. Dicionário de abreviações

Existe um dicionário mínimo de apelidos para tratar variações que não podem ser resolvidas apenas pela normalização textual.

Exemplos:

```text
v pires  → vicente pires
vte pires → vicente pires
```

O dicionário é ampliado conforme novas variantes são identificadas na base.

## 9. Enriquecimento de endereços

O enriquecimento de endereços utiliza duas APIs públicas:

**ViaCEP:** fonte principal.
**BrasilAPI:** fonte alternativa.

A estratégia combina cache local e consulta externa, reduzindo chamadas desnecessárias.

### 9.1. Ordem de consulta

```text
            CEP NORMALIZADO
                   |
                   v
               CACHE LOCAL
                   |
             +-----+-----+
             |           |
         Encontrado    Ausente
             |           |
             v           v
           Retorno     VIACEP
                          |
                    +-----+-----+
                    |           |
                 Sucesso       Falha
                    |           |
                    v           v
                  Cache      BRASILAPI
                                |
                          +-----+-----+
                          |           |
                       Sucesso       Falha
                          |           |
                          v           v
                        Cache     Sem retorno
```

### 9.2. Padronização das respostas

As APIs utilizam nomenclaturas diferentes para representar os mesmos campos.

O VetorFlow converte as respostas para uma estrutura única:

| Campo padronizado | ViaCEP | BrasilAPI |
|---|---|---|
| `bairro` | `bairro` | `neighborhood` |
| `cidade` | `localidade` | `city` |
| `uf` | `uf` | `state` |

Essa conversão permite que o restante do pipeline trabalhe com uma estrutura independente da fonte consultada.

### 9.3. Tratamento de falhas

As consultas utilizam timeout de cinco segundos.

São tratados:

Erros de conexão.
Respostas HTTP diferentes de 200.
JSON inválido.
CEP não encontrado.
Respostas inválidas do serviço.

As falhas retornam `None` e são registradas no log, sem interromper o processamento.

### 9.4. Cache local

O cache é armazenado em:

`data/cache/cep_cache.json`

Suas principais características são:

Chave baseada no CEP normalizado.
Deduplicação das consultas durante a execução.
Reutilização de endereços já consultados.
Gravação atômica com arquivo temporário e `os.replace`.
Recuperação em caso de arquivo ilegível, com aviso no log.

O cache não possui TTL. CEPs sem resposta não são armazenados e podem ser consultados novamente em execuções futuras.

## 10. Qualidade e validação dos dados

A qualidade dos dados é avaliada antes e durante o processamento.

O módulo `pipeline/` concentra os checks e as métricas responsáveis por identificar problemas na base.

### 10.1. Verificações iniciais

A função `executar_checks` avalia:

Colunas obrigatórias ausentes.
Valores nulos em colunas importantes.
Registros duplicados pela chave `id_cliente`.
Linhas completamente vazias.
Existência de dados.

### 10.2. Métricas

A função `calcular_metricas` transforma os resultados das verificações em indicadores quantitativos.

Durante o processamento também são contabilizados problemas relacionados à normalização e à resolução de bairros.

Entre os indicadores acompanhados estão:

Registros rejeitados.
Problemas de CNPJ.
CEPs não encontrados.
Critérios de resolução de bairros.
Quantidade de inconsistências identificadas.

A análise dessas informações permite compreender a condição inicial da base e os resultados obtidos após o tratamento.

### 10.3. Separação entre qualidade e rejeição

Nem toda inconsistência representa motivo para descartar um registro.

O VetorFlow preserva clientes que possuem identificação suficiente, mesmo quando existem problemas em campos secundários.

Essa decisão evita que erros pontuais de preenchimento provoquem perda desnecessária de informações.

## 11. Persistência e banco de dados

O armazenamento dos dados tratados é realizado em PostgreSQL.

O módulo `database/` concentra as operações de conexão e persistência.

### 11.1. Tabela principal

A tabela `usuarios` armazena as informações cadastrais dos clientes.

| Campo | Descrição |
|---|---|
| `id_cliente` | Identificador do cliente |
| `razao_social` | Nome empresarial |
| `cnpj` | Documento cadastral |
| `telefone` | Telefone de contato |
| `email` | Endereço de e-mail |
| `bairro` | Bairro cadastrado ou enriquecido |
| `cep` | Código postal |
| `cidade` | Município |
| `uf` | Unidade federativa |
| `cadastro` | Data de cadastro |
| `responsavel` | Responsável pelo cadastro |

### 11.2. Carga idempotente

A persistência utiliza:

```sql
INSERT INTO usuarios (...)
VALUES (...)
ON CONFLICT (id_cliente) DO NOTHING;
```

A estratégia impede duplicação de clientes durante reexecuções.

O processo utiliza `executemany` para executar a carga em uma transação.

Em caso de falha, ocorre `rollback`.

### 11.3. Comportamento do reprocessamento

A carga não atualiza registros já existentes.

Portanto, alterações nas regras de tratamento não modificam automaticamente os dados anteriormente carregados.

Para reprocessar uma base com novas regras, é necessário considerar a limpeza prévia dos registros existentes.

## 12. API REST

A API REST foi desenvolvida com Django REST Framework e disponibiliza operações de gerenciamento dos clientes armazenados.

A interface de comunicação utiliza JSON e métodos HTTP para executar operações de consulta, criação, atualização e exclusão.

### 12.1. Operações disponíveis

| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/api/clientes/` | Lista clientes |
| GET | `/api/clientes/<id_cliente>/` | Consulta cliente pelo identificador |
| POST | `/api/clientes/` | Cadastra cliente |
| PUT | `/api/clientes/<id_cliente>/` | Atualiza cliente |
| DELETE | `/api/clientes/<id_cliente>/` | Exclui cliente |

### 12.2. Validação das requisições

A API utiliza as regras de normalização compartilhadas com o pipeline, mas adota critérios de validação mais rigorosos para cadastros manuais.

| Situação | Comportamento |
|---|---|
| Telefone inválido | `400 Bad Request` |
| E-mail inválido | `400 Bad Request` |
| Data inválida | `400 Bad Request` |
| Identificador duplicado | `409 Conflict` |
| Registro inexistente | `404 Not Found` |

Diferentemente do processamento em lote, a API permite que o usuário receba o erro e corrija a informação antes de enviar uma nova requisição.

### 12.3. Diferenças entre API e pipeline

O pipeline é tolerante a inconsistências secundárias, pois precisa processar grandes volumes sem interromper toda a execução.

A API, por outro lado, exige dados válidos para operações de cadastro e atualização.

Outra diferença é que o enriquecimento automático de bairro, cidade e UF por CEP está implementado no pipeline, não na API.

## 13. Interface web

O diretório `frontend/` reúne os arquivos responsáveis pela interface de interação com o VetorFlow.

A implementação utiliza HTML, CSS e JavaScript, com comunicação com a API REST.

A interface disponibiliza funcionalidades relacionadas a:

Consulta e enriquecimento de CEP.
Cadastro de clientes.
Busca de registros.
Exclusão de clientes.
Importação e tratamento de arquivos CSV.
Visualização de resultados do benchmark.

A separação entre interface, API e persistência permite que as operações sejam realizadas por meio de uma camada de apresentação, sem necessidade de acesso direto ao banco de dados pelo usuário.

## 14. Auditoria e rastreabilidade

O módulo `audit/` implementa registros para acompanhar o acesso e as operações realizadas na API.

### 14.1. Registro de acessos

O evento `ACESSO` é registrado por middleware e contempla informações como:

Data e horário.
Método HTTP.
URL requisitada.
Endereço IP.
Resultado da requisição.

### 14.2. Registro de operações

O evento `OPERACAO` registra ações de alteração de dados:

`POST`: criação.
`PUT`: atualização.
`DELETE`: exclusão.

O registro contempla os dados gravados, o IP e o resultado da operação.

As requisições `GET` são registradas como acessos, não como operações de alteração.

### 14.3. Auditoria do tratamento

O banco também possui uma estrutura denominada `auditoria_tratamento`, destinada a armazenar informações sobre as transformações realizadas nos campos.

A estrutura prevê informações como:

Valor original.
Valor tratado.
Critério aplicado.
Fonte da informação.
Relacionamento com o cliente.

Entretanto, a gravação individual dessas decisões pelo pipeline ainda não está implementada.

Assim, a rastreabilidade atual é composta por logs da API, registros rejeitados e métricas agregadas do processamento, não sendo possível reconstruir integralmente o histórico de transformação de cada campo.

## 15. Benchmark e análise de desempenho

O módulo `benchmark/` foi desenvolvido para avaliar o comportamento do sistema diante de diferentes volumes de dados.

A proposta é observar como as etapas de processamento e persistência se comportam à medida que a quantidade de registros aumenta.

### 15.1. Geração de dados

O benchmark utiliza bases sintéticas com volumes configuráveis de:

10 mil registros.
100 mil registros.
500 mil registros.
1 milhão de registros.
5 milhões de registros.

Os dados são gerados com inconsistências propositais para simular situações encontradas em bases cadastrais reais.

### 15.2. Indicadores de desempenho

| Indicador | Finalidade |
|---|---|
| Tempo de execução | Medir a duração das operações |
| CPU | Observar a utilização do processador |
| Memória RAM | Avaliar o consumo de memória |
| Registros por segundo | Medir a produtividade do processamento |
| Taxa de erros | Identificar falhas durante a execução |
| Registros rejeitados | Avaliar os resultados das validações |

### 15.3. Estratégias de persistência

O benchmark também contempla a comparação de diferentes estratégias de inserção no PostgreSQL:

Inserção individual.
Inserção em lotes.
`COPY`.

A comparação permite observar diferenças de desempenho entre métodos de persistência.

### 15.4. Resultados

Os resultados são armazenados no diretório:

`data/benchmark/resultados/`

São gerados arquivos de resultados em formatos como JSON e CSV, além de visualizações gráficas e relatório HTML, conforme a execução do benchmark.

Os dados permitem analisar o comportamento do sistema e identificar possíveis gargalos de processamento.

## 16. Testes automatizados

Os testes automatizados utilizam Pytest.

A estratégia de testes prioriza a verificação das regras de negócio e o isolamento das dependências externas.

### 16.1. Cobertura funcional

A suíte contempla testes relacionados a:

Normalizadores cadastrais.
Normalização textual de bairros.
Resolução de divergências.
Regras de validação.
Verificações de qualidade.
Integrações de CEP.
Processamento e carga.
Operações da API.

### 16.2. Simulação de dependências

As consultas às APIs externas e as operações de banco de dados são simuladas por meio de mocks quando aplicável.

Essa abordagem evita chamadas durante os testes e permite reproduzir cenários controlados, como:

Respostas válidas.
CEP não encontrado.
Falha de conexão.
Resposta inválida.
Erros durante a persistência.

Os testes tornam-se mais previsíveis e independentes da disponibilidade dos serviços externos.

## 17. Estrutura do projeto

A organização do repositório segue a separação dos módulos e responsabilidades do sistema.

```text
VetorFlow/
│
├── api/                  # API REST e gerenciamento de clientes
├── audit/                # Logs e auditoria
├── benchmark/            # Geração de dados e avaliações
├── config/               # Configurações do Django
│
├── data/
│   ├── raw/              # Arquivos CSV originais
│   ├── processed/        # Dados processados
│   ├── cache/            # Cache de endereços
│   └── benchmark/        # Resultados das avaliações
│
├── database/             # Conexão e persistência
├── docs/                 # Documentação técnica
│
├── frontend/
│   ├── templates/        # Templates HTML
│   └── static/
│       ├── css/          # Estilos
│       └── js/           # Scripts
│
├── integrations/         # Integrações com serviços externos
├── neighborhood/         # Normalização e resolução de bairros
├── normalizers/          # Normalizadores cadastrais
├── pipeline/             # Processamento ETL e qualidade
├── test/                 # Testes automatizados
│
├── .env.example          # Exemplo de configuração
├── .gitignore
├── Makefile
├── manage.py
├── exceptions.py
├── logging_config.py
├── pytest.ini
├── requirements.txt
└── README.md
```

## 18. Instalação e configuração

### 18.1. Pré-requisitos

Antes de iniciar, é necessário possuir:

- Python 3.10 ou superior.
- PostgreSQL.
- Git.
- Acesso ao terminal.

### 18.2. Clonar o repositório

```bash
git clone https://github.com/Geovannarn/VetorFlow.git

cd VetorFlow
```

### 18.3. Criar o ambiente virtual

Windows:

```powershell
python -m venv .venv
```

Linux:

```bash
python -m venv .venv
```

### 18.4. Ativar o ambiente virtual

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Linux:

```bash
source .venv/bin/activate
```

### 18.5. Instalar dependências

```bash
pip install -r requirements.txt
```

### 18.6. Configurar o PostgreSQL

Crie o banco de dados que será utilizado pela aplicação e separe as credenciais necessárias para a conexão.

### 18.7. Configurar variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto, utilizando `.env.example` como referência.

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

Substitua os valores de exemplo pelas configurações do ambiente local.

**Segurança:** o arquivo `.env` não deve ser versionado, pois contém credenciais e informações sensíveis.

## 19. Execução

### 19.1. Verificar a configuração do Django

```bash
python manage.py check
```

### 19.2. Iniciar o servidor

```bash
python manage.py runserver
```

A aplicação estará disponível em:

`http://127.0.0.1:8000/`

A API REST está disponível a partir de:

`http://127.0.0.1:8000/api/`

### 19.3. Executar os testes

```bash
pytest
```

### 19.4. Executar o benchmark

```bash
python -m benchmark.executar
```

Os resultados são organizados em `data/benchmark/resultados/`.

**Observação:** os comandos de execução do pipeline ETL e de inicialização do banco devem seguir os pontos de entrada e procedimentos específicos implementados nos respectivos módulos.

## 20. Decisões técnicas e limitações

O desenvolvimento do VetorFlow envolve decisões relacionadas à qualidade, integridade, desempenho e manutenção dos dados.

As principais escolhas incluem:

| Decisão | Justificativa |
|---|---|
| Pipeline modular | Permite testar e manter etapas separadamente |
| Normalização determinística | Evita resultados imprevisíveis |
| Comparação de bairros sem acentos | Identifica variações textuais equivalentes |
| Prevalência do bairro informado em divergências | Evita substituir informação original sem confirmação |
| ViaCEP com BrasilAPI como reserva | Reduz dependência de uma única fonte |
| Cache local | Evita consultas repetidas |
| Rejeição seletiva | Preserva clientes com inconsistências secundárias |
| Carga idempotente | Evita duplicação de identificadores |
| Validação rigorosa na API | Permite corrigir dados no momento do cadastro |
| Mocks nos testes | Garante testes controlados e independentes de serviços externos |

### Limitações conhecidas

O sistema possui algumas limitações que devem ser consideradas:

1. Bairros divergentes dependem de revisão manual.
2. O dicionário de abreviações contempla somente variantes conhecidas.
3. Alguns bairros sem correspondência confiável de CEP permanecem com a informação cadastrada.
4. O cache não possui política de expiração.
5. CEPs não encontrados não são armazenados no cache.
6. CNPJs com dígitos verificadores inválidos não bloqueiam registros, devido à natureza fictícia da base.
7. A carga idempotente não atualiza registros já existentes.
8. Datas inválidas são anuladas sem contador próprio no resumo.
9. A API não executa o mesmo enriquecimento de endereço disponível no pipeline.
10. A rastreabilidade individual das transformações ainda não está implementada.
11. O funcionamento do enriquecimento depende da disponibilidade de serviços públicos externos.

Essas limitações são documentadas para diferenciar o comportamento efetivamente implementado das melhorias que podem ser consideradas em evoluções futuras.

## 21. Documentação complementar

A documentação técnica do VetorFlow está organizada no diretório [`docs/`](docs/).

O objetivo é manter o README como ponto de entrada do projeto e distribuir o detalhamento das regras, da arquitetura e das decisões em documentos específicos.

Entre os assuntos documentados estão:

Arquitetura do sistema.
Etapas e funcionamento do ETL.
Regras de tratamento e normalização.
Decisões técnicas e trade-offs.
Estrutura do banco de dados.
Endpoints e funcionamento da API.
Testes e benchmark.

Consulte os documentos complementares para obter detalhes sobre a implementação e as regras específicas de cada módulo.

---

**VetorFlow**