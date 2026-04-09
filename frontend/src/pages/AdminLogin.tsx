import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

export default function AdminLogin() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError]       = useState("");
  const [loading, setLoading]   = useState(false);
  const { adminSignIn } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await adminSignIn(username.trim(), password);
      navigate("/admin");
    } catch (err: any) {
      const status = err.response?.status;
      setError(status === 401 ? "Invalid admin credentials." : "Connection error. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={page}>
      <div style={card}>
        <div style={brandRow}>
          <div style={iconWrap}>⚙️</div>
          <div>
            <h1 style={brandTitle}>Admin Portal</h1>
            <p style={brandSub}>Campus Resource Sync — restricted access</p>
          </div>
        </div>

        <div style={divider} />

        <form onSubmit={handleSubmit}>
          <label style={lbl}>Username</label>
          <input
            style={inp}
            value={username}
            onChange={e => setUsername(e.target.value)}
            placeholder="Admin"
            required
            autoComplete="username"
          />

          <label style={lbl}>Password</label>
          <input
            style={inp}
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            required
            autoComplete="current-password"
          />

          {error && <div style={errBox}>{error}</div>}

          <button
            type="submit"
            disabled={loading}
            style={{ ...btn, opacity: loading ? 0.7 : 1 }}
          >
            {loading
              ? <span style={{ display:"inline-block", width:16, height:16, border:"2px solid rgba(255,255,255,0.3)", borderTopColor:"#fff", borderRadius:"50%", animation:"spin 0.6s linear infinite" }} />
              : "Sign In to Admin Portal"
            }
          </button>
        </form>

        <div style={footer}>
          <Link to="/login" style={footerLink}>← Back to student portal</Link>
        </div>
      </div>
    </div>
  );
}

const page: React.CSSProperties = {
  minHeight: "100vh",
  display: "flex", alignItems: "center", justifyContent: "center",
  background: "linear-gradient(145deg, #0f0e1a 0%, #1e1b4b 50%, #1a1035 100%)",
  padding: 24,
};
const card: React.CSSProperties = {
  background: "#1c1a2e",
  borderRadius: 20,
  padding: "36px 36px 28px",
  width: "100%", maxWidth: 400,
  boxShadow: "0 20px 60px rgba(0,0,0,0.5), 0 0 0 1px rgba(99,102,241,0.2)",
  border: "1px solid rgba(99,102,241,0.25)",
};
const brandRow: React.CSSProperties = {
  display: "flex", alignItems: "center", gap: 14, marginBottom: 20,
};
const iconWrap: React.CSSProperties = {
  width: 52, height: 52, borderRadius: 14,
  background: "linear-gradient(135deg, #4f46e5, #7c3aed)",
  display: "flex", alignItems: "center", justifyContent: "center",
  fontSize: 24, flexShrink: 0,
  boxShadow: "0 4px 16px rgba(79,70,229,0.4)",
};
const brandTitle: React.CSSProperties = {
  margin: 0, fontSize: 20, fontWeight: 800, color: "#e0e7ff", letterSpacing: "-0.02em",
};
const brandSub: React.CSSProperties = {
  margin: "3px 0 0", fontSize: 11, color: "#6b7280",
};
const divider: React.CSSProperties = {
  height: 1, background: "rgba(255,255,255,0.07)", marginBottom: 24,
};
const lbl: React.CSSProperties = {
  display: "block", fontSize: 12, fontWeight: 600,
  color: "#9ca3af", marginBottom: 6, textTransform: "uppercase", letterSpacing: "0.06em",
};
const inp: React.CSSProperties = {
  width: "100%", padding: "11px 14px",
  borderRadius: 10, border: "1px solid rgba(255,255,255,0.1)",
  fontSize: 14, color: "#e5e7eb", outline: "none",
  boxSizing: "border-box",
  background: "rgba(255,255,255,0.06)", fontFamily: "inherit",
  marginBottom: 16,
};
const btn: React.CSSProperties = {
  width: "100%", padding: 13, marginTop: 4,
  background: "linear-gradient(135deg, #4f46e5, #7c3aed)",
  color: "#fff", border: "none", borderRadius: 10,
  fontSize: 14, fontWeight: 700, cursor: "pointer",
  display: "flex", alignItems: "center", justifyContent: "center", gap: 8,
  letterSpacing: "0.01em",
};
const errBox: React.CSSProperties = {
  background: "rgba(239,68,68,0.12)", border: "1px solid rgba(239,68,68,0.3)",
  borderRadius: 8, padding: "10px 14px", fontSize: 13, color: "#fca5a5", marginBottom: 14,
};
const footer: React.CSSProperties = {
  textAlign: "center", marginTop: 20,
};
const footerLink: React.CSSProperties = {
  color: "#6b7280", fontSize: 13, textDecoration: "none",
};
