import { Navigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

/** Only logged-in students get past this. Everyone else is sent to the right place. */
export default function StudentGuard({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <p className="st-muted" style={{ padding: 40 }}>Loading...</p>;
  if (!user) return <Navigate to="/login" replace />;
  if (user.role !== "student") return <Navigate to="/" replace />;
  return children;
}
