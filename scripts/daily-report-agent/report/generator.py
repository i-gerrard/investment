"""
HTML report generator.

Takes structured data from brokers + market utils and produces
a self-contained HTML file matching the established report format.
"""

from datetime import datetime


# ── CSS (shared style) ────────────────────────────────────────────────────────
_CSS = """
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family:"PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;
       font-size:13px; color:#1a1a2e; background:#fff; padding:40px; line-height:1.7; }
h1   { font-size:24px; color:#0f3460; border-bottom:3px solid #e94560;
       padding-bottom:10px; margin-bottom:6px; }
h2   { font-size:16px; color:#0f3460; margin:24px 0 10px;
       border-left:4px solid #e94560; padding-left:10px; }
.subtitle  { color:#666; font-size:12px; margin-bottom:20px; }
.source    { background:#f0f8ff; border:1px solid #b3d7f0; border-radius:6px;
             padding:8px 14px; margin-bottom:12px; font-size:11px; color:#555; }
.fx-banner { background:#e8f4fd; border:1px solid #b3d7f0; border-radius:6px;
             padding:9px 14px; margin-bottom:12px; font-size:12px; color:#1a5276; }
.action    { background:#fff0e8; border:2px solid #e67e22; border-radius:8px;
             padding:14px 18px; margin-bottom:16px; }
.action h3 { color:#c0392b; font-size:14px; font-weight:700; margin-bottom:8px; }
.grid2     { display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-bottom:18px; }
.card      { background:#f8f9ff; border:1px solid #e0e4f0; border-radius:8px; padding:14px; }
.card .ttl { font-size:11px; color:#1a6fa8; font-weight:700; margin-bottom:6px; }
.card .val { font-size:20px; font-weight:700; color:#0f3460; }
.card .sub { font-size:12px; color:#555; margin-top:4px; }
table      { width:100%; border-collapse:collapse; font-size:12px; margin:6px 0; }
th         { background:#0f3460; color:white; padding:6px 10px; text-align:left; font-weight:600; }
td         { padding:5px 10px; border-bottom:1px solid #f0f2fa; vertical-align:middle; }
.r         { text-align:right; }
tr.sub-tot td { background:#e8f0fc; font-weight:700; border-top:2px solid #0f3460; }
tr.tr-tot  td { background:#d4edda; font-weight:700; border-top:2px solid #2d8a3e; }
.pos  { color:#0a7a4f; font-weight:600; }
.neg  { color:#c0392b; font-weight:600; }
.mkt-grid  { display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin-bottom:14px; }
.mkt-card  { background:#f8f9ff; border:1px solid #e0e4f0; border-radius:8px; padding:11px 13px; }
.mkt-lbl   { font-size:10px; color:#888; text-transform:uppercase; letter-spacing:.5px; margin-bottom:2px; }
.mkt-val   { font-size:19px; font-weight:700; color:#0f3460; }
.mkt-chg   { font-size:12px; margin-top:2px; }
.footer    { margin-top:32px; padding-top:12px; border-top:1px solid #e0e0e0;
             font-size:11px; color:#999; text-align:center; }
"""


# ── Public API ────────────────────────────────────────────────────────────────

def generate(
    etoro_data:  dict,
    tr_data:     dict,
    eur_usd:     float,
    fg_score:    int | None,
    fg_label:    str,
    idx_prices:  dict,
    idx_changes: dict,
    today:       str,
    weekday:     str,
) -> str:
    now = datetime.now().strftime("%H:%M")

    etoro_total = etoro_data.get("total_value") or _sum_holdings_etoro(etoro_data)
    tr_total    = tr_data.get("total_value", 0) or 0
    combined    = (etoro_total or 0) + (tr_total or 0) * eur_usd

    etoro_pnl   = etoro_data.get("today_pnl", 0) or 0
    tr_pnl      = tr_data.get("today_pnl", 0) or 0
    tr_pct      = tr_data.get("today_pct", 0) or 0

    return f"""<!DOCTYPE html>
<html lang="zh"><head>
<meta charset="UTF-8">
<title>每日投资日报 {today}</title>
<style>{_CSS}</style>
</head><body>

<h1>📊 每日投资日报</h1>
<p class="subtitle">{today} {weekday} &nbsp;|&nbsp; 生成 {now} &nbsp;|&nbsp;
  汇率 1 EUR = <strong>${eur_usd:.4f}</strong> &nbsp;|&nbsp;
  两账户合计 <strong style="color:#0f3460">${combined:,.0f}</strong></p>

<div class="source">✅ <strong>数据来源：</strong>
  eToro 实时（etoro.com）· Trade Republic 实时（app.traderepublic.com）·
  EUR/USD Frankfurter API · 指数 Yahoo Finance · Fear&amp;Greed CNN
</div>

<div class="fx-banner">
  💱 <strong>1 EUR = ${eur_usd:.4f} USD</strong> &nbsp;|&nbsp;
  Fear &amp; Greed: {_fg_html(fg_score, fg_label)}
</div>

{_market_section(idx_prices, idx_changes)}

{_accounts_section(etoro_data, tr_data, eur_usd, etoro_pnl, tr_pnl, tr_pct)}

{_etoro_table(etoro_data)}

{_tr_table(tr_data)}

<div class="footer">
  数据抓取：{today} {now} &nbsp;|&nbsp;
  来源：eToro · Trade Republic · Frankfurter API · Yahoo Finance · CNN<br>
  仅供个人参考，不构成投资建议。
</div>
</body></html>"""


# ── Section builders ──────────────────────────────────────────────────────────

def _fg_html(score, label) -> str:
    if score is None:
        return "N/A"
    color = "#c0392b" if score >= 75 or score < 25 else "#0a7a4f" if score >= 55 else "#856404"
    emoji = "😱" if score >= 75 else "🤑" if score >= 55 else "😐" if score >= 45 else "😨" if score >= 25 else "💀"
    return f'<span style="color:{color};font-weight:700">{score} {label} {emoji}</span>'


def _chg_html(v) -> str:
    if v is None:
        return '<span style="color:#aaa">—</span>'
    color = "#0a7a4f" if v >= 0 else "#c0392b"
    sign  = "+" if v >= 0 else ""
    return f'<span style="color:{color};font-weight:600">{sign}{v:.2f}%</span>'


def _market_section(prices, changes) -> str:
    sp   = prices.get("^GSPC");  sp_c  = changes.get("^GSPC")
    ndx  = prices.get("^NDX");   ndx_c = changes.get("^NDX")
    dji  = prices.get("^DJI");   dji_c = changes.get("^DJI")

    def card(label, val, chg):
        v = f"{val:,.0f}" if val else "—"
        return (f'<div class="mkt-card">'
                f'<div class="mkt-lbl">{label}</div>'
                f'<div class="mkt-val">{v}</div>'
                f'<div class="mkt-chg">{_chg_html(chg)}</div></div>')

    return (f'<h2>🌍 市场指数</h2>'
            f'<div class="mkt-grid">'
            f'{card("S&P 500",    sp,  sp_c)}'
            f'{card("Nasdaq 100", ndx, ndx_c)}'
            f'{card("Dow Jones",  dji, dji_c)}'
            f'</div>')


def _accounts_section(etoro, tr, eur_usd, e_pnl, tr_pnl, tr_pct) -> str:
    e_total  = etoro.get("total_value") or _sum_holdings_etoro(etoro)
    tr_total = tr.get("total_value") or 0
    cash     = etoro.get("cash") or "—"

    e_pnl_html  = _fmt_pnl(e_pnl)
    tr_pnl_html = _fmt_pnl(tr_pnl, suffix=" €")
    tr_usd      = (tr_total or 0) * eur_usd

    return f"""
<h2>📊 账户概览</h2>
<div class="grid2">
  <div class="card">
    <div class="ttl">eToro — Lisong Li</div>
    <div class="val">${e_total:,.2f}</div>
    <div class="sub">今日 {e_pnl_html} &nbsp;|&nbsp; 现金 <strong style="color:#c0392b">{_fmt_cash(cash)}</strong></div>
  </div>
  <div class="card">
    <div class="ttl">Trade Republic</div>
    <div class="val">€{tr_total:,.2f} <span style="font-size:13px;color:#555;">≈ ${tr_usd:,.0f}</span></div>
    <div class="sub">今日 {tr_pnl_html} &nbsp;|&nbsp;
      {_chg_html(tr_pct)}</div>
  </div>
</div>"""


def _etoro_table(data: dict) -> str:
    holdings = data.get("holdings", [])
    if not holdings:
        return "<p style='color:#999'>eToro 持仓数据未能提取，请检查日志。</p>"

    rows = ""
    for h in holdings:
        if h.get("is_portfolio"):
            rows += (f"<tr><td><b>{h['ticker']}</b></td>"
                     f"<td colspan='5'>{h.get('name','')}</td>"
                     f"<td class='r'>{_fmt_pnl(h.get('pnl'))}</td>"
                     f"<td class='r'>{h.get('pnl_pct','—')}%</td>"
                     f"<td class='r'>${h.get('net_value') or 0:,.2f}</td></tr>")
        else:
            pnl_pct = h.get("pnl_pct")
            pnl_cls = "pos" if (pnl_pct or 0) >= 0 else "neg"
            rows += (f"<tr><td><b>{h['ticker']}</b></td>"
                     f"<td>{h.get('name','')}</td>"
                     f"<td class='r'>${h.get('price') or 0:,.2f}</td>"
                     f"<td class='r'>{h.get('units') or '—'}</td>"
                     f"<td class='r'>${h.get('avg_cost') or 0:,.2f}</td>"
                     f"<td class='r'>{_fmt_pnl(h.get('pnl'))}</td>"
                     f"<td class='r {pnl_cls}'>{pnl_pct:+.2f}%</td>"
                     f"<td class='r'>${h.get('net_value') or 0:,.2f}</td></tr>")

    return f"""
<h2>📈 eToro 持仓（USD）</h2>
<table>
<tr><th>股票</th><th>名称</th><th class="r">价格</th><th class="r">持仓</th>
    <th class="r">均价</th><th class="r">总盈亏</th><th class="r">盈亏%</th><th class="r">净值</th></tr>
{rows}
</table>"""


def _tr_table(data: dict) -> str:
    holdings = data.get("holdings", [])
    if not holdings:
        return "<p style='color:#999'>Trade Republic 持仓数据未能提取，请检查日志。</p>"

    rows = ""
    for h in holdings:
        pnl     = h.get("since_buy_pnl")
        pnl_cls = "pos" if (pnl or 0) >= 0 else "neg"
        rows += (f"<tr><td><b>{h.get('name','—')}</b></td>"
                 f"<td class='r'>{h.get('units') or '—'}</td>"
                 f"<td class='r'>€{h.get('value_eur') or 0:,.2f}</td>"
                 f"<td class='r {pnl_cls}'>{_fmt_pnl(pnl, prefix='€', suffix='')}</td></tr>")

    total_val = sum(h.get("value_eur") or 0 for h in holdings)
    total_pnl = sum(h.get("since_buy_pnl") or 0 for h in holdings)

    return f"""
<h2>📈 Trade Republic 持仓（EUR）</h2>
<table>
<tr><th>股票</th><th class="r">持仓量</th><th class="r">当前市值</th><th class="r">累计盈亏（Since Buy）</th></tr>
{rows}
<tr class="tr-tot"><td colspan="2"><b>TR 合计</b></td>
  <td class="r"><b>€{total_val:,.2f}</b></td>
  <td class="r {('pos' if total_pnl >= 0 else 'neg')}">{_fmt_pnl(total_pnl, prefix='€', suffix='')}</td></tr>
</table>"""


# ── Formatting helpers ────────────────────────────────────────────────────────

def _fmt_pnl(val, prefix="$", suffix="") -> str:
    if val is None:
        return "—"
    color = "#0a7a4f" if val >= 0 else "#c0392b"
    sign  = "+" if val >= 0 else ""
    return f'<span style="color:{color};font-weight:600">{sign}{prefix}{val:,.2f}{suffix}</span>'


def _fmt_cash(cash) -> str:
    if isinstance(cash, (int, float)):
        return f"${cash:,.2f}"
    return str(cash) if cash else "—"


def _sum_holdings_etoro(data: dict) -> float:
    return sum(
        (h.get("net_value") or 0)
        for h in data.get("holdings", [])
    )
