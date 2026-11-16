import threading
import time
from datetime import datetime

import psutil


MB = 1024 * 1024


def calcular_taxas(linha):
    registros = linha.get("registros")
    tempo = linha.get("tempo_s")

    if registros and tempo:
        linha["registros_por_s"] = registros / tempo

    if registros:
        linha["taxa_rejeicao_pct"] = linha.get("rejeitados", 0) / registros * 100
        linha["taxa_erros_pct"] = linha.get("erros", 0) / registros * 100


class Coletor:

    def __init__(self):
        self.linhas = []

    def medir(self, volume, etapa, variante="", intervalo=0.1):
        return Medicao(self, volume, etapa, variante, intervalo)

    def registrar(self, volume, etapa, variante="", **campos):
        linha = {
            "volume": volume,
            "etapa": etapa,
            "variante": variante,
            "quando": datetime.now().isoformat(timespec="seconds"),
        }
        linha.update(campos)
        calcular_taxas(linha)
        self.linhas.append(linha)

        return linha


class Medicao:

    def __init__(self, coletor, volume, etapa, variante, intervalo):
        self.registros = 0
        self.rejeitados = 0
        self.erros = 0
        self.observacao = ""
        self.extras = {}

        self._coletor = coletor
        self._volume = volume
        self._etapa = etapa
        self._variante = variante
        self._intervalo = intervalo

    def __enter__(self):
        self._processo = psutil.Process()
        self._cpu_inicio = self._processo.cpu_times()
        self._ram_inicial = self._processo.memory_info().rss
        self._ram_pico = self._ram_inicial
        self._cpu_sistema = []
        self._parar = threading.Event()

        psutil.cpu_percent(None)  # a primeira chamada só "zera" o contador

        self._thread = threading.Thread(target=self._amostrar, daemon=True)
        self._thread.start()
        self._inicio = time.perf_counter()

        return self

    def _amostrar(self):
        while not self._parar.wait(self._intervalo):
            self._ram_pico = max(self._ram_pico, self._processo.memory_info().rss)
            self._cpu_sistema.append(psutil.cpu_percent(None))

    def __exit__(self, tipo, valor, rastreio):
        tempo = max(time.perf_counter() - self._inicio, 1e-9)

        self._parar.set()
        self._thread.join()

        self._ram_pico = max(self._ram_pico, self._processo.memory_info().rss)
        self._cpu_sistema.append(psutil.cpu_percent(None))

        cpu_fim = self._processo.cpu_times()
        cpu_usada = (cpu_fim.user + cpu_fim.system) - (
            self._cpu_inicio.user + self._cpu_inicio.system
        )

        observacao = self.observacao

        if tipo is not None:
            observacao = f"falhou: {valor}"
            self.erros += 1

        self._coletor.registrar(
            self._volume,
            self._etapa,
            self._variante,
            tempo_s=tempo,
            registros=self.registros,
            rejeitados=self.rejeitados,
            erros=self.erros,
            cpu_proc_pct=cpu_usada / tempo * 100,
            cpu_sistema_pct=sum(self._cpu_sistema) / len(self._cpu_sistema),
            ram_inicial_mb=self._ram_inicial / MB,
            ram_pico_mb=self._ram_pico / MB,
            ram_delta_mb=(self._ram_pico - self._ram_inicial) / MB,
            observacao=observacao,
            **self.extras,
        )

        return False 