"""
Trade Republic portfolio scraper via Playwright.

Returns a dict:
  total_value  : float  (EUR)
  today_pnl    : float  (EUR)
  today_pct    : float  (%)
  holdings     : list[dict]
    Each holding: name, units, value_eur, since_buy_pnl
"""

import re
import time

from playwright.sync_api import sync_playwright


_LOGIN_URL     = "https://app.traderepublic.com/login"
_PORTFOLIO_URL = "https://app.traderepublic.com/portfolio"


def fetch(phone: str, pin: str, timeout_sec: int = 180) -> dict | None:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False, slow_mo=50)
        context = browser.new_context()
        page    = context.new_page()
        try:
            return _run(page, phone, pin, timeout_sec)
        finally:
            browser.close()


def _run(page, phone, pin, timeout_sec):
    page.goto(_LOGIN_URL, wait_until="domcontentloaded", timeout=20_000)
    page.wait_for_timeout(2_000)

    # Accept cookies if shown
    try:
        page.locator('button[class*="buttonBase"]:has-text("Accept All")').click(timeout=3_000)
        page.wait_for_timeout(1_000)
    except Exception:
        pass

    # ── Enter phone number ────────────────────────────────────────────────────
    phone_digits = re.sub(r"[^\d]", "", phone.replace("+49", "").strip())
    try:
        page.fill('input[placeholder*="123"]', phone_digits, timeout=5_000)
        page.click('button:has-text("Next")', timeout=5_000)
        page.wait_for_timeout(1_500)
    except Exception as e:
        print(f"[TR] 手机号输入失败: {e}")
        return None

    # ── Enter PIN (4 separate inputs) ─────────────────────────────────────────
    try:
        inputs = page.get_by_role("textbox").all()
        for i, digit in enumerate(pin[:4]):
            if i < len(inputs):
                inputs[i].fill(digit)
        page.wait_for_timeout(1_500)
    except Exception as e:
        print(f"[TR] PIN 输入失败: {e}")
        return None

    # ── Wait for 2FA + redirect to /portfolio ─────────────────────────────────
    print(f"[TR] 等待 2FA 验证（最多 {timeout_sec // 60} 分钟）…")
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        if "traderepublic.com/portfolio" in page.url:
            break
        page.wait_for_timeout(5_000)
    else:
        print("[TR] 2FA 超时，退出")
        return None

    print("[TR] 登录成功，读取持仓…")
    page.wait_for_timeout(3_000)

    # ── Extract portfolio total + today's change ──────────────────────────────
    summary = page.evaluate("""() => {
        const h1 = document.querySelector('h1');
        const perf = h1?.nextElementSibling?.innerText || '';
        return {
            total: h1?.innerText?.trim() || '',
            perf:  perf.trim(),
        };
    }""")

    # ── Extract holdings ──────────────────────────────────────────────────────
    holdings_raw = page.evaluate("""() => {
        const items = document.querySelectorAll(
            '[data-testid="portfolio-instrument-item"], '  +
            '.portfolioInstrumentItem, '                   +
            '.instrumentListItem'
        );
        if (items.length > 0) {
            return Array.from(items).map(el => el.innerText.trim());
        }
        // Fallback: broader selector (worked in session)
        const broad = document.querySelectorAll('[class*="instrument"]');
        return Array.from(broad)
            .filter(el => {
                const t = el.innerText?.trim() || '';
                const lines = t.split('\\n').filter(l => l.trim());
                return lines.length >= 3;
            })
            .map(el => el.innerText.trim())
            .slice(0, 20);
    }""")

    holdings = [_parse_holding(raw) for raw in holdings_raw if raw]

    # Parse totals
    total = _extract_eur(summary.get("total", ""))
    pnl, pct = _parse_perf(summary.get("perf", ""))

    return {
        "total_value": total,
        "today_pnl":   pnl,
        "today_pct":   pct,
        "holdings":    holdings,
    }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _extract_eur(s: str) -> float | None:
    try:
        return float(re.sub(r"[^\d.]", "", s.replace(",", ".")))
    except Exception:
        return None


def _parse_perf(s: str) -> tuple:
    """Parse '+2,288 €\n1.70 %' → (2288.0, 1.70)."""
    nums = re.findall(r"[\-\d,]+\.?\d*", s.replace(",", ""))
    if len(nums) >= 2:
        try:
            return float(nums[0]), float(nums[1])
        except Exception:
            pass
    return None, None


def _parse_holding(raw: str) -> dict:
    """
    TR portfolio item text format (Since buy mode):
      Line 0: name (e.g. "Alphabet (A)")
      Line 1: units (e.g. "42.482803")
      Line 2: value in EUR (e.g. "13,885.50 €")
      Line 3: P&L since buy (e.g. "6,340 €")
    """
    lines = [l.strip() for l in raw.splitlines() if l.strip()]
    if len(lines) < 2:
        return {"raw": raw}

    def to_float(s: str) -> float | None:
        try:
            return float(re.sub(r"[^\d.\-]", "", s.replace(",", "")))
        except Exception:
            return None

    return {
        "name":          lines[0],
        "units":         to_float(lines[1]) if len(lines) > 1 else None,
        "value_eur":     to_float(lines[2]) if len(lines) > 2 else None,
        "since_buy_pnl": to_float(lines[3]) if len(lines) > 3 else None,
    }
