/**
 * src/shared/components/Card.jsx
 *
 * A simple boxed panel used to wrap forms and content sections
 * consistently across the app (login card, dashboard widgets, etc.).
 */

export default function Card({ children, maxWidth = "400px" }) {
  return (
    <div
      style={{
        maxWidth,
        width: "100%",
        margin: "0 auto",
        padding: "32px",
        borderRadius: "8px",
        backgroundColor: "#fff",
        border: "1px solid #e3e7ec",
        boxShadow: "0 1px 2px rgba(28,36,48,0.04)",
        boxSizing: "border-box",
      }}
    >
      {children}
    </div>
  );
}
