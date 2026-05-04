"""
eToro portfolio scraper via Playwright.

Returns a dict:
  total_value  : float  (USD)
  cash         : float  (USD)
  today_pnl    : float  (USD)
  today_pct    : float  (%)
  holdings     : list[dict]
    Each holding: ticker, name, price, change_pct, units, avg_cost,
                  pnl, pnl_pct, net_value
"""

import re
import time

from playwright.sync_api import sync_playwright


_PORTFOLIO_URL = "https://www.etoro.com/portfolio/overview"
_LOGIN_URL     = "https://www.etoro.com/login"


def fetch(username: str, password: str, timeout_sec: int = 180) -> dict | None:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False, slow_mo=50)
        context = browser.new_context()
        page    = context.new_page()
        try:
            return _run(page, username, password, timeout_sec)
        finally:
            browser.close()


def _run(page, username, password, timeout_sec):
    page.goto(_LOGIN_URL, wait_until="domcontentloaded", timeout=20_000)
    page.wait_for_timeout(3_000)

    # ── Login if needed ───────────────────────────────────────────────────────
    if "etoro.com/home" not in page.url and "etoro.com/portfolio" not in page.url:
        _do_login(page, username, password)
        _wait_for_home(page, timeout_sec)
        if "etoro.com/home" not in page.url and "etoro.com/portfolio" not in page.url:
            print("[eToro] 登录/2FA 超时，退出")
            return None
    else:
        print("[eToro] 已有登录会话")

    # ── Navigate to portfolio ─────────────────────────────────────────────────
    page.goto(_PORTFOLIO_URL, wait_until="domcontentloaded", timeout=20_000)
    page.wait_for_timeout(3_000)
    print("[eToro] 持仓页面已加载")

    # ── Extract footer summary ────────────────────────────────────────────────
    footer = _extract_footer(page)

    # ── Extract holdings ──────────────────────────────────────────────────────
    holdings_raw = page.evaluate("""() => {
        const items = document.querySelectorAll(
            '[data-testid="portfolio-instrument-item"], '  +
            '.portfolioInstrumentItem, '                   +
            '.instrumentListItem'
        );
        return Array.from(items).map(el => el.innerText.trim());
    }""")

    holdings = [_parse_holding(raw) for raw in holdings_raw if raw]

    return {
        "total_value": footer.get("total"),
        "cash":        footer.get("cash"),
        "today_pnl":   footer.get("pnl"),
        "today_pct":   footer.get("pct"),
        "holdings":    holdings,
    }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _do_login(page, username, password):
    """Fill eToro login form."""
    try:
        page.fill('[automation-id="login-sts-username-input"]', username, timeout=5_000)
        page.fill('[automation-id="login-sts-password-input"]', password, timeout=5_000)
        page.click('[automation-id="login-sts-btn-login"]',    timeout=5_000)
    except Exception:
        # Fallback selectors
        page.fill('input[name="username"], input[type="text"]',     username)
        page.fill('input[name="password"], input[type="password"]', password)
        page.click('button[type="submit"]')


def _wait_for_home(page, timeout_sec):
    print(f"[eToro] 等待 2FA 验证（最多 {timeout_sec // 60} 分钟）…")
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        if "etoro.com/home" in page.url or "etoro.com/portfolio" in page.url:
            return
        page.wait_for_timeout(5_000)


def _extract_footer(page) -> dict:
    raw = page.evaluate("""() => {
        const getText = s => document.querySelector(s)?.innerText?.trim() || '';
        return {
            total:    getText('[automation-id="portfolio-footer-total-value"]'),
            cash:     getText('[automation-id="portfolio-footer-available-balance"]'),
            invested: getText('[automation-id="portfolio-footer-invested"]'),
            pnl:      getText('[automation-id="portfolio-footer-pnl"]'),
            pct:      getText('[automation-id="portfolio-footer-pnl-pct"]'),
        };
    }""")

    # Fallback: parse the visible bottom bar
    if not raw.get("total"):
        bar_text = page.evaluate("""() => {
            const bars = document.querySelectorAll('[class*="footerItem"], [class*="footer-item"]');
            return Array.from(bars).map(b => b.innerText.trim()).join(' | ');
        }""")
        raw["_bar"] = bar_text

    return raw


def _parse_holding(raw: str) -> dict:
    """
    eToro row text (newline-separated):
      Line 0: ticker + optional label (e.g. "AMD")
      Line 1: full name (e.g. "Advanced Micro Devices Inc")
      Line 2: price (e.g. "343.90")
      Line 3: day change (e.g. "2.36 (0.69%)")
      Line 4: units (e.g. "14.00")
      Line 5: 买入 / 卖出
      Line 6: avg cost (e.g. "258.7125")
      Line 7: P&L (e.g. "$1,192.63")
      Line 8: P&L % (e.g. "32.93%")
      Line 9: net value (e.g. "$4,814.59")
      ...
    Smart Portfolios have fewer lines (no price/units/avg).
    """
    lines = [l.strip() for l in raw.splitlines() if l.strip()]
    if len(lines) < 4:
        return {"raw": raw, "ticker": lines[0] if lines else "?"}

    ticker = lines[0].split()[0]  # first word is ticker
    name   = lines[1] if len(lines) > 1 else ""

    def to_float(s: str) -> float | None:
        try:
            return float(re.sub(r"[^\d.\-]", "", s))
        except Exception:
            return None

    if len(lines) >= 10:
        return {
            "ticker":    ticker,
            "name":      name,
            "price":     to_float(lines[2]),
            "change":    lines[3],
            "units":     to_float(lines[4]),
            "direction": lines[5],
            "avg_cost":  to_float(lines[6]),
            "pnl":       to_float(lines[7]),
            "pnl_pct":   to_float(lines[8].replace("%", "")),
            "net_value": to_float(lines[9]),
        }

    # Smart Portfolio or other special item
    return {
        "ticker":    ticker,
        "name":      name,
        "pnl":       to_float(lines[-2]) if len(lines) >= 3 else None,
        "pnl_pct":   to_float(lines[-1].replace("%", "")) if len(lines) >= 2 else None,
        "net_value": to_float(lines[-3]) if len(lines) >= 4 else None,
        "is_portfolio": True,
    }
