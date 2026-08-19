"""Paleta carbono e ambar, tipografia e a textura de fibra de carbono.

Um lugar so para as cores, para que trocar o acabamento seja mexer num arquivo.
"""

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QFontDatabase,
    QLinearGradient,
    QPainter,
    QPen,
    QPixmap,
)

# Estrutura do instrumento
ARO_CLARO = QColor(196, 200, 206)
ARO_MEDIO = QColor(104, 108, 114)
ARO_ESCURO = QColor(28, 30, 34)
ARO_BRILHO = QColor(238, 242, 248)

FUNDO_MOSTRADOR_CENTRO = QColor(30, 31, 34)
FUNDO_MOSTRADOR_BORDA = QColor(9, 9, 11)
VIGNETA = QColor(0, 0, 0, 190)

# Marcacoes e texto
TRACO_MAIOR = QColor(236, 238, 242, 235)
TRACO_MENOR = QColor(214, 218, 226, 110)
NUMERO = QColor(206, 210, 218, 205)
ROTULO = QColor(150, 155, 164, 225)
LEGENDA = QColor(126, 131, 140, 210)
VALOR = QColor(244, 246, 250)

# Ponteiro e faixas
AMBAR = QColor(255, 168, 26)
AMBAR_CLARO = QColor(255, 214, 138)
AMBAR_BRILHO = QColor(255, 158, 12)
ATENCAO = QColor(255, 196, 60)
PERIGO = QColor(233, 58, 44)
ZONA_PERIGO = QColor(214, 44, 32, 62)
SOMBRA_PONTEIRO = QColor(0, 0, 0, 150)

# Cubo central
CUBO_CLARO = QColor(178, 182, 190)
CUBO_ESCURO = QColor(22, 23, 26)

# Carcaca que une os tres mostradores
CARCACA_TOPO = QColor(24, 26, 31, 148)
CARCACA_BASE = QColor(6, 6, 9, 124)
CARCACA_BORDA = QColor(255, 255, 255, 30)
CARCACA_BRILHO = QColor(255, 255, 255, 16)

_FAMILIAS_CONDENSADAS = (
    "Bahnschrift SemiCondensed",
    "Bahnschrift Condensed",
    "Bahnschrift",
    "DIN Condensed",
    "Segoe UI Semibold",
    "Segoe UI",
)

_familia_escolhida = None
_textura = None


def familia_condensada():
    """A primeira familia estreita disponivel. Painel de carro usa fonte estreita."""
    global _familia_escolhida
    if _familia_escolhida is None:
        instaladas = set(QFontDatabase.families())
        _familia_escolhida = next(
            (f for f in _FAMILIAS_CONDENSADAS if f in instaladas), "Segoe UI"
        )
    return _familia_escolhida


def fonte(pixels, peso=QFont.Weight.DemiBold, espacamento=0.0):
    f = QFont(familia_condensada())
    f.setPixelSize(max(1, int(pixels)))
    f.setWeight(peso)
    if espacamento:
        f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, espacamento)
    return f


def textura_carbono():
    """Tecelagem de fibra de carbono gerada em codigo, usada como brush repetido."""
    global _textura
    if _textura is not None:
        return _textura

    lado = 16
    metade = lado // 2
    pixmap = QPixmap(lado, lado)
    pixmap.fill(QColor(0, 0, 0, 0))
    pintor = QPainter(pixmap)
    pintor.setRenderHint(QPainter.RenderHint.Antialiasing, False)

    for coluna in (0, 1):
        for linha in (0, 1):
            x = coluna * metade
            y = linha * metade
            diagonal_para_direita = (coluna + linha) % 2 == 0
            pintor.setBrush(QBrush(QColor(255, 255, 255, 5 if diagonal_para_direita else 0)))
            pintor.setPen(Qt.PenStyle.NoPen)
            pintor.drawRect(x, y, metade, metade)
            pintor.setPen(QPen(QColor(255, 255, 255, 13), 1))
            for deslocamento in range(-metade, metade, 2):
                if diagonal_para_direita:
                    pintor.drawLine(
                        x + deslocamento, y + metade, x + deslocamento + metade, y
                    )
                else:
                    pintor.drawLine(x + deslocamento, y, x + deslocamento + metade, y + metade)
    pintor.end()
    _textura = pixmap
    return _textura


def gradiente_aro(raio):
    """Reflexo vertical do aro escovado, do claro no topo ao escuro embaixo."""
    gradiente = QLinearGradient(QPointF(0, -raio), QPointF(0, raio))
    gradiente.setColorAt(0.00, ARO_BRILHO)
    gradiente.setColorAt(0.16, ARO_CLARO)
    gradiente.setColorAt(0.42, ARO_MEDIO)
    gradiente.setColorAt(0.58, ARO_ESCURO)
    gradiente.setColorAt(0.80, ARO_MEDIO)
    gradiente.setColorAt(1.00, ARO_CLARO)
    return gradiente


def cor_da_faixa(faixa_atual):
    from velocimetro.escala import Faixa

    if faixa_atual is Faixa.PERIGO:
        return PERIGO
    if faixa_atual is Faixa.ATENCAO:
        return ATENCAO
    return AMBAR
