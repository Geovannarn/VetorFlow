## Relatório Trade-offs VetorFlow


O VetorFlow foi desenvolvido como uma solução de ETL para tratamento, validação, enriquecimento e armazenamento dos dados cadastrais de clientes da Distribuidora Vetor. O dataset disponibilizado possui inconsistências propositalmente inseridas, como diferentes formatos de CNPJ, telefone e datas, além de CEPs ausentes, inválidos ou incompatíveis com o bairro informado.

Durante o desenvolvimento, foram adotadas regras determinísticas para automatizar o tratamento dos dados sempre que possível, mantendo critérios explícitos para situações em que as informações apresentavam divergências.

## 2. O que foi automatizado

A maior parte do tratamento foi automatizada por meio de funções específicas de normalização e validação.

Foram desenvolvidos normalizadores para campos como CNPJ, telefone, e-mail, texto e CEP, permitindo transformar diferentes formatos de entrada em uma representação padronizada.

Também foi implementada a normalização dos bairros. Como o dataset apresenta diferentes grafias para uma mesma localidade, foi utilizado um processo de normalização textual e um mecanismo de resolução para comparar o bairro informado com o bairro obtido por meio das consultas de CEP.

O enriquecimento dos dados foi realizado utilizando as APIs ViaCEP e BrasilAPI. Os resultados das consultas são armazenados em cache local, evitando consultas externas repetidas para o mesmo CEP.

O pipeline também possui verificações de qualidade dos dados, incluindo identificação de colunas ausentes, valores nulos, registros duplicados e verificação da existência de registros. A partir dessas verificações são calculadas métricas, como quantidade e percentual de nulos e duplicados.

O carregamento dos dados tratados é realizado no PostgreSQL, permitindo que a base processada seja persistida para utilização posterior.

## 3. Tratamento das Divergências

Um dos principais pontos de decisão do projeto foi o tratamento das diferenças entre o bairro informado no cadastro e o bairro retornado pela API.

Foram definidos critérios para situações convergentes, quando as informações coincidem após a normalização; situações em que somente o bairro informado está disponível; situações em que somente a informação da API está disponível; e situações divergentes, quando as duas informações existem, mas não correspondem.

Nesses casos, a aplicação não tenta assumir automaticamente que uma das informações está sempre correta. O critério utilizado é registrado para permitir que a decisão tomada seja compreendida posteriormente.

Essa abordagem busca evitar que uma informação externa seja utilizada de forma indiscriminada para substituir o dado original.

## 4. O que não foi totalmente automatizado

Embora o sistema automatize grande parte do processo, algumas situações não podem ser resolvidas apenas por regras determinísticas.

Um exemplo são os casos em que o bairro informado e o bairro retornado pela API apresentam divergência. A existência de uma divergência não significa necessariamente que o dado informado pelo cliente esteja incorreto, pois o dataset contém situações em que subdivisões, abreviações e diferentes formas de identificação podem representar contextos semelhantes.

Por esse motivo, o sistema identifica e classifica a divergência em vez de tentar corrigir todos os casos automaticamente.

Essa decisão reduz o risco de substituir um dado válido por uma informação incorreta simplesmente para obter uma padronização automática.

## 5. Principais trade-offs

Uma das principais escolhas do projeto foi priorizar regras determinísticas em vez de utilizar uma abordagem mais agressiva de correção automática. Isso torna o processo mais previsível e fácil de explicar, mas faz com que alguns registros permaneçam classificados como divergentes.

Outro trade-off está relacionado ao uso das APIs externas. ViaCEP e BrasilAPI permitem enriquecer os dados com informações de endereço, mas dependem de serviços externos. Para reduzir esse impacto, foi implementado um cache local, diminuindo a necessidade de realizar consultas repetidas.

Também foi necessário equilibrar padronização e preservação dos dados originais. A normalização facilita análises e agrupamentos, mas uma transformação excessiva poderia eliminar informações importantes presentes no cadastro original. Por isso, o projeto utiliza critérios definidos para decidir quando uma informação pode ser normalizada ou enriquecida.

## 6. Limitações conhecidas

A solução depende da disponibilidade e da qualidade das informações fornecidas pelas APIs externas. Caso um CEP não seja encontrado ou não possua informações suficientes, o sistema não consegue utilizar essa fonte para resolver o bairro.

Além disso, o dataset possui situações ambíguas que não podem ser solucionadas com segurança apenas por comparação textual. O próprio desafio não fornece um gabarito de bairro correto para cada registro, deixando a definição dos critérios de canonicalização sob responsabilidade da equipe.

Outra limitação é que as regras adotadas foram desenvolvidas especificamente para o contexto e as características do dataset disponibilizado. Uma base realista e  maior poderia apresentar novas variações que exigiriam a ampliação do dicionário de correspondências e das regras de tratamento.

## 7. Conclusão

O VetorFlow priorizou um processo de tratamento automatizado, rastreável e baseado em critérios explícitos. As etapas de normalização, validação, enriquecimento, cache, cálculo de métricas e carregamento no banco reduzem a necessidade de tratamento manual e tornam o processo reproduzível.

Ao mesmo tempo, situações ambíguas não foram forçadas a uma correção automática. A decisão de identificar e classificar divergências busca preservar a confiabilidade dos dados e tornar possível compreender o motivo de cada tratamento.

Dessa forma, o projeto procura equilibrar automação, qualidade dos dados e rastreabilidade, reconhecendo que nem toda inconsistência pode ser resolvida de maneira segura apenas por regras automáticas.