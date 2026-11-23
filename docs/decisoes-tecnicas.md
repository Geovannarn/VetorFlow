# Decisões Técnicas — VetorFlow

Registro das decisões tomadas no pipeline de ETL da Distribuidora Vetor (Desafio 1). Cada decisão informa **o que foi decidido, por quê, as alternativas consideradas e as consequências**. Para uma consulta rápida das regras, veja [`regras-de-tratamento.md`](regras-de-tratamento.md).

## Sumário

1. [Visão geral do pipeline](#1-visão-geral-do-pipeline)
2. [D1: Fluxo de tratamento em etapas](#d1-fluxo-de-tratamento-em-etapas)
3. [D2: Normalização textual determinística do bairro](#d2-normalização-textual-determinística-do-bairro)
4. [D3: Critério de resolução entre bairro informado e bairro do CEP](#d3-critério-de-resolução-entre-bairro-informado-e-bairro-do-cep)
5. [D4: Dicionário de apelidos mínimo](#d4-dicionário-de-apelidos-mínimo)
6. [D5: ViaCEP como fonte principal e BrasilAPI como reserva](#d5-viacep-como-fonte-principal-e-brasilapi-como-reserva)
7. [D6: Cache local dos CEPs](#d6-cache-local-dos-ceps)
8. [D7: Tratamento de CNPJ, telefone, e-mail, data e CEP](#d7-tratamento-de-cnpj-telefone-e-mail-data-e-cep)
9. [D8: O que rejeitar e o que apenas anular](#d8-o-que-rejeitar-e-o-que-apenas-anular)
10. [D9: Carga idempotente no PostgreSQL](#d9-carga-idempotente-no-postgresql)
11. [D10: Pipeline tolerante, API rigorosa](#d10-pipeline-tolerante-api-rigorosa)
12. [D11: Checks e métricas de qualidade](#d11-checks-e-métricas-de-qualidade)
13. [D12: Rastreabilidade e auditoria](#d12-rastreabilidade-e-auditoria)
14. [D13: Testes com dependências externas simuladas](#d13-testes-com-dependências-externas-simuladas)
15. [Limites conhecidos](#limites-conhecidos)

## 1. Visão geral do pipeline

```
CSV (data/raw)
   │
   ▼
Checks de qualidade da entrada (pipeline/checks.py, metrics.py)
   │
   ▼
Consulta de CEP: cache → ViaCEP → BrasilAPI (integrations/)
   │
   ▼
Tratamento linha a linha (pipeline/): normalizers/ + neighborhood/
   │
   ├──► rejeitados (id vazio, razão social vazia, id duplicado)
   ▼
Carga no PostgreSQL, tabela usuarios (ON CONFLICT DO NOTHING)
```

A mesma lógica de normalização (`normalizers/`) é reutilizada pela API REST, o que garante um único padrão de dados no banco.

## D1: Fluxo de tratamento em etapas

**Decisão.** Separar o processo em módulos: leitura (`carregar_csv`), checks, enriquecimento por CEP (`buscar_enderecos`), tratamento por linha (`tratar_linha`) e carga (`carregar_no_banco`). A função `processar_csv` orquestra tudo e aceita os parâmetros `consultar_api` e `gravar`.

**Motivo.** Cada etapa pode ser testada isoladamente. Com `consultar_api=False` e `gravar=False`, o pipeline roda sem internet e sem banco, o que facilita testes e demonstrações.

**Alternativas.** Um único script sequencial (mais simples, porém difícil de testar e de simular as APIs).

**Consequências.** Mais arquivos para navegar, mas responsabilidades claras (critério de Arquitetura da ficha).

## D2: Normalização textual determinística do bairro

**Decisão.** O bairro passa por uma sequência fixa de regras em `neighborhood/normalizer.py`:

1. Remove espaços nas pontas e normaliza o Unicode (NFC).
2. Se houver parênteses, **usa o conteúdo de dentro**: `"Norte (Águas Claras)"` → `"Águas Claras"`.
3. Remove sufixo de UF (`" - DF"`, `"/DF"`), só quando a sigla é uma UF válida.
4. Troca pontuação por espaço e colapsa espaços repetidos.
5. Gera uma **chave de comparação** sem acento e em minúsculas (`casefold`): `"AGUAS CLARAS"`, `"Águas Claras"` e `"aguas claras"` viram `"aguas claras"`.
6. Gera o **nome de exibição**, com iniciais maiúsculas, preposições (`de`, `da`, `do`...) em minúsculas e algarismos romanos em maiúsculas.

**Motivo.** Resolve, sem depender de API, as variações de caixa, acentuação, espaços e subdivisões informais citadas no desafio. É determinístico: a mesma entrada sempre gera a mesma saída.

**Separação entre chave e nome.** A chave serve para **comparar**, e o nome serve para **gravar**. Assim a comparação ignora acentos, mas o dado gravado mantém a grafia digitada, com a capitalização corrigida.

**Alternativas.** Distância de edição (fuzzy matching), descartada por risco de unir bairros diferentes com nomes parecidos (ex.: "Guará I" e "Guará II").

**Consequências.** Variações que exigem conhecimento de domínio (abreviações) não são resolvidas pela normalização; ver D4.

## D3: Critério de resolução entre bairro informado e bairro do CEP

**Decisão.** A função `resolver_bairro(bairro_informado, bairro_api)` compara as duas chaves e devolve o **nome final** e o **critério** aplicado:

| Situação | Bairro gravado | Critério |
|---|---|---|
| Os dois ausentes | `NULL` | `sem informação` |
| Só a API tem valor | nome da API | `api` |
| Só o cliente informou | nome informado | `informado` |
| Chaves iguais | nome da API | `convergente` |
| Informado contido no da API (ex.: `"Aguas Claras"` em `"Aguas Claras Norte"`) | nome da API | `convergente` |
| Da API contido no informado | nome informado | `convergente` |
| Conflito real (nomes diferentes) | **nome informado** | `divergente` |

**Regra da "contenção".** Compara-se por **conjunto de palavras**. Palavras puramente direcionais (`norte`, `sul`, `leste`, `oeste`, `centro`) **não bastam** para considerar convergência, para que "Norte" sozinho não seja tratado como igual a qualquer bairro que contenha "Norte".

**Decisão de maior impacto: em caso de divergência, prevalece o bairro informado**, e o registro é marcado como `divergente`.

**Motivo.**
O CEP pode estar errado ou ser genérico (CEP de cidade ou de logradouro grande), enquanto o bairro digitado reflete o que o vendedor viu em campo.

O registro não é descartado nem corrigido às cegas: o rótulo `divergente` permite revisão manual posterior.

Em caso de convergência por contenção, escolhe-se o nome **mais completo** (o mais específico).

**Alternativas.**
*Sempre confiar na API*: propaga erros de CEP para o bairro e apaga informação correta do cliente.
*Descartar divergentes*: perde registros válidos.
*Revisão manual de todos*: não escala.

**Consequências.** Os casos `divergente` ficam no banco com o valor informado e precisam de revisão humana. Essa é a parte que **não foi automatizada de propósito** (ver relatório de trade-offs).

## D4: Dicionário de apelidos mínimo

**Decisão.** Existe um dicionário `APELIDOS` com poucas entradas (`"v pires"` e `"vte pires"` → `"vicente pires"`), aplicado após a normalização.

**Motivo.** Abreviações não são resolvidas por regra textual nem por API. Optou-se por um dicionário pequeno, ampliado **conforme as variantes aparecem** no dataset, em vez de tentar prever todas. O enunciado também orienta que regras de negócio sejam assumidas e documentadas pela própria equipe, sem inferência de fontes externas.

**Alternativas.** Dicionário exaustivo de bairros do DF (exige fonte oficial e manutenção).

**Consequências.** Novas abreviações exigem incluir uma linha no dicionário.

## D5: ViaCEP como fonte principal e BrasilAPI como reserva

**Decisão.** Para cada CEP válido, a ordem de consulta é: **cache local → ViaCEP → BrasilAPI**. O resultado é convertido por `padronizar_endereco` para um formato único (`bairro`, `cidade`, `uf`), pois as duas APIs usam nomes de campos diferentes (`localidade`/`city`, `uf`/`state`, `bairro`/`neighborhood`).

**Motivo.** Uma segunda fonte reduz o número de CEPs sem resposta quando uma API está fora do ar ou não conhece o CEP.

**Tratamento de falhas.** Cada consulta usa timeout de 5 segundos. Erro de rede, resposta diferente de 200 ou JSON inválido retornam `None` e geram um aviso no log, sem interromper o pipeline. O ViaCEP também retorna `None` quando a resposta traz `"erro": true`.

**Consequências.** Se as duas APIs falham, o CEP entra na contagem `cep_nao_encontrados` e o bairro segue pelo critério `informado`.

## D6: Cache local dos CEPs

**Decisão.** Os endereços já consultados ficam em `data/cache/cep_cache.json`, com chave igual ao CEP normalizado.

**Motivos.**
Evita chamadas repetidas e respeita o limite das APIs públicas.
Permite reprocessar sem internet para CEPs já conhecidos.
Reduz o tempo de execução.

**Detalhes de segurança do arquivo.**
- A gravação é **atômica**: escreve num arquivo temporário e depois usa `os.replace`, evitando cache corrompido se o processo for interrompido.
- Se o arquivo estiver ilegível, é recriado, com aviso no log.
- Os CEPs também são deduplicados dentro da própria execução, então cada CEP é consultado uma única vez por rodada.

**Consequências.** O cache **não tem validade (TTL)**, portanto dados desatualizados só mudam se o arquivo for apagado. CEPs não encontrados **não são gravados** no cache e serão consultados de novo na próxima execução.

## D7: Tratamento de CNPJ, telefone, e-mail, data e CEP

| Campo | Regra | Resultado inválido |
|---|---|---|
| **CNPJ** | Remove tudo que não é dígito; exige 14 dígitos | `NULL` |
| **Telefone** | Remove não dígitos; remove DDI `55` quando há mais de 11 dígitos; exige 10 ou 11 dígitos; grava com prefixo `+55` | `NULL` |
| **E-mail** | `strip` e minúsculas; valida com expressão regular | `NULL` |
| **Data** | Aceita `DD/MM/AAAA`, `AAAA-MM-DD`, `DD-MM-AAAA` e `Mês DD, AAAA` (meses em inglês abreviados); grava em ISO | `NULL` |
| **CEP** | Aceita 8 dígitos com ou sem hífen; `00000000` é tratado como ausente | `NULL` |
| **UF** | Maiúsculas; se ausente, é preenchida pela API do CEP | mantém `NULL` |
| **Cidade** | Se ausente, é preenchida pela API do CEP | mantém `NULL` |

**Decisão sobre o dígito verificador do CNPJ.** O pipeline **calcula** o dígito verificador (`validar_cnpj`), mas **não rejeita nem anula** o registro quando ele falha: apenas conta em `cnpj_digito_invalido`. Apenas o formato (14 dígitos) é exigido.

**Motivo.** Os CNPJs do dataset são fictícios por definição do desafio e podem não passar no cálculo. Rejeitá-los esvaziaria a base. A métrica separada deixa o problema visível sem perder registros.

**Consequências.** Em dados reais, seria necessário decidir se CNPJ com dígito inválido deve ser rejeitado.

## D8: O que rejeitar e o que apenas anular

**Decisão.** Só **três** situações rejeitam um registro (ele vai para o DataFrame de `rejeitados`, com o campo `motivo`):

`id_cliente` vazio;
`razao_social` vazia;
`id_cliente` duplicado dentro do arquivo (vale o primeiro).

Qualquer outro campo inválido (CNPJ, telefone, e-mail, CEP, data) **vira `NULL` e é contado**, sem descartar o cliente.

**Motivo.** O cliente continua existindo para o negócio mesmo com um telefone mal digitado. Perder o registro inteiro seria pior do que ter um campo vazio. A identificação (`id_cliente` e `razao_social`) é o mínimo para o registro ter sentido.

**Consequências.** A base final pode ter campos `NULL`, e as métricas mostram a proporção de cada tipo de problema.

## D9: Carga idempotente no PostgreSQL

**Decisão.** A carga usa `INSERT ... ON CONFLICT (id_cliente) DO NOTHING`, em uma única transação (`executemany`), com `rollback` em caso de erro e fechamento da conexão no `finally`.

**Motivo.** O pipeline pode ser executado várias vezes sem duplicar clientes nem falhar por chave repetida.

**Consequências.** Reprocessar **não atualiza** registros já existentes. Se a regra de tratamento mudar, é preciso limpar a tabela antes de recarregar. O número de inseridos reportado indica apenas as linhas realmente novas.

## D10: Pipeline tolerante, API rigorosa

**Decisão.** O mesmo dado inválido tem tratamentos diferentes:

| Situação | Pipeline (carga em lote) | API (cadastro manual) |
|---|---|---|
| Telefone inválido | `NULL` e contagem | `400 Bad Request` |
| E-mail inválido | `NULL` e contagem | `400 Bad Request` |
| Data inválida | `NULL` | `400 Bad Request` |
| `id_cliente` repetido | Ignorado (`DO NOTHING`) | `409 Conflict` |

**Motivo.** Em lote, interromper por um campo ruim impediria a carga de milhares de registros. No cadastro manual, o usuário pode corrigir na hora e informar o valor certo.

**Consequência.** A API não resolve o bairro pelo CEP nem preenche cidade e UF; essa lógica existe apenas no pipeline.

## D11: Checks e métricas de qualidade

**Decisão.** Antes do tratamento, `executar_checks` mede a base de entrada: colunas ausentes, nulos por coluna obrigatória, duplicados pela chave `id_cliente`, registros totalmente vazios e se há dados. `calcular_metricas` transforma isso em percentuais. O pipeline também interrompe com erro (`ValueError`) se faltar qualquer coluna esperada do CSV.

**Motivo.** Medir o "antes" permite comparar com o "depois" e demonstrar a **cobertura do tratamento**, critério da rubrica.

## D12: Rastreabilidade e auditoria

**O que existe.**
**Contagens por tipo de problema e por critério de bairro** (`convergente`, `informado`, `api`, `divergente`, `sem informação`), exibidas no resumo da execução.
**Registros rejeitados** com o motivo.
**Log de auditoria da API** (`audit/audit.log`): `ACESSO` (middleware, toda requisição) e `OPERACAO` (`POST`, `PUT` e `DELETE`, com os dados gravados, o IP e o resultado). O `GET` não é registrado como operação.
**Tabela `auditoria_tratamento`** modelada no banco (valor original, valor tratado, critério e fonte, ligada a `usuarios` por chave estrangeira), prevista para registrar cada decisão por campo.

**Motivo da tabela.** O desafio pede explicar, para qualquer registro, por que ele ficou daquele jeito. O resumo agregado mostra quantos registros caíram em cada critério, mas só a trilha por campo responde por um cliente específico.

**Consequências.** Enquanto a gravação não for implementada, a rastreabilidade por registro é parcial: o critério de bairro é calculado, mas só entra no resumo agregado.

## D13: Testes com dependências externas simuladas

**Decisão.** As chamadas às APIs de CEP e ao banco são simuladas (mocks) nos testes, e a normalização é testada com entradas controladas.

**Motivo.** Exigência do desafio: chamadas externas não podem ser reais nos testes. Isso torna os testes rápidos, repetíveis e independentes de internet.

## Limites conhecidos

1. **Divergência exige revisão manual.** Registros `divergente` mantêm o bairro informado.
2. **Dicionário de apelidos pequeno.** Só cobre as abreviações vistas no dataset.
3. **Bairro sem CEP confiável** (caso do Guará no dataset) fica com o valor informado, normalizado, sem confirmação externa.
4. **CEP com pontuação fora do padrão** (ex.: `71.900-000` ou com espaços) é considerado inválido.
5. **Cache sem validade e sem registro de CEPs não encontrados.**
6. **Dígito verificador do CNPJ não bloqueia o registro.**
7. **Reprocessamento não atualiza registros existentes** (`DO NOTHING`).
8. **Datas inválidas viram `NULL` sem contador próprio** no resumo.
9. **A API não resolve bairro pelo CEP**; essa lógica existe só no pipeline em lote.
10. **Rastreabilidade por registro ainda parcial**: a tabela de auditoria está modelada, mas o pipeline ainda não grava nela.
11. **Dependência de serviços públicos gratuitos**, sujeitos a indisponibilidade e a limites de uso.