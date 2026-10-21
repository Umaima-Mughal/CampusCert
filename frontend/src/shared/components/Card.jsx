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
        borderRadius: "12px",
        backgroundColor: "#fff",
        boxShadow: "0 1px 3px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.06)",
        boxSizing: "border-box",
      }}
    >
      {children}
    </div>
  );
}
