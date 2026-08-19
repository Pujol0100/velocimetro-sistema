# Velocímetro de Sistema — design

Data: 19/08/2026

## Objetivo

Um medidor flutuante permanente na área de trabalho do Windows, com acabamento
de painel de carro esportivo, mostrando processador, memória e atividade de
disco em tempo real.

## Escolhas do usuário

| Decisão | Escolha |
|---|---|
| Arranjo | Cluster: mostrador grande de CPU, dois menores para memória e disco |
| Acabamento | Carbono e âmbar |
| Sempre na frente | Sim |
| Lembrar posição | Sim |
| Ícone na bandeja | Sim |
| Iniciar com o Windows | Sim, por script separado e opcional |
| Métrica de disco | Atividade (não espaço ocupado) |

## Restrição descoberta na máquina alvo

Os conjuntos de contadores de desempenho `PhysicalDisk`, `LogicalDisk`,
`Memory` e `Processor` não existem neste Windows 11 (207 conjuntos instalados,
nenhum dos quatro). Os campos `read_time` e `write_time` do psutil retornam
zero em consequência disso.

"Percentual de tempo ativo do disco", como o Gerenciador de Tarefas mostra, é
portanto inalcançável sem reparar o registro de contadores (`lodctr /R`, exige
administrador, fora do escopo).

**Decisão:** o mostrador de disco mede vazão, não tempo ocupado. A agulha marca
a taxa instantânea de leitura mais escrita contra um teto auto-calibrado; o
valor absoluto em MB/s aparece como legenda. Isso preserva a intenção original
(uma agulha que reage ao trabalho do disco) sem inventar um número.

## Arquitetura

Quatro camadas, com dependência apenas para baixo:

```
__main__.py          ponto de entrada
    |
janela.py            janela sem borda, bandeja, arrasto, persistência
    |
gauge.py             widget que desenha um mostrador (QPainter)
    |
escala.py  tema.py   funções puras: ângulo, cor, suavização, paleta
metricas.py          leitura do sistema
config.py            leitura e gravação do estado da janela
```

`escala.py`, `metricas.py` e `config.py` não importam nada de Qt. São
testáveis sem abrir janela, e é onde ficam os testes automatizados.

### metricas.py

`LeitorDeMetricas.ler()` devolve `Leitura(cpu, memoria, disco, disco_mbps)`,
com os três primeiros em 0–100 e `None` quando a fonte falhou.

A fonte do sistema é injetável (`FonteDeSistema`), o que permite testar o
cálculo de vazão e a auto-calibração do teto com valores determinísticos.

Auto-calibração do teto de disco:

- Piso: 200 MB/s. O teto nunca cai abaixo disso.
- Quando a taxa medida excede o teto, o teto passa a ser a taxa medida.
- A cada leitura o teto decai 0,5% em direção ao piso, para que um pico
  isolado não achate a escala para sempre.

### escala.py

- `percentual_para_angulo(p)`: 0% em 210°, 100% em -30°, varredura de 240° no
  sentido horário. Valores fora de 0–100 são fixados nos extremos.
- `faixa(p)`: `NORMAL` até 60, `ATENCAO` até 85, `PERIGO` acima.
- `Suavizador`: persegue o alvo com mola amortecida, gerando a ultrapassagem
  leve de um ponteiro mecânico. Ultrapassagem limitada a 8% do salto.

### config.py

Estado em `%LOCALAPPDATA%/VelocimetroSistema/config.json`: posição, escala,
opacidade, teto de disco aprendido. Arquivo ausente, ilegível ou corrompido
resulta nos padrões, sem erro visível.

## Tratamento de erro

Só duas fronteiras têm `try`: a leitura do psutil e a leitura do arquivo de
configuração. Uma métrica que falhe mostra agulha em zero e traço no lugar do
número. Todo o resto propaga.

## Interação

| Ação | Efeito |
|---|---|
| Arrastar com botão esquerdo | Move o conjunto |
| Roda do mouse | Opacidade entre 40% e 100% |
| Duplo clique | Alterna tamanho normal e compacto |
| Botão direito | Menu: fixar na frente, opacidade, fechar |
| Ícone na bandeja | Mostrar, ocultar, fechar |

Leitura a cada 1 segundo. Redesenho a 30 quadros por segundo apenas enquanto
alguma agulha está em movimento.

## Fora de escopo

Histórico, gráficos de linha, temperatura, rede, GPU, múltiplos discos
separados, reparo dos contadores de desempenho do Windows.
