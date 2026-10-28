import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import "./student.css";

export default function StudentLayout() {
  const { user, logout } = useAuth();
  return (
    <div className="st-shell">
      <header className="st-topbar">
        <div className="st-brand">
          <div className="st-brand-mark">CC</div>
          <div>
            <h1>CampusCert</h1>
            <p>Student portal</p>
          </div>
        </div>
        <nav className="st-nav">
          <NavLink to="/student" end>My exams</NavLink>
        </nav>
        <div className="st-user">
          <span>{user?.full_name}</span>
          <button type="button" className="st-btn ghost small" onClick={logout}>Log out</button>
        </div>
      </header>
      <main className="st-content">
        <Outlet />
      </main>
    </div>
  );
}
