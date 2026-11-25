VetorFlow
Do dado inconsistente ao dado confiável: tratamento, enriquecimento e rastreabilidade de cadastros.

Pipeline de ETL, API REST e interface web para a base de clientes da Distribuidora Vetor.






</div>Sumário
1. Visão geral
2. Diferenciais
3. O que foi solicitado e o que foi entregue
4. Arquitetura do fluxo
5. Tratamento dos dados
6. Resolução de bairros
7. Enriquecimento por CEP
8. Qualidade dos dados
9. Auditoria e rastreabilidade
10. Banco de dados
11. API REST
12. Estrutura do projeto
13. Configuração do ambiente
14. Execução do sistema
15. Testes automatizados
16. Documentação complementar
17. Roadmap
Visão geral
A Distribuidora Vetor acumulou anos de cadastros preenchidos por pessoas diferentes, sem um padrão único. O resultado são bairros registrados com grafias distintas, telefones e CNPJs em formatos variados, datas inconsistentes e CEPs ausentes ou incompatíveis com o endereço. Essas inconsistências comprometem consultas, relatórios e a confiabilidade da base.

O VetorFlow foi desenvolvido para enfrentar esse cenário. A aplicação recebe os dados em CSV, verifica a qualidade da entrada, normaliza os campos, consulta serviços externos para enriquecer endereços, resolve divergências entre o bairro informado e o retornado pela API e persiste os resultados em PostgreSQL.

O processamento é acompanhado por uma trilha de auditoria, enquanto os dados tratados podem ser consultados e administrados por uma API REST e uma interface web.

O projeto responde ao Desafio Técnico 1 — ETL, Limpeza e Enriquecimento de Dados, do Projeto Integrador do Bolsa Futuro Digital, em parceria com a Empresa Primora. O cenário e os dados utilizados são fictícios e acadêmicos.
O problema na base de entrada
Análise dos 47 registros fornecidos no desafio:
Inconsistência identificada	Ocorrência
Grafias de bairro	25 grafias para 4 bairros reais: Águas Claras, Taguatinga, Vicente Pires e Guará
CEP ausente	13 registros
CEP zerado (00000-000)	3 registros
CNPJ com dígitos verificadores válidos	0 de 47 — base fictícia
Formatos de data	ISO, dd/mm/aaaa, dd-mm-aaaa e texto em inglês (Dec 24, 2023)


Diferenciais
O desafio propôs a construção de um processo de ETL com limpeza, enriquecimento, persistência, auditoria, testes e documentação. O VetorFlow contempla esse fluxo e amplia a solução com recursos que transformam o processamento em uma aplicação utilizável.
1. De um script de ETL para uma aplicação completa
O VetorFlow não termina quando o CSV é processado. O projeto também disponibiliza uma API REST com operações CRUD, construída com Django REST Framework, e uma interface web para interação com os dados.

Com isso, os registros podem ser consultados, cadastrados, atualizados e excluídos pela aplicação, sem exigir acesso direto ao banco de dados.
2. Rastreabilidade das transformações e decisões
A auditoria registra o caminho entre o valor original e o valor tratado, incluindo o critério utilizado e a fonte da informação.

A trilha contempla transformações de campos cadastrais, validações, substituições por dicionário, decisões entre fontes, enriquecimentos e rejeições. Também evita gerar ruído: valores que já estão corretos não precisam produzir eventos de alteração.

Os eventos são armazenados em JSON Lines (.jsonl), formato legível por pessoas e processável por ferramentas. O projeto também mantém um registro separado para operações e acessos à aplicação.
3. Resolução explícita de conflitos entre bairros
A escolha do bairro não depende apenas de uma comparação textual simples. O VetorFlow classifica o resultado da resolução em cinco situações: convergente, informado, api, divergente e sem informação.

As regras evitam falsos positivos. Termos genéricos como “Norte” ou “Sul”, isoladamente, não são considerados correspondências suficientes. Quando há divergência real entre o cadastro e a API, o sistema preserva o bairro informado e registra o motivo da decisão.
4. Preservação de dados e rejeições justificadas
Um dado inválido não é necessariamente um dado que deve ser apagado.
- CNPJ inválido: o valor é mantido e sinalizado, em vez de excluir o cliente da base.
- CEP zerado: é tratado como ausente, evitando consultas desnecessárias.
- Registro rejeitado: permanece identificado em uma saída própria, acompanhado do motivo da rejeição.
Essa abordagem preserva o conteúdo de origem e torna as decisões do processamento verificáveis.
5. Integração resiliente com serviços de CEP
O enriquecimento de endereço utiliza dois provedores: ViaCEP como fonte principal e BrasilAPI como alternativa quando a primeira fonte falha ou não encontra o CEP.

O mecanismo inclui cache local, gravação atômica, timeout e tratamento de diferentes respostas. CEP inexistente é distinguido de indisponibilidade do serviço, e respostas vazias não são armazenadas no cache.
6. Carga repetível e protegida por transação
A persistência utiliza PostgreSQL, transações e operação de upsert com ON CONFLICT, usando id_cliente como chave de conflito.

Assim, reprocessar a mesma base não deve gerar clientes duplicados. Além disso, um valor novo vazio não deve apagar um dado que já estava preenchido. Em caso de falha durante a transação, a carga pode ser revertida com rollback.
7. Qualidade dos dados mensurada
O projeto possui verificações para identificar colunas obrigatórias ausentes, valores nulos, células preenchidas apenas com espaços, duplicidades e registros completamente vazios.

As verificações geram métricas e percentuais, permitindo avaliar a qualidade da base antes e durante o processamento, em vez de presumir que os dados de entrada estão corretos.
8. Organização e manutenção do código
O código é separado por responsabilidade: normalização, integrações, resolução de bairros, auditoria, persistência, API, interface e testes. O projeto também utiliza variáveis de ambiente, configuração centralizada de logs, exceções próprias, Makefile e histórico de desenvolvimento organizado em branches por funcionalidade.
O que foi solicitado e o que foi entregue
Entregável do desafio	Implementação no VetorFlow	Ampliação da solução
Pipeline de ETL em Python	pipeline/, normalizers/, integrations/ e neighborhood/	Resumo do processamento e tratamento separado de rejeições
Limpeza e padronização dos dados	Normalizadores por campo	Regras específicas para preservar e sinalizar valores inválidos
Enriquecimento dos endereços	ViaCEP e BrasilAPI	Fallback automático e cache local
Persistência em banco SQL	PostgreSQL	Upsert e controle transacional
Auditoria das transformações	audit_transformacoes.jsonl	Registro de decisões, enriquecimentos e rejeições
Testes automatizados	Pytest	Testes organizados por componente
Documentação técnica	docs/ e relatório de trade-offs	Registro de regras, limites e decisões
Não solicitado como entrega central	API REST com CRUD	Interface para operações sobre os dados
Não solicitado como entrega central	Interface web	Acesso aos recursos sem manipulação direta do banco
Não solicitado como entrega central	Módulo de qualidade	Métricas para avaliar a base de entrada


Arquitetura do fluxo
                    ┌─────────────────┐
                    │       CSV       │
                    └────────┬────────┘
                             ▼
                    ┌─────────────────┐
                    │   Qualidade da  │
                    │     entrada     │
                    └────────┬────────┘
                             ▼
                    ┌─────────────────┐
                    │  Normalização   │
                    │   dos campos    │
                    └────────┬────────┘
                             ▼
                    ┌─────────────────┐
                    │ Enriquecimento  │
                    │ por CEP (cache) │
                    └────────┬────────┘
                             ▼
                    ┌─────────────────┐
                    │    Bairros      │
                    │ Normalização e  │
                    │    resolução    │
                    └────────┬────────┘
                             ▼
                    ┌─────────────────┐       ┌─────────────────┐
                    │   PostgreSQL    │       │    Auditoria    │
                    │  (upsert/tx)    │       │ (etapas do fluxo)│
                    └────────┬────────┘       └─────────────────┘
                             ▼
                    ┌─────────────────┐
                    │    API REST     │
                    └────────┬────────┘
                             ▼
                    ┌─────────────────┐
                    │    Frontend     │
                    └─────────────────┘
A auditoria acompanha as etapas de tratamento e as decisões tomadas durante o processamento.
Tratamento dos dados
Cada campo possui regras próprias de normalização, organizadas no diretório normalizers/.
Campo	Regra aplicada
CNPJ	Remove máscara e espaços; exige 14 dígitos. Valida os dígitos verificadores, mas mantém e sinaliza valores inválidos
Telefone	Remove máscara e DDI 55; aceita 10 ou 11 dígitos; padroniza com +55
E-mail	Remove espaços, converte para minúsculas e valida o formato
CEP	Aceita com ou sem hífen; padroniza em 8 dígitos; CEP zerado é tratado como ausente
Data	Converte para AAAA-MM-DD a partir dos formatos previstos nas regras do projeto
Texto	Colapsa espaços repetidos e remove acentos na chave de comparação
Cidade/UF	Padroniza a escrita e permite preenchimento pela consulta de CEP quando ausentes


Datas ambíguas: o formato dd-mm-aaaa é interpretado com o dia primeiro. A própria base sustenta essa escolha, pois contém datas como 15-08-2024 e 25-01-2022, que só fazem sentido nessa interpretação.
Resolução de bairros
O bairro é um dos campos centrais do desafio. A resolução, implementada em neighborhood/, acontece em duas etapas.
1. Normalização do texto
- Remove sufixos de UF, como Taguatinga - DF e Águas Claras/DF.
- Utiliza o conteúdo entre parênteses quando aplicável: Sul (Águas Claras) → Águas Claras.
- Remove pontuação e espaços repetidos.
- Gera uma chave de comparação sem acentos e em letras minúsculas.
- Substitui apelidos pelo nome oficial por meio de um dicionário: Vte Pires e V. Pires → Vicente Pires.
- Formata o resultado para exibição, mantendo numerais romanos em caixa alta, como Guará II.
2. Resolução entre bairro informado e bairro da API
Resultado	Quando ocorre
convergente	As chaves são idênticas ou uma denominação contém a outra em uma correspondência válida; prevalece o nome mais completo
informado	A API não trouxe um bairro utilizável; mantém-se o valor informado
api	O bairro informado está ausente ou inválido; utiliza-se o bairro retornado pela API
divergente	Os valores são diferentes e não há correspondência; mantém-se o informado
sem informação	Nenhuma das fontes fornece um valor utilizável


Critério de conflito: diante de divergência real, o bairro informado prevalece. Isso evita substituir silenciosamente um dado cadastral por uma informação externa. A divergência é contabilizada e registrada na auditoria.

Os limites e as justificativas dessa escolha estão descritos em [`Relatório_tradeoffs.md`](Relatório_tradeoffs.md).
Enriquecimento por CEP
Componente	Comportamento
ViaCEP	Fonte principal. Respostas de CEP inexistente são tratadas como resultado sem endereço
BrasilAPI	Alternativa automática quando o ViaCEP falha ou não encontra o CEP
Cache local	Evita consultas repetidas; utiliza gravação atômica e não guarda resultados vazios
Tratamento de falhas	Diferencia CEP inexistente de indisponibilidade, timeout e respostas de erro dos serviços


Quando cidade ou UF estão ausentes no cadastro, os dados retornados pela consulta podem preencher esses campos. Cada preenchimento é registrado na auditoria com a respectiva fonte.
Qualidade dos dados
Os módulos de verificação e métricas em pipeline/ avaliam a base de entrada, considerando:
- colunas obrigatórias ausentes;
- valores nulos, inclusive células preenchidas apenas com espaços;
- registros duplicados pela chave id_cliente;
- registros completamente vazios.
As métricas incluem total de registros, quantidade de nulos e duplicados, percentual de nulos nas colunas obrigatórias avaliadas e percentual de duplicidade.

Registros sem id_cliente, sem razão social ou com id_cliente duplicado são rejeitados com justificativa e mantidos separadamente, em vez de serem descartados silenciosamente.
Auditoria e rastreabilidade
O objetivo da auditoria é permitir responder: para determinado registro, o que foi alterado, por que foi alterado e qual fonte foi utilizada?

O módulo audit/ mantém registros independentes para transformações e operações da aplicação.
Registro	Arquivo	Conteúdo
Trilha de transformações	audit_transformacoes.jsonl	Eventos de alteração, validação, decisão, enriquecimento e rejeição
Operações e acessos	audit.log	Requisições à API (POST, PUT, DELETE) e acessos HTTP, com informações de data, tipo e IP


Exemplo de evento de transformação
{
  "data_hora": "2026-11-25T10:32:07",
  "id_registro": "CLI0003",
  "etapa": "transformacao",
  "campo": "bairro",
  "valor_original": "Taguatinga - DF",
  "valor_tratado": "Taguatinga",
  "alterado": true,
  "criterio": "Remoção do sufixo de UF 'DF' (sigla válida presente em UFS)",
  "fonte": "regras-de-tratamento.md"
}
Exemplo de evento de decisão
{
  "id_registro": "CLI0001",
  "etapa": "decisao",
  "campo": "bairro",
  "valor_original": "informado='Sul (Águas Claras)' | api='Águas Claras'",
  "valor_tratado": "Águas Claras",
  "criterio": "convergente: chaves normalizadas idênticas entre informado e API",
  "fonte": "informado+api"
}
Os exemplos ilustram o formato dos eventos. Os valores efetivos dependem do registro processado.

Etapas registradas
etapa	O que registra
transformacao	Padronização de um campo
validacao	Valor descartado por ser inválido ou vazio
apelido	Substituição por nome oficial via dicionário
exibicao	Formatação final para apresentação
decisao	Escolha entre bairro informado e bairro da API
enriquecimento	Campo preenchido a partir da consulta de CEP
rejeicao	Registro rejeitado, com motivo


Banco de dados
O PostgreSQL armazena a base final. A conexão é centralizada em database/connection.py, e as credenciais são obtidas por variáveis de ambiente.
- Upsert por id_cliente: reprocessar o mesmo arquivo atualiza os registros em vez de duplicá-los.
- Preservação de dados: um valor novo vazio não deve apagar um valor que já estava preenchido.
- Transação: em caso de erro, a operação pode sofrer rollback.
O esquema está documentado em [`docs/banco-de-dados.md`](docs/banco-de-dados.md), e a definição SQL está organizada em database/schema.sql.
API REST
A API foi construída com Django REST Framework e utiliza o PostgreSQL como persistência.
Método HTTP	Operação
GET	Consulta de clientes
POST	Cadastro de cliente
PUT	Atualização de cliente
DELETE	Exclusão de cliente


Os endpoints e exemplos de requisição estão documentados em [`docs/api.md`](docs/api.md).
Estrutura do projeto
VetorFlow/
├── api/                 Endpoints e componentes da API REST
│   └── migrations/      Migrações do Django
├── audit/               Trilha de transformações e registro de operações
├── benchmark/           Rotinas de benchmark
├── config/              Configurações do projeto Django
├── data/
│   ├── raw/             Arquivos de entrada
│   ├── processed/       Dados processados
│   └── benchmark/       Dados utilizados em benchmark
├── database/            Conexão e esquema SQL do PostgreSQL
├── docs/                Documentação técnica complementar
├── frontend/            Interface web
├── integrations/        ViaCEP, BrasilAPI e cache
├── neighborhood/        Normalização e resolução de bairros
├── normalizers/         Normalização dos campos cadastrais
├── pipeline/            ETL, verificações de qualidade e métricas
├── src/                 Código-fonte organizado no projeto
├── test/                Testes automatizados
├── .env.example         Modelo de variáveis de ambiente
├── manage.py            Comandos administrativos do Django
├── pytest.ini           Configuração do Pytest
├── requirements.txt     Dependências Python
├── Makefile             Atalhos de tarefas
├── logging_config.py    Configuração de logs
├── exceptions.py        Exceções do projeto
└── Relatório_tradeoffs.md  Decisões e trade-offs
Configuração do ambiente
As instruções abaixo consideram uma instalação local no Windows com PowerShell, sem Docker.
1. Pré-requisitos
Antes de iniciar, instale:
- Python: necessário para executar o ETL, a API e os testes.
- PostgreSQL: banco de dados utilizado pelo projeto.
- Git: para clonar o repositório e acompanhar o código.
- Editor de código: Visual Studio Code ou PyCharm, por exemplo.
Após instalar, abra o PowerShell e confira se Python e Git estão disponíveis:
python --version
git --version
Confira também se o PostgreSQL está instalado e se o serviço está em execução. O pgAdmin pode ser utilizado para administrar o banco graficamente.
2. Clonar o repositório
Escolha uma pasta para os projetos e execute:
git clone https://github.com/Geovannarn/VetorFlow.git
cd VetorFlow
3. Criar o ambiente virtual
O ambiente virtual mantém as dependências do VetorFlow isoladas de outros projetos Python.
python -m venv .venv
Ative o ambiente:
.\.venv\Scripts\Activate.ps1
Se o PowerShell bloquear a ativação por política de execução, execute:
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
Confirme a alteração quando solicitado e tente ativar novamente:
.\.venv\Scripts\Activate.ps1
Com o ambiente ativo, o terminal deve exibir (.venv) no início da linha.
4. Atualizar o instalador de pacotes
python -m pip install --upgrade pip
5. Instalar as dependências
Com o ambiente virtual ativo e na raiz do projeto:
pip install -r requirements.txt
Aguarde a instalação terminar. Se houver erro, confira se o ambiente virtual está ativo e se o terminal está na pasta que contém requirements.txt.
6. Criar o banco de dados PostgreSQL
Abra o pgAdmin e conecte-se ao servidor PostgreSQL local.
1. Expanda o servidor conectado.
2. Clique com o botão direito em Databases.
3. Selecione Create → Database.
4. Informe o nome do banco utilizado no projeto — por exemplo, Primora, caso esse seja o nome definido no seu .env.
5. Selecione o proprietário adequado e salve.
O usuário configurado no .env precisa ter permissão para acessar o banco e executar as operações necessárias.
Base de demonstração: se você recebeu o arquivo de backup Primora.backup, utilize a opção Restore do pgAdmin para restaurar a base fornecida, em vez de criar uma base vazia. O banco de destino deve estar criado antes da restauração. A forma de restauração depende do formato do arquivo de backup.

7. Configurar as variáveis de ambiente
Na raiz do projeto, crie uma cópia do arquivo de exemplo:
Copy-Item .env.example .env
Abra o .env no editor e preencha as variáveis de acordo com a instalação local:
DB_HOST=localhost
DB_PORT=5432
DB_NAME=Primora
DB_USER=postgres
DB_PASSWORD=sua_senha_do_postgresql

DJANGO_SECRET_KEY=cole_a_chave_gerada_no_passo_abaixo
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
Atenção:
- DB_HOST: endereço do servidor PostgreSQL.
- DB_PORT: porta do PostgreSQL. A instalação local normalmente utiliza 5432.
- DB_NAME: nome do banco criado ou restaurado.
- DB_USER: usuário do PostgreSQL.
- DB_PASSWORD: senha desse usuário.
- DJANGO_SECRET_KEY: chave secreta utilizada pelo Django.
- DJANGO_DEBUG: modo de desenvolvimento.
- DJANGO_ALLOWED_HOSTS: hosts autorizados pelo Django.
Para gerar uma chave secreta do Django, com o ambiente virtual ativo, execute:
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
Copie o resultado para DJANGO_SECRET_KEY no .env.

Os valores acima são um modelo de configuração local. Utilize os nomes e valores previstos no seu .env.example e no código do projeto. Não compartilhe sua senha nem publique o .env.
8. Conferir a conexão com o banco
Antes de executar migrações ou iniciar a aplicação, confirme que:
- o serviço do PostgreSQL está iniciado;
- o banco informado em DB_NAME existe;
- usuário e senha estão corretos;
- a porta e o host correspondem à instalação local;
- o usuário possui as permissões necessárias.
Se aparecer fe_sendauth: no password supplied, verifique se DB_PASSWORD está preenchida corretamente no .env e se a aplicação está carregando esse arquivo.
9. Verificar a configuração do Django
Na raiz do projeto, com o ambiente virtual ativo:
python manage.py check
O resultado esperado, quando não há problemas de configuração, é:
System check identified no issues (0 silenced).
10. Aplicar as migrações
Com a conexão ao PostgreSQL configurada:
python manage.py migrate
Esse comando aplica as migrações registradas no Django. Se houver erro de conexão, não prossiga: corrija primeiro as credenciais e a disponibilidade do PostgreSQL.
11. Conferir o arquivo de entrada
O arquivo CSV utilizado no processamento deve estar no caminho esperado pelo projeto:
data/raw/clientes_distribuidora_vetor.csv
Confira se o arquivo existe nesse diretório antes de executar o processamento.
Execução do sistema
1. Ativar o ambiente virtual
Sempre que abrir um novo PowerShell para trabalhar no projeto, entre na pasta do repositório e ative o ambiente:
cd caminho\para\VetorFlow
.\.venv\Scripts\Activate.ps1
2. Iniciar a aplicação Django
Na raiz do projeto:
python manage.py runserver
A aplicação ficará disponível localmente em:
http://127.0.0.1:8000/
Para encerrar o servidor, pressione Ctrl + C no terminal.
3. Acessar a interface e a API
Com o servidor em execução, acesse:
- Interface web: http://127.0.0.1:8000/
- API de clientes: consulte os caminhos e métodos descritos em [`docs/api.md`](docs/api.md).
Os caminhos específicos das telas e dos endpoints estão sujeitos às rotas configuradas no projeto.
4. Executar o processamento ETL
O arquivo de entrada deve estar em data/raw/clientes_distribuidora_vetor.csv. O processamento utiliza os módulos de qualidade, normalização, enriquecimento, resolução de bairros, auditoria e persistência.

Comando de execução: deve ser informado conforme o ponto de entrada efetivamente definido no projeto. Não execute um comando presumido: confira o Makefile e os módulos de pipeline/ para identificar a rotina de entrada disponível na versão clonada.
Testes automatizados
O projeto utiliza Pytest para verificar os componentes e os fluxos implementados.

Com o ambiente virtual ativo, execute na raiz:
pytest
A suíte contempla testes da API, integração de CEP, carregamento/ETL, resolução de bairros e verificações de qualidade.

Para executar os testes com mais detalhes:
pytest -v
Documentação complementar
Documento	Conteúdo
[`docs/api.md`](docs/api.md)	Endpoints e utilização da API
[`docs/decisoes-tecnicas.md`](docs/decisoes-tecnicas.md)	Decisões técnicas e alternativas consideradas
[`docs/regras-de-tratamento.md`](docs/regras-de-tratamento.md)	Regras aplicadas aos campos e referências utilizadas na auditoria
[`docs/banco-de-dados.md`](docs/banco-de-dados.md)	Estrutura do banco e tabelas
[`Relatório_tradeoffs.md`](Relatório_tradeoffs.md)	O que foi automatizado, o que foi tratado manualmente e por quê


Roadmap
As funcionalidades abaixo representam evoluções planejadas e não devem ser consideradas implementadas na versão atual:
- Evolução da trilha de auditoria: separar, na etapa, a origem do bairro (informado ou API) e identificar cada execução, permitindo distinguir reprocessamentos.
- Módulo de benchmark: utilizar dados sintéticos de 10 mil a 5 milhões de registros para comparar carga individual e em lote no PostgreSQL, medindo CPU, memória e registros por segundo.
- Verificação de CEP por perímetro: regra ainda em definição.
- Migração da lógica para Django: reorganizar a lógica em funções Python no back-end, mantendo JavaScript restrito às interações necessárias.
<div align="center">

VetorFlow
