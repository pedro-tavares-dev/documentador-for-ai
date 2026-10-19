@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul
title Documentador - Instalacao
cd /d "%~dp0"

echo ============================================================
echo   Documentador Universal - Instalacao
echo ============================================================
echo.

set "PYEXE="
call :find_python
if defined PYEXE call :check_version

if defined PYEXE (
    echo [OK] Python encontrado: !PYEXE!
    "!PYEXE!" -c "import tkinter" >nul 2>nul
    if errorlevel 1 (
        echo [!] Este Python nao tem o Tkinter. Sera instalado o Python desta pasta, com Tkinter.
        set "PYEXE="
    ) else (
        echo [OK] Tkinter encontrado.
    )
) else (
    echo [!] Python 3.8+ nao encontrado.
)

if not defined PYEXE (
    set "INST="
    for %%F in ("%~dp0python-3.12*.exe") do set "INST=%%~fF"
    if not defined INST (
        echo [ERRO] O instalador do Python nao foi encontrado nesta pasta ^(python-3.12.exe^).
        echo        Baixe em https://www.python.org/downloads/ e marque "tcl/tk and IDLE".
        goto :fail
    )
    echo.
    echo Instalando o Python ^(com Tkinter e pip^)... aguarde, nao feche esta janela.
    start /wait "" "!INST!" /passive InstallAllUsers=0 PrependPath=1 Include_pip=1 Include_tcltk=1 Include_launcher=1 Include_test=0 Include_doc=0
    set "PYEXE="
    if exist "%LocalAppData%\Programs\Python\Python312\python.exe" set "PYEXE=%LocalAppData%\Programs\Python\Python312\python.exe"
    if not defined PYEXE call :find_python
    if not defined PYEXE (
        echo [ERRO] A instalacao do Python nao foi concluida. Execute este arquivo novamente.
        goto :fail
    )
    "!PYEXE!" -c "import tkinter" >nul 2>nul
    if errorlevel 1 (
        echo [ERRO] O Tkinter nao foi instalado. Rode python-3.12.exe manualmente e marque "tcl/tk and IDLE".
        goto :fail
    )
    echo [OK] Python e Tkinter instalados.
)

echo.
echo Preparando o pip...
"!PYEXE!" -m pip --version >nul 2>nul
if errorlevel 1 "!PYEXE!" -m ensurepip --upgrade >nul 2>nul

echo Instalando a biblioteca da interface ^(customtkinter^)...
"!PYEXE!" -m pip install --user --upgrade --disable-pip-version-check customtkinter
if errorlevel 1 (
    echo [ERRO] Falha ao instalar o customtkinter. Verifique a conexao com a internet e tente de novo.
    goto :fail
)

"!PYEXE!" -c "import tkinter, customtkinter" >nul 2>nul
if errorlevel 1 (
    echo [ERRO] A verificacao final falhou.
    goto :fail
)

echo.
echo ============================================================
echo   PRONTO! Tudo instalado.
echo   Copie o documentador.py para a pasta do projeto que quer
echo   documentar e abra-o com dois cliques ^(ou: python documentador.py^).
echo ============================================================
echo.
pause
exit /b 0

:fail
echo.
echo A instalacao nao foi concluida.
pause
exit /b 1

:find_python
set "PYEXE="
for /f "delims=" %%I in ('py -3 -c "import sys;print(sys.executable)" 2^>nul') do set "PYEXE=%%I"
if defined PYEXE exit /b 0
for /f "delims=" %%I in ('python -c "import sys;print(sys.executable)" 2^>nul') do set "PYEXE=%%I"
if defined PYEXE exit /b 0
for %%V in (313 312 311 310 39 38) do (
    if not defined PYEXE if exist "%LocalAppData%\Programs\Python\Python%%V\python.exe" set "PYEXE=%LocalAppData%\Programs\Python\Python%%V\python.exe"
)
exit /b 0

:check_version
"!PYEXE!" -c "import sys;sys.exit(0 if sys.version_info>=(3,8) else 1)" >nul 2>nul
if errorlevel 1 set "PYEXE="
exit /b 0
