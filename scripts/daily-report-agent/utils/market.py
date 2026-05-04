"""Market data helpers: EUR/USD, Fear & Greed, index prices."""
import json
import urllib.request


def get_eur_usd() -> float:
    try:
        with urllib.request.urlopen(
            "https://api.frankfurter.app/latest?from=EUR&to=USD", timeout=6
        ) as r:
            return float(json.loads(r.read())["rates"]["USD"])
    except Exception:
        return 1.1690


def get_fear_greed() -> tuple[int | None, str]:
    try:
        req = urllib.request.Request(
            "https://production.dataviz.cnn.io/index/fearandgreed/graphdata",
            headers={"User-Agent": "Mozilla/5.0"},
        )
        with urllib.request.urlopen(req, timeout=6) as r:
            d = json.loads(r.read())["fear_and_greed"]
            return int(d["score"]), d["rating"].title()
    except Exception:
        return None, "N/A"


def get_indices() -> tuple[dict, dict]:
    """Return (prices, day_changes) for S&P500, NDX100, DJI."""
    try:
        import yfinance as yf
        tickers = ["^GSPC", "^NDX", "^DJI"]
        raw = yf.download(tickers, period="2d", interval="1d", progress=False, auto_adjust=True)
        prices, changes = {}, {}
        close = raw["Close"]
        for t in close.columns:
            col = close[t].dropna()
            if len(col) >= 1:
                prices[t] = float(col.iloc[-1])
            if len(col) >= 2:
                changes[t] = (float(col.iloc[-1]) - float(col.iloc[-2])) / float(col.iloc[-2]) * 100
        return prices, changes
    except Exception:
        return {}, {}
