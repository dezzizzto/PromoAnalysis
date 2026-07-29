# -*- coding: utf-8 -*-
"""
Banco SQLite para histórico de promoções.

Cria/atualiza promocoes.db, importa do CSV e fornece consultas
agregadas para o dashboard (gráficos, relatórios).
"""

from __future__ import annotations

import re
import sqlite3
import logging
from pathlib import Path
from datetime import date

import pandas as pd

log = logging.getLogger("db")

PASTA_PROJETO = Path(__file__).parent
DB_PATH = PASTA_PROJETO / "promocoes.db"
ARQUIVO_CSV = PASTA_PROJETO / "promocoes_whatsapp.csv"

# Extrai nome da loja a partir de URLs no texto
REGEX_LOJA = re.compile(
    r"(?:https?://(?:www\.)?)?"
    r"(?:s\.)?"
    r"(?P<loja>shopee|mercadolivre|amazon|kabum|magalu|aliexpress|americanas|"
    r"nike|adidas|centauro|netshoes|pontofrio|casasbahia|extra|carrefour)"
    r"(?:\.com[^\s]*)",
    re.IGNORECASE,
)


def extrair_loja(texto: str) -> str:
    match = REGEX_LOJA.search(texto)
    if match:
        nome = match.group("loja").lower()
        mapa = {
            "mercadolivre": "Mercado Livre",
            "magalu": "Magalu",
            "kabum": "KaBuM!",
            "aliexpress": "AliExpress",
        }
        return mapa.get(nome, nome.capitalize())
    return ""


def criar_tabela() -> None:
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS promocoes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            conversa    TEXT,
            remetente   TEXT,
            data_hora_mensagem TEXT,
            texto_original      TEXT,
            preco_encontrado    REAL,
            preco_anterior      REAL,
            desconto_percentual INTEGER,
            keywords_encontradas TEXT,
            data_extracao       TEXT,
            semana      TEXT,
            loja        TEXT,
            UNIQUE(conversa, data_hora_mensagem, texto_original)
        )
    """)
    conn.commit()
    conn.close()


def importar_csv() -> int:
    """Lê o CSV e insere no SQLite. Retorna quantas linhas novas foram inseridas."""
    if not ARQUIVO_CSV.exists():
        log.warning("CSV não encontrado, nada a importar.")
        return 0

    criar_tabela()

    df = pd.read_csv(ARQUIVO_CSV, sep=";", encoding="utf-8-sig")
    df = df.fillna("")

    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=OFF")

    semana_atual = f"{date.today().year}-W{date.today().isocalendar()[1]:02d}"
    inseridas = 0

    for _, row in df.iterrows():
        loja = extrair_loja(str(row.get("texto_original", "")))
        try:
            conn.execute(
                """
                INSERT OR IGNORE INTO promocoes
                    (conversa, remetente, data_hora_mensagem, texto_original,
                     preco_encontrado, preco_anterior, desconto_percentual,
                     keywords_encontradas, data_extracao, semana, loja)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(row.get("conversa", "")),
                    str(row.get("remetente", "")),
                    str(row.get("data_hora_mensagem", "")),
                    str(row.get("texto_original", "")),
                    _parse_preco(row.get("preco_encontrado", "")),
                    _parse_preco(row.get("preco_anterior", "")),
                    _parse_int(row.get("desconto_percentual", "")),
                    str(row.get("keywords_encontradas", "")),
                    str(row.get("data_extracao", "")),
                    semana_atual,
                    loja,
                ),
            )
            if conn.total_changes > 0:
                inseridas += 1
        except Exception as e:
            log.debug(f"Erro ao inserir linha: {e}")

    conn.commit()
    conn.close()
    log.info(f"{inseridas} nova(s) promoção(ões) inserida(s) no banco.")
    return inseridas


def _parse_preco(valor) -> float | None:
    try:
        return float(str(valor).replace("R$", "").replace(".", "").replace(",", ".").strip())
    except (ValueError, AttributeError):
        return None


def _parse_int(valor) -> int | None:
    try:
        return int(re.search(r"\d+", str(valor)).group())
    except (AttributeError, ValueError):
        return None


def stats_resumo() -> dict:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    total = conn.execute("SELECT COUNT(*) AS t FROM promocoes").fetchone()["t"]
    lojas = conn.execute("""
        SELECT loja, COUNT(*) AS total FROM promocoes
        WHERE loja != '' GROUP BY loja ORDER BY total DESC LIMIT 8
    """).fetchall()
    conn.close()
    return {"total": total, "lojas": [dict(l) for l in lojas]}


def stats_por_dia(dias: int = 30) -> list[dict]:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    dados = conn.execute(
        """
        SELECT DATE(data_extracao) AS dia,
               COUNT(*) AS total,
               ROUND(AVG(COALESCE(desconto_percentual, 0)), 1) AS media_desconto
        FROM promocoes
        WHERE data_extracao != ''
        GROUP BY dia
        ORDER BY dia DESC
        LIMIT ?
        """,
        (dias,),
    ).fetchall()
    conn.close()
    return list(reversed([dict(d) for d in dados]))


def stats_por_loja() -> list[dict]:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    dados = conn.execute("""
        SELECT loja, COUNT(*) AS total
        FROM promocoes WHERE loja != ''
        GROUP BY loja ORDER BY total DESC LIMIT 10
    """).fetchall()
    conn.close()
    return [dict(d) for d in dados]


def stats_por_semana() -> list[dict]:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    dados = conn.execute("""
        SELECT semana, COUNT(*) AS total
        FROM promocoes WHERE semana != ''
        GROUP BY semana ORDER BY semana DESC LIMIT 12
    """).fetchall()
    conn.close()
    return list(reversed([dict(d) for d in dados]))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)-7s │ %(message)s")
    importar_csv()
    print(stats_resumo())
    print(stats_por_dia(7))
