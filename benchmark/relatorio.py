import base64
import html
import platform
from datetime import datetime

import matplotlib

matplotlib.use("Agg")  

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import psutil


PRINCIPAIS = [
    ("extracao", "chunks", "Extração (chunks)"),
    ("transformacao", "completa", "Transformação"),
    ("carga", "lote", "Carga em lote"),
    ("carga", "copy", "Carga com COPY"),
]

OPERACOES_TRANSFORMACAO = [
    "leitura_csv", "identificar_vazios", "normalizar_documento", "validar_documento",
    "validar_cep", "normalizar_regiao", "identificar_duplicados",
    "corrigir_inconsistencias", "preparar_armazenamento",
]

ESTRATEGIAS_CARGA = [
    ("individual_commit_por_linha", "Individual (commit por linha)"),
    ("individual_commit_unico", "Individual (1 commit)"),
    ("lote", "Em lote"),
    ("copy", "COPY"),
]

MOTIVOS = [
    ("documento_invalido", "Documento inválido"),
    ("documento_vazio", "Documento vazio"),
    ("cep_invalido", "CEP inválido"),
    ("nome_vazio", "Nome vazio"),
    ("id_vazio", "Id vazio"),
    ("duplicado", "Id duplicado"),
]

PAR_INJETADO = {
    "documento_invalido": "documento_invalido",
    "documento_vazio": "documento_vazio",
    "cep_invalido": "cep_invalido",
    "nome_vazio": "nome_vazio",
    "duplicado": "id_duplicado",
}


def numero(valor, casas=0):
    """Formata no padrão brasileiro: 1.234.567,89"""
    texto = f"{valor:,.{casas}f}"

    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def rotulo_volume(v):
    if v == 0:
        return "tabela atual"

    if v >= 1_000_000:
        return f"{v / 1_000_000:g} mi"

    if v >= 1_000:
        return f"{v / 1_000:g} mil"

    return str(int(v))


COLUNAS_NUMERICAS = [
    "tempo_s", "registros", "rejeitados", "erros", "registros_por_s",
    "taxa_rejeicao_pct", "taxa_erros_pct", "cpu_proc_pct", "cpu_sistema_pct",
    "ram_inicial_mb", "ram_pico_mb", "ram_delta_mb", "amostra", "volume_total",
    "lat_media_ms", "lat_p50_ms", "lat_p95_ms", "lat_p99_ms", "lat_max_ms", "kb_resposta_media",
] + [f"motivo_{chave}" for chave, _ in MOTIVOS]


def preparar(linhas):
    """Monta a tabela de resultados garantindo que todas as colunas existam (mesmo vazias)."""
    df = pd.DataFrame(linhas)

    for coluna in ["ignorado", "observacao"] + COLUNAS_NUMERICAS:
        if coluna not in df.columns:
            df[coluna] = np.nan

    df["ignorado"] = df["ignorado"].fillna(False).astype(bool)
    df["observacao"] = df["observacao"].fillna("")

    return df


def serie(df, etapa, variante, coluna):
    sub = df[(df.etapa == etapa) & (df.variante == variante) & ~df.ignorado]
    sub = sub.dropna(subset=[coluna]).sort_values("volume")

    return sub["volume"].to_numpy(), sub[coluna].to_numpy(dtype=float)


def salvar(fig, pasta, nome):
    caminho = pasta / f"{nome}.png"
    fig.tight_layout()
    fig.savefig(caminho, dpi=130)
    plt.close(fig)

    return caminho


def eixo_volume(ax, volumes):
    volumes = sorted(set(volumes))

    if len(volumes) > 1:
        ax.set_xscale("log")

    ax.set_xticks(volumes)
    ax.set_xticklabels([rotulo_volume(v) for v in volumes])
    ax.minorticks_off()
    ax.set_xlabel("Quantidade de registros")
    ax.grid(True, alpha=0.3)


def grafico_linhas(df, coluna, titulo, ylabel, pasta, nome, log_y=False):
    fig, ax = plt.subplots(figsize=(8, 4.5))
    volumes = []
    desenhou = False

    for etapa, variante, rotulo in PRINCIPAIS:
        x, y = serie(df, etapa, variante, coluna)

        if len(x):
            ax.plot(x, y, marker="o", label=rotulo)
            volumes += list(x)
            desenhou = True

    if not desenhou:
        plt.close(fig)
        return None

    if log_y:
        ax.set_yscale("log")

    eixo_volume(ax, volumes)
    ax.set_title(titulo)
    ax.set_ylabel(ylabel)
    ax.legend()

    return salvar(fig, pasta, nome)


def grafico_cpu(df, pasta):
    fig, eixos = plt.subplots(1, 2, figsize=(11, 4.5), sharex=True)
    volumes = []
    desenhou = False

    for ax, coluna, titulo in (
        (eixos[0], "cpu_proc_pct", "CPU do processo Python (100% = 1 núcleo)"),
        (eixos[1], "cpu_sistema_pct", "CPU do computador inteiro (%)"),
    ):
        for etapa, variante, rotulo in PRINCIPAIS:
            x, y = serie(df, etapa, variante, coluna)

            if len(x):
                ax.plot(x, y, marker="o", label=rotulo)
                volumes += list(x)
                desenhou = True

        ax.set_title(titulo, fontsize=10)

    if not desenhou:
        plt.close(fig)
        return None

    for ax in eixos:
        eixo_volume(ax, volumes)

    eixos[0].set_ylabel("%")
    eixos[0].legend()

    return salvar(fig, pasta, "cpu_por_etapa")


def grafico_operacoes(df, pasta):
    sub = df[(df.etapa == "transformacao") & df.variante.isin(OPERACOES_TRANSFORMACAO) & ~df.ignorado]

    if sub.empty:
        return None

    tabela = sub.pivot_table(index="volume", columns="variante", values="tempo_s", aggfunc="sum")
    tabela = tabela[[o for o in OPERACOES_TRANSFORMACAO if o in tabela.columns]]

    fig, ax = plt.subplots(figsize=(9, 5))
    base = np.zeros(len(tabela))
    posicoes = np.arange(len(tabela))

    for operacao in tabela.columns:
        valores = tabela[operacao].fillna(0).to_numpy()
        ax.bar(posicoes, valores, bottom=base, label=operacao.replace("_", " "))
        base += valores

    ax.set_xticks(posicoes)
    ax.set_xticklabels([rotulo_volume(v) for v in tabela.index])
    ax.set_xlabel("Quantidade de registros")
    ax.set_ylabel("Segundos")
    ax.set_title("Onde a transformação gasta tempo")
    ax.legend(fontsize=8, ncol=2)

    return salvar(fig, pasta, "transformacao_operacoes")


def grafico_estrategias_carga(df, pasta):
    sub = df[(df.etapa == "carga") & ~df.ignorado].dropna(subset=["registros_por_s"])

    if sub.empty:
        return None

    volumes = sorted(sub.volume.unique())
    fig, ax = plt.subplots(figsize=(9, 5))
    largura = 0.8 / len(ESTRATEGIAS_CARGA)

    for i, (variante, rotulo) in enumerate(ESTRATEGIAS_CARGA):
        valores = []

        for v in volumes:
            linha = sub[(sub.volume == v) & (sub.variante == variante)]
            valores.append(float(linha.registros_por_s.iloc[0]) if len(linha) else np.nan)

        ax.bar(np.arange(len(volumes)) + i * largura, valores, largura, label=rotulo)

    ax.set_xticks(np.arange(len(volumes)) + 0.4 - largura / 2)
    ax.set_xticklabels([rotulo_volume(v) for v in volumes])
    ax.set_yscale("log")
    ax.set_xlabel("Quantidade de registros")
    ax.set_ylabel("Registros por segundo (escala log)")
    ax.set_title("Estratégias de inserção no PostgreSQL")
    ax.legend()
    ax.grid(True, axis="y", alpha=0.3)

    return salvar(fig, pasta, "carga_estrategias")


def grafico_qualidade(df, pasta):
    sub = df[(df.etapa == "transformacao") & (df.variante == "completa") & ~df.ignorado].sort_values("volume")

    if sub.empty:
        return None

    fig, ax = plt.subplots(figsize=(9, 5))
    base = np.zeros(len(sub))
    posicoes = np.arange(len(sub))

    for chave, rotulo in MOTIVOS:
        coluna = f"motivo_{chave}"

        if coluna not in sub.columns:
            continue

        valores = (sub[coluna].fillna(0) / sub["registros"] * 100).to_numpy()
        ax.bar(posicoes, valores, bottom=base, label=rotulo)
        base += valores

    ax.set_xticks(posicoes)
    ax.set_xticklabels([rotulo_volume(v) for v in sub.volume])
    ax.set_xlabel("Quantidade de registros")
    ax.set_ylabel("% dos registros (um registro pode ter mais de um problema)")
    ax.set_title("Problemas de qualidade encontrados")
    ax.legend(fontsize=8)

    return salvar(fig, pasta, "qualidade")


def ultimo_por_variante(df, etapa):
    sub = df[(df.etapa == etapa) & ~df.ignorado].sort_values("volume")

    return sub.groupby("variante", sort=False).tail(1)


def grafico_api(df, pasta):
    sub = ultimo_por_variante(df, "api").dropna(subset=["lat_media_ms"])

    if sub.empty:
        return None

    fig, ax = plt.subplots(figsize=(9, 5))
    y = np.arange(len(sub))

    ax.barh(y - 0.2, sub.lat_media_ms, 0.4, label="média")
    ax.barh(y + 0.2, sub.lat_p95_ms, 0.4, label="p95 (95% das requisições são mais rápidas)")
    ax.set_yticks(y)
    ax.set_yticklabels(sub.variante)
    ax.set_xscale("log")
    ax.set_xlabel("Milissegundos (escala log)")
    ax.set_title("Latência da API por operação")
    ax.legend()
    ax.grid(True, axis="x", alpha=0.3)

    return salvar(fig, pasta, "api_latencias")


def grafico_consultas(df, pasta):
    sub = ultimo_por_variante(df, "consultas_banco")

    if sub.empty:
        return None

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh(sub.variante, sub.tempo_s * 1000)
    ax.set_xscale("log")
    ax.set_xlabel("Milissegundos (escala log)")
    ax.set_title(f"Consultas no banco (maior volume: {rotulo_volume(sub.volume.max())})")
    ax.grid(True, axis="x", alpha=0.3)

    return salvar(fig, pasta, "consultas_banco")


def expoente(volumes, tempos):
    pares = [(v, t) for v, t in zip(volumes, tempos) if v > 0 and t > 0]

    if len(pares) < 2:
        return None

    x = np.log10([p[0] for p in pares])
    y = np.log10([p[1] for p in pares])
    a, b = np.polyfit(x, y, 1)

    return float(a), float(b)


def classificar(a):
    if a < 0.9:
        return "ganha escala (cresce menos que o volume)"

    if a <= 1.15:
        return "linear (dobrar o volume dobra o tempo)"

    if a <= 1.5:
        return "um pouco pior que linear"

    return "muito pior que linear: atenção"


def tabela_escalabilidade(df, volume_alvo=5_000_000):
    linhas = []
    candidatos = [(e, v, r) for e, v, r in PRINCIPAIS]
    candidatos += [("transformacao", o, o.replace("_", " ")) for o in OPERACOES_TRANSFORMACAO]

    for etapa, variante, rotulo in candidatos:
        volumes, tempos = serie(df, etapa, variante, "tempo_s")
        ajuste = expoente(volumes, tempos)

        if ajuste is None:
            continue

        a, b = ajuste
        linhas.append({
            "Etapa": rotulo,
            "Expoente": numero(a, 2),
            "Comportamento": classificar(a),
            f"Tempo estimado para {rotulo_volume(volume_alvo)} (s)": numero(10 ** (b + a * np.log10(volume_alvo)), 1),
        })

    return pd.DataFrame(linhas)


def tabela_pivot(df, coluna, casas, filtro=None):
    sub = df[~df.ignorado].dropna(subset=[coluna])

    if filtro is not None:
        sub = sub[filtro(sub)]

    if sub.empty:
        return pd.DataFrame()

    tabela = sub.pivot_table(index=["etapa", "variante"], columns="volume", values=coluna, aggfunc="last")
    tabela.columns = [rotulo_volume(v) for v in tabela.columns]
    tabela.index = [f"{e} / {v}" for e, v in tabela.index]

    return tabela.map(lambda x: "" if pd.isna(x) else numero(x, casas))


def tabela_estimativas_individuais(df):
    sub = df[df.amostra.notna() & ~df.ignorado].dropna(subset=["registros_por_s"])

    if sub.empty:
        return pd.DataFrame()

    return pd.DataFrame({
        "Volume": [rotulo_volume(v) for v in sub.volume],
        "Estratégia": sub.variante.to_numpy(),
        "Linhas medidas": sub.amostra.astype(int).to_numpy(),
        "Registros/s": [numero(x) for x in sub.registros_por_s],
        "Tempo estimado para todos os registros válidos": [
            formatar_duracao(total / rps) for total, rps in zip(sub.volume_total, sub.registros_por_s)
        ],
    })


def formatar_duracao(segundos):
    if segundos < 120:
        return f"{numero(segundos, 1)} s"

    if segundos < 7200:
        return f"{numero(segundos / 60, 1)} min"

    return f"{numero(segundos / 3600, 1)} h"


def tabela_defeitos(df, injetados):
    linhas = []

    for _, linha in df[(df.etapa == "transformacao") & (df.variante == "completa")].sort_values("volume").iterrows():
        meta = injetados.get(int(linha.volume), {})

        for chave, rotulo in MOTIVOS:
            detectado = linha.get(f"motivo_{chave}")
            injetado = meta.get(PAR_INJETADO.get(chave, ""))

            if pd.isna(detectado):
                continue

            linhas.append({
                "Volume": rotulo_volume(linha.volume),
                "Problema": rotulo,
                "Injetado no gerador (aprox.)": "" if injetado is None else numero(injetado),
                "Detectado": numero(detectado),
            })

    return pd.DataFrame(linhas)


def observacoes(df):
    textos = []
    ok = df[~df.ignorado]

    if ok.empty:
        return textos

    maior = int(ok[ok.etapa.isin(["extracao", "transformacao", "carga"])].volume.max())
    rotulo = rotulo_volume(maior)

    ops = ok[(ok.etapa == "transformacao") & (ok.volume == maior) & ok.variante.isin(OPERACOES_TRANSFORMACAO)]

    if not ops.empty:
        total = ops.tempo_s.sum()
        pior = ops.sort_values("tempo_s").iloc[-1]
        textos.append(
            f"Em {rotulo} registros, a parte mais lenta da transformação foi "
            f"<b>{pior.variante.replace('_', ' ')}</b> ({numero(pior.tempo_s / total * 100)}% do tempo)."
        )

    def taxa(variante):
        linha = ok[(ok.etapa == "carga") & (ok.variante == variante) & (ok.volume == maior)]
        return float(linha.registros_por_s.iloc[0]) if len(linha) else None

    copia, lote, uma_por_linha = taxa("copy"), taxa("lote"), taxa("individual_commit_por_linha")

    if copia and lote:
        textos.append(f"Em {rotulo} registros, o COPY foi <b>{numero(copia / lote, 1)}x</b> mais rápido que a inserção em lote.")

    if copia and uma_por_linha:
        textos.append(
            f"O COPY foi <b>{numero(copia / uma_por_linha)}x</b> mais rápido que inserir uma linha por vez com commit a cada linha."
        )

    chunks = ok[(ok.etapa == "extracao") & (ok.variante == "chunks") & (ok.volume == maior)]
    inteiro = ok[(ok.etapa == "extracao") & (ok.variante == "inteiro") & (ok.volume == maior)]

    if len(chunks) and len(inteiro):
        textos.append(
            f"Ler o CSV de {rotulo} linhas em chunks usou {numero(chunks.ram_pico_mb.iloc[0])} MB de memória no pico; "
            f"lendo tudo de uma vez, {numero(inteiro.ram_pico_mb.iloc[0])} MB."
        )

    etapas = ok[ok.volume == maior].dropna(subset=["ram_pico_mb"])

    if not etapas.empty:
        pico = etapas.sort_values("ram_pico_mb").iloc[-1]
        textos.append(f"O maior pico de memória em {rotulo} registros foi de <b>{numero(pico.ram_pico_mb)} MB</b> ({pico.etapa} / {pico.variante}).")

    transf = ok[(ok.etapa == "transformacao") & (ok.variante == "completa") & (ok.volume == maior)]

    if len(transf):
        t = transf.iloc[0]
        textos.append(
            f"Em {rotulo} registros, <b>{numero(t.rejeitados)}</b> foram rejeitados ({numero(t.taxa_rejeicao_pct, 1)}%) "
            f"e ficaram no arquivo de rejeitados com o motivo."
        )

    api = ok[(ok.etapa == "api") & ok.lat_p95_ms.notna()]

    if not api.empty:
        lenta = api.sort_values("lat_p95_ms").iloc[-1]
        textos.append(f"Operação mais lenta da API (p95): <b>{lenta.variante}</b>, com {numero(lenta.lat_p95_ms)} ms.")

    return textos


def ambiente():
    memoria = psutil.virtual_memory().total / 1024 ** 3

    return {
        "Data": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "Sistema": f"{platform.system()} {platform.release()}",
        "Python": platform.python_version(),
        "pandas": pd.__version__,
        "Núcleos de CPU": f"{psutil.cpu_count(logical=False) or '?'} físicos / {psutil.cpu_count()} lógicos",
        "Memória RAM": f"{memoria:.1f} GB",
    }


def para_html(tabela, titulo):
    if tabela is None or tabela.empty:
        return ""

    mostrar_indice = not isinstance(tabela.index, pd.RangeIndex)

    return f"<h3>{html.escape(titulo)}</h3>" + tabela.to_html(
        border=0, classes="tabela", escape=True, index=mostrar_indice
    )


def imagem(caminho):
    if caminho is None:
        return ""

    dados = base64.b64encode(caminho.read_bytes()).decode()

    return f'<img src="data:image/png;base64,{dados}" alt="{html.escape(caminho.stem)}">'


CSS = """
body{font-family:system-ui,Segoe UI,Arial,sans-serif;max-width:1100px;margin:2rem auto;padding:0 1rem;color:#1b1b1b;line-height:1.5}
h1{margin-bottom:.2rem} h2{margin-top:2.2rem;border-bottom:2px solid #ddd;padding-bottom:.3rem} h3{margin-top:1.5rem}
img{max-width:100%;margin:.6rem 0;border:1px solid #e3e3e3;border-radius:6px}
.tabela{border-collapse:collapse;font-size:.88rem;margin:.5rem 0;display:block;overflow-x:auto}
.tabela th,.tabela td{padding:.35rem .7rem;border-bottom:1px solid #e6e6e6;text-align:right;white-space:nowrap}
.tabela th:first-child,.tabela td:first-child{text-align:left}
.aviso{background:#fff6e0;border-left:4px solid #e0a100;padding:.5rem .9rem;margin:.5rem 0}
.nota{color:#555;font-size:.9rem}
@media (prefers-color-scheme:dark){body{background:#17181a;color:#e8e8e8}h2{border-color:#444}.tabela th,.tabela td{border-color:#333}
.aviso{background:#3a3000}.nota{color:#aaa}img{border-color:#333;background:#fff}}
"""


def gerar_relatorio(linhas, pasta, avisos=None, injetados=None):
    """Cria graficos/*.png, relatorio.html, resultados.csv e resultados.json dentro de `pasta`."""
    pasta.mkdir(parents=True, exist_ok=True)
    pasta_graficos = pasta / "graficos"
    pasta_graficos.mkdir(exist_ok=True)

    df = preparar(linhas)
    df.to_csv(pasta / "resultados.csv", index=False, encoding="utf-8")
    df.to_json(pasta / "resultados.json", orient="records", force_ascii=False, indent=2)

    graficos = [
        grafico_linhas(df, "tempo_s", "Tempo de execução por etapa", "Segundos (escala log)", pasta_graficos, "tempo_por_etapa", log_y=True),
        grafico_linhas(df, "registros_por_s", "Registros processados por segundo", "Registros por segundo", pasta_graficos, "registros_por_segundo"),
        grafico_linhas(df, "ram_pico_mb", "Pico de memória RAM do processo", "MB", pasta_graficos, "memoria_por_etapa"),
        grafico_cpu(df, pasta_graficos),
        grafico_operacoes(df, pasta_graficos),
        grafico_estrategias_carga(df, pasta_graficos),
        grafico_qualidade(df, pasta_graficos),
        grafico_consultas(df, pasta_graficos),
        grafico_api(df, pasta_graficos),
    ]

    partes = ["<h1>Benchmark do VetorFlow</h1>"]
    partes.append(para_html(pd.DataFrame([ambiente()]).T.rename(columns={0: "Valor"}), "Ambiente do teste"))

    for aviso in avisos or []:
        partes.append(f'<div class="aviso">{html.escape(aviso)}</div>')

    textos = observacoes(df)

    if textos:
        partes.append("<h2>Principais conclusões</h2><ul>" + "".join(f"<li>{t}</li>" for t in textos) + "</ul>")

    partes.append("<h2>Gráficos</h2>" + "".join(imagem(g) for g in graficos))

    partes.append("<h2>Tabelas</h2>")
    partes.append(para_html(tabela_pivot(df, "tempo_s", 2), "Tempo (segundos)"))
    partes.append(para_html(tabela_pivot(df, "registros_por_s", 0), "Registros por segundo"))
    partes.append(para_html(tabela_pivot(df, "ram_pico_mb", 0), "Pico de memória (MB)"))
    partes.append(para_html(tabela_pivot(df, "cpu_proc_pct", 0), "CPU do processo (%)"))
    partes.append(para_html(tabela_pivot(df, "taxa_rejeicao_pct", 1, lambda s: s.etapa == "transformacao"), "Taxa de rejeição (%)"))
    partes.append(para_html(tabela_pivot(df, "taxa_erros_pct", 2), "Taxa de erros (%)"))
    partes.append(para_html(tabela_pivot(df, "lat_p95_ms", 1), "Latência da API, p95 (ms)"))

    partes.append("<h2>Como o desempenho cresce com o volume</h2>")
    partes.append(
        '<p class="nota">O expoente vem de um ajuste na escala log-log: 1,0 = linear; abaixo de 1 = ganha escala; '
        "acima de 1 = piora mais rápido que o volume. Os tempos para volumes não testados são "
        "<b>estimativas</b>, não medições.</p>"
    )
    partes.append(para_html(tabela_escalabilidade(df), "Escalabilidade"))
    partes.append(para_html(tabela_estimativas_individuais(df), "Inserção linha a linha (estimativa)"))
    partes.append(para_html(tabela_defeitos(df, injetados or {}), "Defeitos injetados × detectados"))

    ignorados = df[df.ignorado]

    if not ignorados.empty:
        itens = "".join(
            f"<li>{html.escape(str(r.etapa))} / {html.escape(str(r.variante))} ({rotulo_volume(r.volume)}): {html.escape(r.observacao)}</li>"
            for r in ignorados.itertuples()
        )
        partes.append(f"<h2>Não executado</h2><ul>{itens}</ul>")

    caminho = pasta / "relatorio.html"
    caminho.write_text(
        f'<!doctype html><html lang="pt-br"><meta charset="utf-8"><title>Benchmark do VetorFlow</title>'
        f"<style>{CSS}</style><body>{''.join(partes)}</body></html>",
        encoding="utf-8",
    )

    return caminho