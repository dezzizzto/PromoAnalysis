# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════╗
║  WhatsApp Promotions Extractor                                       ║
║  Extrai dados de promoções de conversas do WhatsApp Web              ║
║  e salva em planilha CSV para análise de preços.                     ║
╚══════════════════════════════════════════════════════════════════════╝

Requisitos:
    pip install selenium webdriver-manager

Uso:
    python whatsapp_promo_extractor.py

Ao rodar pela primeira vez, escaneie o QR Code do WhatsApp Web.
O perfil do Chrome é salvo em ./chrome_profile para manter a sessão.
"""

from __future__ import annotations

import csv
import os
import re
import sys
import time
import logging
from datetime import datetime
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
)
from webdriver_manager.chrome import ChromeDriverManager

# ─────────────────────────────────────────────────────────────────────
# CONFIGURAÇÃO — Edite aqui conforme sua necessidade
# ─────────────────────────────────────────────────────────────────────

CONVERSAS_ALVO: list[str] = [
    "Lobão das Promoções #136",
    "Investiguei Ofertas #139",
    "REI DA PROMO | 654",
    "#93 Estilo Masculino | Ofertas & Achados"
]

MAX_MENSAGENS_POR_CONVERSA: int | None = 500
SCROLLS_PARA_CARREGAR: int = 25
ARQUIVO_SAIDA: str = "promocoes_whatsapp.csv"
CHROME_PROFILE_DIR: str = os.path.join(os.path.dirname(__file__), "chrome_profile")
TIMEOUT_QR_CODE: int = 120
TIMEOUT_ELEMENTO: int = 30

# ─────────────────────────────────────────────────────────────────────
# PALAVRAS-CHAVE E PADRÕES (PT-BR)
# ─────────────────────────────────────────────────────────────────────

KEYWORDS_PROMOCAO: list[str] = [
    "preço", "preco", "valor", "custa", "custando",
    "reais", "r$", "real", "centavos",
    "promoção", "promocao", "promoçao", "promo",
    "desconto", "oferta", "liquidação", "liquidacao",
    "queima", "queima de estoque", "saldão", "saldao",
    "black friday", "mega oferta",
    "compre", "leve", "pague", "grátis", "gratis", "gratuito",
    "frete grátis", "frete gratis", "cashback",
    "cupom", "código", "codigo", "voucher",
    "de/por", "era", "agora", "antes", "depois",
    "baixou", "caiu", "abaixou", "reduziu",
    "kg", "un", "unidade", "pacote", "caixa", "litro",
    "ml", "cada",
]

REGEX_PRECO = re.compile(
    r"R\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{1,2})?)"
    r"|"
    r"R\$\s*(\d+(?:,\d{1,2})?)"
    r"|"
    r"(\d{1,3}(?:\.\d{3})*,\d{2})\s*(?:reais|real)",
    re.IGNORECASE,
)

REGEX_DESCONTO = re.compile(
    r"(\d{1,3})\s*%\s*(?:de\s+)?(?:desc(?:onto)?|off)",
    re.IGNORECASE,
)

REGEX_DE_POR = re.compile(
    r"de\s+R?\$?\s*(\d[\d.,]*)\s+por\s+R?\$?\s*(\d[\d.,]*)",
    re.IGNORECASE,
)

# ─────────────────────────────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-7s │ %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("whatsapp_extractor")

# ─────────────────────────────────────────────────────────────────────
# DATA CLASSES
# ─────────────────────────────────────────────────────────────────────


@dataclass
class DadosPromocao:
    """Representa uma promoção extraída de uma mensagem."""

    conversa: str = ""
    remetente: str = ""
    data_hora_mensagem: str = ""
    texto_original: str = ""
    produtos_detectados: str = ""
    preco_encontrado: str = ""
    preco_anterior: str = ""
    desconto_percentual: str = ""
    keywords_encontradas: str = ""
    data_extracao: str = field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )


# ─────────────────────────────────────────────────────────────────────
# FUNÇÕES AUXILIARES
# ─────────────────────────────────────────────────────────────────────


def normalizar_texto(texto: str) -> str:
    return texto.lower().strip()


def contem_keyword(texto: str) -> list[str]:
    texto_norm = normalizar_texto(texto)
    return [kw for kw in KEYWORDS_PROMOCAO if kw in texto_norm]


def extrair_precos(texto: str) -> list[str]:
    precos = []
    for match in REGEX_PRECO.finditer(texto):
        valor = next((g for g in match.groups() if g), None)
        if valor:
            precos.append(f"R$ {valor}")
    return precos


def extrair_desconto(texto: str) -> Optional[str]:
    match = REGEX_DESCONTO.search(texto)
    return f"{match.group(1)}%" if match else None


def extrair_de_por(texto: str) -> tuple[Optional[str], Optional[str]]:
    match = REGEX_DE_POR.search(texto)
    if match:
        return (f"R$ {match.group(1)}", f"R$ {match.group(2)}")
    return (None, None)


def eh_mensagem_promocional(texto: str) -> bool:
    if not texto or len(texto.strip()) < 5:
        return False

    texto_norm = normalizar_texto(texto)
    keywords = contem_keyword(texto)
    tem_preco = bool(REGEX_PRECO.search(texto))
    tem_desconto = bool(REGEX_DESCONTO.search(texto))

    keywords_fortes = {"promoção", "promocao", "oferta", "desconto", "promo",
                       "liquidação", "liquidacao", "queima", "saldão", "saldao"}
    tem_keyword_forte = bool(keywords_fortes.intersection(set(keywords)))

    return (len(keywords) >= 1 and tem_preco) or tem_keyword_forte or tem_desconto


def analisar_mensagem(conversa: str, remetente: str, data_hora: str,
                      texto: str) -> Optional[DadosPromocao]:
    if not eh_mensagem_promocional(texto):
        return None

    keywords = contem_keyword(texto)
    precos = extrair_precos(texto)
    desconto = extrair_desconto(texto)
    preco_anterior, preco_de_por = extrair_de_por(texto)

    preco_principal = preco_de_por if preco_de_por else (precos[0] if precos else "")

    if preco_de_por and preco_de_por in precos:
        precos.remove(preco_de_por)

    return DadosPromocao(
        conversa=conversa,
        remetente=remetente,
        data_hora_mensagem=data_hora,
        texto_original=texto[:500],
        preco_encontrado=preco_principal or "; ".join(precos),
        preco_anterior=preco_anterior or "",
        desconto_percentual=desconto or "",
        keywords_encontradas="; ".join(keywords),
    )


# ─────────────────────────────────────────────────────────────────────
# WHATSAPP WEB — AUTOMAÇÃO COM SELENIUM
# ─────────────────────────────────────────────────────────────────────


class WhatsAppExtractor:
    """Controla o Chrome para interagir com o WhatsApp Web."""

    WHATSAPP_URL = "https://web.whatsapp.com"

    def __init__(self) -> None:
        self.driver: Optional[webdriver.Chrome] = None
        self.resultados: list[DadosPromocao] = []

    # ── Ciclo de vida ──────────────────────────────────────────────

    def iniciar_navegador(self) -> None:
        log.info("Iniciando navegador Chrome...")

        opcoes = Options()
        opcoes.add_argument(f"--user-data-dir={CHROME_PROFILE_DIR}")
        opcoes.add_argument("--no-sandbox")
        opcoes.add_argument("--disable-dev-shm-usage")
        opcoes.add_argument("--disable-gpu")
        opcoes.add_argument("--window-size=1400,900")
        opcoes.add_experimental_option("excludeSwitches", ["enable-automation"])
        opcoes.add_experimental_option("useAutomationExtension", False)
        opcoes.add_argument("--disable-blink-features=AutomationControlled")

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=opcoes)
        self.driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

    def abrir_whatsapp(self) -> None:
        log.info("Abrindo WhatsApp Web...")
        self.driver.get(self.WHATSAPP_URL)

        log.info(
            "Aguardando carregamento (escaneie o QR Code se necessário)... "
            f"Timeout: {TIMEOUT_QR_CODE}s"
        )

        try:
            WebDriverWait(self.driver, TIMEOUT_QR_CODE).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '#pane-side'))
            )
            log.info("✔ WhatsApp Web carregado com sucesso!")
            time.sleep(3)
        except TimeoutException:
            log.error(
                "✘ Timeout ao aguardar login. "
                "Verifique se o QR Code foi escaneado."
            )
            self.fechar()
            sys.exit(1)

    def fechar(self) -> None:
        if self.driver:
            log.info("Fechando navegador...")
            self.driver.quit()
            self.driver = None

    # ── Navegação ──────────────────────────────────────────────────

    def _encontrar_caixa_busca(self):
        """Tenta localizar a barra de pesquisa com múltiplos seletores.

        OBS: o WhatsApp Web passou a usar um <input> real para a busca,
        em vez de uma div contenteditable. O aria-label é o mais estável.
        """
        seletores = [
            'input[aria-label="Pesquisar ou começar uma nova conversa"]',
            'input[aria-label="Search or start new chat"]',
            'input[placeholder="Pesquisar ou começar uma nova conversa"]',
            'input[placeholder="Search or start new chat"]',
            'input[data-tab="3"]',
            'div[contenteditable="true"][role="textbox"][title="Pesquisar ou começar uma nova conversa"]',
            'div[contenteditable="true"][role="textbox"]',
        ]

        for seletor in seletores:
            try:
                elem = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, seletor))
                )
                log.debug(f"Caixa de busca encontrada com seletor: {seletor}")
                return elem
            except TimeoutException:
                continue

        try:
            side = self.driver.find_element(By.CSS_SELECTOR, "#side")
            log.debug(f"HTML do #side (primeiros 2000 chars): {side.get_attribute('innerHTML')[:2000]}")
        except Exception:
            log.debug("Elemento #side não encontrado.")

        return None

    def buscar_e_abrir_conversa(self, nome_conversa: str) -> bool:
        log.info(f'Buscando conversa: "{nome_conversa}"...')
        try:
            caixa_busca = self._encontrar_caixa_busca()
            if not caixa_busca:
                log.warning(
                    f'✘ Não foi possível localizar a barra de pesquisa. '
                    f'O WhatsApp Web pode ter atualizado sua interface.'
                )
                return False

            caixa_busca.click()
            time.sleep(0.5)

            caixa_busca.send_keys(Keys.CONTROL + "a")
            caixa_busca.send_keys(Keys.DELETE)
            time.sleep(0.3)

            for char in nome_conversa:
                caixa_busca.send_keys(char)
                time.sleep(0.05)

            time.sleep(2)

            resultados = self.driver.find_elements(
                By.CSS_SELECTOR, f'span[title="{nome_conversa}"]'
            )

            if not resultados:
                resultados = self.driver.find_elements(
                    By.XPATH,
                    f'//span[contains(@title, "{nome_conversa}")]'
                )

            if not resultados:
                resultados = self.driver.find_elements(
                    By.XPATH,
                    f'//span[contains(text(), "{nome_conversa}")]'
                )

            if not resultados:
                resultados = self.driver.find_elements(
                    By.XPATH,
                    f'//div[@role="listitem"]//span[contains(@title, "{nome_conversa.split()[0]}")]'
                )

            if resultados:
                resultados[0].click()
                time.sleep(2)
                log.info(f'✔ Conversa "{nome_conversa}" aberta.')
                return True
            else:
                log.warning(f'✘ Conversa "{nome_conversa}" não encontrada nos resultados.')
                try:
                    todos_spans = self.driver.find_elements(
                        By.CSS_SELECTOR, '#side span[title]'
                    )
                    titulos = [s.get_attribute("title") for s in todos_spans[:10]]
                    log.info(f"  Títulos visíveis no painel: {titulos}")
                except Exception:
                    pass
                return False

        except TimeoutException:
            log.warning(f'✘ Timeout ao buscar "{nome_conversa}".')
            return False
        except Exception as e:
            log.error(f'Erro ao buscar "{nome_conversa}": {e}')
            return False

    # ── Extração de Mensagens ──────────────────────────────────────

    def _scroll_para_carregar_mensagens(self) -> None:
        log.info(f"Carregando mensagens anteriores ({SCROLLS_PARA_CARREGAR} scrolls)...")

        try:
            painel_mensagens = self.driver.find_element(
                By.CSS_SELECTOR, 'div[data-tab="8"]'
            )
        except NoSuchElementException:
            try:
                painel_mensagens = self.driver.find_element(
                    By.CSS_SELECTOR, "#main div.copyable-area > div:nth-child(1)"
                )
            except NoSuchElementException:
                log.warning("Não foi possível localizar o painel de mensagens para scroll.")
                return

        for i in range(SCROLLS_PARA_CARREGAR):
            self.driver.execute_script(
                "arguments[0].scrollTop = 0;", painel_mensagens
            )
            time.sleep(0.8)

            if (i + 1) % 10 == 0:
                log.info(f"  ... {i + 1}/{SCROLLS_PARA_CARREGAR} scrolls realizados")

    def extrair_mensagens_conversa(self, nome_conversa: str) -> list[DadosPromocao]:
        promocoes: list[DadosPromocao] = []

        self._scroll_para_carregar_mensagens()
        time.sleep(1)

        mensagens_elements = self.driver.find_elements(
            By.CSS_SELECTOR,
            'div.message-in, div.message-out, '
            'div[data-pre-plain-text], '
            'div[class*="message-in"], div[class*="message-out"]'
        )

        if not mensagens_elements:
            mensagens_elements = self.driver.find_elements(
                By.CSS_SELECTOR, "div.copyable-text"
            )

        log.info(f"Encontradas {len(mensagens_elements)} mensagens no chat.")

        processadas = 0
        for elem in mensagens_elements:
            if MAX_MENSAGENS_POR_CONVERSA and processadas >= MAX_MENSAGENS_POR_CONVERSA:
                break

            try:
                resultado = self._processar_elemento_mensagem(elem, nome_conversa)
                if resultado:
                    promocoes.append(resultado)
                processadas += 1
            except StaleElementReferenceException:
                continue
            except Exception as e:
                log.debug(f"Erro ao processar mensagem: {e}")
                continue

        log.info(
            f'✔ {len(promocoes)} promoções encontradas em "{nome_conversa}" '
            f'(de {processadas} mensagens analisadas).'
        )
        return promocoes

    def _processar_elemento_mensagem(
        self, elem, nome_conversa: str
    ) -> Optional[DadosPromocao]:
        texto = ""

        spans = elem.find_elements(
            By.CSS_SELECTOR, "span.selectable-text span"
        )
        if spans:
            texto = " ".join(s.text for s in spans if s.text)

        if not texto:
            texto = elem.text

        if not texto or len(texto.strip()) < 5:
            return None

        remetente = ""
        try:
            remetente_elem = elem.find_element(
                By.CSS_SELECTOR, 'span[data-testid="author"]'
            )
            remetente = remetente_elem.text
        except NoSuchElementException:
            pass

        if not remetente:
            try:
                remetente_elem = elem.find_element(
                    By.CSS_SELECTOR, "span.UY4W4"
                )
                remetente = remetente_elem.text
            except NoSuchElementException:
                pass

        if not remetente:
            classes = elem.get_attribute("class") or ""
            remetente = "Eu" if "message-out" in classes else "Desconhecido"

        data_hora = ""
        pre_text = elem.get_attribute("data-pre-plain-text") or ""
        if pre_text:
            match_dt = re.search(r"\[(.+?)\]", pre_text)
            if match_dt:
                data_hora = match_dt.group(1)

        if not data_hora:
            try:
                hora_elem = elem.find_element(
                    By.CSS_SELECTOR, 'span[data-testid="msg-time"], div[data-pre-plain-text]'
                )
                data_hora = hora_elem.text or hora_elem.get_attribute("data-pre-plain-text") or ""
            except NoSuchElementException:
                data_hora = "N/D"

        return analisar_mensagem(nome_conversa, remetente, data_hora, texto)

    # ── Pipeline principal ─────────────────────────────────────────

    def executar(self) -> None:
        if not CONVERSAS_ALVO:
            log.error("Nenhuma conversa configurada em CONVERSAS_ALVO. Encerrando.")
            return

        try:
            self.iniciar_navegador()
            self.abrir_whatsapp()

            for i, nome in enumerate(CONVERSAS_ALVO, 1):
                log.info(f"\n{'═' * 60}")
                log.info(f"Processando conversa {i}/{len(CONVERSAS_ALVO)}: {nome}")
                log.info(f"{'═' * 60}")

                if self.buscar_e_abrir_conversa(nome):
                    promocoes = self.extrair_mensagens_conversa(nome)
                    self.resultados.extend(promocoes)
                    time.sleep(1)

            if self.resultados:
                self._salvar_csv()
            else:
                log.warning("Nenhuma promoção encontrada nas conversas analisadas.")

        except KeyboardInterrupt:
            log.info("\nInterrompido pelo usuário.")
            if self.resultados:
                log.info("Salvando dados coletados até o momento...")
                self._salvar_csv()
        except Exception as e:
            log.error(f"Erro inesperado: {e}", exc_info=True)
        finally:
            self.fechar()

    def _salvar_csv(self) -> None:
        caminho = Path(ARQUIVO_SAIDA)
        colunas = [
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

        with open(caminho, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=colunas, delimiter=";")
            writer.writeheader()
            for promo in self.resultados:
                row = asdict(promo)
                row.pop("produtos_detectados", None)
                writer.writerow(row)

        log.info(f"\n{'═' * 60}")
        log.info(f"✔ {len(self.resultados)} promoções salvas em: {caminho.resolve()}")
        log.info(f"{'═' * 60}")


# ─────────────────────────────────────────────────────────────────────
# PONTO DE ENTRADA
# ─────────────────────────────────────────────────────────────────────

def main() -> None:
    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║        WhatsApp Promotions Extractor v1.0                   ║")
    print("║        Extração de Promoções do WhatsApp Web                ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    print(f"  Conversas configuradas: {len(CONVERSAS_ALVO)}")
    for c in CONVERSAS_ALVO:
        print(f"    • {c}")
    print(f"  Arquivo de saída:       {ARQUIVO_SAIDA}")
    print(f"  Max mensagens/conversa: {MAX_MENSAGENS_POR_CONVERSA or 'Sem limite'}")
    print()

    extractor = WhatsAppExtractor()
    extractor.executar()


if __name__ == "__main__":
    main()