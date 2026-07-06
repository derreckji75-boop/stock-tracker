import { useEffect, useState } from "react";
import { api } from "../api.js";

export default function ManageStocks() {
  const [items, setItems] = useState([]);
  const [symbol, setSymbol] = useState("");
  const [name, setName] = useState("");
  const [market, setMarket] = useState("US");
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  function load() {
    api.getWatchlist().then(setItems).catch((err) => setError(err.message));
  }

  useEffect(load, []);

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
