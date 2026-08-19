@echo off
rem Abre o velocimetro sem janela de console.
cd /d "%~dp0"
if not exist ".venv\Scripts\pythonw.exe" (
    echo O ambiente nao foi instalado. Rode instalar.ps1 primeiro.
    pause
    exit /b 1
)
start "" ".venv\Scripts\pythonw.exe" -m velocimetro
