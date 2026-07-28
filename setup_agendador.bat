@echo off
REM Registra automaticamente a tarefa agendada no Windows para rodar
REM o pipeline (extracao + envio ao Sheets) de hora em hora.
REM Rode este arquivo UMA VEZ para configurar. Precisa ser executado
REM como Administrador (botao direito > Executar como administrador).

set PASTA_PROJETO=%~dp0
set PASTA_PROJETO=%PASTA_PROJETO:~0,-1%

schtasks /create ^
  /tn "PromoAnalysis" ^
  /tr "\"%PASTA_PROJETO%\run_pipeline.bat\"" ^
  /sc hourly ^
  /mo 1 ^
  /rl limited ^
  /f

if %errorlevel% equ 0 (
    echo.
    echo ✔ Tarefa "PromoAnalysis" criada com sucesso!
    echo   Ela vai rodar de hora em hora, apenas quando voce estiver logado no Windows.
    echo.
    echo   Para testar agora, abra o Agendador de Tarefas, encontre "PromoAnalysis"
    echo   e clique com botao direito - Executar.
) else (
    echo.
    echo ✘ Falha ao criar a tarefa. Verifique se voce executou este arquivo
    echo   como Administrador ^(botao direito - Executar como administrador^).
)

pause
