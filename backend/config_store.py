"""Local-only watchlist config: names, target prices, alert ack state.

Never committed to git (see .gitignore) — separate from the public price data
that GitHub Actions collects. See data/tickers.json for the public symbol list
this config is synced to (via github_sync.py).
"""
import json
import threading
from pathlib import Path

CONFIG_FILE = Path(__file__).resolve().parent / "data" / "config.local.json"

_lock = threading.Lock()


def _default_config():
    return {"watchlist": {}}


def load_config():
    if not CONFIG_FILE.exists():
        return _default_config()
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(config):
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
        f.write("\n")


def list_watchlist():
    return load_config()["watchlist"]


def add_stock(symbol, name, market):
    with _lock:
        config = load_config()
        if symbol in config["watchlist"]:
            raise ValueError(f"{symbol} is already in the watchlist")
        config["watchlist"][symbol] = {
            "name": name,
            "market": market,
            "targetHigh": None,
            "targetLow": None,
            "activeBreach": None,
            "ackNeeded": False,
        }
        save_config(config)
        return config["watchlist"][symbol]


def remove_stock(symbol):
    with _lock:
        config = load_config()
        if symbol not in config["watchlist"]:
            raise KeyError(f"{symbol} is not in the watchlist")
        del config["watchlist"][symbol]
        save_config(config)


def set_target(symbol, target_high, target_low):
    with _lock:
        config = load_config()
        if symbol not in config["watchlist"]:
            raise KeyError(f"{symbol} is not in the watchlist")
        config["watchlist"][symbol]["targetHigh"] = target_high
        config["watchlist"][symbol]["targetLow"] = target_low
        save_config(config)
        return config["watchlist"][symbol]


def ack_alert(symbol):
    with _lock:
        config = load_config()
        if symbol not in config["watchlist"]:
            raise KeyError(f"{symbol} is not in the watchlist")
        config["watchlist"][symbol]["ackNeeded"] = False
        save_config(config)
        return config["watchlist"][symbol]


def evaluate_alert(symbol, current_price):
    """Recompute breach state for `symbol` given `current_price` and persist it.

    A new breach event (first crossing, direction flip, or re-breach after
    returning to normal range) sets ackNeeded=True. Staying in the same
    breach direction leaves ackNeeded untouched (so an acknowledged alert
    stays quiet until something actually changes).
    """
    with _lock:
        config = load_config()
        entry = config["watchlist"].get(symbol)
        if entry is None:
            return None

        target_high = entry.get("targetHigh")
        target_low = entry.get("targetLow")

        if target_high is not None and current_price >= target_high:
            current_breach = "above"
        elif target_low is not None and current_price <= target_low:
            current_breach = "below"
        else:
            current_breach = None

        if current_breach != entry.get("activeBreach"):
            entry["activeBreach"] = current_breach
            if current_breach is not None:
                entry["ackNeeded"] = True

        save_config(config)
        return entry
