"""Keep data/tickers.json (the public symbol list GitHub Actions collects) in
sync with the local watchlist whenever a stock is added or removed.

The local file write is synchronous (fast), but the slow git pull/commit/push
runs in a background thread so the API responds immediately. Git operations are
serialized with a lock so rapid add/remove clicks don't clobber each other.

Runs plain `git` subprocess commands against the repo this backend lives in,
reusing whatever credential helper is already configured locally (the repo
was created with `gh repo create`, so pushes just work) -- no separate token
needed.
"""
import json
import subprocess
import threading
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TICKERS_FILE = REPO_ROOT / "data" / "tickers.json"

_git_lock = threading.Lock()

# Records the outcome of the most recent background push so the API can surface
# a warning if syncing to GitHub is failing.
last_sync_error = None


class GithubSyncError(RuntimeError):
    pass


def _run_git(*args):
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0:
        raise GithubSyncError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def _push_tickers():
    """Runs in a background thread: pull, commit tickers.json, push."""
    global last_sync_error
    with _git_lock:
        try:
            try:
                _run_git("pull", "--ff-only")
            except GithubSyncError:
                pass  # best-effort; proceed with local state

            _run_git("add", "data/tickers.json")
            status = _run_git("status", "--porcelain", "data/tickers.json")
            if not status.strip():
                last_sync_error = None
                return  # nothing changed

            _run_git("commit", "-m", "sync: update tracked ticker list")
            _run_git("push")
            last_sync_error = None
        except GithubSyncError as exc:
            last_sync_error = str(exc)


def sync_tickers(watchlist):
    """Write tickers.json now (synchronous), push to GitHub in the background.

    watchlist: dict of symbol -> {market, ...} from config_store.
    """
    tickers = [{"symbol": symbol, "market": entry.get("market", "")} for symbol, entry in watchlist.items()]
    tickers.sort(key=lambda t: t["symbol"])

    with open(TICKERS_FILE, "w", encoding="utf-8") as f:
        json.dump(tickers, f, ensure_ascii=False, indent=2)
        f.write("\n")

    threading.Thread(target=_push_tickers, daemon=True).start()
