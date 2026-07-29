# -*- coding: utf-8 -*-
"""
Extrai mensagens promocionais de grupos/canais do Telegram (via conta de
usuário, usando Telethon) e adiciona ao MESMO CSV usado pelo extrator do
WhatsApp — reaproveita a mesma lógica de detecção de promoção (palavras-chave,
regex de preço/desconto) definida em whatsapp_promo_extractor.py.

Requisitos:
    pip install telethon

Antes de rodar:
    1. Gere suas credenciais em https://my.telegram.org/apps
    2. Configure as variáveis de ambiente (uma vez só):
        setx TELEGRAM_API_ID "seu_api_id"
        setx TELEGRAM_API_HASH "seu_api_hash"
        setx TELEGRAM_PHONE "+5511999999999"
       (feche e abra o terminal depois do setx)
    3. Ajuste GRUPOS_CANAIS_ALVO abaixo com os nomes exatos dos grupos/canais.

Primeira execução:
    Vai pedir o código de confirmação enviado pelo Telegram (no app ou SMS).
    Depois disso, a sessão fica salva em telegram_session.session — não
    pede login de novo nas próximas execuções.

Uso:
    python telegram_promo_extractor.py
"""

from __future__ import annotations

import os
import csv
import logging
from pathlib import Path

from telethon.sync import TelegramClient

# Reaproveita a lógica de detecção de promoção do extrator do WhatsApp.
from whatsapp_promo_extractor import DadosPromocao, analisar_mensagem
from config_loader import carregar_config

_config = carregar_config()

# ─────────────────────────────────────────────────────────────────────
# CONFIGURAÇÃO
# ─────────────────────────────────────────────────────────────────────

# Nomes exatos (ou parte do nome) dos grupos/canais do Telegram para monitorar.
# Editável pelo painel (painel.py) ou diretamente em config.json.
GRUPOS_CANAIS_ALVO: list[str] = _config["telegram_grupos_canais"]

MAX_MENSAGENS_POR_CONVERSA = _config["max_mensagens_por_conversa"]
ARQUIVO_CSV = "promocoes_whatsapp.csv"  # mesmo CSV usado pelo extrator do WhatsApp
ARQUIVO_SESSAO = "telegram_session"

API_ID = os.environ.get("TELEGRAM_API_ID", "")
API_HASH = os.environ.get("TELEGRAM_API_HASH", "")
TELEFONE = os.environ.get("TELEGRAM_PHONE", "")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-7s │ %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("telegram_extractor")

COLUNAS_CSV = [
    "conversa",
    "remetente",
    "data_hora_mensagem",
    "texto_original",
    "preco_encontrado",
    "preco_anterior",
    "desconto_percentual",
    "keywords_encontradas",
    "data_extracao",
]


def validar_configuracao() -> bool:
    if not (API_ID and API_HASH and TELEFONE):
        log.error(
            "Variáveis TELEGRAM_API_ID, TELEGRAM_API_HASH e TELEGRAM_PHONE "
            "não configuradas. Veja as instruções no topo deste arquivo."
        )
        return False
    if not GRUPOS_CANAIS_ALVO:
        log.warning(
            "GRUPOS_CANAIS_ALVO está vazio — nenhum grupo/canal configurado. "
            "Edite a lista no topo deste arquivo."
        )
        return False
    return True


def encontrar_dialogo(client: TelegramClient, nome: str):
    """Procura, entre as conversas do usuário, uma que contenha o nome dado."""
    for dialogo in client.iter_dialogs():
        if nome.lower() in dialogo.name.lower():
            return dialogo
    return None


def extrair_promocoes_do_dialogo(client: TelegramClient, dialogo, nome_busca: str) -> list[DadosPromocao]:
    promocoes: list[DadosPromocao] = []
    processadas = 0

    for msg in client.iter_messages(dialogo.entity, limit=MAX_MENSAGENS_POR_CONVERSA):
        texto = msg.message or ""
        if not texto or len(texto.strip()) < 5:
            continue

        remetente = dialogo.name
        if msg.sender:
            nome_remetente = getattr(msg.sender, "first_name", None) or getattr(
                msg.sender, "title", None
            )
            if nome_remetente:
                remetente = nome_remetente

        data_hora = msg.date.strftime("%H:%M, %d/%m/%Y") if msg.date else ""

        resultado = analisar_mensagem(dialogo.name, remetente, data_hora, texto)
        if resultado:
            promocoes.append(resultado)
        processadas += 1

    log.info(
        f'✔ {len(promocoes)} promoções encontradas em "{dialogo.name}" '
        f'(de {processadas} mensagens analisadas).'
    )
    return promocoes


def salvar_csv_append(promocoes: list[DadosPromocao]) -> None:
    """Adiciona as novas promoções ao CSV existente (não sobrescreve),
    escrevendo o cabeçalho apenas se o arquivo ainda não existir."""
    caminho = Path(ARQUIVO_CSV)
    escrever_cabecalho = not caminho.exists() or caminho.stat().st_size == 0

    with open(caminho, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=COLUNAS_CSV, delimiter=";")
        if escrever_cabecalho:
            writer.writeheader()
        for promo in promocoes:
            from dataclasses import asdict
            row = asdict(promo)
            row.pop("produtos_detectados", None)
            writer.writerow(row)

    log.info(f"✔ {len(promocoes)} promoção(ões) do Telegram adicionadas a {ARQUIVO_CSV}.")


def main() -> None:
    if not validar_configuracao():
        return

    todas_promocoes: list[DadosPromocao] = []

    with TelegramClient(ARQUIVO_SESSAO, int(API_ID), API_HASH) as client:
        client.start(phone=TELEFONE)
        log.info("✔ Conectado ao Telegram.")

        for i, nome in enumerate(GRUPOS_CANAIS_ALVO, 1):
            log.info(f"\n{'═' * 60}")
            log.info(f"Processando {i}/{len(GRUPOS_CANAIS_ALVO)}: {nome}")
            log.info(f"{'═' * 60}")

            dialogo = encontrar_dialogo(client, nome)
            if not dialogo:
                log.warning(f'✘ Grupo/canal "{nome}" não encontrado.')
                continue

            promocoes = extrair_promocoes_do_dialogo(client, dialogo, nome)
            todas_promocoes.extend(promocoes)

    if todas_promocoes:
        salvar_csv_append(todas_promocoes)
    else:
        log.warning("Nenhuma promoção encontrada nos grupos/canais do Telegram.")


if __name__ == "__main__":
    main()
