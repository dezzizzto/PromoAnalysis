# -*- coding: utf-8 -*-
"""
Módulo compartilhado para ler e escrever config.json — o arquivo central
de configuração usado por todos os scripts do projeto (grupos, canais,
limite de desconto, nome da planilha) e editável pelo painel (painel.py).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ARQUIVO_CONFIG = Path(__file__).parent / "config.json"

PADRAO: dict[str, Any] = {
    "whatsapp_grupos": [],
    "whatsapp_canais": [],
    "telegram_grupos_canais": [],
    "limite_desconto_alerta": 60,
    "max_mensagens_por_conversa": 500,
}


def carregar_config() -> dict[str, Any]:
    """Lê config.json. Se não existir, cria com valores padrão."""
    if not ARQUIVO_CONFIG.exists():
        salvar_config(PADRAO)
        return dict(PADRAO)

    with open(ARQUIVO_CONFIG, "r", encoding="utf-8") as f:
        config = json.load(f)

    # Garante que chaves novas (adicionadas em versões futuras) tenham
    # um valor padrão, mesmo em config.json antigos.
    for chave, valor in PADRAO.items():
        config.setdefault(chave, valor)

    return config


def salvar_config(config: dict[str, Any]) -> None:
    with open(ARQUIVO_CONFIG, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
