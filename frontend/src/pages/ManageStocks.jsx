import { useEffect, useState } from "react";
import { api } from "../api.js";

export default function ManageStocks() {
  const [items, setItems] = useState([]);
  const [symbol, setSymbol] = useState("");
  const [name, setName] = useState("");
  const [market, setMarket] = useState("US");
  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  function load() {
    api.getWatchlist().then(setItems).catch((err) => setError(err.message));
  }

  useEffect(load, []);

  useEffect(() => {
    const q = query.trim();
    if (q.length < 1) {
      setSuggestions([]);
      return;
    }
    setSearching(true);
    const timer = setTimeout(() => {
      api
        .search(q)
        .then(setSuggestions)
        .catch(() => setSuggestions([]))
        .finally(() => setSearching(false));
    }, 300);
    return () => clearTimeout(timer);
  }, [query]);

  function pickSuggestion(item) {
    setSymbol(item.symbol);
    setName(item.name);
    setMarket(item.market);
    setQuery("");
    setSuggestions([]);
  }

  async function handleAdd(e) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await api.addStock({ symbol: symbol.trim(), name: name.trim(), market });
      setSymbol("");
      setName("");
      load();
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  async function handleRemove(sym) {
    try {
      await api.removeStock(sym);
      load();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div>
      <h1>종목 관리</h1>
      {error && <div className="error-banner">{error}</div>}

      <div style={{ position: "relative", marginBottom: "1rem" }}>
        <input
          style={{ width: "100%", padding: "0.6rem" }}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="종목명 또는 티커로 검색 (예: apple, toyota, AAPL)"
        />
        {query.trim() && (
          <ul
            style={{
              listStyle: "none",
              margin: 0,
              padding: 0,
              position: "absolute",
              top: "100%",
              left: 0,
              right: 0,
              background: "white",
              border: "1px solid #ddd",
              borderRadius: 6,
              boxShadow: "0 4px 10px rgba(0,0,0,0.1)",
              zIndex: 10,
              maxHeight: 260,
              overflowY: "auto",
            }}
          >
            {searching && <li style={{ padding: "0.5rem 0.75rem", color: "#888" }}>검색 중...</li>}
            {!searching && suggestions.length === 0 && (
              <li style={{ padding: "0.5rem 0.75rem", color: "#888" }}>검색 결과 없음</li>
            )}
            {suggestions.map((s) => (
              <li key={s.symbol}>
                <button
                  type="button"
                  className="secondary"
                  style={{ width: "100%", textAlign: "left", borderRadius: 0 }}
                  onClick={() => pickSuggestion(s)}
                >
                  {s.name} <span style={{ color: "#888" }}>({s.symbol} · {s.market === "US" ? "미국" : "일본"})</span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      <form className="stock-form" onSubmit={handleAdd}>
        <label>
          티커
          <input
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
            placeholder="예: AAPL, 7203.T"
            required
          />
        </label>
        <label>
          종목명
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="예: Apple Inc."
            required
          />
        </label>
        <label>
          시장
          <select value={market} onChange={(e) => setMarket(e.target.value)}>
            <option value="US">미국</option>
            <option value="JP">일본</option>
          </select>
        </label>
        <button type="submit" disabled={submitting}>
          추가
        </button>
      </form>

      <table>
        <thead>
          <tr>
            <th>티커</th>
            <th>종목명</th>
            <th>시장</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.symbol}>
              <td>{item.symbol}</td>
              <td>{item.name}</td>
              <td>{item.market === "US" ? "미국" : "일본"}</td>
              <td>
                <button className="danger" onClick={() => handleRemove(item.symbol)}>
                  삭제
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
