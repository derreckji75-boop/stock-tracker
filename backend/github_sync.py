"""Keep data/tickers.json (the public symbol list GitHub Actions collects) in
sync with the local watchlist whenever a stock is added or removed.

Runs plain `git` subprocess commands against the repo this backend lives in,
reusing whatever credential helper is already configured locally (the repo
was created with `gh repo create`, so pushes just work) -- no separate token
needed.
"""
import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TICKERS_FILE = REPO_ROOT / "data" / "tickers.json"


class GithubSyncError(RuntimeError):
    pass


def _run_git(*args):
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise GithubSyncError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def sync_tickers(watchlist):
    """watchlist: dict of symbol -> {market, ...} from config_store."""
    tickers = [{"symbol": symbol, "market": entry.get("market", "")} for symbol, entry in watchlist.items()]
    tickers.sort(key=lambda t: t["symbol"])

    try:
        _run_git("pull", "--ff-only")
    except GithubSyncError:
        pass  # best-effort; proceed with whatever local state we have

    with open(TICKERS_FILE, "w", encoding="utf-8") as f:
        json.dump(tickers, f, ensure_ascii=False, indent=2)
        f.write("\n")

    _run_git("add", "data/tickers.json")

    status = _run_git("status", "--porcelain", "data/tickers.json")
    if not status.strip():
        return  # no change, nothing to commit

    _run_git("commit", "-m", "sync: update tracked ticker list")
    _run_git("push")
