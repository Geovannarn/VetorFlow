import time

from benchmark import config
from benchmark.api import ApiIndisponivel, testar_api
from benchmark.carga import conectar_banco, testar_carga
from benchmark.extracao import testar_extracao
from benchmark.gerador import arquivo_reaproveitavel, caminho_meta, gerar_csv, ler_meta
from benchmark.medidor import Coletor
from benchmark.relatorio import gerar_relatorio
from benchmark.transformacao import testar_transformacao, validar_cpf, validar_documento


VOLUMES = config.PERFIS["rapido"]

TESTAR_BANCO = True

TESTAR_API = False
URL_API = "http://127.0.0.1:8000/"

APAGAR_ARQUIVOS_NO_FINAL = True


def mostrar_tempo(texto, inicio):
    segundos = time.perf_counter() - inicio
    print(f"  {texto}: {segundos:.1f} segundos")


def autoteste():
    problemas = []

    if not validar_documento("11222333000181"):
        problemas.append("O CNPJ válido 11.222.333/0001-81 foi rejeitado. Corrija o normalizers/cnpj.py.")

    if not validar_cpf("52998224725"):
        problemas.append("O CPF válido 529.982.247-25 foi rejeitado.")

    return problemas


def main():
    coletor = Coletor()
    avisos = []
    injetados = {}

    problemas = autoteste()

    if len(problemas) > 0:
        print("O teste inicial falhou:")
        for problema in problemas:
            print("  -", problema)
        return

    print("Volumes:", VOLUMES)

    banco_ok = TESTAR_BANCO

    if banco_ok:
        try:
            conexao = conectar_banco()
            conexao.close()
        except Exception as erro:
            banco_ok = False
            avisos.append(f"Gravação no PostgreSQL não executada: {erro}")
            print("Aviso: não consegui conectar ao banco:", erro)

    config.PASTA_DADOS.mkdir(parents=True, exist_ok=True)
    inicio_total = time.perf_counter()

    for volume in VOLUMES:
        print(f"\n=== {volume} registros ===")

        bruto = config.PASTA_DADOS / f"clientes_{volume}.csv"
        limpo = config.PASTA_DADOS / f"limpo_{volume}.csv"
        rejeitados = config.PASTA_DADOS / f"rejeitados_{volume}.csv"

        inicio = time.perf_counter()

        if arquivo_reaproveitavel(bruto, volume, config.SEMENTE):
            print("  geração: o arquivo já existe, vou usar ele")
        else:
            with coletor.medir(volume, "geracao", "csv_sintetico") as m:
                gerar_csv(volume, bruto)
                m.registros = volume

            mostrar_tempo("geração", inicio)

        meta = ler_meta(bruto)
        injetados[volume] = meta.get("defeitos_injetados", {})

        inicio = time.perf_counter()
        testar_extracao(coletor, volume, bruto)
        mostrar_tempo("extração", inicio)

        inicio = time.perf_counter()
        resumo = testar_transformacao(coletor, volume, bruto, limpo, rejeitados)
        mostrar_tempo("transformação", inicio)
        print(f"  válidos: {resumo['validos']} | rejeitados: {resumo['rejeitados']}")

        if banco_ok:
            inicio = time.perf_counter()

            try:
                testar_carga(coletor, volume, limpo, resumo["validos"], config.LIMITE_INDIVIDUAL)
                mostrar_tempo("carga no banco (todos os testes)", inicio)
            except Exception as erro:
                avisos.append(f"A gravação no PostgreSQL falhou com {volume} registros: {erro}")
                print("  Aviso: a gravação no banco falhou:", erro)

        gerar_relatorio(coletor.linhas, config.PASTA_RESULTADOS, avisos, injetados)

        if APAGAR_ARQUIVOS_NO_FINAL:
            for caminho in [bruto, limpo, rejeitados, caminho_meta(bruto)]:
                caminho.unlink(missing_ok=True)

    if TESTAR_API:
        print("\n=== API ===")

        try:
            existentes = testar_api(coletor, 0, URL_API)
            avisos.append(f'A API foi testada com os {existentes} clientes que já estavam na tabela "usuarios".')
        except ApiIndisponivel as erro:
            avisos.append(f"A API não foi testada: {erro}")
            print("Aviso:", erro)

    caminho_relatorio = gerar_relatorio(coletor.linhas, config.PASTA_RESULTADOS, avisos, injetados)

    mostrar_tempo("tempo total", inicio_total)
    print("Relatório:", caminho_relatorio)


if __name__ == "__main__":
    main()