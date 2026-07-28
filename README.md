# WhatsApp Promo Extractor

Extrai mensagens de promoções/ofertas de grupos do WhatsApp Web e envia os dados (produto, preço, desconto, link) para uma planilha do Google Sheets — rodando automaticamente de hora em hora.

## Como funciona

1. **`whatsapp_promo_extractor.py`** — abre o WhatsApp Web via Selenium, entra nos grupos configurados, identifica mensagens promocionais (por palavras-chave e regex de preço/desconto) e salva tudo em `promocoes_whatsapp.csv`.
2. **`enviar_para_sheets.py`** — lê esse CSV e envia os dados para uma planilha do Google Sheets via API.
3. **`run_pipeline.bat`** — roda os dois scripts acima em sequência e grava log em `pipeline_log.txt`.
4. **`setup_agendador.bat`** — registra automaticamente a execução horária no Agendador de Tarefas do Windows.

## Stack

- Python 3.12
- Selenium + webdriver-manager
- gspread + Google Service Account (API do Sheets)
- pandas

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
3. Ajuste `NOME_DA_PLANILHA` em `enviar_para_sheets.py` para o nome exato da sua planilha.

### 5. Automatizar a execução (Windows)

**Opção A — Automática (recomendada):**

Clique com o botão direito em `setup_agendador.bat` → **Executar como administrador**. Isso cria a tarefa "PromoAnalysis" no Agendador de Tarefas do Windows, rodando de hora em hora enquanto você estiver logado.

**Opção B — Manual, pela interface do Agendador de Tarefas:**

1. Abra o **Agendador de Tarefas** (pesquise no menu Iniciar).
2. **Ação → Criar Tarefa Básica...**
3. Disparador: Diariamente → habilite "Repetir a tarefa a cada: 1 hora", duração "Indefinidamente".
4. Ação: Iniciar um programa → aponte para `run_pipeline.bat` (caminho completo).
5. Na aba Geral, marque **"Executar somente quando o usuário estiver conectado"** (necessário porque o Selenium precisa de uma sessão gráfica ativa).

> **Por que precisa do Agendador de Tarefas?** O extrator usa automação de navegador (Selenium), que exige uma janela do Chrome real — por isso não dá para rodar como um serviço totalmente invisível/sem sessão. É preciso estar logado no Windows para a extração funcionar.

## Aviso

Este projeto interage com o WhatsApp Web via automação de navegador (Selenium), não pela API oficial do WhatsApp Business. Use com moderação e por sua conta e risco — uso excessivo ou automatizado pode não ser bem-visto pela política de uso do WhatsApp.
