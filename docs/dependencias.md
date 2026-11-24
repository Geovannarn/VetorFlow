## Dependências do projeto

O VetorFlow utiliza bibliotecas Python para processamento de dados, comunicação com serviços externos, gerenciamento da aplicação web, acesso ao banco de dados e execução de testes.

| Biblioteca | Finalidade |
|---|---|
| NumPy | Operações numéricas e manipulação de estruturas de dados. |
| Pandas | Leitura, transformação, validação e manipulação dos dados cadastrais. |
| python-dateutil | Manipulação e interpretação de datas. |
| six | Compatibilidade entre diferentes versões do Python. |
| tzdata | Disponibilização de informações sobre fusos horários. |
| psycopg | Conexão e comunicação com o PostgreSQL. |
| python-dotenv | Leitura de variáveis de ambiente armazenadas no arquivo `.env`. |
| Django | Framework utilizado na estrutura da aplicação web. |
| Django REST Framework | Desenvolvimento dos endpoints da API REST. |
| Requests | Realização de requisições HTTP para serviços externos, como ViaCEP e BrasilAPI. |
| psutil | Monitoramento de recursos do sistema, como memória e CPU, durante os benchmarks. |
| Matplotlib | Geração de gráficos para análise dos resultados do benchmark. |
| Pytest | Execução dos testes automatizados. |
| pytest-django | Integração do Pytest com o ambiente Django. |

### Instalação

As dependências devem ser instaladas no ambiente virtual do projeto utilizando o arquivo de dependências localizado na raiz do repositório:

```powershell
pip install -r NOME_DO_ARQUIVO_DE_DEPENDENCIAS
```