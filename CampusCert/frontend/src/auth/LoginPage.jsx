/**
 * src/auth/LoginPage.jsx
 *
 * LEFT = dark glass branding panel (photo background, gradient headline,
 *        feature list) — matches the CyberSentrix reference.
 * RIGHT = light boxed form with role tabs and a red header — matches
 *         the NED-portal reference.
 */

import { useState } from "react";
import { loginUser, getCurrentUser } from "../api/auth";
import { useAuth } from "./AuthContext";

const ROLE_TABS = [
  { key: "student", label: "Student" },
  { key: "examiner", label: "Examiner" },
  { key: "admin", label: "Admin" },
];

export default function LoginPage({ onNavigateToRegister, onLoginSuccess }) {
  const { setUser } = useAuth();
  const [activeTab, setActiveTab] = useState("student");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const roleLabel = ROLE_TABS.find((t) => t.key === activeTab)?.label || "Student";

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await loginUser({ email, password });
      const me = await getCurrentUser();
      setUser(me);
      onLoginSuccess?.(me);
    } catch (err) {
      setError(err.message || "Login failed. Check your email and password.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-container">
        {/* LEFT — dark branding panel */}
        <div className="auth-brand-panel">
          <div className="brand-mark">
            <div className="brand-icon">🎓</div>
            <div>
              <div className="brand-name">CampusCert</div>
              <div className="brand-tagline">Online Examination Platform</div>
            </div>
          </div>

          <h1 className="brand-headline">
            Secure exams. <span className="accent">Verified results.</span>
          </h1>
          <p className="brand-subtext">
            Take and manage certification exams online — proctored,
            auto-graded, and built for every role.
          </p>

          <div className="feature-list">
            <div className="feature-item">
              <div className="feature-icon">🛡️</div>
              <div className="feature-text">
                <strong>Live integrity monitoring</strong> keeps every exam session honest.
              </div>
            </div>
            <div className="feature-item">
              <div className="feature-icon">⚡</div>
              <div className="feature-text">
                <strong>Instant auto-grading</strong> gets results back the moment you submit.
              </div>
            </div>
            <div className="feature-item">
              <div className="feature-icon">🔑</div>
              <div className="feature-text">
                <strong>Role-based access</strong> for students, examiners, and admins.
              </div>
            </div>
          </div>
        </div>

        {/* RIGHT — light portal-style form */}
        <div className="auth-form-panel">
          <div className="portal-header">CampusCert Portal Login</div>

          <div className="portal-tabs">
            {ROLE_TABS.map((tab) => (
              <button
                key={tab.key}
                type="button"
                className={`portal-tab ${activeTab === tab.key ? "active" : ""}`}
                onClick={() => setActiveTab(tab.key)}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <div className="portal-form-area">
            <div className="portal-role-heading">{roleLabel} 🔐</div>

            <div className="portal-links-row">
              <button type="button" onClick={onNavigateToRegister}>Create account</button>
              <span className="sep">|</span>
              <span className="notice">Welcome back</span>
            </div>

            <form onSubmit={handleSubmit}>
              <div className="portal-field">
                <label className="portal-label">👤 Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@university.edu"
                  required
                />
              </div>

              <div className="portal-field">
                <label className="portal-label">🔒 Password</label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  required
                />
                <p className="portal-hint">Password is case sensitive</p>
              </div>

              {error && <div className="portal-error">{error}</div>}

              <button type="submit" className="portal-login-btn" disabled={loading}>
                {loading ? "Logging in..." : "Login"}
              </button>
            </form>

            <p className="portal-footer-note">
              Don't have an account?{" "}
              <button type="button" onClick={onNavigateToRegister}>Register here</button>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
