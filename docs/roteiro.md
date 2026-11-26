# VETORFLOW
## Apresentação técnica do projeto
### Da inconsistência cadastral à informação estruturada, enriquecida e rastreável

---

# 1. Abertura e apresentação do projeto

Boa noite.

Hoje vou apresentar o **VetorFlow**, um sistema desenvolvido para solucionar um problema bastante comum em ambientes empresariais: a existência de dados cadastrais inconsistentes, incompletos e sem padronização.

O projeto foi desenvolvido a partir de um desafio envolvendo uma distribuidora e sua base de clientes. A proposta não era simplesmente importar um arquivo CSV para um banco de dados, mas construir uma solução capaz de interpretar, tratar, validar, enriquecer e armazenar informações, mantendo a possibilidade de rastrear as transformações realizadas.

O VetorFlow foi desenvolvido em Python, utilizando Pandas para o processamento dos dados, Django e Django REST Framework para a estrutura da aplicação e da API, e PostgreSQL para persistência.

Ao longo do desenvolvimento, a solução foi ampliada para contemplar não apenas o processamento dos dados, mas também uma interface de gerenciamento e mecanismos de auditoria.

**O principal objetivo foi transformar uma base cadastral desorganizada em informações mais consistentes, sem perder o histórico das decisões tomadas durante o processamento.**

# 2. Contextualização do problema

Para compreender a solução, primeiro precisamos entender o problema apresentado.

O conjunto de dados disponibilizado continha 47 registros fictícios de clientes. Entretanto, os dados foram propositalmente construídos com inconsistências que simulam situações encontradas em cadastros reais.

Entre os problemas identificados estavam:

- CNPJs apresentados com diferentes formatações;
- Telefones com e sem máscara, com variações de DDI e DDD;
- Datas registradas em formatos diferentes, inclusive em inglês;
- CEPs ausentes, inválidos ou incompatíveis com o bairro informado;
- Nomes de bairros escritos de maneiras diferentes, embora representassem a mesma localidade;
- Informações cadastrais incompletas, que não poderiam ser corrigidas simplesmente aplicando uma regra de formatação.

Um dos pontos mais relevantes do desafio estava no campo `bairro_informado`.

O mesmo bairro poderia aparecer com abreviações, erros de digitação, diferenças de acentuação, variações de caixa e subdivisões utilizadas pelos Correios.

Além disso, existiam situações em que o bairro informado pelo usuário não correspondia à localidade retornada pela consulta do CEP.

Isso criou um problema importante: **qual informação deveria prevalecer quando duas fontes apresentavam resultados diferentes?**

Não seria adequado substituir automaticamente o dado informado pelo cliente apenas porque uma API retornou outro bairro. Da mesma forma, também não seria adequado ignorar uma divergência que poderia representar um erro cadastral.

Foi a partir dessa dificuldade que surgiu uma das principais decisões técnicas do VetorFlow: tratar a resolução de bairros como uma etapa própria do processamento, com critérios explícitos e resultados rastreáveis.

# 3. Visão geral da solução

O VetorFlow foi estruturado para conduzir os dados por um fluxo de processamento organizado.

De maneira geral, o funcionamento pode ser dividido nas seguintes etapas:

1. Recebimento e leitura do arquivo CSV.
2. Análise inicial da qualidade dos dados.
3. Normalização dos campos cadastrais.
4. Validação e identificação de inconsistências.
5. Enriquecimento de informações por meio de APIs externas.
6. Resolução de divergências entre o bairro informado e o bairro retornado pela consulta.
7. Persistência dos dados tratados no PostgreSQL.
8. Disponibilização das informações por meio de uma API REST e da interface web.
9. Registro das transformações e decisões realizadas.

Cada etapa possui uma responsabilidade específica.

Essa separação evita concentrar todo o processamento em um único arquivo ou em uma única função, facilitando a manutenção, a identificação de falhas e a evolução do sistema.

**O VetorFlow não foi pensado como um script isolado de limpeza de dados, mas como uma aplicação organizada em componentes com responsabilidades distintas.**

# 4. Processamento e qualidade dos dados

A primeira etapa do processamento consiste em receber o arquivo CSV e realizar sua leitura.

A partir daí, o sistema identifica problemas estruturais e inconsistências presentes na base.

O Pandas é utilizado para manipulação dos dados, permitindo analisar colunas, identificar valores ausentes, verificar duplicidades e executar transformações de maneira estruturada.

Uma preocupação importante foi não confundir padronização com validação.

Por exemplo, um CNPJ pode estar escrito com pontuação, espaços ou sem máscara. A normalização remove essas diferenças de apresentação.

Entretanto, isso não significa que o documento seja matematicamente válido.

Por essa razão, o VetorFlow diferencia a formatação do valor da sua validade. Um CNPJ que não atende aos critérios de validação não deve ser apresentado como válido apenas porque foi padronizado.

O mesmo raciocínio se aplica aos demais campos.

No caso dos CEPs, valores ausentes, inválidos ou representados por zeros não devem ser tratados como endereços confiáveis.

Para as datas, o sistema precisa lidar com formatos diferentes e convertê-los para uma representação consistente.

O objetivo dessa etapa é reduzir a heterogeneidade da base sem mascarar problemas que ainda precisam de análise.

**Uma informação padronizada não é necessariamente uma informação válida. Essa distinção orientou o tratamento dos dados no projeto.**

# 5. O principal diferencial: resolução inteligente de bairros

Esta é uma das partes mais importantes do VetorFlow.

O desafio apresentava diferentes grafias para os mesmos bairros do Distrito Federal.

Durante a análise da base, foram identificadas 25 variações de escrita relacionadas a quatro bairros: Águas Claras, Taguatinga, Vicente Pires e Guará.

Uma solução simples poderia utilizar substituições de texto ou comparações diretas. Entretanto, esse tipo de abordagem não seria suficiente para resolver todos os casos.

O problema não estava apenas na escrita. Também existiam divergências entre o endereço informado no cadastro e o endereço retornado pela consulta do CEP.

Por isso, o VetorFlow possui uma etapa específica para normalização e resolução de bairros.

Primeiro, são aplicadas regras de limpeza textual, como:

- Padronização de caixa;
- Tratamento de acentuação;
- Remoção de espaços desnecessários;
- Tratamento de abreviações;
- Reconhecimento de aliases conhecidos;
- Tratamento de variações de nomenclatura.

Depois dessa etapa, o sistema utiliza critérios de comparação e resolução para analisar a relação entre o bairro informado e o bairro obtido por meio do enriquecimento.

O resultado não é simplesmente um texto substituído. O sistema classifica a situação encontrada.

Foram estabelecidas cinco possibilidades:

**Convergente:** quando as informações apresentam compatibilidade.

**Informado:** quando o bairro informado é preservado como referência da decisão.

**API:** quando a informação retornada pela consulta externa é utilizada como referência.

**Divergente:** quando existe conflito entre as informações e a divergência precisa ser preservada.

**Sem informação:** quando não existem elementos suficientes para determinar o bairro.

Essa classificação é importante porque evita que o sistema tome decisões silenciosas.

Imagine que o cliente informou um bairro, mas o CEP consultado retorna outro. Substituir automaticamente o bairro original poderia introduzir um erro diferente daquele que já existia.

O VetorFlow procura preservar o contexto da informação e registrar o critério utilizado para chegar ao resultado.

Outro cuidado foi evitar correspondências excessivamente genéricas. Uma palavra como “Norte” ou “Sul”, por exemplo, não deve ser suficiente, isoladamente, para determinar um bairro.

Também foram considerados aliases conhecidos, como abreviações de Vicente Pires.

Essa lógica foi organizada em módulos próprios, separando a normalização textual da resolução das informações.

**O diferencial não está apenas em reconhecer que dois textos são diferentes. Está em avaliar se eles representam a mesma localidade e decidir o que fazer quando as fontes entram em conflito.**

# 6. Integração com serviços externos: ViaCEP e BrasilAPI

Outra etapa importante é o enriquecimento dos dados cadastrais.

Para isso, o VetorFlow utiliza duas fontes externas: ViaCEP e BrasilAPI.

O ViaCEP é utilizado como serviço principal. Quando necessário, o sistema possui uma alternativa de consulta por meio da BrasilAPI.

Essa estratégia reduz a dependência de uma única fonte externa.

Entretanto, integrar uma API não significa apenas enviar uma requisição e receber um JSON.

É necessário considerar situações como:

- CEP inválido;
- Resposta sem informações;
- Indisponibilidade do serviço;
- Erros de comunicação;
- Tempo limite de resposta;
- Falhas durante a interpretação do retorno.

O sistema diferencia essas situações para evitar que uma falha temporária de comunicação seja confundida com um CEP inexistente.

Também foi implementado um mecanismo de cache local em JSON.

A finalidade do cache é evitar consultas desnecessárias para CEPs que já foram processados anteriormente, reduzindo o volume de requisições externas e melhorando a eficiência do processamento.

Outro cuidado está na gravação do cache: os arquivos são atualizados de maneira atômica, reduzindo o risco de deixar um arquivo parcialmente gravado em caso de interrupção.

Além disso, respostas vazias não devem ser armazenadas como se fossem resultados válidos.

Essa integração foi pensada considerando não apenas o cenário ideal, mas também as falhas que podem ocorrer quando uma aplicação depende de serviços externos.

# 7. Auditoria e rastreabilidade das transformações

Uma das decisões mais importantes do projeto foi a implementação de uma trilha de auditoria.

Em processos de ETL, é comum que os dados sejam transformados sem que exista uma explicação clara sobre o que aconteceu com cada informação.

Isso cria uma dificuldade: quando um valor chega diferente ao banco de dados, como identificar sua origem e entender por que foi alterado?

O VetorFlow procura responder a essa pergunta.

Durante o processamento, são registrados eventos relacionados às transformações, validações, decisões, enriquecimentos e rejeições.

A auditoria contempla informações como:

- Identificação do registro;
- Campo submetido ao processamento;
- Valor original;
- Valor resultante;
- Critério aplicado;
- Origem da informação;
- Tipo de transformação realizada.

A ideia é permitir que o processamento seja compreendido posteriormente, e não apenas que seu resultado final seja consultado.

O projeto também separa a trilha de transformações dos registros de operação e execução da aplicação.

Isso é importante porque uma transformação de dado e um evento operacional representam acontecimentos diferentes.

Por exemplo, alterar a grafia de um bairro é uma transformação. Já registrar uma falha durante uma operação da aplicação é um evento operacional.

Essa separação contribui para a organização dos registros e facilita a investigação de problemas.

A auditoria também evita gerar registros desnecessários quando não existe alteração relevante.

**O VetorFlow não registra somente o resultado. Ele busca registrar o caminho que levou até esse resultado.**

# 8. Banco de dados e persistência

Depois do processamento, os dados precisam ser armazenados de forma estruturada.

Para isso, foi utilizado o PostgreSQL.

A conexão com o banco foi organizada em um módulo específico, com utilização de variáveis de ambiente para configuração das credenciais e dos parâmetros de conexão.

Essa abordagem evita deixar informações sensíveis diretamente no código-fonte.

Outro ponto considerado foi a integridade dos dados durante a persistência.

O sistema utiliza operações transacionais para que alterações relacionadas sejam confirmadas de maneira consistente. Quando ocorre uma falha, a operação pode ser revertida, evitando deixar o banco em um estado parcialmente atualizado.

Também foi considerada a identificação dos clientes por meio do campo `id_cliente`, evitando inserir novamente registros que já possuem identificação correspondente.

Uma decisão relevante foi evitar que uma nova carga substitua indiscriminadamente informações já preenchidas por valores vazios.

Isso é importante porque uma carga posterior pode conter menos informações do que uma carga anterior.

Portanto, o processo de persistência precisa considerar não apenas a existência de um registro, mas também a qualidade dos valores que serão utilizados na atualização.

O banco de dados não é apenas o destino do ETL. Ele faz parte da estratégia de consistência e integridade da aplicação.

# 9. API REST e operações CRUD

Além do processamento dos arquivos, o VetorFlow disponibiliza uma API REST desenvolvida com Django REST Framework.

A API permite trabalhar com os registros de clientes por meio das operações fundamentais de um CRUD:

- **GET:** consultar registros;
- **POST:** cadastrar registros;
- **PUT:** atualizar registros;
- **DELETE:** excluir registros.

A utilização de uma API permite que outros sistemas consumam as informações sem depender diretamente da interface web.

Isso também estabelece uma separação entre a camada responsável pela disponibilização dos dados e a camada de apresentação.

A API foi organizada para trabalhar com os registros persistidos no banco de dados, permitindo que as operações sejam realizadas de maneira estruturada.

Durante a demonstração, será possível visualizar as rotas e executar operações para verificar o comportamento da aplicação.

# 10. Interface web

O projeto também possui uma interface web, desenvolvida para facilitar a visualização e o gerenciamento das informações.

A proposta foi oferecer uma maneira mais acessível de interagir com o sistema, sem exigir que o usuário realize todas as operações diretamente pelo terminal ou por ferramentas de requisição HTTP.

A interface complementa a API, permitindo apresentar as funcionalidades de gerenciamento de clientes de maneira visual.

É importante destacar que a interface não substitui o processamento do back-end. Ela funciona como uma camada de interação com as funcionalidades disponibilizadas pela aplicação.

Dessa maneira, o usuário consegue acessar as informações por uma apresentação visual, enquanto as regras de processamento e persistência permanecem concentradas no back-end.

# 11. Organização da arquitetura e qualidade do código

Durante o desenvolvimento, houve uma preocupação em evitar que todas as responsabilidades ficassem concentradas em um único módulo.

O projeto foi organizado em componentes específicos para processamento, normalização, resolução de bairros, integração externa, persistência, auditoria e disponibilização das funcionalidades.

Essa organização permite que cada parte do sistema tenha uma finalidade mais clara.

Por exemplo, a lógica de resolução de bairros não precisa estar misturada ao código responsável por consultar uma API externa.

Da mesma forma, a conexão com o banco de dados não precisa estar repetida em diferentes partes da aplicação.

A modularização facilita a manutenção, permite corrigir problemas de maneira localizada e torna o projeto mais preparado para receber novas funcionalidades.

Também foram utilizados arquivos de configuração e variáveis de ambiente para separar parâmetros de execução do código-fonte.

O versionamento foi realizado com Git e GitHub, mantendo o histórico das alterações e a organização do desenvolvimento.

O projeto também contempla testes automatizados, importantes para verificar comportamentos e reduzir o risco de regressões durante alterações no código.

# 12. Demonstração prática do VetorFlow

Agora, vou demonstrar o funcionamento do sistema.

A ideia é apresentar o fluxo de maneira progressiva, começando pelo problema que motivou o desenvolvimento e chegando ao resultado disponibilizado pela aplicação.

**Primeira etapa — apresentação da base original**

Vou apresentar o arquivo CSV utilizado no desafio.

Aqui é possível observar que os registros não estão completamente padronizados. Existem diferentes formatos de CNPJ, telefone e data, além de problemas relacionados aos CEPs e aos bairros.

Esse é o cenário inicial que o VetorFlow precisa tratar.

**Segunda etapa — processamento e tratamento**

Em seguida, vou demonstrar a execução do processamento.

Nesta etapa, o sistema realiza a leitura dos dados, identifica inconsistências e aplica as regras de normalização.

O objetivo é mostrar que o tratamento não acontece por uma substituição indiscriminada de valores, mas por regras específicas para cada campo.

**Terceira etapa — resolução de bairros**

Aqui vou demonstrar um dos principais diferenciais do projeto.

Vou apresentar exemplos de grafias diferentes que representam o mesmo bairro e situações em que existe divergência entre o bairro informado e o retornado pelo CEP.

O ponto principal é demonstrar que o sistema classifica o resultado da resolução e não simplesmente substitui uma informação pela outra.

**Quarta etapa — enriquecimento por CEP**

Vou demonstrar a integração com os serviços externos, explicando a utilização do ViaCEP como fonte principal e da BrasilAPI como alternativa.

Também será possível apresentar o mecanismo de cache e explicar sua finalidade.

**Quinta etapa — auditoria**

Nesta etapa, vou apresentar os registros de auditoria.

O objetivo é mostrar que as transformações podem ser acompanhadas e que existe informação sobre o valor original, o resultado, o critério aplicado e a origem da informação.

Essa etapa demonstra que o sistema não trabalha como uma caixa-preta.

**Sexta etapa — banco de dados e aplicação**

Por fim, vou apresentar os registros persistidos no PostgreSQL, a interface web e as operações disponibilizadas pela API REST.

A intenção é demonstrar o resultado do fluxo completo: os dados deixam de ser apenas um arquivo de entrada e passam a integrar uma aplicação com processamento, persistência e consulta.

# 13. Considerações finais

O desenvolvimento do VetorFlow partiu de um problema específico, mas exigiu decisões que vão além da simples limpeza de uma base de dados.

Foi necessário estabelecer critérios para tratar informações inconsistentes, lidar com fontes externas, resolver divergências, preservar dados existentes e registrar as transformações realizadas.

O projeto também foi ampliado para disponibilizar os dados por meio de uma API REST e de uma interface web.

Entre os principais diferenciais, destaco:

1. **Resolução contextual de bairros:** tratamento de variações textuais e conflitos entre fontes de informação.
2. **Auditoria das transformações:** registro dos valores originais, resultados e critérios aplicados.
3. **Enriquecimento com redundância de fontes:** integração com ViaCEP e BrasilAPI, além de cache local.
4. **Preservação da integridade dos dados:** cuidados na validação, atualização e persistência.
5. **Aplicação completa:** integração entre processamento, banco de dados, API REST e interface web.

O resultado é uma solução que procura tornar o tratamento cadastral mais organizado, transparente e confiável.

**A principal contribuição do VetorFlow é demonstrar que qualidade de dados não significa apenas corrigir valores: significa compreender as inconsistências, estabelecer critérios, preservar informações relevantes e permitir que cada decisão possa ser explicada.**

Obrigada.

---

# 14. Perguntas técnicas que podem surgir

## Por que utilizar Pandas?

O Pandas oferece recursos para leitura, análise, transformação e validação de dados tabulares. Como o desafio parte de um arquivo CSV, ele é adequado para estruturar o processamento e executar as operações necessárias no conjunto de dados.

## Por que utilizar Django e Django REST Framework?

O Django fornece a estrutura principal da aplicação, enquanto o Django REST Framework facilita a construção de endpoints e a disponibilização dos dados por meio de uma API REST.

## Por que utilizar PostgreSQL?

O PostgreSQL foi escolhido como banco de dados relacional para armazenar os registros tratados, oferecendo recursos de integridade, transações e persistência estruturada.

## Por que não substituir automaticamente o bairro informado pelo bairro retornado pela API?

Porque as fontes podem apresentar divergências. O CEP pode estar incorreto, desatualizado ou associado a uma localidade diferente da informação fornecida pelo cliente. Uma substituição automática poderia introduzir um erro. Por isso, o sistema utiliza critérios de resolução e registra a decisão.

## Qual é a diferença entre normalização e validação?

Normalização é a padronização da representação de um valor. Validação é a verificação de que ele atende a determinadas regras. Um CNPJ pode estar corretamente formatado e ainda assim ser inválido.

## Qual é a finalidade do cache?

Reduzir consultas repetidas às APIs externas, reaproveitando resultados já obtidos e diminuindo a dependência de novas requisições.

## O que acontece se o ViaCEP estiver indisponível?

O sistema possui uma alternativa de consulta pela BrasilAPI. Além disso, o tratamento das falhas diferencia problemas de comunicação de respostas que indicam ausência ou invalidade de informação.

## Por que implementar auditoria?

Para permitir compreender as transformações realizadas. Sem auditoria, seria possível visualizar o valor final, mas não necessariamente identificar o que foi alterado, qual critério foi utilizado ou de onde veio a informação.

## Qual é o maior diferencial do VetorFlow?

A combinação entre resolução contextual de bairros, enriquecimento de dados e rastreabilidade das transformações. O sistema não se limita a limpar os dados: ele procura explicar as decisões tomadas durante o processamento.

## O que poderia ser melhorado em uma próxima versão?

Uma evolução possível seria ampliar a cobertura dos testes, implementar mecanismos adicionais de monitoramento, aprimorar os indicadores de qualidade e expandir as possibilidades de integração com outros sistemas. Essas melhorias poderiam ser incorporadas sem alterar o princípio central de processamento rastreável.

---

# 15. Orientação para a demonstração

A apresentação deve seguir uma sequência que permita ao avaliador enxergar o problema, compreender a solução e verificar seu funcionamento.

| Ordem | O que apresentar | O que demonstrar |
|---|---|---|
| 1 | Arquivo CSV original | Inconsistências da base |
| 2 | Processamento ETL | Leitura e tratamento |
| 3 | Resolução de bairros | Critérios e classificação |
| 4 | Integração de CEP | ViaCEP, BrasilAPI e cache |
| 5 | Auditoria | Histórico das transformações |
| 6 | PostgreSQL | Persistência dos registros |
| 7 | Interface web | Gerenciamento dos clientes |
| 8 | API REST | GET, POST, PUT e DELETE |


# 16. Encerramento da apresentação

> "O VetorFlow nasceu de um problema de inconsistência cadastral, mas sua construção exigiu pensar em algo maior: como garantir que uma transformação de dados seja não apenas executada, mas também justificada, rastreada e compreendida. Esse foi o princípio que orientou o desenvolvimento do projeto."
