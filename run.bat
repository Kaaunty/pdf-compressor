@echo off
title PDF Compressor Launcher
echo ==================================================
echo                PDF COMPRESSOR
echo ==================================================
echo.

rem Check if Python virtual environment exists, if not create it
if not exist .venv (
    echo [1/3] Criando ambiente virtual Python venv...
    python -m venv .venv
    if errorlevel 1 (
        echo.
        echo [ERRO] Falha ao criar o ambiente virtual. Verifique se o Python esta instalado corretamente.
        pause
        exit /b 1
    )
) else (
    echo [1/3] Ambiente virtual venv ja existe.
)

rem Activate virtual environment
echo [2/3] Ativando ambiente virtual...
call .venv\Scripts\activate
if errorlevel 1 (
    echo.
    echo [ERRO] Falha ao ativar o ambiente virtual venv.
    pause
    exit /b 1
)

rem Install dependencies
echo [3/3] Instalando ou Atualizando dependencias - isso pode levar um momento...
python -m pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [ERRO] Falha ao instalar dependencias do requirements.txt.
    pause
    exit /b 1
)

echo.
echo ==================================================
echo   Iniciando o servidor local em http://127.0.0.1:8000
echo   Pressione Ctrl+C para encerrar o aplicativo.
echo ==================================================
echo.

rem Launch browser asynchronously
start http://127.0.0.1:8000

rem Start server
python main.py

pause
