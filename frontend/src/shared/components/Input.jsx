/**
 * src/shared/components/Input.jsx
 *
 * Reusable labeled input field with built-in error message display.
 * Used by login/register forms, and anything else the team builds later
 * (exam settings forms, question forms, etc.).
 */

export default function Input({
  label,
  type = "text",
  value,
  onChange,
  placeholder = "",
  error = "",
  required = false,
}) {
  return (
    <div style={{ marginBottom: "16px", textAlign: "left" }}>
      {label && (
        <label
          style={{
            display: "block",
            marginBottom: "6px",
            fontSize: "13px",
            fontWeight: 600,
            color: "#374151",
          }}
        >
          {label}
          {required && <span style={{ color: "#DC2626" }}> *</span>}
        </label>
      )}
      <input
        type={type}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        style={{
          width: "100%",
          padding: "10px 12px",
          borderRadius: "8px",
          border: error ? "1px solid #DC2626" : "1px solid #D1D5DB",
          fontSize: "14px",
          boxSizing: "border-box",
        }}
      />
      {error && (
        <p style={{ color: "#DC2626", fontSize: "12px", marginTop: "4px" }}>
          {error}
        </p>
      )}
    </div>
  );
}
