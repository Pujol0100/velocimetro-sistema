"""Ponto de entrada: python -m velocimetro"""

import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from velocimetro.janela import JanelaVelocimetro


def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName("Velocímetro de Sistema")
    # Ocultar pela bandeja nao pode encerrar o programa.
    app.setQuitOnLastWindowClosed(False)
    janela = JanelaVelocimetro()
    janela.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
