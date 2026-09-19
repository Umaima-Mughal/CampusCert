/**
 * src/auth/RegisterPage.jsx
 *
 * Same hybrid layout as LoginPage.jsx: dark branding left, light
 * portal-style form right.
 */

import { useState } from "react";
import { registerUser } from "../api/auth";

export default function RegisterPage({ onNavigateToLogin, onRegisterSuccess }) {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
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
      await registerUser({ fullName, email, password });
      onRegisterSuccess?.();
      onNavigateToLogin?.();
    } catch (err) {
      setError(err.message || "Registration failed. Please try again.");
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
            Join a <span className="accent">smarter</span> way to test.
          </h1>
          <p className="brand-subtext">
            Create your account to start taking exams, or to manage exams
            and question banks for your organization.
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
          <div className="portal-header">Create Your CampusCert Account</div>

          <div className="portal-form-area">
            <div className="portal-role-heading">New Registration 📝</div>

            <div className="portal-links-row">
              <button type="button" onClick={onNavigateToLogin}>Back to login</button>
              <span className="sep">|</span>
              <span className="notice">Join CampusCert</span>
            </div>

            <form onSubmit={handleSubmit}>
              <div className="portal-field">
                <label className="portal-label">👤 Full Name</label>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Jane Doe"
                  required
                />
              </div>

              <div className="portal-field">
                <label className="portal-label">📧 Email</label>
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
                  placeholder="At least 8 characters"
                  required
                />
                <p className="portal-hint">Password is case sensitive</p>
              </div>

              <div className="portal-field">
                <label className="portal-label">🔒 Confirm Password</label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Re-enter your password"
                  required
                />
              </div>

              {error && <div className="portal-error">{error}</div>}

              <button type="submit" className="portal-login-btn" disabled={loading}>
                {loading ? "Creating account..." : "Create Account"}
              </button>
            </form>

            <p className="portal-footer-note">
              Already have an account?{" "}
              <button type="button" onClick={onNavigateToLogin}>Log in</button>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
