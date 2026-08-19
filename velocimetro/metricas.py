"""Leitura de CPU, memoria e atividade de disco.

O disco e medido por vazao, nao por tempo ocupado: nesta maquina os contadores
de desempenho PhysicalDisk do Windows nao existem e os campos read_time e
write_time do psutil retornam zero. A vazao instantanea e comparada a um teto
que se auto-calibra, e o valor absoluto em MB/s viaja junto na leitura para que
o numero verdadeiro apareca na tela.
"""

import time
from dataclasses import dataclass

import psutil

UM_MB = 1024 * 1024
PISO_TETO_MBPS = 200.0
DECAIMENTO_TETO = 0.005


@dataclass(frozen=True)
class Leitura:
    """Uma amostra. Campo em None significa que a fonte falhou."""

    cpu: float | None
    memoria: float | None
    disco: float | None
    disco_mbps: float | None


class FonteDeSistema:
    """Fronteira com o psutil. Trocavel por uma fonte falsa nos testes."""

    def cpu(self):
        return psutil.cpu_percent(interval=None)

    def memoria(self):
        return psutil.virtual_memory().percent

    def bytes_disco(self):
        contadores = psutil.disk_io_counters()
        if contadores is None:
            raise OSError("psutil nao expos contadores de disco nesta maquina")
        return contadores.read_bytes + contadores.write_bytes

    def agora(self):
        return time.perf_counter()


class LeitorDeMetricas:
    def __init__(self, fonte=None, teto_inicial_mbps=PISO_TETO_MBPS):
        self._fonte = fonte if fonte is not None else FonteDeSistema()
        self.teto_mbps = max(PISO_TETO_MBPS, float(teto_inicial_mbps))
        self._bytes_anterior = None
        self._instante_anterior = None

    def ler(self):
        disco, disco_mbps = self._ler_disco()
        return Leitura(
            cpu=self._ler_percentual(self._fonte.cpu),
            memoria=self._ler_percentual(self._fonte.memoria),
            disco=disco,
            disco_mbps=disco_mbps,
        )

    def _ler_percentual(self, funcao):
        try:
            bruto = float(funcao())
        except Exception:
            return None
        return max(0.0, min(100.0, bruto))

    def _ler_disco(self):
        try:
            bytes_agora = self._fonte.bytes_disco()
            instante = self._fonte.agora()
        except Exception:
            return None, None

        if self._bytes_anterior is None:
            self._bytes_anterior = bytes_agora
            self._instante_anterior = instante
            return 0.0, 0.0

        decorrido = instante - self._instante_anterior
        if decorrido <= 0.0:
            return 0.0, 0.0

        transferido = max(0, bytes_agora - self._bytes_anterior)
        self._bytes_anterior = bytes_agora
        self._instante_anterior = instante

        mbps = transferido / UM_MB / decorrido
        self._ajustar_teto(mbps)
        return min(100.0, mbps / self.teto_mbps * 100.0), mbps

    def _ajustar_teto(self, mbps):
        if mbps > self.teto_mbps:
            self.teto_mbps = mbps
        else:
            self.teto_mbps += (PISO_TETO_MBPS - self.teto_mbps) * DECAIMENTO_TETO
