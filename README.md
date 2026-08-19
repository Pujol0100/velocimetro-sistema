# Velocímetro de Sistema

Um painel flutuante para a área de trabalho do Windows, com acabamento de
instrumento automotivo, mostrando processador, memória e atividade de disco em
tempo real.

Três mostradores: um grande para o processador e dois menores para memória e
disco. O ponteiro persegue o valor como uma agulha mecânica, com uma leve
ultrapassagem antes de assentar. A escala acende de âmbar a vermelho conforme
sobe, e a zona vermelha começa em 85%.

---

## Como instalar e abrir

Os passos abaixo estão na ordem. O passo 1 é o único que você roda no
PowerShell; depois disso, é clique duplo.

### Passo 1 — instalar as bibliotecas

**Onde:** no seu PowerShell do Windows.

Abra a pasta do projeto no Explorador de Arquivos, clique com o botão direito
num espaço vazio e escolha **Abrir no Terminal**. Isso já deixa o PowerShell na
pasta certa.

Depois cole a linha abaixo:

```powershell
.\instalar.ps1
```

**O que você deve ver:** algumas linhas de progresso e, no fim,
`Instalacao concluida.` em verde, junto com as versões do PySide6 e do psutil.

**Se vier diferente:** se aparecer uma mensagem sobre execução de scripts
desabilitada, rode a linha abaixo uma vez e repita o passo 1.

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Se aparecer `Python nao foi encontrado no PATH`, instale o Python de
[python.org](https://python.org), marcando a caixa **Add Python to PATH** durante
a instalação, e repita o passo 1.

Este passo baixa cerca de 90 MB e leva de 1 a 3 minutos. Ele não altera nada
fora da pasta do projeto.

### Passo 2 — abrir o velocímetro

**Onde:** no Explorador de Arquivos do Windows.

Abra a pasta do projeto e dê **clique duplo em `Velocimetro.bat`**.

**O que você deve ver:** o painel com três mostradores aparece no canto superior
direito da tela, os ponteiros saem do zero e assentam nos valores atuais em
menos de um segundo. Um ícone redondo aparece perto do relógio do Windows.

**Se vier diferente:** se uma janela preta de console ficar aberta, algo falhou
no passo 1 — a mensagem dentro dela diz o quê.

### Passo 3 — abrir junto com o Windows (opcional)

**Onde:** no seu PowerShell, na mesma pasta do passo 1.

Só faça este passo depois de usar o medidor um pouco e decidir que quer ele
sempre. Cole:

```powershell
.\ativar-inicio-automatico.ps1
```

**O que você deve ver:** `Pronto. O velocimetro vai abrir junto com o Windows.`
em verde, e o caminho do atalho criado.

**Para desfazer:** cole a linha abaixo. Ela remove só o atalho; o programa
continua instalado.

```powershell
.\ativar-inicio-automatico.ps1 -Remover
```

---

## Como usar

| O que fazer | O que acontece |
|---|---|
| Arrastar com o botão esquerdo | Move o painel pela tela |
| Girar a roda do mouse | Ajusta a transparência, entre 40% e 100% |
| Clique duplo | Alterna entre tamanho normal e compacto |
| Botão direito | Menu com "Sempre na frente", "Tamanho compacto" e "Fechar" |
| Clique no ícone perto do relógio | Oculta ou mostra o painel |

A posição, o tamanho e a transparência são gravados quando você solta o mouse, e
voltam iguais na próxima vez que abrir.

---

## O que cada mostrador mede

**CPU** — percentual de uso do processador, somando todos os núcleos. É o mesmo
número que o Gerenciador de Tarefas mostra na coluna CPU.

**MEM** — percentual da memória física em uso.

**DISCO** — a taxa de leitura mais escrita do disco neste instante, comparada a
um teto que se ajusta ao seu equipamento. O valor absoluto em MB/s aparece
embaixo, ao lado da palavra DISCO.

Sobre o disco, uma explicação honesta: o número que o Gerenciador de Tarefas
mostra na coluna "Disco" é o percentual de *tempo ativo*, e ele vem dos
contadores de desempenho `PhysicalDisk` do Windows. Nesta máquina esses
contadores não existem — o registro de contadores de desempenho está incompleto,
e por consequência os campos `read_time` e `write_time` do psutil retornam zero.
Então o mostrador mede **vazão**, não tempo ativo: quantos megabytes por segundo
estão passando. O ponteiro reage ao trabalho do disco do mesmo jeito, e o número
verdadeiro em MB/s está sempre na tela ao lado da porcentagem.

O teto da escala começa em 200 MB/s, sobe sozinho quando você excede esse valor,
e decai devagar de volta. Ou seja: depois de alguns dias de uso, o fundo de
escala corresponde ao que o seu disco realmente entrega.

---

## Rodar os testes

**Onde:** no seu PowerShell, na pasta do projeto.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

**O que você deve ver:** `47 passed`.

Os testes cobrem as três camadas que não dependem de tela: o cálculo do ângulo
do ponteiro e a suavização (`escala.py`), a leitura e a auto-calibração do teto
de disco (`metricas.py`), e a gravação e leitura do arquivo de configuração
(`config.py`). O desenho em si não tem teste automatizado — quem valida isso é o
olho, olhando o painel na tela.

---

## Estrutura

| Arquivo | O que faz |
|---|---|
| `velocimetro/metricas.py` | Lê CPU, memória e disco e devolve três números de 0 a 100 |
| `velocimetro/escala.py` | Converte porcentagem em ângulo, decide a faixa de cor, suaviza o ponteiro |
| `velocimetro/tema.py` | A paleta carbono e âmbar, a tipografia e a textura de fibra de carbono |
| `velocimetro/gauge.py` | Desenha um mostrador com QPainter |
| `velocimetro/janela.py` | Janela sem borda, arrasto, bandeja, persistência |
| `velocimetro/config.py` | Grava e lê o estado da janela |
| `velocimetro/__main__.py` | Ponto de entrada |
| `docs/` | O documento de design, com as decisões e o motivo de cada uma |

O estado fica em `%LOCALAPPDATA%\VelocimetroSistema\config.json`. Apagar esse
arquivo devolve o painel aos padrões.

## Requisitos

Windows 10 ou 11, Python 3.10 ou mais novo.

Consumo medido, não estimado: **61 MB de memória** e **5,3 segundos de CPU numa
janela de 90 segundos**, o que dá 5,9% de um núcleo ou 0,49% de um processador de
12 threads.

O que segura esse número: aro, face, textura de carbono, escala e vidro são
desenhados uma única vez e guardados como imagem, refeita só quando o tamanho
muda; a cada quadro só o arco, a agulha, o cubo e o número são redesenhados. O
redesenho acontece a 25 quadros por segundo e apenas quando o ponteiro andou mais
de 0,2 grau.
