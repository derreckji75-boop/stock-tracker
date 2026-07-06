import { HashRouter, Routes, Route, NavLink } from "react-router-dom";
import Dashboard from "./pages/Dashboard.jsx";
import StockDetail from "./pages/StockDetail.jsx";
import ManageStocks from "./pages/ManageStocks.jsx";

export default function App() {
  return (
    <HashRouter>
      <nav>
        <NavLink to="/" end>
          대시보드
        </NavLink>
        <NavLink to="/manage">종목 관리</NavLink>
      </nav>
      <main>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/stock/:symbol" element={<StockDetail />} />
          <Route path="/manage" element={<ManageStocks />} />
        </Routes>
      </main>
    </HashRouter>
  );
}
