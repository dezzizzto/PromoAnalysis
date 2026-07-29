@echo off
REM Executa o pipeline completo: extrai promoções do WhatsApp e envia ao Google Sheets.
REM Usado pelo Agendador de Tarefas do Windows.

cd /d "C:\Users\Erik e Bia\Documents\Antigravity"

set PYTHON="C:\Users\Erik e Bia\AppData\Local\Programs\Python\Python312\python.exe"
set PYTHONIOENCODING=utf-8

echo [%date% %time%] Iniciando extracao... >> pipeline_log.txt
%PYTHON% whatsapp_promo_extractor.py >> pipeline_log.txt 2>&1

echo [%date% %time%] Extraindo do Telegram... >> pipeline_log.txt
%PYTHON% telegram_promo_extractor.py >> pipeline_log.txt 2>&1

echo [%date% %time%] Enviando para o Sheets... >> pipeline_log.txt
%PYTHON% enviar_para_sheets.py >> pipeline_log.txt 2>&1

echo [%date% %time%] Verificando descontos altos... >> pipeline_log.txt
%PYTHON% alerta_desconto.py >> pipeline_log.txt 2>&1

echo [%date% %time%] Pipeline concluido. >> pipeline_log.txt
echo. >> pipeline_log.txt