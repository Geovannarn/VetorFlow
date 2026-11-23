Relatório

## 1. Contextualização do projeto

O VetorFlow foi desenvolvido como uma solução de ETL (Extract, Transform, Load) destinada ao tratamento, à validação, ao enriquecimento e ao armazenamento dos dados cadastrais de clientes da Distribuidora Vetor.

O objetivo principal do projeto é transformar uma base de dados originalmente inconsistente em informações mais estruturadas, padronizadas e adequadas para utilização posterior.

O dataset disponibilizado apresenta inconsistências propositalmente inseridas, como diferentes formatos de CNPJ, telefone, e-mail e datas, além de valores ausentes, inválidos ou incompatíveis entre diferentes campos. Entre os problemas identificados, destacam-se CEPs inexistentes ou incompletos e divergências entre os bairros informados nos cadastros e aqueles retornados pelos serviços externos de consulta.

Diante desse cenário, o desenvolvimento exigiu mais do que a implementação de funções de limpeza. Foi necessário estabelecer critérios para determinar quais informações poderiam ser corrigidas automaticamente, quais poderiam ser complementadas por fontes externas e quais deveriam permanecer classificadas como inconsistentes.

As decisões foram orientadas por três aspectos principais:

**Confiabilidade:** evitar alterações automáticas que pudessem introduzir informações incorretas.
**Automação:** reduzir intervenções manuais por meio de regras reproduzíveis e funções específicas.
**Rastreabilidade:** permitir compreender os critérios utilizados durante o processamento e identificar situações que não puderam ser resolvidas automaticamente.

Assim, o VetorFlow foi estruturado para priorizar a consistência dos dados sem assumir que toda inconsistência representa necessariamente um erro que pode ser corrigido de maneira automática.

## 2. O que foi automatizado

A automação foi concentrada nas etapas em que existiam critérios objetivos para identificar, validar ou transformar os valores recebidos.

Em vez de utilizar uma única rotina genérica para tratar todos os campos, foram desenvolvidas funções específicas de normalização e validação, considerando as características e as regras de cada tipo de informação.

### 2.1. Normalização dos dados cadastrais

Foram implementados normalizadores para diferentes campos do cadastro, incluindo CNPJ, telefone, e-mail, texto e CEP.

Cada normalizador possui uma finalidade específica:

**CNPJ:** padronização da representação do documento, considerando diferentes formatos de entrada.
**Telefone:** tratamento de caracteres e variações de formatação.
**E-mail:** padronização textual para facilitar verificações e comparações.
**Texto:** tratamento de espaços, caracteres especiais, acentuação e diferenças de representação.
**CEP:** padronização do formato e preparação do valor para consultas externas.

A separação dessas responsabilidades permite que cada campo seja tratado conforme suas próprias características, evitando que uma regra genérica produza transformações inadequadas.

Um dos benefícios dessa abordagem é a possibilidade de ampliar ou modificar as regras de determinado campo sem precisar alterar toda a estrutura do pipeline.

Entretanto, essa escolha também aumenta a quantidade de funções e regras que precisam ser mantidas, testadas e documentadas.

### 2.2. Normalização e resolução de bairros

O tratamento dos bairros exigiu uma abordagem específica porque a comparação entre nomes de localidades não depende exclusivamente da igualdade textual.

Um mesmo bairro pode aparecer com diferenças de acentuação, capitalização, espaçamento, caracteres especiais e sufixos de identificação de unidades federativas.

Para reduzir essas variações, foi implementado um processo de normalização textual que permite comparar os valores em uma representação padronizada.

Também foi adicionada uma regra para identificar e remover sufixos de UF no final do nome do bairro, desde que a sigla corresponda a uma unidade federativa válida. Isso evita remover indiscriminadamente qualquer combinação de duas letras que apareça depois de um hífen ou de uma barra.

Entretanto, a normalização textual não é suficiente para determinar se dois nomes diferentes representam a mesma localidade.

Por esse motivo, foi desenvolvido um mecanismo complementar de resolução, responsável por comparar o bairro informado no cadastro com o bairro retornado pela consulta de CEP.

Essa separação entre normalização e resolução permite distinguir duas operações diferentes:

1. **Normalização:** transforma os valores para uma representação comparável.
2. **Resolução:** avalia a disponibilidade e a compatibilidade das informações e determina qual valor será utilizado.

Essa distinção é importante porque dois valores podem ser textualmente diferentes, mas representar a mesma localidade, assim como podem apresentar semelhanças textuais sem corresponder ao mesmo bairro.

### 2.3. Enriquecimento por APIs externas

O enriquecimento dos dados foi implementado utilizando duas fontes externas: ViaCEP e BrasilAPI.

Esses serviços permitem consultar informações associadas ao CEP, possibilitando complementar os registros que possuem informações incompletas e fornecer uma segunda referência para comparação dos dados cadastrais.

A utilização de duas APIs também permite estabelecer uma estratégia de consulta alternativa quando a primeira fonte não fornece o resultado esperado.

Entretanto, a consulta externa não representa uma garantia absoluta de correção. As informações retornadas dependem da disponibilidade, da abrangência e da atualização das bases utilizadas pelos serviços.

Dessa forma, os dados externos são utilizados como fontes de enriquecimento e comparação, e não como uma autoridade incontestável sobre todas as informações presentes no cadastro.

### 2.4. Implementação de cache

Para reduzir consultas repetidas às APIs, foi implementado um mecanismo de cache local.

Quando um CEP já possui uma resposta armazenada, o sistema pode reutilizar essa informação em vez de realizar uma nova requisição externa.

Essa decisão apresenta benefícios importantes:

Redução da quantidade de requisições externas.
Diminuição do tempo de processamento em consultas repetidas.
Menor dependência da disponibilidade momentânea das APIs.
Redução do consumo de recursos de comunicação.
Maior previsibilidade durante o processamento de registros que compartilham o mesmo CEP.

O cache, entretanto, introduz uma limitação: uma resposta armazenada pode deixar de representar a informação mais atualizada disponibilizada pelo serviço externo.

Portanto, existe um equilíbrio entre desempenho e atualização dos dados. O reaproveitamento de respostas reduz o custo das consultas, mas exige considerar que informações externas podem sofrer alterações.

### 2.5. Verificações de qualidade dos dados

O pipeline também automatiza verificações destinadas a identificar problemas estruturais e inconsistências presentes na base.

Entre as verificações implementadas estão:

Identificação de colunas ausentes.
Identificação de valores nulos.
Detecção de registros duplicados.
Verificação da existência de registros.
Cálculo de métricas relacionadas à qualidade dos dados.

A partir dessas verificações, são produzidas informações quantitativas, como a quantidade e o percentual de valores nulos e registros duplicados.

Essas métricas permitem avaliar as condições da base antes e durante o processamento, oferecendo uma visão mais objetiva dos problemas encontrados.

A escolha de utilizar métricas também evita que a avaliação da qualidade dependa exclusivamente de inspeções manuais ou de observações isoladas.

Entretanto, a identificação de um valor nulo ou de um registro duplicado não significa necessariamente que o problema possa ser corrigido automaticamente. A detecção é uma etapa diferente da decisão sobre o tratamento adequado.

### 2.6. Persistência dos dados

Após as etapas de extração, transformação, validação e enriquecimento, os dados processados são carregados no PostgreSQL.

A utilização de um banco de dados relacional permite manter as informações persistidas e disponíveis para operações posteriores, evitando que o resultado do processamento dependa exclusivamente de arquivos intermediários.

O processo de carregamento também considera a identificação dos registros, utilizando mecanismos para evitar a inserção repetida de clientes que já estejam registrados na base.

Essa decisão contribui para a integridade dos dados e para a possibilidade de executar novamente determinadas etapas sem necessariamente duplicar os registros já carregados.

Por outro lado, a persistência em banco de dados introduz responsabilidades adicionais, como configuração de conexão, gerenciamento de credenciais, tratamento de falhas e manutenção da estrutura das tabelas.

## 3. Tratamento das divergências

Um dos pontos de maior complexidade do projeto foi definir como tratar as diferenças entre o bairro informado originalmente pelo cliente e aquele retornado pela consulta de CEP.

Diferentemente de campos que possuem formatos bem definidos, como CNPJ e CEP, os nomes de bairros apresentam particularidades geográficas e cadastrais que dificultam a criação de uma regra universal de correção.

Uma diferença textual pode representar apenas uma variação de escrita, mas também pode indicar localidades distintas.

Por esse motivo, foi implementado um mecanismo de resolução baseado em critérios explícitos.

### 3.1. Critérios de resolução

O mecanismo considera a disponibilidade e a compatibilidade dos dois valores após a normalização.

Foram estabelecidas cinco situações:

| Critério | Condição | Comportamento |
|---|---|---|
| Convergente | Os dois bairros coincidem após a normalização. | Utiliza o bairro informado, considerando a compatibilidade entre as fontes. |
| Informado | O bairro da API está ausente ou inválido, mas o informado é válido. | Mantém o bairro informado. |
| API | O bairro informado está ausente ou inválido, mas a API fornece um valor válido. | Utiliza o bairro retornado pela API. |
| Divergente | Os dois bairros são válidos, mas não coincidem após a normalização. | Mantém o bairro informado e classifica a divergência. |
| Sem informação | Nenhuma das fontes fornece um bairro válido. | Retorna ausência de informação. |

A utilização desses critérios evita que o sistema dependa de decisões implícitas ou de substituições automáticas sem justificativa.

### 3.2. Por que não substituir sempre pelo bairro da API?

Uma possibilidade seria considerar o bairro retornado pela API como a informação prioritária em todos os casos.

Entretanto, essa abordagem apresenta um risco: a informação externa pode não representar exatamente a mesma referência utilizada no cadastro original.

O fato de uma API retornar determinado bairro para um CEP não comprova, por si só, que qualquer outra informação de bairro associada ao registro esteja incorreta.

Além disso, diferenças de nomenclatura, subdivisões territoriais e particularidades de identificação podem produzir divergências que não são solucionadas apenas pela comparação textual.

Por isso, foi adotada uma política conservadora: quando as duas fontes apresentam informações válidas, mas incompatíveis após a normalização, o sistema preserva o bairro informado como referência e registra a classificação de divergência.

Essa decisão prioriza a preservação da informação original em vez de produzir uma correção automática cuja confiabilidade não pode ser garantida.

### 3.3. Consequências dessa abordagem

A principal vantagem é reduzir o risco de substituições indevidas e manter explícitas as situações que precisam de avaliação complementar.

Em contrapartida, essa estratégia significa que nem todos os registros terminarão o processamento com um bairro considerado definitivamente correto.

Algumas divergências permanecerão classificadas como tal, mesmo depois da execução de todas as regras automáticas.

Isso não representa necessariamente uma falha do pipeline. É uma consequência consciente da decisão de não transformar uma informação incerta em uma informação aparentemente correta sem evidências suficientes.

## 4. O que não foi totalmente automatizado

Embora grande parte do processamento seja automatizada, existem situações em que as regras determinísticas não conseguem estabelecer uma resposta confiável.

A principal limitação está relacionada à interpretação de informações geográficas.

### 4.1. Ambiguidade entre nomes de bairros

A normalização textual consegue reduzir diferenças de representação, mas não estabelece equivalência geográfica.

Por exemplo, dois nomes podem apresentar diferenças de escrita e ainda representar a mesma localidade. Da mesma forma, nomes semelhantes podem corresponder a bairros distintos.

Sem uma base de correspondência geográfica confiável ou um gabarito que determine o bairro correto para cada registro, não seria adequado estabelecer equivalências apenas por aproximação textual.

### 4.2. Informações incompletas ou inválidas

Quando um CEP não é encontrado ou não apresenta informações suficientes nas APIs consultadas, o sistema não possui uma fonte externa confiável para complementar o registro.

Nessas situações, a aplicação pode preservar o dado original quando disponível, mas não consegue garantir que ele esteja correto.

A ausência de informação também precisa ser diferenciada de uma informação inválida, pois são situações que podem exigir tratamentos diferentes em uma evolução futura do sistema.

### 4.3. Necessidade de avaliação complementar

Alguns registros podem exigir análise adicional para determinar se a divergência representa um erro cadastral, uma variação de nomenclatura ou uma particularidade geográfica.

A automação foi projetada para identificar essas situações e classificá-las, mas não para produzir uma resposta definitiva quando os dados disponíveis não oferecem evidências suficientes.

Essa decisão evita a falsa sensação de qualidade que poderia ser produzida por um sistema que substitui automaticamente todos os valores divergentes.

## 5. Principais trade-offs

Durante o desenvolvimento, diferentes decisões exigiram equilibrar automação, desempenho, confiabilidade, manutenção e preservação das informações.

### 5.1. Automação versus confiabilidade

A utilização de regras determinísticas permite automatizar grande parte do tratamento e garantir que os mesmos dados sejam processados seguindo os mesmos critérios.

Isso facilita a reprodução dos resultados, a realização de testes e a identificação de comportamentos inesperados.

Entretanto, regras determinísticas possuem limites diante de informações ambíguas. Quanto mais agressiva for a tentativa de corrigir automaticamente os dados, maior poderá ser o risco de introduzir alterações incorretas.

**Decisão adotada:** automatizar transformações objetivas e classificar situações ambíguas, evitando correções sem evidências suficientes.

**Consequência:** maior previsibilidade e confiabilidade das decisões, mas manutenção de alguns registros divergentes.

### 5.2. Enriquecimento externo versus dependência de serviços

A utilização das APIs permite complementar os registros com informações que não estão disponíveis diretamente no dataset.

A combinação entre ViaCEP e BrasilAPI amplia as possibilidades de consulta e oferece uma alternativa quando uma das fontes não fornece o resultado esperado.

Entretanto, os serviços externos podem apresentar indisponibilidade, lentidão, respostas incompletas ou diferenças entre suas bases.

**Decisão adotada:** utilizar fontes externas para enriquecimento e comparação, complementadas por cache local.

**Consequência:** maior capacidade de enriquecimento e redução de consultas repetidas, mas dependência da disponibilidade e da qualidade das informações externas.

### 5.3. Desempenho versus atualização das informações

A implementação de cache reduz o número de requisições e melhora o desempenho em consultas repetidas.

Entretanto, reutilizar uma resposta armazenada significa que o sistema pode deixar de consultar uma informação mais recente disponível na API.

**Decisão adotada:** priorizar o reaproveitamento de respostas já consultadas para reduzir operações externas repetidas.

**Consequência:** processamento mais eficiente, com a limitação de que os resultados armazenados podem não refletir atualizações posteriores dos serviços.

### 5.4. Padronização versus preservação dos dados originais

A padronização facilita comparações, agrupamentos, validações e operações posteriores.

Entretanto, uma transformação excessiva pode eliminar características relevantes do dado original ou produzir equivalências incorretas.

Esse problema é especialmente importante no tratamento de bairros, pois a semelhança textual não garante equivalência geográfica.

**Decisão adotada:** aplicar regras específicas de normalização e utilizar critérios separados para resolver divergências.

**Consequência:** maior consistência na representação dos dados, sem assumir que toda diferença deve resultar em substituição automática.

### 5.5. Simplicidade de implementação versus separação de responsabilidades

Uma alternativa seria concentrar as operações de tratamento em uma única rotina.

Entretanto, essa abordagem dificultaria a manutenção, os testes isolados e a identificação de erros específicos.

**Decisão adotada:** separar as responsabilidades em funções e módulos específicos para normalização, validação, resolução, integração e carregamento.

**Consequência:** maior organização e facilidade de manutenção, embora exista um custo adicional de gerenciamento dos diferentes componentes e suas dependências.

### 5.6. Qualidade dos dados versus descarte de registros

Uma estratégia possível para melhorar a aparência da base seria remover todos os registros que apresentam inconsistências.

Entretanto, isso poderia resultar na perda de informações úteis, principalmente quando o problema está restrito a um ou mais campos do cadastro.

**Decisão adotada:** identificar e mensurar problemas de qualidade, sem considerar automaticamente toda inconsistência como motivo para descartar um registro.

**Consequência:** maior preservação dos dados disponíveis, embora parte dos registros continue apresentando campos que exigem atenção.

### 5.7. Reprodutibilidade versus intervenção manual

A utilização de critérios explícitos permite que o processamento seja executado novamente mantendo o mesmo comportamento diante das mesmas entradas e condições.

Por outro lado, algumas situações poderiam ser resolvidas mais rapidamente por uma intervenção manual ou por uma análise individualizada.

**Decisão adotada:** priorizar um fluxo automatizado e reproduzível, mantendo classificações para os casos que não podem ser resolvidos com segurança.

**Consequência:** maior consistência operacional e facilidade de auditoria, mas sem eliminar completamente a necessidade de análise complementar.

## 6. Limitações conhecidas

Apesar das funcionalidades implementadas, o VetorFlow possui limitações relacionadas às características do dataset, às fontes externas e ao alcance das regras de tratamento.

### 6.1. Dependência da qualidade das fontes externas

O enriquecimento depende das informações disponibilizadas pelas APIs ViaCEP e BrasilAPI.

Quando os serviços não encontram determinado CEP ou retornam informações incompletas, a aplicação não possui garantia de que conseguirá complementar o registro.

Além disso, diferenças entre as bases externas podem produzir resultados distintos para uma mesma consulta.

### 6.2. Ausência de um gabarito geográfico

O dataset não disponibiliza uma referência definitiva para determinar o bairro correto de cada cliente.

Consequentemente, não é possível avaliar todas as divergências como erros ou estabelecer automaticamente qual fonte possui razão.

As regras implementadas representam critérios de tratamento definidos para o contexto do projeto, e não uma validação geográfica absoluta.

### 6.3. Limitações da normalização textual

A normalização reduz diferenças de escrita, mas não substitui uma base de conhecimento geográfico.

Novas abreviações, denominações alternativas, nomes históricos e particularidades regionais podem exigir regras adicionais.

Portanto, o conjunto atual de regras não deve ser considerado universal para qualquer base cadastral.

### 6.4. Evolução das regras de tratamento

Como as regras foram desenvolvidas considerando as características do dataset disponibilizado, uma base maior ou com diferentes padrões de inconsistência poderá exigir novas validações, normalizadores e mecanismos de correspondência.

Isso significa que a manutenção e a ampliação das regras fazem parte da evolução natural da solução.

### 6.5. Dependência de infraestrutura

O processamento também depende da configuração correta do ambiente, das variáveis de ambiente, da conexão com o PostgreSQL e da disponibilidade dos serviços utilizados.

Falhas nessas dependências podem interromper determinadas etapas do pipeline, mesmo quando as regras de transformação estão funcionando corretamente.

Por isso, a configuração e o tratamento de erros são aspectos importantes para a execução confiável do projeto.

## 7. Possíveis evoluções

Algumas melhorias poderiam ampliar a capacidade de tratamento do VetorFlow sem comprometer os critérios de confiabilidade adotados.

Entre as possibilidades estão:

 **Dicionário de correspondências geográficas:** criação de uma base controlada de nomes alternativos, abreviações e correspondências conhecidas entre bairros.
 **Mecanismo de revisão de divergências:** disponibilização de uma etapa específica para análise dos registros classificados como divergentes.
 **Expiração de cache:** implementação de políticas de validade para evitar a utilização indefinida de respostas externas antigas.
 **Ampliação dos testes automatizados:** inclusão de novos cenários para casos extremos de normalização, resolução e integração.
 **Monitoramento da qualidade:** acompanhamento histórico das métricas de nulos, duplicidades, divergências e falhas de enriquecimento.
 **Expansão das regras de validação:** inclusão de novas verificações conforme forem identificados outros padrões de inconsistência.

Essas evoluções poderiam aumentar a abrangência do sistema, mantendo a separação entre transformações seguras e decisões que exigem informações complementares.

## 8. Conclusão

O desenvolvimento do VetorFlow demonstrou que o tratamento de dados cadastrais não consiste apenas em remover caracteres, preencher valores ausentes ou padronizar formatos.

Uma parte significativa do desafio está em determinar até que ponto uma transformação automática é confiável e quando uma inconsistência deve ser preservada para análise posterior.

Nesse contexto, o projeto priorizou regras determinísticas para operações objetivas, utilização de fontes externas para enriquecimento, cache para redução de consultas repetidas e critérios explícitos para resolução de divergências.

As decisões adotadas envolveram diferentes compromissos: maior automação em troca da necessidade de manter regras específicas; enriquecimento externo em troca da dependência de serviços; melhor desempenho com cache em troca de possíveis informações desatualizadas; e padronização em equilíbrio com a preservação dos dados originais.

A decisão de não substituir automaticamente informações divergentes representa um dos principais critérios de confiabilidade da solução. Em vez de produzir uma correção sem evidências suficientes, o sistema identifica a inconsistência e mantém explícito o critério utilizado.

Dessa forma, o VetorFlow busca entregar um processo de ETL reproduzível, organizado e rastreável, no qual a automação é utilizada para reduzir inconsistências, mas não para ocultar incertezas.

O principal compromisso do projeto foi equilibrar eficiência operacional e qualidade da informação, reconhecendo que um dado padronizado não é necessariamente um dado correto e que a confiabilidade de um processo de tratamento depende também da capacidade de reconhecer os limites das próprias regras.

VetorFlow
