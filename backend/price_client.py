"""Fetch collected price/FX history directly from GitHub raw URLs.

Reading via raw.githubusercontent.com (instead of the local git clone) means
this always reflects whatever GitHub Actions most recently pushed, with no
need to `git pull` before every read.
"""
import httpx

GITHUB_OWNER = "derreckji75-boop"
GITHUB_REPO = "stock-tracker"
GITHUB_BRANCH = "master"
RAW_BASE = f"https://raw.githubusercontent.com/{GITHUB_OWNER}/{GITHUB_REPO}/{GITHUB_BRANCH}"


def _fetch_json(path):
    url = f"{RAW_BASE}/{path}"
    try:
        resp = httpx.get(url, timeout=10)
    except httpx.HTTPError:
        return []
    if resp.status_code != 200:
        return []
    try:
        return resp.json()
    except ValueError:
        return []


def get_price_history(symbol):
    """Returns list of {date, close, prevClose, collectedAt}, oldest first."""
    return _fetch_json(f"data/prices/{symbol}.json")


def get_latest_price(symbol):
    rows = get_price_history(symbol)
    return rows[-1] if rows else None


def get_fx_history():
    return _fetch_json("data/fx.json")


def get_latest_fx():
    rows = get_fx_history()
    return rows[-1] if rows else None
