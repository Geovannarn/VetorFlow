Bom dia a todos. Eu sou a Geovanna e vou apresentar o VetorFlow, o sistema que desenvolvi para o Desafio 1 do Projeto Integrador: tratamento, validação e enriquecimento de dados cadastrais.

Em 15 minutos, vou mostrar o problema, como o sistema funciona, as decisões mais importantes, uma demonstração e o que ainda falta."

2. O problema (1:45)

"O cenário é a Distribuidora Vetor, uma atacadista fictícia que vende para varejistas. Depois de anos de operação, a base de clientes acumulou cadastros preenchidos por pessoas diferentes, sem padronização.

O exemplo mais claro é o bairro. 'Águas Claras', 'Aguas claras' e 'AGUAS CLARAS' são o mesmo lugar, mas, em um relatório por região, viram três linhas separadas. Isso dilui a análise. Existe ainda uma subdivisão informal, como 'Norte (Águas Claras)', que não tem correspondência oficial garantida.

Os outros campos têm o mesmo problema: CNPJ, telefone e data aparecem em formatos diferentes, e há CEPs ausentes, inválidos ou que não combinam com o bairro digitado. A base de teste tem 47 registros com essas inconsistências inseridas de propósito, incluindo um grupo de bairro, o Guará, sem nenhum CEP confiável."

3. Objetivo e ideia central (1:00)

"O objetivo foi construir um pipeline que recebe essa base, identifica as inconsistências e entrega uma base final limpa, guardada em banco de dados, com as decisões documentadas.

Uma ideia guiou o projeto: nem tudo deve ser corrigido automaticamente. Em dados reais, parte do trabalho é decidir o que automatizar e o que deixar para uma pessoa revisar. Eu quis que o sistema fosse claro sobre isso."

4. Arquitetura (2:00)

"O fluxo tem etapas em sequência. O CSV passa primeiro por verificações de qualidade, que medem colunas ausentes, nulos e duplicados.

Depois, cada campo é normalizado: CNPJ, telefone, e-mail, data, texto e CEP, cada um com o seu módulo.

Em seguida vem o enriquecimento por CEP. Consulto o ViaCEP como fonte principal e a BrasilAPI como reserva, e guardo as respostas em um cache local. Isso evita consultas repetidas e faz o sistema continuar funcionando se uma das APIs cair.

Com o endereço, entra a etapa de bairros, que é o coração do desafio. Depois, os dados são gravados no PostgreSQL e ficam disponíveis por uma API REST e por uma interface web.

O código é dividido por responsabilidade em pastas: normalizers, integrations, neighborhood, pipeline, audit, api e frontend. Essa separação permitiu testar cada parte isoladamente."

5. A decisão mais importante: o bairro (2:30)

"Resolvi o bairro em duas etapas.

A primeira é a normalização. Ela tira diferenças de caixa, acento e espaços, usa só o conteúdo dos parênteses e remove o sufixo de UF. Assim, 'Norte (Águas Claras)' vira 'Águas Claras', e as três grafias do início passam a ser o mesmo bairro. Uso uma chave sem acento para comparar e o nome formatado para gravar.

A segunda é a resolução: comparo o bairro digitado com o bairro retornado pelo CEP e classifico o resultado em cinco critérios:

convergente, quando os dois concordam;
informado, quando só o cliente informou;
api, quando só a consulta tem o dado;
divergente, quando os dois discordam;
sem informação, quando nenhum dos dois tem.

A decisão principal foi esta: quando há divergência, mantenho o bairro informado no cadastro e marco o registro como divergente. Eu poderia sempre confiar na API, mas o CEP pode estar errado ou ser genérico, e isso apagaria uma informação que pode estar correta. Também poderia descartar o registro, mas perderia um cliente válido. Marcar como divergente mantém o dado e deixa o caso visível para revisão.

Há também um dicionário pequeno de apelidos, como 'V Pires' para Vicente Pires, que cresce conforme aparecem novas variações."

6. Os outros campos e a qualidade dos dados (1:30)

"Para os demais campos, adotei uma regra simples: dado inválido vira vazio e é contado, em vez de derrubar o cliente. O telefone é padronizado com o prefixo +55, o CNPJ fica só com os 14 dígitos, as datas de vários formatos viram o padrão ISO, e o e-mail é validado.

Só rejeito um registro em três casos: código do cliente vazio, razão social vazia ou código duplicado.

Um detalhe sobre o CNPJ: o sistema calcula o dígito verificador, mas não bloqueia o registro quando ele falha, porque os CNPJs da base são fictícios. O problema aparece em uma métrica separada, sem perder clientes.

Antes de tratar, o pipeline mede a base: total de registros, percentual de nulos e de duplicados. No final, imprime um resumo, o que permite comparar o antes e o depois."

7. Banco de dados e API (1:15)

"Os dados tratados vão para a tabela usuarios no PostgreSQL. A carga é idempotente: se eu rodar o pipeline de novo, ele não duplica clientes.

A API REST, feita com Django REST Framework, tem as quatro operações: GET, POST, PUT e DELETE. Ela usa os mesmos normalizadores do pipeline, então um cadastro manual também entra padronizado.

Aqui há uma diferença de propósito: o pipeline é tolerante, porque em lote um campo ruim não pode parar tudo, e a API é rigorosa, porque quem cadastra pode corrigir na hora. Ela devolve erros claros, como 400 para dado inválido e 409 para código repetido."

8. Demonstração (2:00)

"Agora vou mostrar funcionando."

Roteiro da demonstração (ensaie antes):

Mostre o CSV original e aponte as grafias diferentes do mesmo bairro (15 s).
Rode o pipeline e mostre o resumo final: aceitos, rejeitados, CEPs consultados e a contagem por critério de bairro (45 s).
Abra a interface web ou /api/clientes/ e mostre os dados já tratados (30 s).
Envie um cadastro com telefone e CNPJ "sujos" e mostre o dado devolvido padronizado (30 s).

Fala sugerida ao rodar o pipeline: "Dos 47 registros, [SEU NÚMERO] foram aceitos, [SEU NÚMERO] ficaram convergentes e [SEU NÚMERO] divergentes. Esses divergentes são os que precisam de uma pessoa."

Plano B: se a internet falhar, os CEPs já consultados estão no cache e o pipeline continua. Tenha um print do resumo guardado.

9. Testes e organização do desenvolvimento (0:45)

"Os testes rodam com Pytest, e as chamadas às APIs de CEP são simuladas, então não dependem de internet.

No GitHub, organizei o trabalho em uma branch por funcionalidade: banco de dados, normalizadores, enriquecimento por CEP, normalização e resolução de bairros, auditoria, pipeline e carga, qualidade dos dados e API. Isso deixa o histórico fácil de acompanhar."

10. Limitações e próximos passos (1:00)

"Quero ser transparente sobre o que ainda não está resolvido.

Os registros divergentes exigem revisão manual. Foi uma escolha, mas continua sendo trabalho humano. O dicionário de apelidos é pequeno. A API ainda não tem autenticação, porque foi pensada para uso acadêmico local. E a trilha de auditoria por registro, com valor original, valor tratado e critério, está modelada no banco, mas o pipeline ainda não grava nela. Hoje existe o resumo por critério e o log de auditoria da API.

Os próximos passos são gravar essa trilha, aplicar a resolução de bairros também na API e incluir autenticação."

11. Encerramento (0:30)

"Em resumo, o VetorFlow transforma uma base inconsistente em uma base padronizada, com critérios claros para os casos ambíguos e com a revisão humana reservada para onde ela realmente importa. A documentação completa está na pasta docs do repositório. Obrigada! Fico à disposição para as perguntas."
