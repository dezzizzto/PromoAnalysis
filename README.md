# WhatsApp Promotions Extractor 🛒📊

Extrai dados de promoções e preços de conversas do WhatsApp Web e salva
em uma planilha CSV pronta para análise.

## Como funciona

```
WhatsApp Web ──▶ Selenium (Chrome) ──▶ Filtra promoções ──▶ CSV
```

1. Abre o Chrome e navega para o WhatsApp Web
2. Você escaneia o QR Code (apenas na primeira vez — a sessão é salva)
3. O script navega até cada conversa configurada
4. Rola o chat para carregar mensagens antigas
5. Analisa cada mensagem procurando:
   - Palavras-chave de promoção (PT-BR)
   - Valores monetários (`R$ X,XX`)
   - Percentuais de desconto (`XX% off`)
   - Padrões "de R$ X por R$ Y"
6. Salva os dados estruturados em CSV

## Instalação

```bash
# 1. Instale Python 3.10+

# 2. Instale as dependências
pip install -r requirements.txt
```

> **Nota:** É necessário ter o Google Chrome instalado.

## Configuração

Edite a seção **CONFIGURAÇÃO** no início do arquivo
[`whatsapp_promo_extractor.py`](whatsapp_promo_extractor.py):

```python
# Nomes dos contatos/grupos para extrair
CONVERSAS_ALVO = [
    "Promoções do Dia",
    "Ofertas Atacadão",
]

# Limite de mensagens por conversa
MAX_MENSAGENS_POR_CONVERSA = 500

# Quantos scrolls para carregar histórico
SCROLLS_PARA_CARREGAR = 25

# Nome do arquivo de saída
ARQUIVO_SAIDA = "promocoes_whatsapp.csv"
```

## Uso

```bash
python whatsapp_promo_extractor.py
```

Na primeira execução:
1. O Chrome abrirá o WhatsApp Web
2. Escaneie o QR Code com seu celular
3. O script começará a extração automaticamente

Execuções seguintes reutilizam a sessão salva em `./chrome_profile/`.

## Saída CSV

O arquivo gerado usa **`;`** como separador (compatível com Excel PT-BR) e
contém as seguintes colunas:

| Coluna | Descrição |
|---|---|
| `conversa` | Nome do contato/grupo |
| `remetente` | Quem enviou a mensagem |
| `data_hora_mensagem` | Data/hora extraída da mensagem |
| `texto_original` | Texto da mensagem (até 500 chars) |
| `preco_encontrado` | Preço principal identificado |
| `preco_anterior` | Preço "de" em padrões "de/por" |
| `desconto_percentual` | Desconto em % se mencionado |
| `keywords_encontradas` | Palavras-chave de promoção detectadas |
| `data_extracao` | Quando os dados foram extraídos |

## Palavras-chave reconhecidas

O script detecta mensagens contendo termos como:
- **Preço:** `R$`, `reais`, `valor`, `custa`
- **Promoção:** `promoção`, `oferta`, `desconto`, `liquidação`, `queima`
- **Ação:** `compre X leve Y`, `grátis`, `cashback`, `cupom`
- **Comparação:** `de/por`, `baixou`, `caiu`, `era/agora`

## Dicas

- **Conversas longas**: Aumente `SCROLLS_PARA_CARREGAR` (cada scroll ≈ 20 msgs)
- **Excel**: O CSV usa encoding `utf-8-sig` e separador `;` — abra direto no Excel
- **Segurança**: O perfil do Chrome (`chrome_profile/`) contém sua sessão.
  Não compartilhe esta pasta.
