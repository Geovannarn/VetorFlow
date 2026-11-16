from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]

PASTA_SAIDA = RAIZ / "data" / "benchmark"
PASTA_DADOS = PASTA_SAIDA / "dados"
PASTA_RESULTADOS = PASTA_SAIDA / "resultados"

PERFIS = {
    "rapido": [10_000, 100_000],
    "completo": [10_000, 100_000, 500_000, 1_000_000, 5_000_000],
}

SEMENTE = 42                       
TAMANHO_CHUNK = 100_000            
LIMITE_LEITURA_INTEIRA = 1_000_000 
LIMITE_INDIVIDUAL = 2_000          
TAMANHO_LOTE = 10_000              

TABELA_BENCHMARK = "benchmark_clientes"

PREFIXO_ID = "BM"

COLUNAS = [
    "id_cliente",
    "nome",
    "documento",
    "cep",
    "endereco",
    "regiao_administrativa",
]