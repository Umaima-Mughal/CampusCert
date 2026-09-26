import { Navigate, NavLink, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import "./admin.css";

const ADMIN_ROLES = ["admin", "super_admin"];

export default function AdminDashboard() {
  const { user, loading, logout } = useAuth();
  const location = useLocation();

  if (loading) {
    return <p className="admin-muted" style={{ padding: 40 }}>Loading...</p>;
  }
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  if (!ADMIN_ROLES.includes(user.role)) {
    return <Navigate to="/" replace />;
  }

  const title = location.pathname.includes("/exams/")
    ? "Exam"
    : location.pathname.includes("/exams")
      ? "Exam management"
      : "Admin overview";

  return (
    <div className="admin-shell">
      <aside className="admin-sidebar">
        <div className="admin-brand">
          <div className="admin-brand-mark">CC</div>
          <div>
            <h1>CampusCert</h1>
            <p>Admin portal</p>
          </div>
        </div>
        <nav className="admin-nav">
          <NavLink to="/admin" end>
            Overview
          </NavLink>
          {/*<NavLink to="/admin/exams">Exams</NavLink>*/}
          <NavLink to="/admin/exams" end>Exams</NavLink>
          <NavLink to="/admin/exams/new">Create exam</NavLink>
        </nav>
      </aside>
      <div className="admin-main">
        <header className="admin-topbar">
          <h2>{title}</h2>
          <div className="admin-topbar-meta">
            <span>{user.full_name}</span>
            <span>{user.role}</span>
            <button type="button" className="admin-btn secondary small" onClick={logout}>
              Log out
            </button>
          </div>
        </header>
        <main className="admin-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
