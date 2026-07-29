# -*- coding: utf-8 -*-
"""
Painel de controle local do PromoAnalysis.

Abre um painel no navegador (http://localhost:5050) onde você pode:
- Editar os grupos/canais do WhatsApp e do Telegram
- Editar o limite de desconto do alerta e o nome da planilha
- Rodar o pipeline completo com um clique
- Acompanhar o log da última execução em tempo real
- Ver um resumo rápido (total de promoções, última execução)

Requisitos:
    pip install flask

Uso:
    python painel.py
Depois abra http://localhost:5050 no navegador (abre automaticamente).
"""

from __future__ import annotations

import csv
import subprocess
import threading
import webbrowser
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

from config_loader import carregar_config, salvar_config
from db import stats_resumo, stats_por_dia, stats_por_loja, stats_por_semana

app = Flask(__name__)

PASTA_PROJETO = Path(__file__).parent
ARQUIVO_LOG = PASTA_PROJETO / "pipeline_log.txt"
ARQUIVO_CSV = PASTA_PROJETO / "promocoes_whatsapp.csv"
SCRIPT_PIPELINE = PASTA_PROJETO / "run_pipeline.bat"
PASTA_DASHBOARD = PASTA_PROJETO / "dashboard" / "dist"

_estado = {"rodando": False, "processo": None}
_lock = threading.Lock()


def _executar_pipeline_em_thread() -> None:
    with _lock:
        _estado["rodando"] = True
    try:
        processo = subprocess.Popen(
            [str(SCRIPT_PIPELINE)],
            cwd=str(PASTA_PROJETO),
            shell=True,
        )
        with _lock:
            _estado["processo"] = processo
        processo.wait()
    finally:
        with _lock:
            _estado["rodando"] = False
            _estado["processo"] = None


@app.route("/")
def index():
    if PASTA_DASHBOARD.exists():
        return send_from_directory(str(PASTA_DASHBOARD), "index.html")
    return PAGINA_HTML


@app.route("/assets/<path:filename>")
def dashboard_assets(filename):
    return send_from_directory(str(PASTA_DASHBOARD / "assets"), filename)


@app.route("/favicon.svg")
def favicon():
    return "", 204


@app.route("/api/config", methods=["GET"])
def api_config_get():
    return jsonify(carregar_config())


@app.route("/api/config", methods=["POST"])
def api_config_post():
    novo_config = request.get_json(force=True)
    salvar_config(novo_config)
    return jsonify({"ok": True})


@app.route("/api/run", methods=["POST"])
def api_run():
    with _lock:
        if _estado["rodando"]:
            return jsonify({"ok": False, "motivo": "Já está rodando."}), 409

    if not SCRIPT_PIPELINE.exists():
        return jsonify({"ok": False, "motivo": "run_pipeline.bat não encontrado."}), 404

    thread = threading.Thread(target=_executar_pipeline_em_thread, daemon=True)
    thread.start()
    return jsonify({"ok": True})


@app.route("/api/status", methods=["GET"])
def api_status():
    with _lock:
        rodando = _estado["rodando"]
    return jsonify({"rodando": rodando})


@app.route("/api/logs", methods=["GET"])
def api_logs():
    if not ARQUIVO_LOG.exists():
        return jsonify({"conteudo": "(sem execuções ainda)"})
    try:
        with open(ARQUIVO_LOG, "r", encoding="utf-8", errors="replace") as f:
            linhas = f.readlines()
        ultimas = linhas[-200:]
        return jsonify({"conteudo": "".join(ultimas)})
    except Exception as e:
        return jsonify({"conteudo": f"Erro ao ler log: {e}"})


@app.route("/api/stats", methods=["GET"])
def api_stats():
    total_linhas = 0
    if ARQUIVO_CSV.exists():
        try:
            with open(ARQUIVO_CSV, "r", encoding="utf-8-sig", newline="") as f:
                total_linhas = max(sum(1 for _ in csv.reader(f, delimiter=";")) - 1, 0)
        except Exception:
            total_linhas = 0

    ultima_execucao = None
    if ARQUIVO_LOG.exists():
        try:
            ts = ARQUIVO_LOG.stat().st_mtime
            ultima_execucao = datetime.fromtimestamp(ts).strftime("%d/%m/%Y %H:%M")
        except Exception:
            ultima_execucao = None

    config = carregar_config()
    total_fontes = (
        len(config.get("whatsapp_grupos", []))
        + len(config.get("whatsapp_canais", []))
        + len(config.get("telegram_grupos_canais", []))
    )

    return jsonify({
        "total_promocoes": total_linhas,
        "ultima_execucao": ultima_execucao or "—",
        "total_fontes": total_fontes,
        "limite_desconto": config.get("limite_desconto_alerta", 60),
    })


@app.route("/api/promocoes", methods=["GET"])
def api_promocoes():
    return jsonify({
        "resumo": stats_resumo(),
        "por_dia": stats_por_dia(30),
        "por_loja": stats_por_loja(),
        "por_semana": stats_por_semana(),
    })


PAGINA_HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>PromoAnalysis — Painel de Controle</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #0b0d12;
    --bg-soft: #10131a;
    --card: #151922;
    --border: #262b38;
    --text: #eef0f3;
    --muted: #8b93a3;
    --flame-1: #ff6b35;
    --flame-2: #ffb238;
    --flame-grad: linear-gradient(135deg, var(--flame-1), var(--flame-2));
    --success: #3ecf8e;
    --danger: #ff5d6c;
    --radius: 14px;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    font-family: 'Inter', -apple-system, "Segoe UI", sans-serif;
    background:
      radial-gradient(1200px 500px at 15% -10%, rgba(255,107,53,0.10), transparent 60%),
      radial-gradient(900px 500px at 100% 0%, rgba(255,178,56,0.06), transparent 60%),
      var(--bg);
    color: var(--text);
    padding: 28px 32px 48px;
  }
  h1, h2 { font-family: 'Space Grotesk', 'Inter', sans-serif; margin: 0; }

  header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 28px;
    flex-wrap: wrap;
    gap: 16px;
  }
  .brand { display: flex; align-items: center; gap: 12px; }
  .brand .logo-wrap {
    width: 42px; height: 42px;
    border-radius: 11px;
    background: var(--flame-grad);
    display: flex; align-items: center; justify-content: center;
    box-shadow: 0 6px 18px rgba(255,107,53,0.35);
  }
  .brand h1 { font-size: 21px; letter-spacing: -0.02em; }
  .brand .sub { color: var(--muted); font-size: 12.5px; margin-top: 2px; }

  .status-pill {
    display: inline-flex; align-items: center; gap: 8px;
    padding: 7px 14px; border-radius: 999px; font-size: 12.5px; font-weight: 600;
    border: 1px solid var(--border);
  }
  .status-pill.ocioso { color: var(--muted); }
  .status-pill.rodando { color: var(--flame-2); border-color: rgba(255,178,56,0.4); background: rgba(255,178,56,0.08); }
  .dot { width: 7px; height: 7px; border-radius: 50%; background: currentColor; }
  .dot.rodando { animation: pulse 1s infinite; }
  @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.25; } }

  .stats {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
    margin-bottom: 22px;
    max-width: 1180px;
  }
  .stat {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 16px 18px;
  }
  .stat .label { font-size: 11.5px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 6px; }
  .stat .value { font-family: 'Space Grotesk', sans-serif; font-size: 24px; font-weight: 700; }
  .stat .value.flame { background: var(--flame-grad); -webkit-background-clip: text; background-clip: text; color: transparent; }

  .grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    max-width: 1180px;
  }
  .card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 20px;
  }
  .card-head { display: flex; align-items: center; gap: 10px; margin-bottom: 14px; }
  .card-head .icon {
    width: 28px; height: 28px; border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    background: rgba(255,107,53,0.12);
    color: var(--flame-2);
  }
  .card-head h2 { font-size: 13.5px; color: var(--text); text-transform: uppercase; letter-spacing: 0.04em; font-weight: 600; }
  .full { grid-column: 1 / -1; }

  .run-row { display: flex; align-items: center; justify-content: space-between; }

  button.primary {
    background: var(--flame-grad);
    color: #16110a;
    border: none;
    border-radius: 9px;
    padding: 11px 20px;
    font-weight: 700;
    font-size: 13.5px;
    cursor: pointer;
    box-shadow: 0 6px 16px rgba(255,107,53,0.25);
  }
  button.primary:hover { filter: brightness(1.06); }
  button.primary:disabled { background: var(--border); color: var(--muted); box-shadow: none; cursor: not-allowed; }
  button.secondary {
    background: transparent;
    border: 1px solid var(--border);
    color: var(--text);
    border-radius: 8px;
    padding: 9px 14px;
    font-size: 12.5px;
    cursor: pointer;
  }
  button.secondary:hover { border-color: var(--flame-1); color: var(--flame-2); }
  button.danger {
    background: transparent;
    border: 1px solid rgba(255,93,108,0.25);
    color: var(--danger);
    border-radius: 6px;
    padding: 3px 9px;
    font-size: 11px;
    cursor: pointer;
  }
  button.danger:hover { background: rgba(255,93,108,0.12); }

  input[type="text"], input[type="number"] {
    width: 100%;
    background: var(--bg-soft);
    border: 1px solid var(--border);
    border-radius: 8px;
    color: var(--text);
    padding: 9px 11px;
    font-size: 13px;
    font-family: inherit;
  }
  input:focus { outline: none; border-color: var(--flame-1); }

  .lista { display: flex; flex-direction: column; gap: 6px; margin-bottom: 10px; max-height: 240px; overflow-y: auto; }
  .item {
    display: flex; align-items: center; gap: 8px;
    background: var(--bg-soft);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 7px 10px;
    font-size: 13px;
  }
  .item span { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .add-row { display: flex; gap: 8px; }
  .add-row input { flex: 1; }

  .field { margin-bottom: 14px; }
  .field label { display: block; font-size: 12px; color: var(--muted); margin-bottom: 6px; }

  pre#logs {
    background: var(--bg-soft);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 16px;
    height: 300px;
    overflow-y: auto;
    font-family: ui-monospace, Consolas, monospace;
    font-size: 12px;
    line-height: 1.55;
    white-space: pre-wrap;
    word-break: break-word;
    color: #9fdcb8;
  }

  .toast {
    position: fixed; bottom: 22px; right: 22px;
    background: var(--success); color: #06231a;
    padding: 11px 18px; border-radius: 9px;
    font-size: 13px; font-weight: 700;
    opacity: 0; transform: translateY(8px);
    transition: opacity 0.25s, transform 0.25s;
    pointer-events: none;
  }
  .toast.show { opacity: 1; transform: translateY(0); }

  ::-webkit-scrollbar { width: 8px; }
  ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 8px; }
</style>
</head>
<body>

<header>
  <div class="brand">
    <div class="logo-wrap">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
        <path d="M12 2c1.2 3-1.6 4.2-1.6 7 0 1.5 1 2.5 2.3 2.5 1.7 0 2.5-1.4 2.3-3 2 1.8 3 4 3 6.2C18 18.8 15.4 22 12 22s-6-3-6-6.8c0-3.6 2.2-6 3.3-8.4C10 5 11 3.3 12 2Z"
              fill="#16110a"/>
      </svg>
    </div>
    <div>
      <h1>PromoAnalysis</h1>
      <div class="sub">Painel de controle do pipeline de extração de promoções</div>
    </div>
  </div>
  <span id="badge" class="status-pill ocioso"><span class="dot"></span> Ocioso</span>
</header>

<div class="stats">
  <div class="stat">
    <div class="label">Promoções no CSV</div>
    <div class="value flame" id="stat-total">—</div>
  </div>
  <div class="stat">
    <div class="label">Fontes monitoradas</div>
    <div class="value" id="stat-fontes">—</div>
  </div>
  <div class="stat">
    <div class="label">Limite de alerta</div>
    <div class="value" id="stat-limite">—</div>
  </div>
  <div class="stat">
    <div class="label">Última execução</div>
    <div class="value" id="stat-execucao" style="font-size:16px;">—</div>
  </div>
</div>

<div class="grid">

  <div class="card full">
    <div class="run-row">
      <div style="color:var(--muted); font-size:13px;">Roda a extração do WhatsApp e Telegram, envia ao Sheets e verifica alertas de desconto.</div>
      <button class="primary" id="btnRun" onclick="rodarPipeline()">▶ Rodar Pipeline Agora</button>
    </div>
  </div>

  <div class="card">
    <div class="card-head">
      <div class="icon">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.5 2 2 6.5 2 12c0 1.9.5 3.7 1.5 5.3L2 22l4.9-1.3A10 10 0 0 0 12 22c5.5 0 10-4.5 10-10S17.5 2 12 2Z"/></svg>
      </div>
      <h2>Grupos do WhatsApp</h2>
    </div>
    <div class="lista" id="lista-whatsapp_grupos"></div>
    <div class="add-row">
      <input type="text" id="input-whatsapp_grupos" placeholder="Nome exato do grupo">
      <button class="secondary" onclick="adicionarItem('whatsapp_grupos')">+ Adicionar</button>
    </div>
  </div>

  <div class="card">
    <div class="card-head">
      <div class="icon">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10 10-4.5 10-10S17.5 2 12 2Zm4.9 7.2-1.6 7.6c-.1.5-.4.7-.9.4l-2.5-1.8-1.2 1.1c-.1.1-.3.2-.5.2l.2-2.6 4.7-4.3c.2-.2 0-.3-.3-.1l-5.8 3.7-2.5-.8c-.5-.2-.5-.5.1-.7l9.9-3.8c.4-.2.8.1.7.6Z"/></svg>
      </div>
      <h2>Canais do WhatsApp</h2>
    </div>
    <div class="lista" id="lista-whatsapp_canais"></div>
    <div class="add-row">
      <input type="text" id="input-whatsapp_canais" placeholder="Nome (ou parte) do canal">
      <button class="secondary" onclick="adicionarItem('whatsapp_canais')">+ Adicionar</button>
    </div>
  </div>

  <div class="card">
    <div class="card-head">
      <div class="icon">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10 10-4.5 10-10S17.5 2 12 2Zm3.5 8.5c0 1.4-1.1 2.5-2.5 2.5s-2.5-1.1-2.5-2.5S11.6 8 13 8s2.5 1.1 2.5 2.5ZM12 20c-2.4 0-4.5-1-5.9-2.7.5-1.4 1.8-2.4 3.4-2.4h5c1.6 0 2.9 1 3.4 2.4C16.5 19 14.4 20 12 20Z"/></svg>
      </div>
      <h2>Grupos/Canais do Telegram</h2>
    </div>
    <div class="lista" id="lista-telegram_grupos_canais"></div>
    <div class="add-row">
      <input type="text" id="input-telegram_grupos_canais" placeholder="Nome (ou parte) do grupo/canal">
      <button class="secondary" onclick="adicionarItem('telegram_grupos_canais')">+ Adicionar</button>
    </div>
  </div>

  <div class="card">
    <div class="card-head">
      <div class="icon">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2Zm0 2v.01L12 12l8-5.99V6H4Zm16 12V8.24l-7.4 5.55a1 1 0 0 1-1.2 0L4 8.24V18h16Z"/></svg>
      </div>
      <h2>Alertas e Planilha</h2>
    </div>
    <div class="field">
      <label>Limite de desconto para alerta por e-mail (%)</label>
      <input type="number" id="limite_desconto_alerta" min="1" max="100">
    </div>
    <div class="field">
      <label>Nome da planilha no Google Sheets</label>
      <input type="text" id="nome_planilha_sheets">
    </div>
    <button class="primary" onclick="salvarConfig()">💾 Salvar Configurações</button>
  </div>

  <div class="card full">
    <div class="card-head">
      <div class="icon">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor"><path d="M4 4h16v2H4V4Zm0 5h10v2H4V9Zm0 5h16v2H4v-2Zm0 5h10v2H4v-2Z"/></svg>
      </div>
      <h2>Log da última execução</h2>
    </div>
    <pre id="logs">Carregando...</pre>
  </div>

</div>

<div id="toast" class="toast">Salvo!</div>

<script>
let config = {};

async function carregarConfig() {
  const res = await fetch('/api/config');
  config = await res.json();
  renderizarListas();
  document.getElementById('limite_desconto_alerta').value = config.limite_desconto_alerta;
  document.getElementById('nome_planilha_sheets').value = config.nome_planilha_sheets;
}

function renderizarListas() {
  for (const chave of ['whatsapp_grupos', 'whatsapp_canais', 'telegram_grupos_canais']) {
    const container = document.getElementById('lista-' + chave);
    container.innerHTML = '';
    (config[chave] || []).forEach((nome, idx) => {
      const div = document.createElement('div');
      div.className = 'item';
      div.innerHTML = `<span title="${nome}">${nome}</span><button class="danger" onclick="removerItem('${chave}', ${idx})">remover</button>`;
      container.appendChild(div);
    });
  }
}

function adicionarItem(chave) {
  const input = document.getElementById('input-' + chave);
  const valor = input.value.trim();
  if (!valor) return;
  config[chave] = config[chave] || [];
  config[chave].push(valor);
  input.value = '';
  renderizarListas();
}

function removerItem(chave, idx) {
  config[chave].splice(idx, 1);
  renderizarListas();
}

async function salvarConfig() {
  config.limite_desconto_alerta = parseInt(document.getElementById('limite_desconto_alerta').value, 10);
  config.nome_planilha_sheets = document.getElementById('nome_planilha_sheets').value;
  await fetch('/api/config', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(config),
  });
  mostrarToast();
  atualizarStats();
}

function mostrarToast() {
  const t = document.getElementById('toast');
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2000);
}

async function rodarPipeline() {
  const res = await fetch('/api/run', { method: 'POST' });
  if (res.ok) atualizarStatus();
}

async function atualizarStatus() {
  const res = await fetch('/api/status');
  const data = await res.json();
  const badge = document.getElementById('badge');
  const btn = document.getElementById('btnRun');
  if (data.rodando) {
    badge.className = 'status-pill rodando';
    badge.innerHTML = '<span class="dot rodando"></span> Rodando...';
    btn.disabled = true;
  } else {
    badge.className = 'status-pill ocioso';
    badge.innerHTML = '<span class="dot"></span> Ocioso';
    btn.disabled = false;
  }
}

async function atualizarLogs() {
  const res = await fetch('/api/logs');
  const data = await res.json();
  const pre = document.getElementById('logs');
  const estavaNoFim = pre.scrollTop + pre.clientHeight >= pre.scrollHeight - 10;
  pre.textContent = data.conteudo;
  if (estavaNoFim) pre.scrollTop = pre.scrollHeight;
}

async function atualizarStats() {
  const res = await fetch('/api/stats');
  const data = await res.json();
  document.getElementById('stat-total').textContent = data.total_promocoes.toLocaleString('pt-BR');
  document.getElementById('stat-fontes').textContent = data.total_fontes;
  document.getElementById('stat-limite').textContent = data.limite_desconto + '%';
  document.getElementById('stat-execucao').textContent = data.ultima_execucao;
}

carregarConfig();
atualizarStatus();
atualizarLogs();
atualizarStats();
setInterval(atualizarStatus, 2000);
setInterval(atualizarLogs, 3000);
setInterval(atualizarStats, 5000);
</script>

</body>
</html>
"""


if __name__ == "__main__":
    threading.Timer(1.2, lambda: webbrowser.open("http://localhost:5050")).start()
    app.run(host="127.0.0.1", port=5050, debug=False)
