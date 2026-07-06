import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api.js";

function formatNumber(n, digits = 2) {
  if (n === null || n === undefined) return "-";
  return n.toLocaleString("ko-KR", { maximumFractionDigits: digits });
}

function formatCollectedAt(iso) {
  if (!iso) return "수집 대기 중";
  const d = new Date(iso);
  return d.toLocaleString("ko-KR", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function isStale(iso) {
  if (!iso) return true;
  const hours = (Date.now() - new Date(iso).getTime()) / 3600000;
  return hours > 30; // 하루 2회 수집 기준, 30시간 이상 지나면 신선도 경고
}

export default function Dashboard() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  function load() {
    setLoading(true);
    api
      .getWatchlist()
      .then((data) => {
        setItems(data);
        setError(null);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }

  useEffect(load, []);

  async function handleAck(symbol) {
    await api.ackAlert(symbol);
    load();
  }

  return (
    <div>
      <h1>관심종목 대시보드</h1>
      {error && <div className="error-banner">{error}</div>}
      {loading ? (
        <p>불러오는 중...</p>
      ) : items.length === 0 ? (
        <p>
          등록된 종목이 없습니다. <Link to="/manage">종목 관리</Link>에서 추가해주세요.
        </p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>종목</th>
              <th>현재가</th>
              <th>등락률</th>
              <th>원화환산가</th>
              <th>목표가</th>
              <th>마지막 수집</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.symbol} className={item.ackNeeded ? "breach" : ""}>
                <td>
                  <Link to={`/stock/${encodeURIComponent(item.symbol)}`}>{item.name}</Link>
                  <div style={{ fontSize: "0.75rem", color: "#888" }}>{item.symbol}</div>
                </td>
                <td>{formatNumber(item.currentPrice)}</td>
                <td className={item.changePct >= 0 ? "up" : "down"}>
                  {item.changePct === null
                    ? "-"
                    : `${item.changePct >= 0 ? "+" : ""}${formatNumber(item.changePct)}%`}
                </td>
                <td>{item.krwValue === null ? "-" : `${formatNumber(item.krwValue, 0)}원`}</td>
                <td>
                  {item.targetHigh !== null && <div>상한 {formatNumber(item.targetHigh)}</div>}
                  {item.targetLow !== null && <div>하한 {formatNumber(item.targetLow)}</div>}
                  {item.targetHigh === null && item.targetLow === null && "-"}
                  {item.ackNeeded && (
                    <span className={`badge ${item.activeBreach}`}>
                      {item.activeBreach === "above" ? "상한 도달" : "하한 도달"}
                    </span>
                  )}
                </td>
                <td className={isStale(item.lastCollectedAt) ? "stale" : ""}>
                  {formatCollectedAt(item.lastCollectedAt)}
                </td>
                <td>
                  {item.ackNeeded && (
                    <button className="secondary" onClick={() => handleAck(item.symbol)}>
                      확인
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
