"""
Configuration: credentials + output paths.
Credentials are stored in ~/.credentials/investment_accounts.json (never committed to git).
"""
import json
from pathlib import Path
from datetime import date

# ── Paths ─────────────────────────────────────────────────────────────────────
CREDENTIALS_PATH = Path.home() / ".credentials" / "investment_accounts.json"
OUTPUT_DIR       = Path.home() / "Desktop" / "claude"

TODAY   = date.today().strftime("%Y-%m-%d")
WEEKDAY = ["周一","周二","周三","周四","周五","周六","周日"][date.today().weekday()]

# ── Timeouts ──────────────────────────────────────────────────────────────────
TWO_FA_TIMEOUT_SEC = 180   # 3 minutes to complete 2FA before giving up


def load_credentials() -> dict:
    """Load eToro + Trade Republic credentials from local file."""
    if not CREDENTIALS_PATH.exists():
        raise FileNotFoundError(
            f"Credentials file not found: {CREDENTIALS_PATH}\n"
            "Create it with this structure:\n"
            '{\n'
            '  "etoro":          {"username": "...", "password": "..."},\n'
            '  "trade_republic": {"phone": "+49 ...", "pin": "1234"}\n'
            '}'
        )
    return json.loads(CREDENTIALS_PATH.read_text())


def report_path() -> Path:
    """Return path for today's HTML report."""
    out = OUTPUT_DIR / TODAY
    out.mkdir(parents=True, exist_ok=True)
    return out / f"report-{TODAY}.html"
