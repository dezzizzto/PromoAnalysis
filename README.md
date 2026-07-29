# WhatsApp & Telegram Promo Extractor

Extrai mensagens de promoções/ofertas de grupos e canais do WhatsApp e do Telegram, e envia os dados (produto, preço, desconto, link) para uma planilha do Google Sheets — rodando automaticamente de hora em hora, com deduplicação e alerta por e-mail para descontos altos.

## Como funciona

1. **`whatsapp_promo_extractor.py`** — abre o WhatsApp Web via Selenium, entra nos grupos e canais de transmissão configurados, identifica mensagens promocionais (por palavras-chave e regex de preço/desconto) e salva tudo em `promocoes_whatsapp.csv`.
2. **`telegram_promo_extractor.py`** — conecta na sua conta do Telegram via Telethon, lê os grupos/canais configurados, aplica a mesma lógica de detecção de promoção do extrator do WhatsApp, e **adiciona** os resultados ao mesmo `promocoes_whatsapp.csv`.
3. **`enviar_para_sheets.py`** — lê o CSV consolidado (WhatsApp + Telegram) e envia os dados novos para uma planilha do Google Sheets via API, evitando duplicatas com um histórico local (`enviados.json`).
4. **`alerta_desconto.py`** — verifica se alguma promoção tem desconto igual ou maior que o limite configurado e envia um e-mail de alerta, evitando alertar a mesma promoção duas vezes (registro em uma aba `alertas_log` na própria planilha).
5. **`run_pipeline.bat`** — roda os scripts de extração, Sheets, banco de dados e alertas em sequência e grava log em `pipeline_log.txt`.
6. **`painel.py`** — painel de controle local (Flask + React) em `http://localhost:5050` para gerenciar grupos, rodar o pipeline e acompanhar logs.
7. **`db.py`** — banco SQLite com histórico de todas as promoções, alimenta os gráficos e relatórios do dashboard.
8. **`setup_agendador.bat`** — registra automaticamente a execução horária no Agendador de Tarefas do Windows.

## Stack

- Python 3.12
- Selenium + webdriver-manager (WhatsApp Web)
- Telethon (Telegram, via conta de usuário)
- gspread + Google Service Account (API do Sheets)
- pandas
- Flask (painel de controle)
- React + Vite + TailwindCSS + Recharts (dashboard)
- SQLite (histórico e analytics)
- smtplib (alerta por e-mail via Gmail SMTP)

## Setup

### 1. Instalar dependências

```bash
pip install -r requirements.txt
```

### 2. Configurar o WhatsApp

1. Edite `CONVERSAS_ALVO` e `CANAIS_ALVO` no topo de `whatsapp_promo_extractor.py` com os nomes exatos dos grupos e canais de transmissão que você quer monitorar.
2. Rode e escaneie o QR Code na primeira execução:
   ```bash
   python whatsapp_promo_extractor.py
   ```
   A sessão fica salva em `chrome_profile/`, então as próximas execuções não pedem QR de novo.

### 3. Configurar o Telegram

1. Gere suas credenciais em https://my.telegram.org/apps
2. Configure as variáveis de ambiente (uma vez só):
   ```bash
   setx TELEGRAM_API_ID "seu_api_id"
   setx TELEGRAM_API_HASH "seu_api_hash"
   setx TELEGRAM_PHONE "+55SEUNUMERO"
   ```
   (feche e abra o terminal depois do `setx`)
3. Edite `GRUPOS_CANAIS_ALVO` no topo de `telegram_promo_extractor.py` com os nomes dos grupos/canais.
4. Rode e digite o código de confirmação enviado pelo Telegram na primeira execução:
   ```bash
   python telegram_promo_extractor.py
   ```
   A sessão fica salva em `telegram_session.session`, não pede login de novo depois.

### 4. Configurar o Google Sheets

1. Coloque sua Service Account do Google como `credentials.json` na raiz do projeto (não é versionado — veja `.gitignore`).
2. Compartilhe sua planilha do Google Sheets com o `client_email` da Service Account (permissão de Editor).
3. Ajuste `NOME_DA_PLANILHA` em `enviar_para_sheets.py` para o nome exato da sua planilha.

### 5. Configurar o alerta por e-mail

1. Gere uma Senha de App do Gmail em https://myaccount.google.com/apppasswords (exige verificação em duas etapas ativa).
2. Configure as variáveis de ambiente:
   ```bash
   setx EMAIL_REMETENTE "seuemail@gmail.com"
   setx EMAIL_SENHA_APP "sua-senha-de-app-16-digitos"
   setx EMAIL_DESTINATARIO "seuemail@gmail.com"
   ```
3. Ajuste `LIMITE_DESCONTO` em `alerta_desconto.py` para o percentual mínimo desejado.

### 6. Automatizar a execução (Windows)

**Opção A — Automática (recomendada):**

Clique com o botão direito em `setup_agendador.bat` → **Executar como administrador**. Isso cria a tarefa "PromoAnalysis" no Agendador de Tarefas do Windows, rodando de hora em hora enquanto você estiver logado.

**Opção B — Manual, pela interface do Agendador de Tarefas:**

1. Abra o **Agendador de Tarefas** (pesquise no menu Iniciar).
2. **Ação → Criar Tarefa Básica...**
3. Disparador: Diariamente → habilite "Repetir a tarefa a cada: 1 hora", duração "Indefinidamente".
4. Ação: Iniciar um programa → aponte para `run_pipeline.bat` (caminho completo).
5. Na aba Geral, marque **"Executar somente quando o usuário estiver conectado"** (necessário porque o Selenium precisa de uma sessão gráfica ativa).

> **Por que precisa do Agendador de Tarefas?** O extrator do WhatsApp usa automação de navegador (Selenium), que exige uma janela do Chrome real — por isso não dá para rodar como um serviço totalmente invisível/sem sessão. É preciso estar logado no Windows para a extração funcionar.

## Painel de Controle

O `painel.py` serve um dashboard React em `http://localhost:5050` com:

- Cards com métricas (promoções, fontes, limite de alerta)
- Pipeline visual com etapas animadas
- Log colorido com filtros por nível
- Gráfico de extrações (últimos 30 dias)
- Listagem de promoções por loja
- Botões de ação rápida (executar pipeline, exportar)
- Gerenciamento de grupos/canais

Para usar, execute:

```cmd
python painel.py
```

O dashboard React é servido diretamente pelo Flask (build estático em `dashboard/dist/`).

## Planilha Semanal

O `enviar_para_sheets.py` cria abas semanais automaticamente na planilha `promocoes_whatsapp`:

- `W30` → dados da semana 30
- `W31` → dados da semana 31
- `W32` → dados da semana 32

A cada semana, uma nova aba é criada, mantendo o histórico das semanas anteriores separado por aba.

## Versões

| Versão | Funcionalidade |
|--------|---------------|
| v1.0 | Extrator WhatsApp funcional (Selenium → CSV) |
| v2.0 | Integração com Google Sheets |
| v3.0 | Automação horária via Task Scheduler |
| v3.1 | setup_agendador.bat com encoding UTF-8 |
| v4.0 | Alerta por e-mail (descontos ≥ limite) |
| v5.0 | Deduplicação via Google Sheets (aba `alertas_log`) |
| v5.1 | Alertas e reenvios configurados |
| v6.0 | Canais de transmissão do WhatsApp + rate limit |
| v7.0 | Integração com Telegram via Telethon |
| v8.0 | Painel de controle Flask (tema fogo, stats, log) |
| v9.0 | SQLite (db.py), abas semanais no Sheets, dashboard React |

## Aviso

Este projeto interage com o WhatsApp Web via automação de navegador (Selenium) e com o Telegram via conta de usuário (Telethon), não pelas APIs oficiais de negócio dessas plataformas. Use com moderação e por sua conta e risco — uso excessivo ou automatizado pode não ser bem-visto pelas políticas de uso dos respectivos serviços.
