"""A janela flutuante: carcaca dos tres mostradores, arrasto, bandeja, timers."""

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import (
    QAction,
    QBrush,
    QColor,
    QGuiApplication,
    QIcon,
    QLinearGradient,
    QPainter,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import QMenu, QSystemTrayIcon, QWidget

from velocimetro import config as configuracao
from velocimetro import tema
from velocimetro.gauge import Mostrador
from velocimetro.metricas import LeitorDeMetricas

DIAMETRO_GRANDE = 200
DIAMETRO_PEQUENO = 130
MARGEM = 14
ESPACO = 10
RAIO_CARCACA = 22

INTERVALO_LEITURA_MS = 1000
INTERVALO_QUADRO_MS = 33
ESCALA_COMPACTA = 0.68
ESCALA_NORMAL = 1.0
PASSO_OPACIDADE = 0.08
MARGEM_TELA = 24


class JanelaVelocimetro(QWidget):
    def __init__(self):
        super().__init__()
        self.config = configuracao.carregar()
        self._leitor = LeitorDeMetricas(teto_inicial_mbps=self.config.teto_disco_mbps)
        self._leitor.ler()  # primeira leitura de CPU do psutil sempre volta zero

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowTitle("Velocímetro de Sistema")

        self.cpu = Mostrador("CPU", DIAMETRO_GRANDE, principal=True, parent=self)
        self.memoria = Mostrador("MEM", DIAMETRO_PEQUENO, parent=self)
        self.disco = Mostrador("DISCO", DIAMETRO_PEQUENO, parent=self)

        self._arrasto = None
        self._sempre_na_frente = True
        self.setWindowOpacity(self.config.opacidade)
        self._aplicar_escala(self.config.escala)
        self._posicionar(self.config.posicao)

        self._relogio_leitura = QTimer(self)
        self._relogio_leitura.timeout.connect(self._atualizar_metricas)
        self._relogio_leitura.start(INTERVALO_LEITURA_MS)

        self._relogio_quadro = QTimer(self)
        self._relogio_quadro.timeout.connect(self._avancar_ponteiros)

        self._bandeja = self._montar_bandeja()
        self._atualizar_metricas()

    # ------------------------------------------------------------- geometria

    def _aplicar_escala(self, escala):
        self._escala = escala
        grande = int(DIAMETRO_GRANDE * escala)
        pequeno = int(DIAMETRO_PEQUENO * escala)
        margem = int(MARGEM * escala)
        espaco = int(ESPACO * escala)

        largura = max(grande, pequeno * 2 + espaco) + margem * 2
        altura = margem * 2 + grande + espaco + pequeno
        self.setFixedSize(largura, altura)

        self.cpu.setFixedSize(grande, grande)
        self.memoria.setFixedSize(pequeno, pequeno)
        self.disco.setFixedSize(pequeno, pequeno)

        self.cpu.move((largura - grande) // 2, margem)
        base = margem + grande + espaco
        centro = largura // 2
        self.memoria.move(centro - espaco // 2 - pequeno, base)
        self.disco.move(centro + espaco // 2, base)
        self.update()

    def _posicionar(self, posicao):
        """Sem posicao gravada, nasce no canto superior direito do monitor
        principal. Com varios monitores, self.screen() pode apontar para um
        monitor lateral antes da janela aparecer, e o painel nasceria fora de
        vista."""
        if posicao and self._visivel_em_alguma_tela(posicao):
            self.move(posicao[0], posicao[1])
            return
        tela = QGuiApplication.primaryScreen().availableGeometry()
        self.move(
            tela.right() - self.width() - MARGEM_TELA,
            tela.top() + MARGEM_TELA,
        )

    def _visivel_em_alguma_tela(self, posicao):
        canto = QRectF(posicao[0], posicao[1], self.width(), self.height())
        return any(
            QRectF(t.availableGeometry()).intersects(canto)
            for t in QGuiApplication.screens()
        )

    # --------------------------------------------------------------- métricas

    def _atualizar_metricas(self):
        leitura = self._leitor.ler()
        self.cpu.definir_valor(leitura.cpu)
        self.memoria.definir_valor(leitura.memoria)
        self.disco.definir_valor(leitura.disco)
        self.disco.legenda = self._formatar_vazao(leitura.disco_mbps)
        if not self._relogio_quadro.isActive():
            self._relogio_quadro.start(INTERVALO_QUADRO_MS)

    def _formatar_vazao(self, mbps):
        if mbps is None:
            return "sem leitura"
        if mbps >= 1024:
            return f"{mbps / 1024:.1f} GB/s"
        if mbps >= 10:
            return f"{mbps:.0f} MB/s"
        return f"{mbps:.1f} MB/s"

    def _avancar_ponteiros(self):
        segundos = INTERVALO_QUADRO_MS / 1000.0
        em_movimento = [m.avancar(segundos) for m in (self.cpu, self.memoria, self.disco)]
        if not any(em_movimento):
            # Ponteiros assentados: parar de redesenhar para nao consumir CPU.
            self._relogio_quadro.stop()

    # ---------------------------------------------------------------- pintura

    def paintEvent(self, evento):
        pintor = QPainter(self)
        pintor.setRenderHint(QPainter.RenderHint.Antialiasing)
        caixa = QRectF(0.5, 0.5, self.width() - 1, self.height() - 1)
        raio = RAIO_CARCACA * self._escala
        fundo = QLinearGradient(QPointF(0, 0), QPointF(0, self.height()))
        fundo.setColorAt(0.0, tema.CARCACA_TOPO)
        fundo.setColorAt(1.0, tema.CARCACA_BASE)
        pintor.setPen(Qt.PenStyle.NoPen)
        pintor.setBrush(QBrush(fundo))
        pintor.drawRoundedRect(caixa, raio, raio)
        pintor.setPen(QPen(tema.CARCACA_BORDA, 1.0))
        pintor.setBrush(Qt.BrushStyle.NoBrush)
        pintor.drawRoundedRect(caixa, raio, raio)
        pintor.setPen(QPen(tema.CARCACA_BRILHO, 1.0))
        pintor.drawLine(
            QPointF(raio, 1.5), QPointF(self.width() - raio, 1.5)
        )
        pintor.end()

    # ---------------------------------------------------------------- entrada

    def mousePressEvent(self, evento):
        if evento.button() == Qt.MouseButton.LeftButton:
            self._arrasto = evento.globalPosition().toPoint() - self.frameGeometry().topLeft()
            evento.accept()

    def mouseMoveEvent(self, evento):
        if self._arrasto and evento.buttons() & Qt.MouseButton.LeftButton:
            self.move(evento.globalPosition().toPoint() - self._arrasto)
            evento.accept()

    def mouseReleaseEvent(self, evento):
        self._arrasto = None
        self._gravar_estado()

    def mouseDoubleClickEvent(self, evento):
        self._alternar_compacto()

    def wheelEvent(self, evento):
        passos = evento.angleDelta().y() / 120.0
        nova = self.windowOpacity() + passos * PASSO_OPACIDADE
        self.setWindowOpacity(
            max(configuracao.OPACIDADE_MINIMA, min(configuracao.OPACIDADE_MAXIMA, nova))
        )
        self._gravar_estado()

    def contextMenuEvent(self, evento):
        self._menu().exec(evento.globalPos())

    def closeEvent(self, evento):
        self._gravar_estado()
        super().closeEvent(evento)

    # ------------------------------------------------------------------ menus

    def _menu(self):
        menu = QMenu(self)
        frente = QAction("Sempre na frente", menu, checkable=True)
        frente.setChecked(self._sempre_na_frente)
        frente.triggered.connect(self._alternar_frente)
        menu.addAction(frente)

        compacto = QAction("Tamanho compacto", menu, checkable=True)
        compacto.setChecked(self._escala < ESCALA_NORMAL)
        compacto.triggered.connect(self._alternar_compacto)
        menu.addAction(compacto)

        menu.addSeparator()
        sair = QAction("Fechar", menu)
        sair.triggered.connect(self._sair)
        menu.addAction(sair)
        return menu

    def _montar_bandeja(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return None
        bandeja = QSystemTrayIcon(self._icone(), self)
        bandeja.setToolTip("Velocímetro de Sistema")
        menu = QMenu()
        mostrar = QAction("Mostrar / ocultar", menu)
        mostrar.triggered.connect(self._alternar_visibilidade)
        menu.addAction(mostrar)
        menu.addSeparator()
        sair = QAction("Fechar", menu)
        sair.triggered.connect(self._sair)
        menu.addAction(sair)
        bandeja.setContextMenu(menu)
        bandeja.activated.connect(self._bandeja_clicada)
        bandeja.show()
        return bandeja

    def _icone(self):
        lado = 64
        pixmap = QPixmap(lado, lado)
        pixmap.fill(QColor(0, 0, 0, 0))
        pintor = QPainter(pixmap)
        pintor.setRenderHint(QPainter.RenderHint.Antialiasing)
        caixa = QRectF(3, 3, lado - 6, lado - 6)
        pintor.setPen(QPen(tema.ARO_CLARO, 3.5))
        pintor.setBrush(QBrush(QColor(16, 17, 20)))
        pintor.drawEllipse(caixa)
        pintor.setBrush(Qt.BrushStyle.NoBrush)
        pintor.setPen(QPen(tema.AMBAR, 5.0))
        pintor.drawArc(QRectF(10, 10, lado - 20, lado - 20), 210 * 16, -150 * 16)
        pintor.setPen(QPen(QColor(245, 247, 250), 3.5))
        pintor.drawLine(QPointF(lado / 2, lado / 2), QPointF(lado * 0.74, lado * 0.30))
        pintor.end()
        return QIcon(pixmap)

    def _bandeja_clicada(self, motivo):
        if motivo == QSystemTrayIcon.ActivationReason.Trigger:
            self._alternar_visibilidade()

    def _alternar_visibilidade(self):
        self.hide() if self.isVisible() else self.show()

    def _alternar_frente(self):
        self._sempre_na_frente = not self._sempre_na_frente
        # Recolocar a flag exige reexibir a janela no Windows.
        self.setWindowFlag(
            Qt.WindowType.WindowStaysOnTopHint, self._sempre_na_frente
        )
        self.show()

    def _alternar_compacto(self):
        alvo = ESCALA_COMPACTA if self._escala >= ESCALA_NORMAL else ESCALA_NORMAL
        self._aplicar_escala(alvo)
        self._gravar_estado()

    def _sair(self):
        self._gravar_estado()
        if self._bandeja:
            self._bandeja.hide()
        from PySide6.QtWidgets import QApplication

        QApplication.instance().quit()

    def _gravar_estado(self):
        configuracao.salvar(
            configuracao.Config(
                posicao=(self.x(), self.y()),
                escala=self._escala,
                opacidade=self.windowOpacity(),
                teto_disco_mbps=self._leitor.teto_mbps,
            )
        )
