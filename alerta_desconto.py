# -*- coding: utf-8 -*-
"""
Lê o CSV de promoções e envia um alerta por e-mail quando encontra
descontos acima do limite configurado (LIMITE_DESCONTO).

Requisitos:
    pip install pandas

Configuração (edite abaixo ou use variáveis de ambiente):
    EMAIL_REMETENTE   - conta Gmail que envia o alerta
    EMAIL_SENHA_APP   - senha de app gerada em myaccount.google.com/apppasswords
    EMAIL_DESTINATARIO - quem recebe o alerta (pode ser o mesmo remetente)

Uso:
    python alerta_desconto.py
"""

from __future__ import annotations

import os
import re
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

import pandas as pd

# ─────────────────────────────────────────────────────────────────────
# CONFIGURAÇÃO
# ─────────────────────────────────────────────────────────────────────

ARQUIVO_CSV = "promocoes_whatsapp.csv"
LIMITE_DESCONTO = 80  # percentual mínimo para disparar o alerta

# Prefira configurar via variáveis de ambiente (mais seguro do que deixar
# hardcoded aqui, principalmente se o arquivo for parar no GitHub por engano).
# No Windows, defina com:
#   setx EMAIL_REMETENTE "seuemail@gmail.com"
#   setx EMAIL_SENHA_APP "sua-senha-de-app-16-digitos"
#   setx EMAIL_DESTINATARIO "seuemail@gmail.com"
# (feche e abra o terminal depois do setx para o valor ficar disponível)
EMAIL_REMETENTE = os.environ.get("EMAIL_REMETENTE", "")
EMAIL_SENHA_APP = os.environ.get("EMAIL_SENHA_APP", "")
EMAIL_DESTINATARIO = os.environ.get("EMAIL_DESTINATARIO", "")

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-7s │ %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("alerta_desconto")


def carregar_csv() -> pd.DataFrame:
    caminho = Path(ARQUIVO_CSV)
    if not caminho.exists():
        raise FileNotFoundError(f'Arquivo "{ARQUIVO_CSV}" não encontrado.')
    df = pd.read_csv(caminho, sep=";", encoding="utf-8-sig")
    return df.fillna("")


def extrair_percentual(valor: str) -> int:
    """Converte string tipo '85%' em 85 (int). Retorna -1 se não houver número."""
    match = re.search(r"(\d{1,3})", str(valor))
    return int(match.group(1)) if match else -1


def filtrar_descontos_altos(df: pd.DataFrame) -> pd.DataFrame:
    if "desconto_percentual" not in df.columns:
        return df.iloc[0:0]
    df = df.copy()
    df["_desconto_num"] = df["desconto_percentual"].apply(extrair_percentual)
    return df[df["_desconto_num"] >= LIMITE_DESCONTO]


def montar_corpo_email(promocoes: pd.DataFrame) -> str:
    linhas = []
    for _, row in promocoes.iterrows():
        linhas.append(
            f"• {row.get('texto_original', '')[:200]}\n"
            f"  Desconto: {row.get('desconto_percentual', '')} | "
            f"Preço: {row.get('preco_encontrado', '')}\n"
            f"  Grupo: {row.get('conversa', '')}\n"
        )
    return (
        f"Encontramos {len(promocoes)} promoção(ões) com desconto "
        f"igual ou maior que {LIMITE_DESCONTO}%:\n\n" + "\n".join(linhas)
    )


def enviar_email(corpo: str, quantidade: int) -> None:
    if not (EMAIL_REMETENTE and EMAIL_SENHA_APP and EMAIL_DESTINATARIO):
        log.error(
            "Variáveis de e-mail não configuradas. "
            "Defina EMAIL_REMETENTE, EMAIL_SENHA_APP e EMAIL_DESTINATARIO."
        )
        return

    msg = MIMEMultipart()
    msg["From"] = EMAIL_REMETENTE
    msg["To"] = EMAIL_DESTINATARIO
    msg["Subject"] = f"🔥 {quantidade} promoção(ões) com desconto ≥ {LIMITE_DESCONTO}%"
    msg.attach(MIMEText(corpo, "plain", "utf-8"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_REMETENTE, EMAIL_SENHA_APP)
        server.send_message(msg)

    log.info(f"✔ E-mail de alerta enviado para {EMAIL_DESTINATARIO}.")


def main() -> None:
    log.info(f'Lendo "{ARQUIVO_CSV}"...')
    df = carregar_csv()

    promocoes = filtrar_descontos_altos(df)

    if promocoes.empty:
        log.info(f"Nenhuma promoção com desconto ≥ {LIMITE_DESCONTO}% encontrada.")
        return

    log.info(f"{len(promocoes)} promoção(ões) com desconto ≥ {LIMITE_DESCONTO}% encontradas.")
    corpo = montar_corpo_email(promocoes)
    enviar_email(corpo, len(promocoes))


if __name__ == "__main__":
    main()