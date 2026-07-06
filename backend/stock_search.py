"""Look up ticker/company name suggestions via yfinance's search endpoint.

Only US and Japan (Yahoo ".T" suffix) equities are returned since that's all
this app tracks -- other exchanges are filtered out.
"""
import yfinance as yf

JP_SUFFIX = ".T"


def search_stocks(query, limit=8):
    query = (query or "").strip()
    if not query:
        return []

    try:
        quotes = yf.Search(query, max_results=limit * 3).quotes
    except Exception:
        return []

    items = []
    seen = set()
    for q in quotes:
        if q.get("quoteType") != "EQUITY":
            continue
        symbol = q.get("symbol", "")
        if symbol.endswith(JP_SUFFIX):
            market = "JP"
        elif "." not in symbol:
            market = "US"
        else:
            continue  # other exchanges (Frankfurt, London, ...) are out of scope

        if symbol in seen:
            continue
        seen.add(symbol)

        name = q.get("longname") or q.get("shortname") or symbol
        items.append({"symbol": symbol, "name": name, "market": market})
        if len(items) >= limit:
            break

    return items
