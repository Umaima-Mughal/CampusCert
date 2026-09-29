/**
 * src/shared/components/Layout.jsx
 *
 * Full-page wrapper that centers content vertically/horizontally with a
 * consistent background. Used by auth screens now; other members will
 * likely reuse it (or build their own layout) for dashboards later.
 */

export default function Layout({ children }) {
  return (
    <div
      style={{
        minHeight: "100vh",
        width: "100%",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        backgroundColor: "#F3F4F6",
        fontFamily:
          "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
      }}
    >
      {children}
    </div>
  );
}
