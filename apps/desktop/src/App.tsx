import { NavLink, Route, Routes, useNavigate } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import Tutor from "./pages/Tutor";
import ProgressMap from "./pages/ProgressMap";
import SrsReview from "./pages/SrsReview";
import Setup from "./pages/Setup";
import Settings from "./pages/Settings";
import { BookSwitcher } from "./components/BookSwitcher";

export default function App() {
  const navigate = useNavigate();
  return (
    <div className="app-shell">
      <nav className="nav">
        <p className="brand">
          J<span>tutor</span>
        </p>
        <p className="nav-sub">Irodori · local tutor</p>
        <BookSwitcher
          compact
          onChanged={() => {
            navigate("/");
            window.location.reload();
          }}
        />
        <NavLink to="/" end className={({ isActive }) => (isActive ? "active" : undefined)}>
          Home
        </NavLink>
        <NavLink to="/tutor" className={({ isActive }) => (isActive ? "active" : undefined)}>Tutor</NavLink>
        <NavLink to="/progress" className={({ isActive }) => (isActive ? "active" : undefined)}>Progress</NavLink>
        <NavLink to="/srs" className={({ isActive }) => (isActive ? "active" : undefined)}>SRS</NavLink>
        <NavLink to="/setup" className={({ isActive }) => (isActive ? "active" : undefined)}>Setup</NavLink>
        <NavLink to="/settings" className={({ isActive }) => (isActive ? "active" : undefined)}>Settings</NavLink>
      </nav>
      <main className="main">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/tutor" element={<Tutor />} />
          <Route path="/tutor/:lessonId" element={<Tutor />} />
          <Route path="/progress" element={<ProgressMap />} />
          <Route path="/srs" element={<SrsReview />} />
          <Route path="/setup" element={<Setup />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </main>
    </div>
  );
}
