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

import { BrowserRouter, Routes, Route, Navigate, useNavigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./auth/AuthContext";
import AuthPage from "./auth/AuthPage";

function LoginRoute() {
  const navigate = useNavigate();
  return <AuthPage initialMode="login" onAuthSuccess={() => navigate("/")} />;
}

function RegisterRoute() {
  return <AuthPage initialMode="register" />;
}

function HomePage() {
  const { user, loading, logout } = useAuth();

  if (loading) return <p style={{ textAlign: "center", marginTop: "40px" }}>Loading...</p>;
  if (!user) return <Navigate to="/login" replace />;

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
          <Route path="/" element={<HomePage />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
