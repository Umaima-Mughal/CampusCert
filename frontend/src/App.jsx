/**
 * src/App.jsx
 *
 * Root component and router. /login and /register both render the
 * same AuthPage, just starting on a different tab — since the design
 * is one screen with a Sign In / Register switch, not two screens.
 *
 * Other members will add their own routes here later:
 *   <Route path="/admin/*" element={<AdminDashboard />} />
 *   <Route path="/student/*" element={<StudentDashboard />} />
 *   <Route path="/examiner/*" element={<ExaminerDashboard />} />
 * Since this file is shared, give the team a heads-up before editing it.
 */
import OrganizationOnboardPage from "./auth/OrganizationOnboardPage";
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./auth/AuthContext";
import AuthPage from "./auth/AuthPage";
import AdminRoutes from "./admin/AdminRoutes";

const ADMIN_ROLES = ["admin", "super_admin"];

function postLoginPath(user) {
  if (user && ADMIN_ROLES.includes(user.role)) return "/admin";
  return "/";
}

function LoginRoute() {
  const navigate = useNavigate();
  return (
    <AuthPage
      initialMode="login"
      onAuthSuccess={(user) => navigate(postLoginPath(user))}
    />
  );
}

function RegisterRoute() {
  const navigate = useNavigate();

  return (
    <AuthPage
      initialMode="register"
      onAuthSuccess={(user) => navigate(postLoginPath(user))}
    />
  );
}

function HomePage() {
  const { user, loading, logout } = useAuth();

  if (loading) return <p style={{ textAlign: "center", marginTop: "40px" }}>Loading...</p>;
  if (!user) return <Navigate to="/login" replace />;
  if (ADMIN_ROLES.includes(user.role)) return <Navigate to="/admin" replace />;

  return (
    <div style={{ padding: "40px", textAlign: "center", color: "#fff", background: "#030712", minHeight: "100vh" }}>
      <h1>Welcome, {user.full_name} 👋</h1>
      <p>Role: {user.role}</p>
      <button onClick={logout} style={{ marginTop: "16px" }}>
        Log out
      </button>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginRoute />} />
          <Route path="/register" element={<RegisterRoute />} />
          <Route path="/organization/onboard" element={<OrganizationOnboardPage />} /> 
          <Route path="/admin/*" element={<AdminRoutes />} />
          <Route path="/" element={<HomePage />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
