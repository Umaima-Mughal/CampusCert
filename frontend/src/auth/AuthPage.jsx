/**
 * src/auth/AuthPage.jsx
 *
 * One screen, two modes — "Sign In" and "Register" toggle via the
 * switch tabs at the top of the right panel (like the CyberSentrix
 * reference), instead of being two separate page designs.
 */

import { useState } from "react";
import { loginUser, registerUser, getCurrentUser, logoutUser } from "../api/auth";
import { useAuth } from "./AuthContext";

export default function AuthPage({ initialMode = "login", onAuthSuccess }) {
  const { setUser } = useAuth();
  const [mode, setMode] = useState(initialMode); // "login" | "register"
  const [activeRole, setActiveRole] = useState("student"); // label only — see note below

  const ROLE_TABS = [
    { key: "student", label: "Student" },
    { key: "examiner", label: "Examiner" },
    { key: "admin", label: "Admin" },
  ];

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function switchMode(next) {
    setMode(next);
    setError("");
  }

  async function handleLogin(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await loginUser({ email, password });
      const me = await getCurrentUser();

      // The tab the user picked (Student / Examiner / Admin) must match
      // the role that's actually on their account, or we bail out and
      // don't let them into the wrong portal.
      if (me.role !== activeRole) {
        logoutUser();
        const pickedLabel = ROLE_TABS.find((t) => t.key === activeRole)?.label || activeRole;
        const actualLabel = ROLE_TABS.find((t) => t.key === me.role)?.label || me.role;
        setError(
          `This account is registered as ${actualLabel}, not ${pickedLabel}. Select the ${actualLabel} tab to log in.`
        );
        return;
      }

      setUser(me);
      onAuthSuccess?.(me);
    } catch (err) {
      setError(err.message || "Login failed. Check your email and password.");
    } finally {
      setLoading(false);
    }
  }

  async function handleRegister(e) {
    e.preventDefault();
    setError("");

    if (password !== confirmPassword) {
      setError("Passwords don't match.");
      return;
    }
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }

    setLoading(true);
    try {
      await registerUser({ fullName, email, password, role: activeRole });
      switchMode("login");
      setPassword("");
      setConfirmPassword("");
    } catch (err) {
      setError(err.message || "Registration failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="container">
      <div className="card">
        {/* LEFT PANEL */}
        <div className="left-panel">
          <div className="brand">
            <div className="logo">🎓</div>
            <div className="brand-text">
              <h3>CampusCert</h3>
              <span>Online Examination Platform</span>
            </div>
          </div>

          <div className="hero">
            <h1>
              Secure exams. <span>Verified results.</span>
            </h1>
            <p>
              Take and manage certification exams online — proctored,
              auto-graded, and built for every role from student to
              administrator.
            </p>
          </div>

          <ul className="features">
            <li>🛡️ Live integrity monitoring keeps every exam session honest</li>
            <li>⚡ Instant auto-grading gets results back the moment you submit</li>
            <li>🔑 Role-based access for students, examiners, and admins</li>
          </ul>
        </div>

        {/* RIGHT PANEL */}
        <div className="right-panel">
          <div className="portal-topbar">CampusCert Portal Login</div>

          <div className="role-tabs">
            {ROLE_TABS.map((tab) => (
              <button
                key={tab.key}
                type="button"
                className={`role-tab ${activeRole === tab.key ? "active" : ""}`}
                onClick={() => setActiveRole(tab.key)}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <div className="right-panel-body">
          <div className="auth-container">
            <div className="switch">
              <button
                type="button"
                className={mode === "login" ? "active" : ""}
                onClick={() => switchMode("login")}
              >
                Sign In
              </button>
              <button
                type="button"
                className={mode === "register" ? "active" : ""}
                onClick={() => switchMode("register")}
              >
                Register
              </button>
            </div>

            {mode === "login" ? (
              <div className="form">
                <h2>Welcome back</h2>
                <p className="subtitle">Log in to your CampusCert account</p>

                <form onSubmit={handleLogin}>
                  <div className="input-group">
                    <span className="input-icon">✉️</span>
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="you@university.edu"
                      required
                    />
                  </div>

                  <div className="input-group">
                    <span className="input-icon">🔒</span>
                    <input
                      type={showPassword ? "text" : "password"}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Password"
                      required
                    />
                    <button
                      type="button"
                      className="eye"
                      onClick={() => setShowPassword((s) => !s)}
                      aria-label="Toggle password visibility"
                    >
                      {showPassword ? "🙈" : "👁️"}
                    </button>
                  </div>

                  {error && <div className="form-error">{error}</div>}

                  <button type="submit" className="btn-primary" disabled={loading}>
                    {loading ? "Logging in..." : "Access Platform"}
                  </button>
                </form>

                <p className="switch-text">
                  Don't have an account?{" "}
                  <button type="button" onClick={() => switchMode("register")}>
                    Register
                  </button>
                </p>
              </div>
            ) : (
              <div className="form">
                <h2>Create your account</h2>
                <p className="subtitle">Join CampusCert to get started</p>

                <form onSubmit={handleRegister}>
                  <div className="input-group">
                    <span className="input-icon">👤</span>
                    <input
                      type="text"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      placeholder="Full name"
                      required
                    />
                  </div>

                  <div className="input-group">
                    <span className="input-icon">✉️</span>
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="you@university.edu"
                      required
                    />
                  </div>

                  <div className="input-group">
                    <span className="input-icon">🔒</span>
                    <input
                      type={showPassword ? "text" : "password"}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Password (min 8 characters)"
                      required
                    />
                    <button
                      type="button"
                      className="eye"
                      onClick={() => setShowPassword((s) => !s)}
                      aria-label="Toggle password visibility"
                    >
                      {showPassword ? "🙈" : "👁️"}
                    </button>
                  </div>

                  <div className="input-group">
                    <span className="input-icon">🔒</span>
                    <input
                      type={showPassword ? "text" : "password"}
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder="Confirm password"
                      required
                    />
                  </div>

                  {error && <div className="form-error">{error}</div>}

                  <button type="submit" className="btn-primary" disabled={loading}>
                    {loading ? "Creating account..." : "Create Account"}
                  </button>
                </form>

                <p className="switch-text">
                  Already have an account?{" "}
                  <button type="button" onClick={() => switchMode("login")}>
                    Sign In
                  </button>
                </p>
              </div>
            )}
          </div>
          </div>
        </div>
      </div>
    </div>
  );
}