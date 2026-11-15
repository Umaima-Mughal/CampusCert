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
// import QuestionBank from './questionbank/QuestionBank'
// import OrganizationOnboardPage from "./auth/OrganizationOnboardPage";
// import { BrowserRouter, Routes, Route, Navigate, useNavigate } from "react-router-dom";
// import { AuthProvider, useAuth } from "./auth/AuthContext";
// import AuthPage from "./auth/AuthPage";
// import AdminRoutes from "./admin/AdminRoutes";
// import SecurityControlRoom from "./examiner/SecurityControlRoom";
// import StudentRoutes from "./student/StudentRoutes";


// const ADMIN_ROLES = ["admin", "super_admin"];

// function postLoginPath(user) {
//   if (user && ADMIN_ROLES.includes(user.role)) return "/admin";
//   if (user && user.role === "examiner") return "/question-bank";
//   return "/";
// }

// function LoginRoute() {
//   const navigate = useNavigate();
//   return (
//     <AuthPage
//       initialMode="login"
//       onAuthSuccess={(user) => navigate(postLoginPath(user))}
//     />
//   );
// }

// function RegisterRoute() {
//   const navigate = useNavigate();

//   return (
//     <AuthPage
//       initialMode="register"
//       onAuthSuccess={(user) => navigate(postLoginPath(user))}
//     />
//   );
// }

// function HomePage() {
//   const { user, loading, logout } = useAuth();

//   if (loading) return <p style={{ textAlign: "center", marginTop: "40px" }}>Loading...</p>;
//   if (!user) return <Navigate to="/login" replace />;
//   if (ADMIN_ROLES.includes(user.role)) return <Navigate to="/admin" replace />;
//   if (user.role === "examiner") return <Navigate to="/question-bank" replace />;

//   return (
//     <div style={{ padding: "40px", textAlign: "center", color: "#fff", background: "#030712", minHeight: "100vh" }}>
//       <h1>Welcome, {user.full_name} 👋</h1>
//       <p>Role: {user.role}</p>
//       <button onClick={logout} style={{ marginTop: "16px" }}>
//         Log out
//       </button>
//     </div>
//   );
// }

// export default function App() {
//   return (
//     <AuthProvider>
//       <BrowserRouter>
//         <Routes>
//           <Route path="/login" element={<LoginRoute />} />
//           <Route path="/register" element={<RegisterRoute />} />
//           <Route path="/organization/onboard" element={<OrganizationOnboardPage />} />
//           <Route path="/question-bank" element={<QuestionBank />} />
//           <Route path="/admin/*" element={<AdminRoutes />} />
//           <Route path="/" element={<HomePage />} />
// <Route path="/examiner/security"element={<SecurityControlRoom />} />
// <Route path="/student/*" element={<StudentRoutes />} />
//         </Routes>
//       </BrowserRouter>
//     </AuthProvider>
//   );
// }


import QuestionBank from "./questionbank/QuestionBank";
import OrganizationOnboardPage from "./auth/OrganizationOnboardPage";
import {
  BrowserRouter,
  Routes,
  Route,
  Navigate,
  Link,
  useNavigate,
} from "react-router-dom";
import { AuthProvider, useAuth } from "./auth/AuthContext";
import AuthPage from "./auth/AuthPage";
import AdminRoutes from "./admin/AdminRoutes";
import SecurityControlRoom from "./examiner/SecurityControlRoom";
import StudentRoutes from "./student/StudentRoutes";

const ADMIN_ROLES = ["admin", "super_admin"];


function postLoginPath(user) {
  if (user && ADMIN_ROLES.includes(user.role)) return "/admin";
  if (user && user.role === "examiner") return "/question-bank";
  if (user && user.role === "student") return "/student";
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

// Member 5: Add Security Control Room navigation
// to the existing Examiner Question Bank page.
function ExaminerQuestionBank() {
  const { user, loading } = useAuth();

  if (loading) {
    return <p style={{ textAlign: "center" }}>Loading...</p>;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div>
      {user.role === "examiner" && (
        <div
          style={{
            backgroundColor: "#ffffff",
            padding: "16px 24px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: "12px",
            flexWrap: "wrap",
            borderBottom: "3px solid #e36a12",
          }}
        >
          <div>
            <strong
              style={{
                color: "#1c2430",
                fontSize: "18px",
              }}
            >
              Examiner Portal
            </strong>

            <p
              style={{
                color: "#5c6773",
                margin: "4px 0 0",
                fontSize: "13px",
              }}
            >
              Manage questions and monitor exam security
            </p>
          </div>

          <Link
            to="/examiner/security"
            style={{
              backgroundColor: "#e36a12",
              color: "#ffffff",
              padding: "10px 16px",
              borderRadius: "6px",
              textDecoration: "none",
              fontWeight: "600",
              display: "inline-block",
            }}
          >
            🛡️ Open Security Control Room
          </Link>
        </div>
      )}

      <QuestionBank />
    </div>
  );
}


function HomePage() {
  const { user, loading, logout } = useAuth();

  if (loading) {
    return (
      <p style={{ textAlign: "center", marginTop: "40px" }}>
        Loading...
      </p>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (ADMIN_ROLES.includes(user.role)) {
    return <Navigate to="/admin" replace />;
  }

  if (user.role === "examiner") {
    return <Navigate to="/question-bank" replace />;
  }

  // Member 5: Student ko direct My Exams page par bhejo
  if (user.role === "student") {
    return <Navigate to="/student" replace />;
  }

  return (
    <div
      style={{
        padding: "40px",
        textAlign: "center",
        color: "#1c2430",
        background: "#f4f6f8",
        minHeight: "100vh",
      }}
    >
      <h1>Welcome, {user.full_name} 👋</h1>
      <p>Role: {user.role}</p>

      <button
        onClick={logout}
        style={{ marginTop: "16px" }}
      >
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

          <Route
            path="/register"
            element={<RegisterRoute />}
          />

          <Route
            path="/organization/onboard"
            element={<OrganizationOnboardPage />}
          />

          <Route
            path="/question-bank"
            element={<ExaminerQuestionBank />}
          />

          <Route
            path="/admin/*"
            element={<AdminRoutes />}
          />

          <Route path="/" element={<HomePage />} />

          <Route
            path="/examiner/security"
            element={<SecurityControlRoom />}
          />

          <Route
            path="/student/*"
            element={<StudentRoutes />}
          />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
