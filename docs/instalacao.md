# Instalação e configuração

Este documento apresenta os procedimentos necessários para configurar o ambiente de desenvolvimento, instalar as dependências e executar o VetorFlow localmente.

## 1. Pré-requisitos

Antes de iniciar a instalação, é necessário possuir:

- Python instalado.
- PostgreSQL instalado e em execução.
- Git instalado.
- Acesso ao repositório do projeto.

## 2. Clonar o repositório

Clone o repositório e acesse o diretório do projeto:

```powershell
git clone https://github.com/Geovannarn/VetorFlow.git
cd VetorFlow
```

## 3. Criar o ambiente virtual

O ambiente virtual permite isolar as dependências do projeto das demais instalações do Python.

No PowerShell, execute:

```powershell
python -m venv .venv
```

Ative o ambiente virtual:

```powershell
.venv\Scripts\Activate.ps1
```

Caso o PowerShell bloqueie a execução do script, configure a política de execução para o usuário atual:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Depois, tente ativar novamente o ambiente virtual.

## 4. Instalar as dependências

Com o ambiente virtual ativado, instale as bibliotecas utilizadas pelo projeto a partir do arquivo de dependências localizado na raiz do repositório.

```powershell
pip install -r NOME DO ARQUIVO DE DEPENDENCIAS
```

Substitua o nome acima pelo arquivo de dependências utilizado atualmente no projeto.

## 5. Configurar as variáveis de ambiente

O projeto utiliza variáveis de ambiente para armazenar configurações da aplicação e informações de conexão com o banco de dados.

Na raiz do projeto, copie o arquivo de exemplo:

```powershell
Copy-Item .env.example .env
```

Edite o arquivo `.env` e preencha os valores necessários conforme a configuração do PostgreSQL.

O arquivo `.env.example` serve como referência para identificar as variáveis exigidas pela aplicação.

**Importante:** não compartilhe credenciais nem versione o arquivo `.env`. Ele deve permanecer protegido pelo `.gitignore`.

## 6. Configurar o banco de dados

Certifique-se de que o PostgreSQL esteja instalado e em execução.

Crie o banco de dados utilizado pelo projeto e configure as credenciais correspondentes no arquivo `.env`.

A estrutura do banco está documentada em:

```text
database/
├── connection.py
└── schema.sql
```

O arquivo `schema.sql` contém a definição da estrutura do banco de dados.

Consulte também [`banco-de-dados.md`](banco-de-dados.md) para conhecer a organização das tabelas e dos campos.

## 7. Executar a aplicação

Com as dependências instaladas e as configurações realizadas, execute o servidor de desenvolvimento Django:

```powershell
python manage.py runserver
```

Por padrão, a aplicação fica disponível em:

```text
http://127.0.0.1:8000/
```

## 8. Executar os testes

Para executar os testes automatizados utilizando Pytest:

```powershell
pytest
```

Os testes estão organizados no diretório `test/`, abrangendo funcionalidades da API, processamento ETL, consultas de CEP, qualidade dos dados e resolução de bairros.

## 9. Executar o benchmark

O benchmark possui execução independente do servidor de desenvolvimento Django.

Seu ponto de entrada está localizado em:

```text
benchmark/executar.py
```

A execução deve ser realizada conforme as instruções e configurações definidas pelo módulo de benchmark.

## 10. Estrutura de configuração

Após a instalação, os principais arquivos e diretórios relacionados à configuração são:

| Caminho | Finalidade |
|---|---|
| `.env` | Configurações locais e variáveis de ambiente. |
| `.env.example` | Modelo das variáveis necessárias. |
| `config/` | Configurações do Django. |
| `database/` | Conexão e estrutura do banco de dados. |
| `manage.py` | Gerenciamento da aplicação Django. |
| `test/` | Testes automatizados. |
| `benchmark/` | Execução dos experimentos de desempenho. |

---

**Observação:** os comandos e configurações podem variar conforme o ambiente de desenvolvimento e os valores definidos no arquivo `.env`.