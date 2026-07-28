# PromoAnalysis — WhatsApp Promotions Extractor

Extrai automaticamente promoções de grupos do WhatsApp Web, envia para o Google Sheets e dispara alertas por e-mail quando encontra descontos altos (≥80%). Tudo rodando de hora em hora sem intervenção manual.

## Fluxo completo

```
WhatsApp Web (Selenium) → CSV → Google Sheets → E-mail de alerta (se ≥80%)
                              ↕
                     Deduplicação via alertas_log
```

## Scripts

| Script | Função |
|--------|--------|
| `whatsapp_promo_extractor.py` | Abre o WhatsApp Web via Selenium, entra nos grupos configurados, extrai mensagens promocionais (palavras-chave + regex de preço/desconto) e salva em `promocoes_whatsapp.csv` |
| `enviar_para_sheets.py` | Lê o CSV e empurra os dados para o Google Sheets (gspread + Service Account) |
| `alerta_desconto.py` | Verifica promoções com desconto ≥ 80%, envia alerta por e-mail (Gmail SMTP) — **com deduplicação**: consulta a aba `alertas_log` na planilha para não re-enviar alertas já disparados |
| `run_pipeline.bat` | Executa os 3 scripts em sequência e grava log em `pipeline_log.txt` |
| `setup_agendador.bat` | Registra a tarefa "PromoAnalysis" no Agendador do Windows (execução horária) |

## Stack

- Python 3.12
- Selenium + webdriver-manager
- gspread + google-auth (Google Sheets API)
- pandas
- smtplib (e-mail)

## Setup

### 1. Instalar dependências

```bash
pip install -r requirements.txt
```

### 2. Configurar os grupos-alvo

Edite `CONVERSAS_ALVO` no topo de `whatsapp_promo_extractor.py` com os nomes exatos dos grupos/contatos do WhatsApp que você quer monitorar.

### 3. Primeiro login no WhatsApp Web

```bash
python whatsapp_promo_extractor.py
```

Escaneie o QR Code na primeira execução. A sessão fica salva em `chrome_profile/`, então as próximas execuções não pedem QR de novo.

### 4. Configurar o Google Sheets

1. Coloque sua Service Account do Google como `credentials.json` na raiz do projeto (não é versionado — veja `.gitignore`).
2. Compartilhe sua planilha do Google Sheets com o `client_email` da Service Account (permissão de Editor).
3. Ajuste `NOME_DA_PLANILHA` em `enviar_para_sheets.py` e `alerta_desconto.py` para o nome exato da sua planilha.

> A aba `alertas_log` é criada automaticamente na primeira execução do `alerta_desconto.py`.

### 5. Configurar o alerta por e-mail

Defina as variáveis de ambiente (mais seguro que colocar direto no código):

```cmd
setx EMAIL_REMETENTE "seuemail@gmail.com"
setx EMAIL_SENHA_APP "sua-senha-de-app-16-digitos"
setx EMAIL_DESTINATARIO "seuemail@gmail.com"
```

> A `EMAIL_SENHA_APP` é gerada em [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords) — você precisa ter a verificação em duas etapas ativada.

### 6. Automatizar a execução (Windows)

**Opção A — Automática (recomendada):**

Clique com o botão direito em `setup_agendador.bat` → **Executar como administrador**. Isso registra a tarefa "PromoAnalysis" no Agendador de Tarefas, rodando a cada 1 hora enquanto você estiver logado.

**Opção B — Manual, pela interface do Agendador de Tarefas:**

1. Abra o **Agendador de Tarefas** (pesquise no menu Iniciar).
2. **Ação → Criar Tarefa Básica...**
3. Nome: `PromoAnalysis`
4. Disparador: Diariamente → habilite "Repetir a tarefa a cada: 1 hora", duração "Indefinidamente".
5. Ação: Iniciar um programa → aponte para `run_pipeline.bat` (caminho completo).
6. Na aba Geral, marque **"Executar somente quando o usuário estiver conectado"** (necessário porque o Selenium precisa de uma sessão gráfica ativa).

> **Por que precisa do Agendador de Tarefas?** O extrator usa automação de navegador (Selenium), que exige uma janela do Chrome real — por isso não dá para rodar como um serviço totalmente invisível/sem sessão. É preciso estar logado no Windows para a extração funcionar.

## Versões

| Versão | Funcionalidade |
|--------|---------------|
| v1.0 | Extrator funcional (Selenium → CSV) |
| v2.0 | Integração com Google Sheets |
| v3.0 | Automação horária via Task Scheduler |
| v3.1 | setup_agendador.bat com encoding UTF-8 |
| v4.0 | Alerta por e-mail (descontos ≥ 80%) |
| v5.0 | Deduplicação via Google Sheets (aba `alertas_log`) |

## Aviso

Este projeto interage com o WhatsApp Web via automação de navegador (Selenium), não pela API oficial do WhatsApp Business. Use com moderação e por sua conta e risco — uso excessivo ou automatizado pode não ser bem-visto pela política de uso do WhatsApp.
