import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

export default function Login() {
  const [fullName, setFullName] = useState("");
  const [dorm, setDorm]         = useState(1);
  const [room, setRoom]         = useState("");
  const [password, setPassword] = useState("");
  const [error, setError]       = useState("");
  const [loading, setLoading]   = useState(false);
  const { signIn } = useAuth();
  const navigate   = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await signIn(fullName.trim(), dorm, room.trim(), password);
      navigate("/");
    } catch (err: any) {
      const status = err.response?.status;
      if (status === 401 || status === 422) {
        setError("Name, dorm, room or password is incorrect.");
      } else {
        setError("Connection error. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={page}>
      <div style={card}>
        {/* Brand */}
        <div style={brand}>
          <span style={{ fontSize: 36 }}>🏛️</span>
          <h1 style={brandTitle}>Campus Resource Sync</h1>
          <p style={brandSub}>Sign in to your account</p>
        </div>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: 16 }}>
            <label style={lbl}>Full Name</label>
            <input
              style={inp}
              value={fullName}
              onChange={e => setFullName(e.target.value)}
              placeholder="First Last"
              required
              autoComplete="name"
            />
          </div>

          <div style={{ display: "flex", gap: 12, marginBottom: 16 }}>
            <div style={{ flex: "0 0 130px" }}>
              <label style={lbl}>Dorm</label>
              <select style={inp} value={dorm} onChange={e => setDorm(+e.target.value)} required>
                {[1,2,3,4,5,6,7].map(n => (
                  <option key={n} value={n}>Dorm {n}</option>
                ))}
              </select>
            </div>
            <div style={{ flex: 1 }}>
              <label style={lbl}>Room</label>
              <input
                style={inp}
                value={room}
                onChange={e => setRoom(e.target.value)}
                placeholder="e.g. 204"
                required
              />
            </div>
          </div>

          <div style={{ marginBottom: 20 }}>
            <label style={lbl}>Password</label>
            <input
              style={inp}
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
              autoComplete="current-password"
            />
          </div>

          {error && (
            <div style={errBox}>
              ⚠ {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{ ...btn, opacity: loading ? 0.75 : 1 }}
          >
            {loading
              ? <span style={spinner} />
              : "Sign In"}
          </button>
        </form>

        <p style={footer}>
          No account yet?{" "}
          <Link to="/register" style={footerLink}>Register here</Link>
        </p>
      </div>
    </div>
  );
}

const page: React.CSSProperties  = { minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "var(--bg-page)", padding: 24 };
const card: React.CSSProperties  = { background: "var(--bg-card)", borderRadius: 20, padding: "40px 36px", width: "100%", maxWidth: 420, boxShadow: "var(--shadow-md)", border: "1px solid var(--border)" };
const brand: React.CSSProperties = { textAlign: "center", marginBottom: 32 };
const brandTitle: React.CSSProperties = { margin: "8px 0 4px", fontSize: 19, fontWeight: 700, color: "var(--text-primary)" };
const brandSub: React.CSSProperties   = { margin: 0, fontSize: 14, color: "var(--text-secondary)" };
const lbl: React.CSSProperties = { display: "block", fontSize: 13, fontWeight: 600, color: "var(--text-primary)", marginBottom: 6 };
const inp: React.CSSProperties = { width: "100%", padding: "10px 14px", borderRadius: 8, border: "1.5px solid var(--border)", fontSize: 14, color: "var(--text-primary)", outline: "none", boxSizing: "border-box", background: "var(--bg-input)", fontFamily: "inherit" };
const btn: React.CSSProperties = { width: "100%", padding: 13, background: "linear-gradient(135deg,#4f46e5,#7c3aed)", color: "#fff", border: "none", borderRadius: 10, fontSize: 15, fontWeight: 600, cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", gap: 8 };
const errBox: React.CSSProperties     = { background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 8, padding: "10px 14px", fontSize: 13, color: "#dc2626", marginBottom: 14 };
const footer: React.CSSProperties     = { textAlign: "center", marginTop: 22, fontSize: 14, color: "var(--text-secondary)" };
const footerLink: React.CSSProperties = { color: "var(--accent)", fontWeight: 600, textDecoration: "none" };
const spinner: React.CSSProperties    = { display: "inline-block", width: 16, height: 16, border: "2px solid rgba(255,255,255,0.3)", borderTopColor: "#fff", borderRadius: "50%" };
