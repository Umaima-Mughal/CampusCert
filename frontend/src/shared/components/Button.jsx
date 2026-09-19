/**
 * src/shared/components/Button.jsx
 *
 * Reusable button used across the whole app (login form, admin dashboard,
 * exam-taking screens, etc.) so every screen looks consistent.
 */

export default function Button({
  children,
  onClick,
  type = "button",
  variant = "primary", // "primary" | "secondary" | "danger"
  disabled = false,
  fullWidth = false,
}) {
  const base = {
    padding: "10px 18px",
    borderRadius: "8px",
    border: "none",
    fontSize: "14px",
    fontWeight: 600,
    cursor: disabled ? "not-allowed" : "pointer",
    opacity: disabled ? 0.6 : 1,
    width: fullWidth ? "100%" : "auto",
    transition: "opacity 0.15s ease",
  };

  const variants = {
    primary: { backgroundColor: "#4F46E5", color: "#fff" },
    secondary: { backgroundColor: "#E5E7EB", color: "#111827" },
    danger: { backgroundColor: "#DC2626", color: "#fff" },
  };

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      style={{ ...base, ...variants[variant] }}
    >
      {children}
    </button>
  );
}
