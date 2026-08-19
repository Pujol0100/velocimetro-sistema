# Coloca (ou remove) um atalho do velocimetro na inicializacao do Windows.
#
#   Ativar:   .\ativar-inicio-automatico.ps1
#   Remover:  .\ativar-inicio-automatico.ps1 -Remover

param([switch]$Remover)

$ErrorActionPreference = 'Stop'
Set-Location -Path $PSScriptRoot

$pastaInicializacao = [Environment]::GetFolderPath('Startup')
$atalho = Join-Path $pastaInicializacao 'Velocimetro de Sistema.lnk'

if ($Remover) {
    if (Test-Path $atalho) {
        Remove-Item $atalho -Force
        Write-Host 'Atalho removido. O velocimetro nao abre mais sozinho.' -ForegroundColor Green
    } else {
        Write-Host 'Nao havia atalho na inicializacao. Nada a fazer.' -ForegroundColor Yellow
    }
    exit 0
}

$executavel = Join-Path $PSScriptRoot '.venv\Scripts\pythonw.exe'
if (-not (Test-Path $executavel)) {
    Write-Host 'O ambiente .venv nao existe. Rode instalar.ps1 primeiro.' -ForegroundColor Red
    exit 1
}

$shell = New-Object -ComObject WScript.Shell
$link = $shell.CreateShortcut($atalho)
$link.TargetPath = $executavel
$link.Arguments = '-m velocimetro'
$link.WorkingDirectory = $PSScriptRoot
$link.Description = 'Velocimetro de Sistema: CPU, memoria e disco'
$link.Save()

Write-Host ''
Write-Host 'Pronto. O velocimetro vai abrir junto com o Windows.' -ForegroundColor Green
Write-Host ("Atalho criado em: " + $atalho)
Write-Host 'Para desfazer, rode: .\ativar-inicio-automatico.ps1 -Remover'
Write-Host ''
