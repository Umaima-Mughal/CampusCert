import { Component } from "react";

/**
 * Catches a crash in anything below it and shows what went wrong instead of a blank white page.
 * (React unmounts the whole screen when a component throws and nothing catches it.)
 */
export default class ErrorBoundary extends Component {
  state = { error: null };

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, info) {
    console.error("Screen crashed:", error, info?.componentStack);
  }

  render() {
    if (!this.state.error) return this.props.children;
    return (
      <div style={{ maxWidth: 640, margin: "60px auto", padding: 24, color: "#fff", background: "#0b1433",
                    border: "1px solid #ef4444", borderRadius: 12, fontFamily: "system-ui, sans-serif" }}>
        <h2 style={{ marginTop: 0 }}>Something went wrong on this page</h2>
        <p style={{ opacity: 0.85 }}>Your data is safe. Try reloading the page. If it keeps happening, send this message to the developer:</p>
        <pre style={{ whiteSpace: "pre-wrap", background: "rgba(0,0,0,.35)", padding: 12, borderRadius: 8 }}>
          {String(this.state.error?.message || this.state.error)}
        </pre>
        <button type="button" onClick={() => window.location.reload()}
                style={{ padding: "8px 16px", borderRadius: 8, border: 0, cursor: "pointer" }}>
          Reload page
        </button>
      </div>
    );
  }
}
