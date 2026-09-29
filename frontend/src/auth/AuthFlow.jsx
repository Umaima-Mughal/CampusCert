/**
 * src/auth/AuthFlow.jsx
 *
 * Ties LoginPage and RegisterPage together with simple state-based
 * navigation, so you can test the whole auth flow standalone before
 * it's wired into the app's real router (React Router, etc.).
 *
 * Once the team sets up real routing, replace this with actual routes:
 *   <Route path="/login" element={<LoginPage />} />
 *   <Route path="/register" element={<RegisterPage />} />
 */

import { useState } from "react";
import LoginPage from "./LoginPage";
import RegisterPage from "./RegisterPage";

export default function AuthFlow() {
  const [screen, setScreen] = useState("login"); // "login" | "register"

  if (screen === "register") {
    return (
      <RegisterPage
        onNavigateToLogin={() => setScreen("login")}
        onRegisterSuccess={() => alert("Account created! Please log in.")}
      />
    );
  }

  return (
    <LoginPage
      onNavigateToRegister={() => setScreen("register")}
      onLoginSuccess={(user) => console.log("Logged in as:", user)}
    />
  );
}
