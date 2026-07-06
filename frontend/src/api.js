const BASE_URL = "http://127.0.0.1:8000";

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `요청 실패 (${res.status})`);
  }
  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  getWatchlist: () => request("/api/watchlist"),
  addStock: (payload) =>
    request("/api/watchlist", { method: "POST", body: JSON.stringify(payload) }),
  removeStock: (symbol) =>
    request(`/api/watchlist/${encodeURIComponent(symbol)}`, { method: "DELETE" }),
  setTarget: (symbol, payload) =>
    request(`/api/watchlist/${encodeURIComponent(symbol)}/target`, {
      method: "PUT",
      body: JSON.stringify(payload),
    }),
  ackAlert: (symbol) =>
    request(`/api/watchlist/${encodeURIComponent(symbol)}/ack`, { method: "POST" }),
  getHistory: (symbol, days) =>
    request(`/api/watchlist/${encodeURIComponent(symbol)}/history?days=${days}`),
};
