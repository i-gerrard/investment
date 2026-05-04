#!/usr/bin/env python3
"""
Daily Investment Report Agent
==============================
Logs into eToro + Trade Republic via Playwright, fetches live portfolio
data, and generates a self-contained HTML report.

Usage:
    python agent.py [--out PATH]

The agent waits up to 3 minutes for each 2FA verification before giving up.
Credentials are read from ~/.credentials/investment_accounts.json.
"""

import argparse
import subprocess
import sys
from pathlib import Path

import config
from brokers import etoro, tr
from report  import generator
from utils   import market


def log(msg: str):
    print(f"[agent] {msg}", flush=True)


def run(out_path: Path | None = None) -> Path | None:
    # ── Load credentials ──────────────────────────────────────────────────────
    try:
        creds = config.load_credentials()
    except FileNotFoundError as e:
        print(f"❌ {e}")
        return None

    out = out_path or config.report_path()

    # ── Fetch market data (non-blocking, can run before browser) ──────────────
    log("抓取市场数据（EUR/USD · F&G · 指数）…")
    eur_usd           = market.get_eur_usd()
    fg_score, fg_lbl  = market.get_fear_greed()
    idx_prices, idx_changes = market.get_indices()
    log(f"EUR/USD={eur_usd:.4f}  F&G={fg_score} {fg_lbl}")

    # ── eToro ─────────────────────────────────────────────────────────────────
    log("登录 eToro…")
    e_creds   = creds["etoro"]
    etoro_data = etoro.fetch(
        username    = e_creds["username"],
        password    = e_creds["password"],
        timeout_sec = config.TWO_FA_TIMEOUT_SEC,
    )
    if etoro_data is None:
        log("❌ eToro 数据获取失败，退出")
        return None
    log(f"eToro OK — {len(etoro_data.get('holdings', []))} 只持仓")

    # ── Trade Republic ────────────────────────────────────────────────────────
    log("登录 Trade Republic…")
    tr_creds  = creds["trade_republic"]
    tr_data   = tr.fetch(
        phone       = tr_creds["phone"],
        pin         = tr_creds["pin"],
        timeout_sec = config.TWO_FA_TIMEOUT_SEC,
    )
    if tr_data is None:
        log("❌ Trade Republic 数据获取失败，退出")
        return None
    log(f"TR OK — {len(tr_data.get('holdings', []))} 只持仓  "
        f"总值 €{tr_data.get('total_value', 0):,.2f}")

    # ── Generate report ───────────────────────────────────────────────────────
    log("生成 HTML 报告…")
    html = generator.generate(
        etoro_data  = etoro_data,
        tr_data     = tr_data,
        eur_usd     = eur_usd,
        fg_score    = fg_score,
        fg_label    = fg_lbl,
        idx_prices  = idx_prices,
        idx_changes = idx_changes,
        today       = config.TODAY,
        weekday     = config.WEEKDAY,
    )

    out.write_text(html, encoding="utf-8")
    log(f"✅ 报告已保存: {out}")

    # ── Open in browser ───────────────────────────────────────────────────────
    try:
        subprocess.run(["open", str(out)], check=False)
    except Exception:
        pass

    return out


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Daily Investment Report Agent")
    parser.add_argument("--out", type=Path, default=None,
                        help="Output HTML path (default: ~/Desktop/claude/YYYY-MM-DD/report-YYYY-MM-DD.html)")
    args = parser.parse_args()

    result = run(args.out)
    sys.exit(0 if result else 1)
