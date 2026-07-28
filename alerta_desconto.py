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
import hashlib
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from datetime import datetime

import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

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

# ─────────────────────────────────────────────────────────────────────
# CONFIGURAÇÃO GOOGLE SHEETS (para deduplicação)
# ─────────────────────────────────────────────────────────────────────
CREDENTIALS_PATH = "credentials.json"
NOME_DA_PLANILHA = "promocoes_whatsapp"
NOME_ABA_ALERTAS = "alertas_log"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
]

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


def gerar_hash_promocao(row: dict) -> str:
    """Gera hash único para identificar a promoção."""
    raw = f"{row.get('conversa','')}|{row.get('data_hora_mensagem','')}|{str(row.get('texto_original',''))[:200]}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def conectar_aba_alertas() -> gspread.Worksheet | None:
    """Conecta na planilha e retorna (ou cria) a aba alertas_log."""
    try:
        creds = Credentials.from_service_account_file(CREDENTIALS_PATH, scopes=SCOPES)
        gc = gspread.authorize(creds)
        planilha = gc.open(NOME_DA_PLANILHA)
        try:
            return planilha.worksheet(NOME_ABA_ALERTAS)
        except gspread.WorksheetNotFound:
            aba = planilha.add_worksheet(NOME_ABA_ALERTAS, 1, 4)
            aba.append_row(["id_hash", "conversa", "data_hora_mensagem", "data_alerta"])
            return aba
    except Exception as e:
        log.warning(f"Não foi possível conectar ao Google Sheets: {e}")
        return None


def carregar_hashes_alertados(aba: gspread.Worksheet) -> set[str]:
    """Retorna set com os hashes já registrados na aba de alertas."""
    try:
        registros = aba.get_all_values()
        if len(registros) <= 1:
            return set()
        return {linha[0] for linha in registros[1:] if linha and linha[0] and linha[0] != "id_hash"}
    except Exception:
        return set()


def registrar_alertas(aba: gspread.Worksheet, hashes: list[tuple[str, str, str, str]]) -> None:
    """Append dos novos alertas na aba (id_hash, conversa, data_hora_mensagem, data_alerta)."""
    if not hashes:
        return
    try:
        for h in hashes:
            aba.append_row(list(h))
    except Exception as e:
        log.warning(f"Erro ao registrar alertas no Sheets: {e}")


def main() -> None:
    log.info(f'Lendo "{ARQUIVO_CSV}"...')
    df = carregar_csv()

    promocoes = filtrar_descontos_altos(df)

    if promocoes.empty:
        log.info(f"Nenhuma promoção com desconto ≥ {LIMITE_DESCONTO}% encontrada.")
        return

    log.info(f"{len(promocoes)} promoção(ões) com desconto ≥ {LIMITE_DESCONTO}% encontradas.")

    # ── Deduplicação via Google Sheets ──────────────────────────────
    aba_alertas = conectar_aba_alertas()
    if aba_alertas:
        alertados = carregar_hashes_alertados(aba_alertas)
        novas = []
        for _, row in promocoes.iterrows():
            h = gerar_hash_promocao(row)
            if h not in alertados:
                novas.append(row)

        if not novas:
            log.info("Todas as promoções já foram alertadas anteriormente. Nada a enviar.")
            return

        log.info(f"{len(novas)} nova(s) promoção(ões) para alertar.")
        df_novas = pd.DataFrame(novas)
        corpo = montar_corpo_email(df_novas)
        enviar_email(corpo, len(novas))

        # Registra os hashes enviados
        agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        novos_registros = [
            (gerar_hash_promocao(row), row.get("conversa", ""), row.get("data_hora_mensagem", ""), agora)
            for row in novas
        ]
        registrar_alertas(aba_alertas, novos_registros)
    else:
        # Fallback: sem sheets, envia alerta tradicional (sem dedup)
        corpo = montar_corpo_email(promocoes)
        enviar_email(corpo, len(promocoes))


if __name__ == "__main__":
    main()