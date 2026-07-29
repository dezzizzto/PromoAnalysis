@echo off
REM Abre o painel de controle do PromoAnalysis.

cd /d "%~dp0"
set PYTHON="C:\Users\Erik e Bia\AppData\Local\Programs\Python\Python312\python.exe"

%PYTHON% painel.py
pause
