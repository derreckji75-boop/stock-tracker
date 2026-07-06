from datetime import datetime, timedelta, timezone
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import config_store
import github_sync
import price_client

app = FastAPI(title="Stock Tracker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AddStockRequest(BaseModel):
    symbol: str
    name: str
    market: Literal["US", "JP"]


class TargetRequest(BaseModel):
    targetHigh: Optional[float] = None
    targetLow: Optional[float] = None


def _krw_value(close, market, fx):
    if fx is None:
        return None
    if market == "US":
        return close * fx["usdkrw"]
    if market == "JP":
        return close * (fx["jpykrw100"] / 100)
    return None


def _merge_symbol(symbol, entry, fx):
    price = price_client.get_latest_price(symbol)
    close = price.get("close") if price else None
    prev_close = price.get("prevClose") if price else None
    change_pct = None
    if close is not None and prev_close:
        change_pct = (close - prev_close) / prev_close * 100

    alert_state = entry
    if close is not None:
        alert_state = config_store.evaluate_alert(symbol, close)

    return {
        "symbol": symbol,
        "name": entry["name"],
        "market": entry["market"],
        "currentPrice": close,
        "changePct": change_pct,
        "krwValue": _krw_value(close, entry["market"], fx) if close is not None else None,
        "targetHigh": alert_state["targetHigh"],
        "targetLow": alert_state["targetLow"],
        "activeBreach": alert_state["activeBreach"],
        "ackNeeded": alert_state["ackNeeded"],
        "lastCollectedAt": price.get("collectedAt") if price else None,
    }


@app.get("/api/watchlist")
def get_watchlist():
    watchlist = config_store.list_watchlist()
    fx = price_client.get_latest_fx()
    return [_merge_symbol(symbol, entry, fx) for symbol, entry in watchlist.items()]


@app.post("/api/watchlist")
def add_stock(body: AddStockRequest):
    try:
        config_store.add_stock(body.symbol, body.name, body.market)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    try:
        github_sync.sync_tickers(config_store.list_watchlist())
    except github_sync.GithubSyncError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Saved locally, but failed to sync ticker list to GitHub: {exc}",
        )

    fx = price_client.get_latest_fx()
    entry = config_store.list_watchlist()[body.symbol]
    return _merge_symbol(body.symbol, entry, fx)


@app.delete("/api/watchlist/{symbol}")
def remove_stock(symbol: str):
    try:
        config_store.remove_stock(symbol)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    try:
        github_sync.sync_tickers(config_store.list_watchlist())
    except github_sync.GithubSyncError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Removed locally, but failed to sync ticker list to GitHub: {exc}",
        )
    return {"ok": True}


@app.put("/api/watchlist/{symbol}/target")
def set_target(symbol: str, body: TargetRequest):
    try:
        entry = config_store.set_target(symbol, body.targetHigh, body.targetLow)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    fx = price_client.get_latest_fx()
    return _merge_symbol(symbol, entry, fx)


@app.post("/api/watchlist/{symbol}/ack")
def ack_alert(symbol: str):
    try:
        entry = config_store.ack_alert(symbol)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    fx = price_client.get_latest_fx()
    return _merge_symbol(symbol, entry, fx)


@app.get("/api/watchlist/{symbol}/history")
def get_history(symbol: str, days: int = 30):
    if symbol not in config_store.list_watchlist():
        raise HTTPException(status_code=404, detail=f"{symbol} is not in the watchlist")
    rows = price_client.get_price_history(symbol)
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    return [r for r in rows if r["date"] >= cutoff]
