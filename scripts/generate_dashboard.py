#!/usr/bin/env python3
"""
Genera docs/index.html — Dashboard Validación Tesis Escasez y Resiliencia
Sin dependencias externas. Lee historico/macro_snapshot.json.
Uso: python3 scripts/generate_dashboard.py
"""
import json, math, os, sys
from datetime import datetime
from pathlib import Path

ROOT     = Path(__file__).parent.parent
SNAP     = ROOT / "historico" / "macro_snapshot.json"
OUT_DIR  = ROOT / "docs"
OUT_FILE = OUT_DIR / "index.html"

# ── Cargar datos ──────────────────────────────────────────────────────────────
if not SNAP.exists():
    print(f"ERROR: {SNAP} no existe. Ejecuta primero macro_recorder.py")
    sys.exit(1)

with open(SNAP, encoding="utf-8") as f:
    snap = json.load(f)

ind     = snap.get("indicadores", {})
updated = snap.get("updated", "—")

# ── Helpers ───────────────────────────────────────────────────────────────────
def gv(k):
    """(valor, chg_1m, nombre)"""
    v = ind.get(k, {})
    return v.get("valor"), v.get("chg_1mes"), v.get("nombre", k)

def fval(v, dec=2, unit=""):
    if v is None: return "—"
    return f"{v:,.{dec}f}{unit}".replace(",", ".")

def fchg(c, unit="%"):
    if c is None: return '<span style="color:#888">—</span>'
    col = "#4ade80" if c >= 0 else "#f87171"
    sign = "+" if c >= 0 else ""
    return f'<span style="color:{col}">{sign}{c:.1f}{unit}</span>'

# ── Calcular señales ──────────────────────────────────────────────────────────
sox_v,   sox_1m,  _  = gv("SOX")
cop_v,   cop_1m,  _  = gv("COPPER")
nas_v,   nas_1m,  _  = gv("NASDAQ")
robo_v,  robo_1m, _  = gv("ROBO")
qtum_v,  qtum_1m, _  = gv("QTUM")
btc_v,   btc_1m,  _  = gv("BTC")
ur_v,    ur_1m,   _  = gv("URANIUM")
xlu_v,   xlu_1m,  _  = gv("XLU")
gold_v,  gold_1m, _  = gv("GOLD")
sp_v,    sp_1m,   _  = gv("SPREAD")
vix_v,   vix_1m,  _  = gv("VIX")

sox_up   = sox_1m  is not None and sox_1m  >= 2
cop_up   = cop_1m  is not None and cop_1m  >= 2
nas_ok   = nas_1m  is not None and nas_1m  >= 2
robo_ok  = robo_1m is not None and robo_1m >= 2
qtum_ok  = qtum_1m is not None and qtum_1m >= 3
btc_mom  = btc_1m  is not None and btc_1m  >= 5
btc_beat = btc_1m  is not None and nas_1m  is not None and btc_1m > nas_1m
ur_ok    = ur_1m   is not None and ur_1m   >= 2
xlu_ok   = xlu_1m  is not None and xlu_1m  >= 1
gold_ok  = gold_1m is not None and gold_1m >= 2
spr_ok   = sp_v    is not None and sp_v    > 0.3
vix_ok   = vix_v   is not None and vix_v   < 20

checks = [sox_up, nas_ok, robo_ok, qtum_ok, btc_mom, btc_beat, ur_ok, xlu_ok, cop_up, gold_ok, spr_ok, vix_ok]
score_n   = sum(1 for c in checks if c)
score_pct = score_n / len(checks) * 100

if score_pct >= 65:
    score_label = "TESIS EN MARCHA"
    score_col   = "#4ade80"
elif score_pct >= 40:
    score_label = "SEÑALES MIXTAS"
    score_col   = "#facc15"
else:
    score_label = "TESIS DÉBIL"
    score_col   = "#f87171"

# Correlación SOX/Cobre
if sox_up and cop_up:
    corr_icon, corr_label, corr_col, corr_msg = (
        "🟢", "ERA DE CONSTRUCCIÓN", "#4ade80",
        "Mantener metales + IA — tesis completa en marcha")
elif sox_up and not cop_up:
    corr_icon, corr_label, corr_col, corr_msg = (
        "🔴", "DIVERGENCIA · ALERTA", "#f87171",
        "Vigilar rotación: reducir mineras, reforzar IA pura")
elif not sox_up and cop_up:
    corr_icon, corr_label, corr_col, corr_msg = (
        "🟡", "ESCASEZ FÍSICA", "#facc15",
        "Metales fuertes — esperar confirmación de rebote en SOX")
else:
    corr_icon, corr_label, corr_col, corr_msg = (
        "🔴", "CONTRACCIÓN", "#f87171",
        "Modo defensivo — esperar estabilización")

bar_pct = int(score_pct)

# ── SVG helpers ───────────────────────────────────────────────────────────────
def svg_bar_chart(data, w=640, h=160):
    """data = [(label, value, color)] — valores pueden ser negativos."""
    if not data: return ""
    vals   = [d[1] for d in data if d[1] is not None]
    if not vals: return ""
    mn, mx = min(min(vals), 0), max(max(vals), 0)
    rng    = mx - mn or 1
    pad    = 40
    bw     = (w - pad*2) / len(data)
    zero_y = pad + (mx / rng) * (h - pad*2)

    bars = []
    for i, (lbl, v, col) in enumerate(data):
        if v is None: continue
        x      = pad + i * bw + bw * 0.1
        bw2    = bw * 0.8
        bar_h  = abs(v) / rng * (h - pad*2)
        y      = zero_y - max(v, 0) / rng * (h - pad*2)
        bars.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw2:.1f}" height="{bar_h:.1f}" '
            f'fill="{col}" rx="3"/>')
        lbl_y  = h - 4
        bars.append(
            f'<text x="{x+bw2/2:.1f}" y="{lbl_y}" text-anchor="middle" '
            f'font-size="9" fill="#888">{lbl}</text>')
        sign = "+" if v >= 0 else ""
        val_y = y - 4 if v >= 0 else y + bar_h + 10
        bars.append(
            f'<text x="{x+bw2/2:.1f}" y="{val_y:.1f}" text-anchor="middle" '
            f'font-size="9" fill="{col}">{sign}{v:.1f}%</text>')

    # Zero line
    bars.append(
        f'<line x1="{pad}" y1="{zero_y:.1f}" x2="{w-pad}" y2="{zero_y:.1f}" '
        f'stroke="#444" stroke-width="1"/>')

    return (f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" '
            f'style="width:100%;height:{h}px;display:block">'
            + "".join(bars) + "</svg>")


# Datos para el gráfico de barras (variación 1M de los indicadores clave)
chart_data = []
for k, lbl in [("SOX","SOX"), ("COPPER","Cobre"), ("NASDAQ","NASDAQ"),
                ("BTC","BTC"), ("URANIUM","Uranio"), ("XLU","XLU"),
                ("GOLD","Oro"), ("SP500","S&P500")]:
    v = ind.get(k, {}).get("chg_1mes")
    col = "#4ade80" if (v is not None and v >= 0) else "#f87171"
    chart_data.append((lbl, v, col))

chart_svg = svg_bar_chart(chart_data)

# ── Señales por pilar (HTML) ──────────────────────────────────────────────────
def signal_row(icon, label, val_s, chg_html, condition, ok):
    dot = '<span style="color:#4ade80;font-size:1.1em">🟢</span>' if ok else \
          '<span style="color:#f87171;font-size:1.1em">🔴</span>'
    return f"""
        <tr>
          <td style="padding:6px 10px;color:#ccc">{icon} {label}</td>
          <td style="padding:6px 10px;color:#fff;text-align:right">{val_s}</td>
          <td style="padding:6px 10px;text-align:right">{chg_html}</td>
          <td style="padding:6px 10px;color:#666;font-size:.85em">{condition}</td>
          <td style="padding:6px 10px;text-align:center">{dot}</td>
        </tr>"""

signals_html = ""
# Autoreplicación IA
signals_html += f'<tr><td colspan="5" style="padding:8px 10px 2px;color:#38bdf8;font-weight:bold;font-size:.8em;letter-spacing:.1em">AUTOREPLICACIÓN IA</td></tr>'
signals_html += signal_row("📡","SOX Semiconductores", fval(sox_v,2,""),  fchg(sox_1m),  "+2%/1M", sox_up)
signals_html += signal_row("💻","NASDAQ Tech",          fval(nas_v,0,""),  fchg(nas_1m),  "+2%/1M", nas_ok)
signals_html += signal_row("🤖","ROBO Robótica",        fval(robo_v,2,""), fchg(robo_1m), "+2%/1M", robo_ok)
signals_html += signal_row("⚛","QTUM Cuántica",         fval(qtum_v,2,""), fchg(qtum_1m), "+3%/1M", qtum_ok)

signals_html += f'<tr><td colspan="5" style="padding:8px 10px 2px;color:#facc15;font-weight:bold;font-size:.8em;letter-spacing:.1em">ESCASEZ DIGITAL</td></tr>'
signals_html += signal_row("₿","BTC momentum",        fval(btc_v,0,"€"), fchg(btc_1m), "+5%/1M", btc_mom)
btc_beat_chg  = fchg(btc_1m) if btc_1m is not None else '—'
signals_html += signal_row("₿","BTC vs NASDAQ",       "—", btc_beat_chg, "BTC > NASDAQ 1M", btc_beat)

signals_html += f'<tr><td colspan="5" style="padding:8px 10px 2px;color:#fb923c;font-weight:bold;font-size:.8em;letter-spacing:.1em">ENERGÍA / GRID</td></tr>'
signals_html += signal_row("⚛️","Uranio (Cameco)",     fval(ur_v,2,"$"), fchg(ur_1m), "+2%/1M", ur_ok)
signals_html += signal_row("⚡","XLU Utilities",       fval(xlu_v,2,"$"), fchg(xlu_1m), "+1%/1M", xlu_ok)

signals_html += f'<tr><td colspan="5" style="padding:8px 10px 2px;color:#86efac;font-weight:bold;font-size:.8em;letter-spacing:.1em">ESCASEZ FÍSICA</td></tr>'
signals_html += signal_row("🟠","Cobre",               fval(cop_v,3,"$"), fchg(cop_1m), "+2%/1M", cop_up)
signals_html += signal_row("🥇","Oro",                  fval(gold_v,0,"$"), fchg(gold_1m), "+2%/1M", gold_ok)

signals_html += f'<tr><td colspan="5" style="padding:8px 10px 2px;color:#94a3b8;font-weight:bold;font-size:.8em;letter-spacing:.1em">RESILIENCIA</td></tr>'
signals_html += signal_row("📈","Spread 10Y-13W",      fval(sp_v,2,"%"), "—", ">0.3%", spr_ok)
signals_html += signal_row("😰","VIX Volatilidad",     fval(vix_v,1,""), "—", "<20", vix_ok)

# Contexto
def ctx_row(k, label, dec=2, unit=""):
    v, c1m, _ = gv(k)
    return f"""<div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid #1e293b">
      <span style="color:#94a3b8">{label}</span>
      <span style="color:#fff">{fval(v,dec,unit)}&nbsp;&nbsp;{fchg(c1m)}</span>
    </div>"""

ctx_html  = ctx_row("SP500",  "S&P 500",    0)
ctx_html += ctx_row("VIX",    "VIX",        1)
ctx_html += ctx_row("SPREAD", "Spread 10Y-13W", 2, "%")
ctx_html += ctx_row("EURUSD", "EUR/USD",    4)
ctx_html += ctx_row("GOLD",   "Oro (USD)",  0, "$")
ctx_html += ctx_row("OIL",    "Petróleo WTI", 1, "$")

# ── Generar HTML ──────────────────────────────────────────────────────────────
html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>⚡ Tesis Escasez y Resiliencia</title>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{background:#0a0f1a;color:#e2e8f0;font-family:'Segoe UI',system-ui,sans-serif;min-height:100vh}}
  .wrap{{max-width:900px;margin:0 auto;padding:24px 16px}}
  h1{{font-size:1.4rem;font-weight:700;letter-spacing:.05em}}
  h2{{font-size:.85rem;font-weight:600;letter-spacing:.12em;text-transform:uppercase;margin-bottom:12px}}
  .card{{background:#0f172a;border:1px solid #1e293b;border-radius:10px;padding:20px;margin-bottom:18px}}
  .grid2{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}
  @media(max-width:600px){{.grid2{{grid-template-columns:1fr}}}}
  .kpi{{text-align:center}}
  .kpi .val{{font-size:2rem;font-weight:700;line-height:1.1}}
  .kpi .lbl{{font-size:.75rem;color:#64748b;margin-top:4px;text-transform:uppercase;letter-spacing:.08em}}
  table{{width:100%;border-collapse:collapse}}
  .bar-bg{{background:#1e293b;border-radius:999px;height:12px;overflow:hidden;margin:8px 0}}
  .bar-fg{{height:12px;border-radius:999px;transition:width .4s}}
  .tag{{display:inline-block;padding:3px 10px;border-radius:999px;font-size:.8rem;font-weight:600}}
  .upd{{color:#475569;font-size:.8rem}}
</style>
</head>
<body>
<div class="wrap">

  <!-- Header -->
  <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:20px;flex-wrap:wrap;gap:8px">
    <div>
      <h1>⚡ Tesis Escasez y Resiliencia</h1>
      <p style="color:#475569;font-size:.85rem;margin-top:4px">
        V(t) = Capital × (1+r)ᵗ × Φ_L(t) &nbsp;·&nbsp; Jose Vilar
      </p>
    </div>
    <div style="text-align:right">
      <span class="tag" style="background:{score_col}22;color:{score_col};border:1px solid {score_col}44">
        {score_label}
      </span>
      <p class="upd" style="margin-top:6px">Datos: {updated}</p>
    </div>
  </div>

  <!-- Score y correlación SOX/Cobre -->
  <div class="card">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;flex-wrap:wrap;gap:8px">
      <h2 style="margin:0;color:#38bdf8">⚡ SCORE ESCASEZ</h2>
      <span style="font-size:1.5rem;font-weight:700;color:{score_col}">{score_pct:.0f}%
        <span style="font-size:.9rem;color:#64748b">({score_n}/12)</span>
      </span>
    </div>
    <div class="bar-bg">
      <div class="bar-fg" style="width:{bar_pct}%;background:{score_col}"></div>
    </div>
    <div style="margin-top:16px;padding:14px;background:#0a0f1a;border-radius:8px;border-left:3px solid {corr_col}">
      <div style="font-size:1rem;font-weight:700;color:{corr_col}">
        {corr_icon} CORRELACIÓN SOX/COBRE — {corr_label}
      </div>
      <div style="color:#94a3b8;font-size:.85rem;margin-top:6px">{corr_msg}</div>
      <div style="color:#64748b;font-size:.8rem;margin-top:8px">
        SOX {fval(sox_v,2)} ({fchg(sox_1m)}/1M) &nbsp;·&nbsp; Cobre {fval(cop_v,3,"$")} ({fchg(cop_1m)}/1M)
      </div>
    </div>
  </div>

  <!-- KPIs rápidos -->
  <div class="grid2">
    <div class="card kpi">
      <div class="val" style="color:#38bdf8">{fval(sox_v,0)}</div>
      <div class="lbl">SOX Semiconductores</div>
      <div style="margin-top:6px">{fchg(sox_1m)} en 1 mes</div>
    </div>
    <div class="card kpi">
      <div class="val" style="color:#fb923c">{fval(cop_v,3,"$")}</div>
      <div class="lbl">Cobre (USD/lb)</div>
      <div style="margin-top:6px">{fchg(cop_1m)} en 1 mes</div>
    </div>
    <div class="card kpi">
      <div class="val" style="color:#facc15">₿ {fval(btc_v,0,"€")}</div>
      <div class="lbl">Bitcoin (EUR)</div>
      <div style="margin-top:6px">{fchg(btc_1m)} en 1 mes</div>
    </div>
    <div class="card kpi">
      <div class="val" style="color:#94a3b8">{fval(vix_v,1)}</div>
      <div class="lbl">VIX Volatilidad</div>
      <div style="margin-top:6px;color:{'#4ade80' if vix_ok else '#f87171'}">
        {'< 20 — entorno favorable' if vix_ok else '≥ 20 — precaución'}
      </div>
    </div>
  </div>

  <!-- Gráfico variación 1M -->
  <div class="card">
    <h2 style="color:#64748b">VARIACIÓN 1 MES — INDICADORES CLAVE</h2>
    {chart_svg}
  </div>

  <!-- Señales por pilar -->
  <div class="card">
    <h2 style="color:#64748b">SEÑALES POR PILAR</h2>
    <div style="overflow-x:auto">
    <table>
      <thead>
        <tr style="border-bottom:1px solid #1e293b">
          <th style="padding:6px 10px;text-align:left;color:#475569;font-weight:500;font-size:.8em">SEÑAL</th>
          <th style="padding:6px 10px;text-align:right;color:#475569;font-weight:500;font-size:.8em">VALOR</th>
          <th style="padding:6px 10px;text-align:right;color:#475569;font-weight:500;font-size:.8em">1 MES</th>
          <th style="padding:6px 10px;color:#475569;font-weight:500;font-size:.8em">CONDICIÓN</th>
          <th style="padding:6px 10px;text-align:center;color:#475569;font-weight:500;font-size:.8em"></th>
        </tr>
      </thead>
      <tbody>{signals_html}</tbody>
    </table>
    </div>
  </div>

  <!-- Contexto -->
  <div class="card">
    <h2 style="color:#64748b">CONTEXTO DE MERCADO</h2>
    {ctx_html}
  </div>

  <!-- Footer -->
  <div style="text-align:center;color:#334155;font-size:.75rem;margin-top:24px;line-height:1.8">
    V(t) = Capital × (1+r)ᵗ × Φ_L(t) &nbsp;·&nbsp; Φ_L(t) = 1 + K/(1+e^(−γ·(t−t₀)))<br>
    Fuente: Yahoo Finance · Actualizado: {updated}<br>
    Jose Vilar · UOC Data Science
  </div>

</div>
</body>
</html>"""

# ── Guardar ───────────────────────────────────────────────────────────────────
OUT_DIR.mkdir(exist_ok=True)
OUT_FILE.write_text(html, encoding="utf-8")
print(f"OK  {len(html):,} chars  →  {OUT_FILE}")
