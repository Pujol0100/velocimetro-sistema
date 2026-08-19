# Cria o ambiente isolado e instala as bibliotecas.
# Rode uma vez, no seu PowerShell, dentro da pasta do projeto.

$ErrorActionPreference = 'Stop'
Set-Location -Path $PSScriptRoot

Write-Host ''
Write-Host '=== Velocimetro de Sistema: instalacao ===' -ForegroundColor Cyan
Write-Host ''

$python = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $python) {
    Write-Host 'Python nao foi encontrado no PATH.' -ForegroundColor Red
    Write-Host 'Instale o Python 3.10 ou mais novo em https://python.org e rode este script de novo.'
    exit 1
}
Write-Host ("Python encontrado: " + $python)

if (-not (Test-Path '.venv\Scripts\python.exe')) {
    Write-Host 'Criando o ambiente isolado em .venv ...'
    & $python -m venv .venv
} else {
    Write-Host 'O ambiente .venv ja existe, reaproveitando.'
}

Write-Host 'Instalando PySide6, psutil e pytest (pode levar 1 a 3 minutos) ...'
& '.venv\Scripts\python.exe' -m pip install --upgrade pip --quiet
& '.venv\Scripts\python.exe' -m pip install -r requirements.txt --quiet

Write-Host ''
Write-Host 'Conferindo a instalacao ...'
& '.venv\Scripts\python.exe' -c "import PySide6, psutil; print('PySide6', PySide6.__version__, '| psutil', psutil.__version__)"

Write-Host ''
Write-Host 'Instalacao concluida.' -ForegroundColor Green
Write-Host 'Agora clique duas vezes em Velocimetro.bat para abrir o medidor.'
Write-Host ''
