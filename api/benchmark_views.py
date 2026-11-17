import json

from django.http import FileResponse, Http404, JsonResponse

from benchmark import config


def listar_graficos():
    pasta = config.PASTA_RESULTADOS / "graficos"
    graficos = {}

    if pasta.exists():
        for arquivo in pasta.glob("*.png"):
            graficos[arquivo.stem] = arquivo

    return graficos


def benchmark_dados(request):
    arquivo = config.PASTA_RESULTADOS / "resultados.json"

    if not arquivo.exists():
        return JsonResponse({"existe": False, "resultados": [], "graficos": []})

    with arquivo.open(encoding="utf-8") as f:
        resultados = json.load(f)

    graficos = []

    for nome in sorted(listar_graficos()):
        graficos.append({"nome": nome, "url": f"/api/benchmark/grafico/{nome}/"})

    return JsonResponse({
        "existe": True,
        "gerado_em": arquivo.stat().st_mtime,
        "resultados": resultados,
        "graficos": graficos,
    })


def benchmark_grafico(request, nome):
    graficos = listar_graficos()

    if nome not in graficos:
        raise Http404("Gráfico não encontrado.")

    return FileResponse(open(graficos[nome], "rb"), content_type="image/png")


def benchmark_relatorio(request):
    arquivo = config.PASTA_RESULTADOS / "relatorio.html"

    if not arquivo.exists():
        raise Http404("Relatório não encontrado.")

    return FileResponse(open(arquivo, "rb"), content_type="text/html; charset=utf-8")