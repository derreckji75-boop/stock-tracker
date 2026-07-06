"""Fetch latest close prices + FX rates for tracked tickers and upsert into data/*.json.

Run manually with `python collector/collect.py` or via the GitHub Actions cron workflow.
Failures on individual tickers are logged and skipped so one bad symbol doesn't block the rest.
"""
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

import yfinance as yf

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
PRICES_DIR = DATA_DIR / "prices"
TICKERS_FILE = DATA_DIR / "tickers.json"
FX_FILE = DATA_DIR / "fx.json"

KST = timezone(timedelta(hours=9))


def load_json(path, default):
    if not path.exists():
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def upsert_by_date(rows, new_row):
    """Replace the row for new_row['date'] if present, otherwise append. Keeps rows sorted by date."""
    rows = [r for r in rows if r["date"] != new_row["date"]]
    rows.append(new_row)
    rows.sort(key=lambda r: r["date"])
    return rows


def collect_ticker(symbol):
    hist = yf.Ticker(symbol).history(period="5d")
    if hist.empty:
        raise ValueError(f"no history returned for {symbol}")
    closes = hist["Close"].dropna()
    if len(closes) < 1:
        raise ValueError(f"no close price for {symbol}")
    last_date = closes.index[-1].strftime("%Y-%m-%d")
    close = float(closes.iloc[-1])
    prev_close = float(closes.iloc[-2]) if len(closes) >= 2 else close
    collected_at = datetime.now(timezone.utc).isoformat()
    return {"date": last_date, "close": close, "prevClose": prev_close, "collectedAt": collected_at}


def collect_fx():
    usdkrw_hist = yf.Ticker("USDKRW=X").history(period="5d")["Close"].dropna()
    usdjpy_hist = yf.Ticker("USDJPY=X").history(period="5d")["Close"].dropna()
    usdkrw = float(usdkrw_hist.iloc[-1])
    usdjpy = float(usdjpy_hist.iloc[-1])
    jpykrw100 = (usdkrw / usdjpy) * 100
    today = datetime.now(KST).strftime("%Y-%m-%d")
    collected_at = datetime.now(timezone.utc).isoformat()
    return {
        "date": today,
        "usdkrw": round(usdkrw, 2),
        "jpykrw100": round(jpykrw100, 2),
        "collectedAt": collected_at,
    }


def main():
    tickers = load_json(TICKERS_FILE, [])
    if not tickers:
        print("No tickers registered in data/tickers.json — nothing to collect.")
    for entry in tickers:
        symbol = entry["symbol"]
        try:
            row = collect_ticker(symbol)
        except Exception as exc:
            print(f"[WARN] failed to collect {symbol}: {exc}")
            continue
        price_file = PRICES_DIR / f"{symbol}.json"
        rows = load_json(price_file, [])
        rows = upsert_by_date(rows, row)
        save_json(price_file, rows)
        print(f"[OK] {symbol} -> {row}")

    try:
        fx_row = collect_fx()
        fx_rows = load_json(FX_FILE, [])
        fx_rows = upsert_by_date(fx_rows, fx_row)
        save_json(FX_FILE, fx_rows)
        print(f"[OK] fx -> {fx_row}")
    except Exception as exc:
        print(f"[WARN] failed to collect fx rates: {exc}")


if __name__ == "__main__":
    main()
