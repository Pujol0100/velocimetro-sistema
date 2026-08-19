"""Estado da janela gravado entre sessoes: posicao, tamanho, opacidade, teto.

Arquivo ausente, ilegivel ou corrompido resulta nos padroes, sem erro visivel.
Perder a posicao da janela nao justifica derrubar o programa.
"""

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path

OPACIDADE_MINIMA = 0.4
OPACIDADE_MAXIMA = 1.0
ESCALA_MINIMA = 0.6
ESCALA_MAXIMA = 2.5
TETO_DISCO_MINIMO = 200.0
TETO_DISCO_MAXIMO = 20000.0


@dataclass(frozen=True)
class Config:
    posicao: tuple | None = None
    escala: float = 1.0
    opacidade: float = 1.0
    teto_disco_mbps: float = 200.0


def caminho_padrao():
    raiz = os.environ.get("LOCALAPPDATA") or str(Path.home())
    return Path(raiz) / "VelocimetroSistema" / "config.json"


def _numero(bruto, padrao, minimo, maximo):
    if isinstance(bruto, bool) or not isinstance(bruto, (int, float)):
        return padrao
    return max(minimo, min(maximo, float(bruto)))


def _posicao(bruto):
    if not isinstance(bruto, (list, tuple)) or len(bruto) != 2:
        return None
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) for v in bruto):
        return None
    return (int(bruto[0]), int(bruto[1]))


def carregar(caminho=None):
    caminho = Path(caminho) if caminho else caminho_padrao()
    padrao = Config()
    try:
        dados = json.loads(caminho.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return padrao
    if not isinstance(dados, dict):
        return padrao
    return Config(
        posicao=_posicao(dados.get("posicao")),
        escala=_numero(dados.get("escala"), padrao.escala, ESCALA_MINIMA, ESCALA_MAXIMA),
        opacidade=_numero(
            dados.get("opacidade"), padrao.opacidade, OPACIDADE_MINIMA, OPACIDADE_MAXIMA
        ),
        teto_disco_mbps=_numero(
            dados.get("teto_disco_mbps"),
            padrao.teto_disco_mbps,
            TETO_DISCO_MINIMO,
            TETO_DISCO_MAXIMO,
        ),
    )


def salvar(config, caminho=None):
    caminho = Path(caminho) if caminho else caminho_padrao()
    try:
        caminho.parent.mkdir(parents=True, exist_ok=True)
        dados = asdict(config)
        dados["posicao"] = list(config.posicao) if config.posicao else None
        caminho.write_text(
            json.dumps(dados, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    except OSError:
        pass
