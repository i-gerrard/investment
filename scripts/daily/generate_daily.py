#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日投资日报 — 自动抓取行情、生成 HTML/PDF、发送至邮箱
运行方式：python3 generate_daily.py
"""

import json, subprocess, sys, urllib.request
from datetime import datetime, date
from pathlib import Path

# ── 路径配置 ──────────────────────────────────────────────────────────────────
BASE   = Path.home() / "Desktop/claude/daily"
BASE.mkdir(parents=True, exist_ok=True)
TODAY  = date.today().strftime("%Y-%m-%d")
WEEKDAY = ["周一","周二","周三","周四","周五","周六","周日"][date.today().weekday()]
HTML_F = BASE / f"日报_{TODAY}.html"
PDF_F  = BASE / f"日报_{TODAY}.pdf"
CONFIG = BASE / "config.json"
LOG_F  = BASE / "run.log"

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_F, "a") as f: f.write(line + "\n")

# ── 账户配置 ──────────────────────────────────────────────────────────────────
cfg = json.loads(CONFIG.read_text())

# eToro: ticker → {n: shares, avg: USD cost}
ETORO = {
    "NVDA": {"n": 50,      "avg": 163.068, "label": "NVIDIA"},
    "MSFT": {"n": 22,      "avg": 422.15,  "label": "Microsoft"},
    "TSM":  {"n": 20,      "avg": 288.63,  "label": "TSMC"},
    "META": {"n": 10,      "avg": 647.408, "label": "Meta"},
    "VOO":  {"n": 9,       "avg": 592.594, "label": "S&P500 ETF"},
    "AAPL": {"n": 20,      "avg": 265.20,  "label": "Apple"},
    "GOOG": {"n": 15,      "avg": 338.44,  "label": "Alphabet"},
    "AMD":  {"n": 14,      "avg": 258.71,  "label": "AMD"},
    "JEPQ": {"n": 60,      "avg": 55.603,  "label": "JPM Nasdaq Premium"},
    "AMZN": {"n": 14,      "avg": 235.69,  "label": "Amazon"},
    "AVGO": {"n": 8,       "avg": 232.27,  "label": "Broadcom"},
    "RXRX": {"n": 800,     "avg": 4.72,    "label": "Recursion Pharma ⚠️"},
    "TSLA": {"n": 7,       "avg": 352.78,  "label": "Tesla"},
    "JEPI": {"n": 39,      "avg": 56.347,  "label": "JPM Equity Premium"},
    "CRSP": {"n": 55,      "avg": 36.42,   "label": "CRISPR Therapeutics"},
}
# NDQ100: 0.128181 units tracking Nasdaq 100 index (^NDX), avg index level 17942.51
NDQ_UNITS = 0.128181
NDQ_AVG   = 17942.51

# Trade Republic: 数据来源于 19.04.2026 PDF（Vermögensübersicht）
# ref_eur = PDF 中每股价格（欧元）, ref_val = PDF 中持仓市值（欧元）
# 注意：PDF 不含买入成本，因此日报只显示当日估值变化，不计算总盈亏
# yf_ticker = Yahoo Finance 对应代码（USD，运行时除以汇率换算为 EUR）
# etf=True 表示欧洲 ETF，用 proxy 代码追踪日涨跌
TR = {
    "NVDA": {"n": 66.260325, "ref_eur": 171.10, "ref_val": 11337.14, "yf": "NVDA",  "label": "NVIDIA"},
    "GOOG": {"n": 42.482803, "ref_eur": 289.90, "ref_val": 12315.76, "yf": "GOOG",  "label": "Alphabet"},
    "AVGO": {"n": 32.721547, "ref_eur": 345.00, "ref_val": 11288.93, "yf": "AVGO",  "label": "Broadcom"},
    "GS":   {"n": 13.47566,  "ref_eur": 786.00, "ref_val": 10591.87, "yf": "GS",    "label": "Goldman Sachs ⚠️"},
    "META": {"n": 17.083892, "ref_eur": 584.50, "ref_val":  9985.53, "yf": "META",  "label": "Meta"},
    "TSLA": {"n": 28.179765, "ref_eur": 340.15, "ref_val":  9585.35, "yf": "TSLA",  "label": "Tesla"},
    "MSFT": {"n": 27,        "ref_eur": 358.90, "ref_val":  9690.30, "yf": "MSFT",  "label": "Microsoft"},
    "AMZN": {"n": 40,        "ref_eur": 212.90, "ref_val":  8516.00, "yf": "AMZN",  "label": "Amazon"},
    "MU":   {"n": 21,        "ref_eur": 386.40, "ref_val":  8114.40, "yf": "MU",    "label": "Micron"},
    "WDC":  {"n": 26,        "ref_eur": 316.05, "ref_val":  8217.30, "yf": "WDC",   "label": "Western Digital"},
    "TSM":  {"n": 26.400934, "ref_eur": 314.50, "ref_val":  8303.09, "yf": "TSM",   "label": "TSMC"},
    "AMD":  {"n": 32.817648, "ref_eur": 236.10, "ref_val":  7748.25, "yf": "AMD",   "label": "AMD"},
    "AAPL": {"n": 30,        "ref_eur": 229.40, "ref_val":  6882.00, "yf": "AAPL",  "label": "Apple"},
    # S&P500 InfoTech UCITS ETF (IE00B3WJKG14) — 用 XLK 追踪日涨跌
    "IUIT": {"n": 139.735605,"ref_eur":  37.06, "ref_val":  5177.90, "yf": "XLK",   "label": "S&P500 InfoTech ETF", "etf": True},
    # NASDAQ100 UCITS ETF (IE00B53SZB19) — 用 ^NDX 追踪日涨跌
    "CNDX": {"n": 1.860969,  "ref_eur":1296.40, "ref_val":  2412.56, "yf": "^NDX",  "label": "Nasdaq100 ETF", "etf": True},
    "NFLX": {"n": 0.836,     "ref_eur":  82.61, "ref_val":    69.06, "yf": "NFLX",  "label": "Netflix"},
}

# ── 数据获取 ──────────────────────────────────────────────────────────────────
def get_eur_usd():
    try:
        with urllib.request.urlopen(
            "https://api.frankfurter.app/latest?from=EUR&to=USD", timeout=6
        ) as r:
            return json.loads(r.read())["rates"]["USD"]
    except:
        return 1.1765

def get_fear_greed():
    try:
        req = urllib.request.Request(
            "https://production.dataviz.cnn.io/index/fearandgreed/graphdata",
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=6) as r:
            d = json.loads(r.read())["fear_and_greed"]
            return int(d["score"]), d["rating"].title()
    except:
        return None, "N/A"

def get_prices():
    try:
        import yfinance as yf
        tr_yf = [h["yf"] for h in TR.values()]
        tickers = list(set(list(ETORO.keys()) + tr_yf)) + ["^NDX", "^GSPC", "^IXIC", "^DJI"]
        raw = yf.download(tickers, period="2d", interval="1d",
                          progress=False, auto_adjust=True)
        prices, changes = {}, {}
        close = raw["Close"]
        for t in close.columns:
            col = close[t].dropna()
            if len(col) >= 1:
                prices[t] = float(col.iloc[-1])
            if len(col) >= 2:
                prev = float(col.iloc[-2])
                curr = float(col.iloc[-1])
                changes[t] = (curr - prev) / prev * 100
        return prices, changes
    except Exception as e:
        log(f"yfinance error: {e}")
        return {}, {}

# ── HTML 生成 ─────────────────────────────────────────────────────────────────
def fmt_pnl(val, pct=False):
    s = f"{val:+.2f}%" if pct else f"${val:+,.0f}"
    c = "#0a7a4f" if val >= 0 else "#c0392b"
    return f'<span style="color:{c};font-weight:600">{s}</span>'

def fmt_chg(v):
    if v is None: return '<span style="color:#aaa">—</span>'
    s = f"{v:+.2f}%"
    c = "#0a7a4f" if v >= 0 else "#c0392b"
    return f'<span style="color:{c};font-weight:600">{s}</span>'

def fg_html(score, label):
    if score is None: return "N/A"
    if score >= 75: c, e = "#c0392b", "😱 极度贪婪"
    elif score >= 55: c, e = "#0a7a4f", "🤑 贪婪"
    elif score >= 45: c, e = "#856404", "😐 中性"
    elif score >= 25: c, e = "#c0392b", "😨 恐惧"
    else: c, e = "#c0392b", "💀 极度恐惧"
    return f'<span style="color:{c};font-weight:700;font-size:18px">{score}</span> <span style="color:{c}">{label} {e}</span>'

def index_card(name, val, chg, prefix=""):
    if val is None: return f'<div class="card"><div class="lbl">{name}</div><div class="val">—</div></div>'
    chg_html = fmt_chg(chg)
    return f'<div class="card"><div class="lbl">{name}</div><div class="val">{prefix}{val:,.0f}</div><div class="sub2">{chg_html}</div></div>'

def etoro_rows(prices, changes):
    rows = []
    tc, tv = 0, 0
    for t, h in ETORO.items():
        p = prices.get(t)
        chg = changes.get(t)
        cost = h["n"] * h["avg"]
        val  = h["n"] * p if p else 0
        pnl  = val - cost
        pct  = pnl / cost * 100 if cost else 0
        tc += cost; tv += val if p else cost
        bg = ""
        if t == "RXRX": bg = ' style="background:#fff5f5"'
        elif pct > 30: bg = ' style="background:#f0fff8"'
        p_str   = f"${p:.2f}" if p else "—"
        val_str = f"${val:,.0f}" if p else "—"
        rows.append(f'<tr{bg}><td><b>{t}</b> <span class="sm">{h["label"]}</span></td>'
                    f'<td class="r">{p_str}</td><td class="r">{fmt_chg(chg)}</td>'
                    f'<td class="r">{h["n"]}</td><td class="r">${cost:,.0f}</td>'
                    f'<td class="r">{val_str}</td>'
                    f'<td class="r">{fmt_pnl(pnl)}<br>{fmt_pnl(pct,True)}</td></tr>')
    # NDQ100
    ndx = prices.get("^NDX")
    ndx_chg = changes.get("^NDX")
    if ndx:
        v = NDQ_UNITS * ndx; c = NDQ_UNITS * NDQ_AVG
        pnl = v - c; pct = pnl/c*100; tc += c; tv += v
        rows.append(f'<tr style="background:#f0fff8"><td><b>NDQ100</b> <span class="sm">Nasdaq100 Index</span></td>'
                    f'<td class="r">${ndx:,.0f}</td><td class="r">{fmt_chg(ndx_chg)}</td>'
                    f'<td class="r">0.128</td><td class="r">${c:,.0f}</td><td class="r">${v:,.0f}</td>'
                    f'<td class="r">{fmt_pnl(pnl)}<br>{fmt_pnl(pct,True)}</td></tr>')
    tp = tv - tc
    rows.append(f'<tr class="total"><td colspan="4"><b>eToro 合计</b></td>'
                f'<td class="r"><b>${tc:,.0f}</b></td><td class="r"><b>${tv:,.0f}</b></td>'
                f'<td class="r">{fmt_pnl(tp)}<br>{fmt_pnl(tp/tc*100 if tc else 0,True)}</td></tr>')
    return "\n".join(rows), tv

def tr_rows(prices, changes, eur_usd):
    """TR 表格：显示当日价格、日涨跌、当前估值、相对 PDF 参考值(4/17)的变化。
    不显示买入成本盈亏（PDF 无成本数据）。"""
    rows = []
    ref_total = sum(h["ref_val"] for h in TR.values())
    cur_total  = 0

    for ticker, h in TR.items():
        yf_t = h["yf"]
        is_etf = h.get("etf", False)
        chg  = changes.get(yf_t)
        ref_val = h["ref_val"]
        ref_eur = h["ref_eur"]

        if is_etf:
            # ETF：只用代理 ticker 的日涨跌，当前估值 = ref_val * (1 + chg/100)
            cur_eur = ref_eur * (1 + chg / 100) if chg is not None else ref_eur
            cur_val = h["n"] * cur_eur
            price_str = f"≈€{cur_eur:.2f}*"
        else:
            usd = prices.get(yf_t)
            cur_eur = usd / eur_usd if usd else None
            cur_val = h["n"] * cur_eur if cur_eur else ref_val
            price_str = f"€{cur_eur:.2f}" if cur_eur else "—"

        cur_total += cur_val
        delta     = cur_val - ref_val
        delta_pct = delta / ref_val * 100 if ref_val else 0

        bg = ' style="background:#fffbf0"' if ticker == "GS" else ""
        rows.append(
            f'<tr{bg}>'
            f'<td><b>{ticker}</b> <span class="sm">{h["label"]}</span></td>'
            f'<td class="r">{price_str}</td>'
            f'<td class="r">{fmt_chg(chg)}</td>'
            f'<td class="r">{h["n"]:.3f}</td>'
            f'<td class="r">€{ref_val:,.0f}</td>'
            f'<td class="r">€{cur_val:,.0f}</td>'
            f'<td class="r">{fmt_pnl(delta).replace("$","€")}<br>{fmt_pnl(delta_pct, True)}</td>'
            f'</tr>'
        )

    total_delta = cur_total - ref_total
    rows.append(
        f'<tr class="total tr-tot">'
        f'<td colspan="4"><b>TR 合计</b> <span class="sm">* ETF 用代理 ticker 估算</span></td>'
        f'<td class="r"><b>€{ref_total:,.0f}</b></td>'
        f'<td class="r"><b>€{cur_total:,.0f}</b></td>'
        f'<td class="r">{fmt_pnl(total_delta).replace("$","€")}<br>'
        f'{fmt_pnl(total_delta/ref_total*100 if ref_total else 0, True)}</td>'
        f'</tr>'
    )
    return "\n".join(rows), cur_total

def build_html(prices, changes, eur_usd, fg_score, fg_label):
    now = datetime.now().strftime("%H:%M")
    sp500 = prices.get("^GSPC"); sp_chg = changes.get("^GSPC")
    ndx   = prices.get("^NDX");  ndx_chg = changes.get("^NDX")
    dji   = prices.get("^DJI");  dji_chg = changes.get("^DJI")

    e_rows, e_total = etoro_rows(prices, changes)
    t_rows, t_total = tr_rows(prices, changes, eur_usd)
    grand = e_total + t_total * eur_usd

    return f"""<!DOCTYPE html>
<html lang="zh"><head>
<meta charset="UTF-8">
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:"PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;
       font-size:13px; color:#1a1a2e; background:#fff; padding:32px; line-height:1.65; }}
h1 {{ font-size:22px; color:#0f3460; border-bottom:3px solid #e94560;
      padding-bottom:8px; margin-bottom:4px; }}
.sub {{ color:#666; font-size:12px; margin-bottom:18px; }}
h2 {{ font-size:14px; color:#0f3460; margin:20px 0 8px;
      border-left:4px solid #e94560; padding-left:8px; }}
.banner {{ background:#e8f4fd; border:1px solid #b3d7f0; border-radius:6px;
           padding:9px 14px; margin-bottom:12px; font-size:12px; color:#1a5276; }}
.grid3 {{ display:grid; grid-template-columns:repeat(3,1fr); gap:12px; margin-bottom:14px; }}
.grid4 {{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin-bottom:14px; }}
.card {{ background:#f8f9ff; border:1px solid #e0e4f0; border-radius:8px; padding:11px 13px; }}
.lbl  {{ font-size:10px; color:#888; text-transform:uppercase; letter-spacing:.5px; margin-bottom:2px; }}
.val  {{ font-size:20px; font-weight:700; color:#0f3460; }}
.sub2 {{ font-size:12px; margin-top:2px; }}
.news {{ background:#fff8e1; border:1px solid #ffe082; border-radius:6px;
         padding:10px 14px; margin-bottom:12px; font-size:12px; }}
.news h3 {{ color:#5d4037; font-size:12px; font-weight:700; margin-bottom:5px; }}
.news li {{ margin-left:16px; margin-bottom:3px; }}
.earn {{ background:#fce4ec; border:1px solid #f48fb1; border-radius:6px;
         padding:9px 14px; margin-bottom:12px; font-size:12px; color:#880e4f; }}
table {{ width:100%; border-collapse:collapse; font-size:12px; margin-bottom:6px; }}
th {{ background:#0f3460; color:white; padding:7px 10px; text-align:left; font-weight:600; }}
td {{ padding:5px 10px; border-bottom:1px solid #f0f2fa; vertical-align:middle; }}
.r {{ text-align:right; }}
.sm {{ font-size:10px; color:#888; margin-left:4px; }}
tr.total td {{ background:#e8f0fc; font-weight:700; border-top:2px solid #0f3460; }}
tr.tr-tot td {{ background:#d4edda; border-top:2px solid #2d8a3e; }}
.footer {{ margin-top:24px; padding-top:8px; border-top:1px solid #e0e0e0;
           font-size:10px; color:#aaa; text-align:center; }}
</style>
</head><body>
<h1>📊 每日投资日报</h1>
<p class="sub">{TODAY} {WEEKDAY} &nbsp;|&nbsp; 生成 {now} &nbsp;|&nbsp; 汇率 1 EUR = ${eur_usd:.4f} &nbsp;|&nbsp;
  两账户合计约 <strong style="color:#0f3460">${grand:,.0f}</strong></p>

<div class="banner">
  <strong>本周重磅财报：</strong>
  TSLA 明日（4/22 AMC）· AMD 4/29 · AMZN 4/29 · GOOG 4/29 · META 4/30 · MSFT 4/30
</div>

<h2>🌍 市场指数</h2>
<div class="grid4">
  {index_card("S&P 500", sp500, sp_chg)}
  {index_card("Nasdaq 100", ndx, ndx_chg)}
  {index_card("Dow Jones", dji, dji_chg)}
  <div class="card">
    <div class="lbl">Fear &amp; Greed</div>
    <div style="margin-top:3px">{fg_html(fg_score, fg_label)}</div>
  </div>
</div>

<div class="news">
  <h3>📰 今日关键新闻</h3>
  <ul>
    <li>🇮🇷 伊朗开放霍尔木兹海峡 → 油价下跌，科技股反弹，地缘风险阶段性缓解</li>
    <li>🍎 AAPL +1.4%：Reuters 数据显示中国 Q1 iPhone 出货量 +20%，超越行业均值</li>
    <li>🎬 NFLX -9.3%：Q2 营收指引低于预期；Reed Hastings 宣布 6 月辞去董事长一职</li>
    <li>⚡ TSLA 明日财报（4/22 AMC）：关注 Q1 交付量、FSD 进展、Optimus 量产时间线</li>
    <li>📊 今日 GE Aerospace · UNH · RTX · 3M 等 Q1 财报结果将影响大盘情绪</li>
  </ul>
</div>

<div class="earn">
  📅 <b>本周财报日历</b> &nbsp;|&nbsp;
  今日（4/21）GE · UNH · RTX · 3M &nbsp;|&nbsp;
  <b>4/22 TSLA ⚡</b> &nbsp;|&nbsp;
  <b>4/29 AMZN · GOOG · AMD</b> &nbsp;|&nbsp;
  <b>4/30 META · MSFT</b>
</div>

<h2>📈 eToro 持仓（USD）</h2>
<table>
<tr><th>股票</th><th class="r">现价</th><th class="r">今日±%</th>
    <th class="r">持仓</th><th class="r">成本(USD)</th>
    <th class="r">市值(USD)</th><th class="r">总盈亏</th></tr>
{e_rows}
</table>

<h2>📈 Trade Republic 持仓（EUR · 1EUR=${eur_usd:.4f}）</h2>
<p style="font-size:11px;color:#888;margin-bottom:6px">
  基准：2026-04-17 PDF 市值 &nbsp;|&nbsp; TR 无买入成本数据，显示相对 PDF 基准的变化
</p>
<table>
<tr><th>股票</th><th class="r">现价(EUR)</th><th class="r">今日±%</th>
    <th class="r">持仓量</th><th class="r">基准市值(4/17)</th>
    <th class="r">当前估值</th><th class="r">较基准变化</th></tr>
{t_rows}
</table>

<div class="footer">
  仅供个人参考，不构成投资建议。数据：Yahoo Finance · CNN · Frankfurter API &nbsp;|&nbsp; 生成：{TODAY} {now}
</div>
</body></html>"""

# ── PDF 生成 ──────────────────────────────────────────────────────────────────
def make_pdf(html):
    HTML_F.write_text(html, encoding="utf-8")
    r = subprocess.run([
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "--headless", "--disable-gpu", "--no-margins",
        f"--print-to-pdf={PDF_F}",
        f"file://{HTML_F}"
    ], capture_output=True, text=True)
    if PDF_F.exists():
        log(f"PDF OK: {PDF_F.stat().st_size:,} bytes")
        return True
    else:
        log(f"PDF failed: {r.stderr[-200:]}")
        return False

# ── 邮件发送（通过 macOS Mail app，无需存储密码）────────────────────────────
def send_email(_html_unused):
    to  = cfg["to_email"]
    pdf = str(PDF_F)
    subj = f"📊 每日投资日报 {TODAY}"
    body = f"请查收 {TODAY} 每日投资日报（PDF 附件）。\\n\\n本日行情数据已更新，详见附件。"

    # AppleScript 通过已登录的 Mail app 发送，密码由系统 Keychain 管理
    script = f"""
tell application "Mail"
    set m to make new outgoing message with properties {{subject:"{subj}", content:"{body}", visible:false}}
    tell m
        make new to recipient at end of to recipients with properties {{address:"{to}"}}
        make new attachment with properties {{file name:(POSIX file "{pdf}") as alias}} at after last paragraph
    end tell
    send m
end tell
"""
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if r.returncode == 0:
        log(f"✅ 邮件已通过 Mail app 发送至 {to}")
        return True
    else:
        log(f"❌ 邮件发送失败: {r.stderr.strip()}")
        return False

# ── 主程序 ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    log(f"=== 日报生成开始 {TODAY} ===")
    eur_usd = get_eur_usd();      log(f"汇率: 1 EUR = ${eur_usd:.4f}")
    fg_score, fg_label = get_fear_greed(); log(f"Fear&Greed: {fg_score} {fg_label}")
    prices, changes = get_prices(); log(f"抓取行情: {len(prices)} 支")
    html = build_html(prices, changes, eur_usd, fg_score, fg_label)
    make_pdf(html)
    send_email(html)
    log("=== 完成 ===")
