# -*- coding: utf-8 -*-
"""
Lê o CSV gerado pelo whatsapp_promo_extractor.py e envia os dados
para uma planilha do Google Sheets, evitando reenviar promoções
já enviadas anteriormente (controle via enviados.json).

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

import json
import hashlib
import logging
from pathlib import Path

import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# ─────────────────────────────────────────────────────────────────────
# CONFIGURAÇÃO
# ─────────────────────────────────────────────────────────────────────

ARQUIVO_CSV = "promocoes_whatsapp.csv"
ARQUIVO_ENVIADOS = "enviados.json"
CREDENTIALS_PATH = "credentials.json"
NOME_DA_PLANILHA = "promocoes_whatsapp"
NOME_DA_ABA = None  # None = usa a primeira aba (sheet1)

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
    df = pd.read_csv(caminho, sep=";", encoding="utf-8-sig")
    df = df.fillna("")
    return df


def gerar_id(linha: dict) -> str:
    """Gera um hash único para a linha, baseado em conversa + remetente +
    data/hora + texto original. Serve para identificar duplicatas."""
    chave = "|".join([
        str(linha.get("conversa", "")),
        str(linha.get("remetente", "")),
        str(linha.get("data_hora_mensagem", "")),
        str(linha.get("texto_original", "")),
    ])
    return hashlib.sha256(chave.encode("utf-8")).hexdigest()


def carregar_enviados() -> set[str]:
    caminho = Path(ARQUIVO_ENVIADOS)
    if not caminho.exists():
        return set()
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except (json.JSONDecodeError, OSError):
        log.warning(f'Não foi possível ler "{ARQUIVO_ENVIADOS}", começando do zero.')
        return set()


def salvar_enviados(ids: set[str]) -> None:
    with open(ARQUIVO_ENVIADOS, "w", encoding="utf-8") as f:
        json.dump(sorted(ids), f, ensure_ascii=False, indent=2)


def enviar(df: pd.DataFrame, aba, ja_enviados: set[str]) -> set[str]:
    valores_atuais = aba.get_all_values()
    if len(valores_atuais) == 0:
        aba.append_row(df.columns.tolist())

    novos_ids: set[str] = set()
    linhas_enviadas = 0

    for _, row in df.iterrows():
        registro = row.to_dict()
        id_msg = gerar_id(registro)

        if id_msg in ja_enviados:
            continue

        linha = [str(v) for v in row.tolist()]
        aba.append_row(linha)
        novos_ids.add(id_msg)
        linhas_enviadas += 1

    if linhas_enviadas:
        log.info(f"✔ {linhas_enviadas} linha(s) nova(s) adicionada(s) à planilha.")
    else:
        log.info("Nenhuma linha nova — todas já haviam sido enviadas anteriormente.")

    return novos_ids


def main() -> None:
    log.info(f'Lendo "{ARQUIVO_CSV}"...')
    df = carregar_csv()
    log.info(f"{len(df)} linhas encontradas no CSV.")

    if df.empty:
        log.warning("CSV vazio, nada para enviar.")
        return

    ja_enviados = carregar_enviados()
    log.info(f"{len(ja_enviados)} promoção(ões) já enviadas anteriormente (histórico local).")

    log.info(f'Conectando na planilha "{NOME_DA_PLANILHA}"...')
    aba = conectar_planilha()

    log.info("Enviando dados novos...")
    novos_ids = enviar(df, aba, ja_enviados)

    if novos_ids:
        ja_enviados.update(novos_ids)
        salvar_enviados(ja_enviados)

    log.info("Concluído.")


if __name__ == "__main__":
    main()