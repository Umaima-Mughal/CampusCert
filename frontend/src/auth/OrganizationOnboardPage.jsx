/**
 * Organization-first onboarding. Creates a university record and
 * returns a user-facing Org Code for Admin / Examiner / Student registration.
 */

import { useState } from "react";
import { Link } from "react-router-dom";
import { onboardOrganization } from "../api/organizations";

export default function OrganizationOnboardPage() {
  const [name, setName] = useState("");
  const [contactEmail, setContactEmail] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [created, setCreated] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const org = await onboardOrganization({ name, contactEmail });
      setCreated(org);
    } catch (err) {
      setError(err.message || "Could not create the organization.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="container">
      <div className="card">
        <div className="left-panel">
          <div className="brand">
            <div className="logo">CC</div>
            <div className="brand-text">
              <h3>CampusCert</h3>
              <span>Online Examination Platform</span>
            </div>
          </div>
          <div className="hero">
            <h1>
              Register your <span>institution</span> first.
            </h1>
            <p>
              Create the organization once. Admins, examiners, and students
              then join with the same Org Code.
            </p>
          </div>
        </div>

        <div className="right-panel">
          <div className="portal-topbar">Create organization</div>
          <div className="right-panel-body">
            <div className="auth-container">
              {created ? (
                <div className="form">
                  <h2>Organization created</h2>
                  <p className="subtitle">
                    Share this Org Code with admins, examiners, and students.
                    It is unique to {created.name}.
                  </p>
                  <div className="input-group">
                    <input
                      readOnly
                      value={created.org_code}
                      aria-label="Organization code"
                    />
                  </div>
                  <p className="subtitle">
                    Keep this code. Users cannot register without it.
                  </p>
                  <Link
                    className="btn-primary"
                   // to={`/register?org=${encodeURIComponent(created.org_code)}`}
                   to={`/register?org=${encodeURIComponent(
                    created.org_code
                  )}&role=admin`}
                    style={{ display: "block", textAlign: "center", textDecoration: "none" }}
                  >
                    Continue to Admin registration
                  </Link>
                </div>
              ) : (
                <div className="form">
                  <h2>New organization</h2>
                  <p className="subtitle">
                    You will receive an Org Code to use during registration.
                  </p>
                  <form onSubmit={handleSubmit}>
                    <div className="input-group">
                      <input
                        type="text"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        placeholder="Organization name"
                        required
                        minLength={2}
                      />
                    </div>
                    <div className="input-group">
                      <input
                        type="email"
                        value={contactEmail}
                        onChange={(e) => setContactEmail(e.target.value)}
                        placeholder="Official contact email"
                        required
                      />
                    </div>
                    {error && <div className="form-error">{error}</div>}
                    <button type="submit" className="btn-primary" disabled={loading}>
                      {loading ? "Creating..." : "Create organization"}
                    </button>
                  </form>
                  <p className="switch-text">
                    Already have an Org Code?{" "}
                    <Link to="/register">Register</Link>
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
