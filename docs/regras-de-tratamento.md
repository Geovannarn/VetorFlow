# Regras de Tratamento — VetorFlow

Resumo de todas as regras aplicadas aos dados da Distribuidora Vetor. Para saber **por que** cada regra foi escolhida, veja [`decisoes-tecnicas.md`](decisoes-tecnicas.md).

## Sumário

1. [Visão geral](#1-visão-geral)
2. [Regras por campo](#2-regras-por-campo)
3. [Regras de bairro](#3-regras-de-bairro)
4. [Enriquecimento por CEP](#4-enriquecimento-por-cep)
5. [Quando um registro é rejeitado](#5-quando-um-registro-é-rejeitado)
6. [Diferenças entre pipeline e API](#6-diferenças-entre-pipeline-e-api)
7. [Limites conhecidos](#7-limites-conhecidos)

## 1. Visão geral

Cada linha do CSV passa por três etapas, nesta ordem:

1. **Verificação da entrada**: colunas esperadas, nulos e duplicados.
2. **Normalização de cada campo** (seção 2) e **resolução do bairro** com apoio da consulta de CEP (seções 3 e 4).
3. **Carga** na tabela `usuarios`.

**Princípio geral:** dado inválido vira `NULL` e é contado; o cliente só é rejeitado se faltar a identificação (seção 5).

## 2. Regras por campo

| Campo | Regra aplicada | Exemplo de entrada → saída | Se for inválido |
|---|---|---|---|
| `id_cliente` | Espaços repetidos removidos; obrigatório e único | `" 12 "` → `12` | Registro rejeitado |
| `razao_social` | Espaços repetidos removidos; obrigatória | `"Mercado  Sol  LTDA"` → `Mercado Sol LTDA` | Registro rejeitado |
| `cnpj` | Mantém só os dígitos; exige 14 | `12.345.678/0001-90` → `12345678000190` | `NULL` |
| `telefone` | Mantém só os dígitos; remove o DDI `55` se houver mais de 11 dígitos; exige 10 ou 11; grava com `+55` | `(61) 99999-8888` → `+5561999998888` | `NULL` |
| `email` | Remove espaços, converte para minúsculas e valida o formato | `Contato@Exemplo.COM` → `contato@exemplo.com` | `NULL` |
| `cep` | Aceita 8 dígitos, com ou sem hífen; `00000000` é tratado como ausente | `71900-000` → `71900000` | `NULL` |
| `cadastro` | Converte para ISO `AAAA-MM-DD` | `05/03/2024` → `2024-03-05` | `NULL` |
| `cidade` | Remove espaços repetidos; se vazia, é preenchida pela consulta de CEP | vazio → `Brasília` | Fica `NULL` se a consulta falhar |
| `uf` | Converte para maiúsculas; se vazia, é preenchida pela consulta de CEP | `df` → `DF` | Fica `NULL` se a consulta falhar |
| `responsavel` | Remove espaços repetidos | `"Ana   Lima"` → `Ana Lima` | `NULL` se vazio |

### Formatos de data aceitos

| Formato | Exemplo |
|---|---|
| `DD/MM/AAAA` | `05/03/2024` |
| `AAAA-MM-DD` | `2024-03-05` |
| `DD-MM-AAAA` | `05-03-2024` |
| Mês em inglês abreviado | `Mar 5, 2024` |

Datas impossíveis (como `31/02/2024`) são tratadas como inválidas.

### CNPJ: dígito verificador

O dígito verificador é **calculado**, mas um CNPJ que falha no cálculo **não é anulado nem rejeitado**: ele é apenas contado em `cnpj_digito_invalido`. Só o formato (14 dígitos) define se o valor é gravado.

## 3. Regras de bairro

### 3.1 Normalização do texto

Aplicadas nesta ordem a `bairro_informado`:

| Passo | Regra | Exemplo |
|:---:|---|---|
| 1 | Remove espaços nas pontas | `" Taguatinga "` → `Taguatinga` |
| 2 | Se houver parênteses, usa só o conteúdo de dentro | `Norte (Águas Claras)` → `Águas Claras` |
| 3 | Remove sufixo de UF válida | `Taguatinga - DF` → `Taguatinga` |
| 4 | Troca pontuação por espaço e junta espaços repetidos | `Vicente  Pires.` → `Vicente Pires` |
| 5 | Gera uma **chave de comparação** (sem acento, minúscula) | `AGUAS CLARAS` e `Águas Claras` → `aguas claras` |
| 6 | Gera o **nome de exibição** (iniciais maiúsculas, preposições em minúsculas, romanos em maiúsculas) | `guará ii` → `Guará II` |

Bairros diferentes só são considerados iguais se as **chaves** forem iguais (ou se uma estiver contida na outra, ver 3.3).

### 3.2 Dicionário de apelidos

| Variante | Bairro canônico |
|---|---|
| `v pires` | Vicente Pires |
| `vte pires` | Vicente Pires |

Para incluir uma nova variante, basta acrescentar uma linha ao dicionário `APELIDOS` em `neighborhood/resolver.py`.

### 3.3 Comparação entre o bairro informado e o bairro do CEP

| Situação | Bairro gravado | Critério registrado |
|---|---|---|
| Os dois ausentes | `NULL` | `sem informação` |
| Só a consulta de CEP tem valor | Nome da consulta | `api` |
| Só o cliente informou | Nome informado | `informado` |
| Chaves iguais | Nome da consulta | `convergente` |
| O informado está contido no da consulta (ex.: `aguas claras` em `aguas claras norte`) | Nome da consulta | `convergente` |
| O da consulta está contido no informado | Nome informado | `convergente` |
| Nomes realmente diferentes | **Nome informado** | `divergente` |

**Regra da contenção:** a comparação é feita por conjunto de palavras. Palavras apenas direcionais (`norte`, `sul`, `leste`, `oeste`, `centro`) **não bastam** para considerar convergência.

**Em divergência, prevalece o que o cliente informou**, e o registro fica marcado como `divergente` para revisão manual.

### 3.4 Exemplos

| Informado | Retorno do CEP | Gravado | Critério |
|---|---|---|---|
| `AGUAS CLARAS` | `Águas Claras` | `Águas Claras` | `convergente` |
| `Norte (Águas Claras)` | `Águas Claras` | `Águas Claras` | `convergente` |
| `v pires` | `Vicente Pires` | `Vicente Pires` | `convergente` |
| `Taguatinga` | `Ceilândia` | `Taguatinga` | `divergente` |
| `Guará II` | *(CEP ausente)* | `Guará II` | `informado` |
| *(vazio)* | `Taguatinga` | `Taguatinga` | `api` |
| *(vazio)* | *(sem CEP)* | `NULL` | `sem informação` |

## 4. Enriquecimento por CEP

| Item | Regra |
|---|---|
| Quando consulta | Para cada CEP válido e diferente de `00000000`, uma vez por execução |
| Ordem das fontes | Cache local → ViaCEP → BrasilAPI |
| Timeout | 5 segundos por consulta |
| Dados aproveitados | Bairro, cidade e UF |
| Cache | `data/cache/cep_cache.json`, gravado de forma atômica |
| Falha nas duas APIs | O CEP é contado como não encontrado e o bairro segue pelo critério `informado` |
| Uso de cidade e UF | Só preenchem campos que vieram **vazios** no CSV; nunca substituem o que o cliente informou |

## 5. Quando um registro é rejeitado

| Motivo | Observação |
|---|---|
| `id_cliente` vazio | |
| `razao_social` vazia | |
| `id_cliente` duplicado no arquivo | Mantém o primeiro registro e rejeita os seguintes |

Qualquer outro problema **não rejeita** o cliente: o campo vira `NULL` e entra na contagem do resumo da execução.

**Carga repetida:** se o `id_cliente` já existe no banco, o registro é ignorado (`ON CONFLICT DO NOTHING`), sem erro e sem atualizar os dados.

## 6. Diferenças entre pipeline e API

| Situação | Pipeline (carga em lote) | API (cadastro manual) |
|---|---|---|
| Telefone, e-mail, CNPJ, CEP ou data inválidos | `NULL` e contagem | `400 Bad Request` com mensagem |
| Resolução de bairro com a consulta de CEP | Sim | Não: o bairro é gravado como enviado |
| Preenchimento de cidade e UF pelo CEP | Sim | Não |
| `id_cliente` repetido | Ignorado | `409 Conflict` |

## 7. Limites conhecidos

| # | Limite | Efeito |
|:---:|---|---|
| 1 | Divergência de bairro exige revisão manual | O registro `divergente` mantém o valor do cliente |
| 2 | O dicionário de apelidos é pequeno | Abreviações novas não são reconhecidas até serem incluídas |
| 3 | Sem CEP confiável, não há confirmação externa do bairro | O valor informado é normalizado, mas não validado (caso do Guará no dataset) |
| 4 | Sem consulta de CEP, o nome sai sem acento se o cliente digitou sem acento | `AGUAS CLARAS` → `Aguas Claras` |
| 5 | CEP com pontuação fora do padrão é inválido | `71.900-000` e CEP com espaços viram `NULL` |
| 6 | Meses em inglês só no formato abreviado de 3 letras | `March 5, 2024` não é reconhecido |
| 7 | Datas inválidas viram `NULL` sem contador próprio no resumo | Não aparecem nas métricas |
| 8 | O dígito verificador do CNPJ não bloqueia o registro | CNPJ com dígito errado pode ser gravado |
| 9 | O cache não tem validade e não guarda CEPs não encontrados | Dados antigos persistem; CEPs ausentes são consultados de novo a cada execução |
| 10 | Reprocessar não atualiza registros existentes | Para aplicar regras novas, é preciso limpar a tabela antes |
| 11 | Dependência de APIs públicas gratuitas | Indisponibilidade reduz o enriquecimento |