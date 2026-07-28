# -*- coding: utf-8 -*-
"""
Lê o CSV gerado pelo whatsapp_promo_extractor.py e envia os dados
para uma planilha do Google Sheets.

Requisitos:
    pip install gspread google-auth pandas

Antes de rodar:
    1. Coloque o JSON da sua Service Account nesta mesma pasta,
       renomeado para "credentials.json" (ou ajuste o caminho abaixo).
    2. Compartilhe a planilha do Google Sheets com o "client_email"
       que está dentro do credentials.json, com permissão de Editor.
    3. Ajuste NOME_DA_PLANILHA abaixo para o nome exato da sua planilha.

Uso:
    python enviar_para_sheets.py
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# ─────────────────────────────────────────────────────────────────────
# CONFIGURAÇÃO
# ─────────────────────────────────────────────────────────────────────

ARQUIVO_CSV = "promocoes_whatsapp.csv"
CREDENTIALS_PATH = "credentials.json"
NOME_DA_PLANILHA = "promocoes_whatsapp"   # nome exato da planilha no Google Sheets
NOME_DA_ABA = None                # None = usa a primeira aba (sheet1)

# Se True, apaga os dados antigos da aba antes de subir os novos.
# Se False, só adiciona (append) as linhas novas no final.
SUBSTITUIR_TUDO = False

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-7s │ %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("enviar_sheets")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
]


def conectar_planilha():
    creds = Credentials.from_service_account_file(CREDENTIALS_PATH, scopes=SCOPES)
    gc = gspread.authorize(creds)
    planilha = gc.open(NOME_DA_PLANILHA)
    return planilha.worksheet(NOME_DA_ABA) if NOME_DA_ABA else planilha.sheet1


def carregar_csv() -> pd.DataFrame:
    caminho = Path(ARQUIVO_CSV)
    if not caminho.exists():
        raise FileNotFoundError(
            f'Arquivo "{ARQUIVO_CSV}" não encontrado. Rode o extrator primeiro.'
        )
    # O CSV foi salvo com separador ";" e encoding utf-8-sig.
    df = pd.read_csv(caminho, sep=";", encoding="utf-8-sig")
    df = df.fillna("")
    return df


def enviar(df: pd.DataFrame, aba) -> None:
    if SUBSTITUIR_TUDO:
        aba.clear()
        aba.update([df.columns.tolist()] + df.astype(str).values.tolist())
        log.info(f"✔ Planilha substituída com {len(df)} linhas.")
    else:
        # Evita duplicar: pega quantas linhas já existem (menos o cabeçalho)
        # e só envia o que ainda não foi enviado, assumindo que o CSV
        # é sempre reescrito do zero a cada execução do extrator.
        valores_atuais = aba.get_all_values()
        se_vazia = len(valores_atuais) == 0

        if se_vazia:
            aba.append_row(df.columns.tolist())

        linhas = df.astype(str).values.tolist()
        for linha in linhas:
            aba.append_row(linha)

        log.info(f"✔ {len(linhas)} linhas adicionadas ao final da planilha.")


def main() -> None:
    log.info(f'Lendo "{ARQUIVO_CSV}"...')
    df = carregar_csv()
    log.info(f"{len(df)} linhas encontradas no CSV.")

    if df.empty:
        log.warning("CSV vazio, nada para enviar.")
        return

    log.info(f'Conectando na planilha "{NOME_DA_PLANILHA}"...')
    aba = conectar_planilha()

    log.info("Enviando dados...")
    enviar(df, aba)

    log.info("Concluído.")


if __name__ == "__main__":
    main()