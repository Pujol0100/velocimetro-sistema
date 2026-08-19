"""Geometria e dinamica do mostrador: angulo, faixa de cor e movimento do ponteiro.

Sem dependencia de Qt: tudo aqui e funcao pura ou estado numerico simples.
"""

from enum import Enum

ANGULO_INICIAL = 210.0
ANGULO_FINAL = -30.0
VARREDURA = ANGULO_INICIAL - ANGULO_FINAL

LIMITE_ATENCAO = 60.0
LIMITE_PERIGO = 85.0

# Mola subamortecida. zeta = 0.65 produz ultrapassagem de cerca de 7% do salto,
# que e o que da ao ponteiro o assentamento de um instrumento mecanico.
FREQUENCIA = 12.0
AMORTECIMENTO = 0.65

PASSO_MAXIMO = 1.0 / 240.0
TEMPO_MAXIMO_POR_QUADRO = 0.25
TOLERANCIA_REPOUSO = 0.05


class Faixa(Enum):
    NORMAL = "normal"
    ATENCAO = "atencao"
    PERIGO = "perigo"


def limitar(valor, minimo=0.0, maximo=100.0):
    return max(minimo, min(maximo, valor))


def percentual_para_angulo(percentual):
    """Converte 0-100 no angulo do ponteiro, em graus, sentido anti-horario."""
    return ANGULO_INICIAL - VARREDURA * (limitar(float(percentual)) / 100.0)


def faixa(percentual):
    if percentual >= LIMITE_PERIGO:
        return Faixa.PERIGO
    if percentual >= LIMITE_ATENCAO:
        return Faixa.ATENCAO
    return Faixa.NORMAL


class Suavizador:
    """Persegue um alvo como uma mola amortecida, para o ponteiro nao saltar."""

    def __init__(self, inicial=0.0):
        self.atual = float(inicial)
        self.alvo = float(inicial)
        self._velocidade = 0.0

    @property
    def em_repouso(self):
        return (
            abs(self.alvo - self.atual) < TOLERANCIA_REPOUSO
            and abs(self._velocidade) < TOLERANCIA_REPOUSO
        )

    def passo(self, segundos):
        if segundos <= 0.0:
            return
        restante = min(float(segundos), TEMPO_MAXIMO_POR_QUADRO)
        rigidez = FREQUENCIA * FREQUENCIA
        atrito = 2.0 * AMORTECIMENTO * FREQUENCIA
        while restante > 0.0:
            dt = min(PASSO_MAXIMO, restante)
            aceleracao = (self.alvo - self.atual) * rigidez - self._velocidade * atrito
            self._velocidade += aceleracao * dt
            self.atual += self._velocidade * dt
            restante -= dt
        if self.em_repouso:
            self.atual = self.alvo
            self._velocidade = 0.0
