import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { api } from "../api.js";

const RANGE_OPTIONS = [
  { label: "1개월", days: 30 },
  { label: "3개월", days: 90 },
  { label: "1년", days: 365 },
];

export default function StockDetail() {
  const { symbol } = useParams();
  const navigate = useNavigate();
  const [days, setDays] = useState(30);
  const [history, setHistory] = useState([]);
  const [watchlistItem, setWatchlistItem] = useState(null);
  const [targetHigh, setTargetHigh] = useState("");
  const [targetLow, setTargetLow] = useState("");
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);

  function loadWatchlist() {
    api.getWatchlist().then((items) => {
      const item = items.find((i) => i.symbol === symbol);
      setWatchlistItem(item || null);
      if (item) {
        setTargetHigh(item.targetHigh ?? "");
        setTargetLow(item.targetLow ?? "");
      }
    });
  }

  function loadHistory() {
    api
      .getHistory(symbol, days)
      .then(setHistory)
      .catch((err) => setError(err.message));
  }

  useEffect(loadWatchlist, [symbol]);
  useEffect(loadHistory, [symbol, days]);

  async function handleSaveTarget(e) {
    e.preventDefault();
    setSaving(true);
    try {
      await api.setTarget(symbol, {
        targetHigh: targetHigh === "" ? null : Number(targetHigh),
        targetLow: targetLow === "" ? null : Number(targetLow),
      });
      loadWatchlist();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  if (!watchlistItem) {
    return (
      <div>
        <button className="secondary" onClick={() => navigate("/")}>
          ← 대시보드로
        </button>
        <p>불러오는 중이거나 등록되지 않은 종목입니다.</p>
      </div>
    );
  }

  return (
    <div>
      <button className="secondary" onClick={() => navigate("/")}>
        ← 대시보드로
      </button>
      <h1>
        {watchlistItem.name} <span style={{ color: "#888", fontSize: "1rem" }}>{symbol}</span>
      </h1>
      {error && <div className="error-banner">{error}</div>}

      <div style={{ marginBottom: "1rem" }}>
        {RANGE_OPTIONS.map((opt) => (
          <button
            key={opt.days}
            className={days === opt.days ? "" : "secondary"}
            style={{ marginRight: "0.5rem" }}
            onClick={() => setDays(opt.days)}
          >
            {opt.label}
          </button>
        ))}
      </div>

      <div style={{ background: "white", borderRadius: 8, padding: "1rem", marginBottom: "1.5rem" }}>
        {history.length === 0 ? (
          <p>차트를 표시할 데이터가 없습니다.</p>
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={history}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" tick={{ fontSize: 12 }} />
              <YAxis domain={["auto", "auto"]} tick={{ fontSize: 12 }} />
              <Tooltip />
              <Line type="monotone" dataKey="close" stroke="#1a1a2e" dot={false} />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      <h2>목표가 설정</h2>
      <form className="stock-form" onSubmit={handleSaveTarget}>
        <label>
          상한가
          <input
            type="number"
            step="0.01"
            value={targetHigh}
            onChange={(e) => setTargetHigh(e.target.value)}
            placeholder="미설정"
          />
        </label>
        <label>
          하한가
          <input
            type="number"
            step="0.01"
            value={targetLow}
            onChange={(e) => setTargetLow(e.target.value)}
            placeholder="미설정"
          />
        </label>
        <button type="submit" disabled={saving}>
          저장
        </button>
      </form>
    </div>
  );
}
