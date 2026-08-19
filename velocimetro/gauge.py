"""O mostrador: um instrumento redondo desenhado com QPainter.

Todo o desenho acontece num sistema de coordenadas onde o raio do aro vale 100,
com a origem no centro. Assim o mesmo codigo serve para o mostrador grande e
para os pequenos, e as medidas ficam legiveis como fracoes do raio.
"""

import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QConicalGradient,
    QFont,
    QFontMetricsF,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPolygonF,
    QRadialGradient,
)
from PySide6.QtWidgets import QWidget

from velocimetro import tema
from velocimetro.escala import (
    ANGULO_INICIAL,
    LIMITE_PERIGO,
    Suavizador,
    faixa,
    percentual_para_angulo,
)

RAIO = 100.0

RAIO_FACE = 91.0
RAIO_TRILHA = 86.0
LARGURA_TRILHA = 6.5
RAIO_TRACO_EXTERNO = 80.0
RAIO_TRACO_MAIOR = 67.0
RAIO_TRACO_MENOR = 74.0
RAIO_NUMERO = 56.0
COMPRIMENTO_PONTEIRO = 63.0
CAUDA_PONTEIRO = 16.0
RAIO_CUBO = 9.5

BASE_VALOR = 56.0
BASE_RODAPE = 78.0


def _ponto(angulo_graus, raio):
    radianos = math.radians(angulo_graus)
    return QPointF(raio * math.cos(radianos), -raio * math.sin(radianos))


def _retangulo(raio):
    return QRectF(-raio, -raio, raio * 2, raio * 2)


class Mostrador(QWidget):
    """Um instrumento. Recebe o valor em 0-100 e move o ponteiro suavemente."""

    def __init__(self, rotulo, diametro, principal=False, parent=None):
        super().__init__(parent)
        self.rotulo = rotulo
        self.principal = principal
        self.legenda = ""
        self._suave = Suavizador()
        self._indisponivel = False
        self.setFixedSize(diametro, diametro)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def definir_valor(self, valor):
        self._indisponivel = valor is None
        self._suave.alvo = 0.0 if valor is None else float(valor)

    def avancar(self, segundos):
        """Move o ponteiro um quadro. Devolve True se ainda esta em movimento."""
        if self._suave.em_repouso:
            return False
        self._suave.passo(segundos)
        self.update()
        return True

    # ------------------------------------------------------------------ pintura

    def paintEvent(self, evento):
        pintor = QPainter(self)
        pintor.setRenderHints(
            QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing
        )
        lado = min(self.width(), self.height())
        fator = (lado / 2.0) / RAIO
        pintor.translate(self.width() / 2.0, self.height() / 2.0)
        pintor.scale(fator, fator)

        valor = max(0.0, min(100.0, self._suave.atual))
        cor = tema.cor_da_faixa(faixa(valor))

        self._aro(pintor)
        self._face(pintor)
        self._trilha(pintor)
        self._arco_de_valor(pintor, valor, cor)
        self._tracos(pintor)
        self._numeros(pintor)
        self._textos(pintor, cor)
        self._ponteiro(pintor, valor, cor)
        self._cubo(pintor)
        self._reflexo(pintor)
        pintor.end()

    def _aro(self, pintor):
        pintor.setPen(Qt.PenStyle.NoPen)
        pintor.setBrush(QBrush(tema.gradiente_aro(RAIO)))
        pintor.drawEllipse(_retangulo(RAIO))
        pintor.setBrush(QBrush(QColor(14, 15, 17)))
        pintor.drawEllipse(_retangulo(RAIO_FACE + 1.6))

    def _face(self, pintor):
        gradiente = QRadialGradient(QPointF(0, -22), RAIO_FACE * 1.5)
        gradiente.setColorAt(0.0, tema.FUNDO_MOSTRADOR_CENTRO)
        gradiente.setColorAt(1.0, tema.FUNDO_MOSTRADOR_BORDA)
        pintor.setPen(Qt.PenStyle.NoPen)
        pintor.setBrush(QBrush(gradiente))
        pintor.drawEllipse(_retangulo(RAIO_FACE))

        caminho = QPainterPath()
        caminho.addEllipse(_retangulo(RAIO_FACE))
        pintor.save()
        pintor.setClipPath(caminho)
        pintor.setBrush(QBrush(tema.textura_carbono()))
        pintor.drawRect(_retangulo(RAIO_FACE))

        vinheta = QRadialGradient(QPointF(0, 0), RAIO_FACE)
        vinheta.setColorAt(0.55, QColor(0, 0, 0, 0))
        vinheta.setColorAt(1.0, tema.VIGNETA)
        pintor.setBrush(QBrush(vinheta))
        pintor.drawEllipse(_retangulo(RAIO_FACE))
        pintor.restore()

    def _trilha(self, pintor):
        """A pista da escala, com a zona vermelha embutida a partir de 85%."""
        caneta = QPen(QColor(255, 255, 255, 16), LARGURA_TRILHA)
        caneta.setCapStyle(Qt.PenCapStyle.FlatCap)
        pintor.setBrush(Qt.BrushStyle.NoBrush)
        pintor.setPen(caneta)
        pintor.drawArc(
            _retangulo(RAIO_TRILHA),
            int(ANGULO_INICIAL * 16),
            int((percentual_para_angulo(100) - ANGULO_INICIAL) * 16),
        )

        inicio = percentual_para_angulo(LIMITE_PERIGO)
        caneta.setColor(tema.ZONA_PERIGO)
        pintor.setPen(caneta)
        pintor.drawArc(
            _retangulo(RAIO_TRILHA),
            int(inicio * 16),
            int((percentual_para_angulo(100) - inicio) * 16),
        )

    def _gradiente_do_arco(self, alfa):
        """Ambar no inicio da escala, vermelho no fim, como a escala de um carro.

        O gradiente conico nasce no angulo de 100% e caminha no sentido
        anti-horario, que e o sentido em que a escala decresce.
        """
        gradiente = QConicalGradient(QPointF(0, 0), percentual_para_angulo(100))
        for posicao, base in (
            (0.000, tema.PERIGO),
            (0.100, QColor(250, 108, 40)),
            (0.267, tema.ATENCAO),
            (0.667, tema.AMBAR),
        ):
            cor = QColor(base)
            cor.setAlpha(alfa)
            gradiente.setColorAt(posicao, cor)
        return gradiente

    def _arco_de_valor(self, pintor, valor, cor):
        if valor <= 0.2 or self._indisponivel:
            return
        varredura = int((percentual_para_angulo(valor) - ANGULO_INICIAL) * 16)
        inicio = int(ANGULO_INICIAL * 16)
        pintor.setBrush(Qt.BrushStyle.NoBrush)
        # Tres passadas de fora para dentro simulam o halo do mostrador aceso.
        for largura, alfa in (
            (LARGURA_TRILHA * 2.4, 30),
            (LARGURA_TRILHA * 1.5, 62),
            (LARGURA_TRILHA, 255),
        ):
            caneta = QPen(QBrush(self._gradiente_do_arco(alfa)), largura)
            caneta.setCapStyle(Qt.PenCapStyle.FlatCap)
            pintor.setPen(caneta)
            pintor.drawArc(_retangulo(RAIO_TRILHA), inicio, varredura)

    def _tracos(self, pintor):
        for passo in range(0, 101, 5):
            maior = passo % 20 == 0
            angulo = percentual_para_angulo(passo)
            interno = RAIO_TRACO_MAIOR if maior else RAIO_TRACO_MENOR
            if passo >= LIMITE_PERIGO:
                cor = QColor(tema.PERIGO)
                cor.setAlpha(235 if maior else 130)
            else:
                cor = tema.TRACO_MAIOR if maior else tema.TRACO_MENOR
            caneta = QPen(cor, 2.8 if maior else 1.2)
            caneta.setCapStyle(Qt.PenCapStyle.FlatCap)
            pintor.setPen(caneta)
            pintor.drawLine(_ponto(angulo, interno), _ponto(angulo, RAIO_TRACO_EXTERNO))

    def _numeros(self, pintor):
        pintor.setPen(QPen(tema.NUMERO))
        pintor.setFont(tema.fonte(15 if self.principal else 16, QFont.Weight.Medium))
        for passo in range(0, 101, 20):
            centro = _ponto(percentual_para_angulo(passo), RAIO_NUMERO)
            caixa = QRectF(centro.x() - 16, centro.y() - 11, 32, 22)
            pintor.drawText(caixa, Qt.AlignmentFlag.AlignCenter, str(passo))

    def _textos(self, pintor, cor):
        """Valor grande e, abaixo dele, a legenda. O topo do mostrador pertence
        aos numeros da escala, e o centro ao cubo e a cauda do ponteiro: a
        abertura de baixo e o unico lugar livre para texto."""
        texto = "--" if self._indisponivel else f"{round(self._suave.atual):.0f}"
        fonte_valor = tema.fonte(44 if self.principal else 40, QFont.Weight.Bold)
        fonte_unidade = tema.fonte(16 if self.principal else 15, QFont.Weight.DemiBold)
        metrica_valor = QFontMetricsF(fonte_valor)
        metrica_unidade = QFontMetricsF(fonte_unidade)

        largura_valor = metrica_valor.horizontalAdvance(texto)
        largura_unidade = metrica_unidade.horizontalAdvance("%")
        folga = 4.0
        esquerda = -(largura_valor + folga + largura_unidade) / 2.0
        base = BASE_VALOR if self.principal else BASE_VALOR - 2.0

        pintor.setPen(QPen(tema.LEGENDA if self._indisponivel else tema.VALOR))
        pintor.setFont(fonte_valor)
        pintor.drawText(QPointF(esquerda, base), texto)
        pintor.setPen(QPen(tema.LEGENDA if self._indisponivel else cor))
        pintor.setFont(fonte_unidade)
        pintor.drawText(
            QPointF(
                esquerda + largura_valor + folga,
                base - metrica_valor.capHeight() * 0.48,
            ),
            "%",
        )

        rodape = f"{self.rotulo.upper()}   {self.legenda}" if self.legenda else self.rotulo.upper()
        pintor.setPen(QPen(tema.ROTULO))
        pintor.setFont(
            tema.fonte(
                12 if self.legenda else 13, QFont.Weight.DemiBold, espacamento=1.8
            )
        )
        pintor.drawText(
            QRectF(-88, BASE_RODAPE - 16, 176, 20),
            Qt.AlignmentFlag.AlignCenter,
            rodape,
        )

    def _ponteiro(self, pintor, valor, cor):
        angulo = percentual_para_angulo(0.0 if self._indisponivel else valor)
        agulha = QPolygonF(
            [
                QPointF(COMPRIMENTO_PONTEIRO, 0.0),
                QPointF(COMPRIMENTO_PONTEIRO * 0.24, -2.4),
                QPointF(-CAUDA_PONTEIRO, -4.2),
                QPointF(-CAUDA_PONTEIRO, 4.2),
                QPointF(COMPRIMENTO_PONTEIRO * 0.24, 2.4),
            ]
        )

        pintor.save()
        pintor.translate(1.6, 2.8)
        pintor.rotate(-angulo)
        pintor.setPen(Qt.PenStyle.NoPen)
        pintor.setBrush(QBrush(tema.SOMBRA_PONTEIRO))
        pintor.drawPolygon(agulha)
        pintor.restore()

        pintor.save()
        pintor.rotate(-angulo)
        halo = QLinearGradient(QPointF(-CAUDA_PONTEIRO, 0), QPointF(COMPRIMENTO_PONTEIRO, 0))
        halo.setColorAt(0.0, QColor(cor.red(), cor.green(), cor.blue(), 200))
        halo.setColorAt(0.7, cor)
        halo.setColorAt(1.0, tema.AMBAR_CLARO if cor is tema.AMBAR else cor.lighter(140))
        pintor.setPen(Qt.PenStyle.NoPen)
        pintor.setBrush(QBrush(halo))
        pintor.drawPolygon(agulha)

        nucleo = QColor(255, 255, 255, 120)
        caneta = QPen(nucleo, 0.9)
        caneta.setCapStyle(Qt.PenCapStyle.RoundCap)
        pintor.setPen(caneta)
        pintor.drawLine(
            QPointF(-CAUDA_PONTEIRO * 0.5, 0.0),
            QPointF(COMPRIMENTO_PONTEIRO * 0.94, 0.0),
        )
        pintor.restore()

        if not self._indisponivel:
            self._bloom(pintor, _ponto(angulo, COMPRIMENTO_PONTEIRO * 0.93), cor)

    def _bloom(self, pintor, centro, cor):
        """Halo difuso na ponta do ponteiro, como uma agulha retroiluminada."""
        gradiente = QRadialGradient(centro, 13.0)
        aceso = QColor(cor)
        aceso.setAlpha(96)
        gradiente.setColorAt(0.0, aceso)
        gradiente.setColorAt(1.0, QColor(cor.red(), cor.green(), cor.blue(), 0))
        pintor.setPen(Qt.PenStyle.NoPen)
        pintor.setBrush(QBrush(gradiente))
        pintor.drawEllipse(centro, 13.0, 13.0)

    def _cubo(self, pintor):
        gradiente = QRadialGradient(QPointF(-RAIO_CUBO * 0.4, -RAIO_CUBO * 0.5), RAIO_CUBO * 2.2)
        gradiente.setColorAt(0.0, tema.CUBO_CLARO)
        gradiente.setColorAt(1.0, tema.CUBO_ESCURO)
        pintor.setPen(QPen(QColor(0, 0, 0, 110), 1.0))
        pintor.setBrush(QBrush(gradiente))
        pintor.drawEllipse(_retangulo(RAIO_CUBO))
        pintor.setPen(Qt.PenStyle.NoPen)
        pintor.setBrush(QBrush(QColor(18, 19, 22)))
        pintor.drawEllipse(_retangulo(RAIO_CUBO * 0.44))

    def _reflexo(self, pintor):
        """O brilho do vidro, por ultimo, para o instrumento parecer coberto."""
        caminho = QPainterPath()
        caminho.addEllipse(_retangulo(RAIO_FACE))
        pintor.save()
        pintor.setClipPath(caminho)
        gradiente = QLinearGradient(QPointF(0, -RAIO_FACE), QPointF(0, 24))
        gradiente.setColorAt(0.0, QColor(255, 255, 255, 30))
        gradiente.setColorAt(1.0, QColor(255, 255, 255, 0))
        pintor.setPen(Qt.PenStyle.NoPen)
        pintor.setBrush(QBrush(gradiente))
        pintor.drawEllipse(QRectF(-RAIO_FACE * 0.94, -RAIO_FACE * 1.02, RAIO_FACE * 1.88, RAIO_FACE * 1.3))
        pintor.restore()
