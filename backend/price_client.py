"""Read collected price/FX history from the local git clone's data/ folder.

Reading straight off the filesystem (instead of raw.githubusercontent.com on
every request) means the dashboard loads with zero network latency. Freshness
is handled separately by pulling the repo in the background (see refresh_data),
so the local files reflect whatever GitHub Actions most recently pushed.
"""
import json
import subprocess
import threading
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
PRICES_DIR = DATA_DIR / "prices"
FX_FILE = DATA_DIR / "fx.json"

_pull_lock = threading.Lock()
_last_pull = 0.0
PULL_INTERVAL = 300  # seconds; avoid pulling more than once per 5 min


def _read_json(path):
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (ValueError, OSError):
        return []


def refresh_data(force=False):
    """git pull the repo so local data/ reflects the latest Actions push.

    Rate-limited to once per PULL_INTERVAL unless force=True. Runs quietly:
    network/merge failures are ignored so the API keeps serving local data.
    """
    global _last_pull
    with _pull_lock:
        if not force and (time.time() - _last_pull) < PULL_INTERVAL:
            return
        _last_pull = time.time()
        try:
            subprocess.run(
                ["git", "pull", "--ff-only"],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                timeout=30,
            )
        except (subprocess.SubprocessError, OSError):
            pass


def refresh_data_async(force=False):
    threading.Thread(target=refresh_data, kwargs={"force": force}, daemon=True).start()


def get_price_history(symbol):
    """Returns list of {date, close, prevClose, collectedAt}, oldest first."""
    return _read_json(PRICES_DIR / f"{symbol}.json")


def get_latest_price(symbol):
    rows = get_price_history(symbol)
    return rows[-1] if rows else None


def get_fx_history():
    return _read_json(FX_FILE)


def get_latest_fx():
    rows = get_fx_history()
    return rows[-1] if rows else None
