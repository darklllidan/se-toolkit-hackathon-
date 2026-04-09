import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

const DORM_FLOORS: Record<number, number> = { 1: 4, 2: 4, 3: 4, 4: 4, 5: 5, 6: 13, 7: 13 };

function roomError(dorm: number, room: string): string | null {
  if (!room) return null; // don't show error while empty
  if (!/^\d+$/.test(room)) return "Digits only";
  if (room.length < 3 || room.length > 4) return "3 or 4 digits required";
  const floor = room.length === 3 ? +room[0] : +room.slice(0, 2);
  const max = DORM_FLOORS[dorm] ?? 4;
  if (floor < 1 || floor > max) return `Dorm ${dorm} has floors 1–${max}`;
  return null;
}

export default function Register() {
  const [fullName, setFullName] = useState("");
  const [dorm, setDorm]         = useState(1);
  const [room, setRoom]         = useState("");
  const [password, setPassword] = useState("");
  const [taCode, setTaCode]     = useState("");
  const [submitError, setSubmitError] = useState("");
  const [loading, setLoading]   = useState(false);
  const { signUp } = useAuth();
  const navigate   = useNavigate();

  const maxFloor = DORM_FLOORS[dorm] ?? 4;
  const rErr     = roomError(dorm, room);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (rErr) return;
    setLoading(true);
    setSubmitError("");
    try {
      await signUp(fullName.trim(), dorm, room.trim(), password, taCode.trim() || undefined);
      navigate("/");
    } catch (err: any) {
      const d = err.response?.data?.detail;
      setSubmitError(
        Array.isArray(d) ? d.map((x: any) => x.msg.replace(/^Value error, /, "")).join("; ")
        : typeof d === "string" ? d
        : "Registration failed. Please try again."
      );
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
          <p style={brandSub}>Create your account</p>
        </div>

        <form onSubmit={handleSubmit}>
          {/* Full name */}
          <Field label="Full Name">
            <input
              style={input}
              value={fullName}
              onChange={e => setFullName(e.target.value)}
              placeholder="First Last"
              required
              autoComplete="name"
            />
          </Field>

          {/* Dorm + Room */}
          <div style={{ display: "flex", gap: 12 }}>
            <Field label="Dorm" style={{ flex: "0 0 130px" }}>
              <select
                style={input}
                value={dorm}
                onChange={e => { setDorm(+e.target.value); setRoom(""); }}
                required
              >
                {[1,2,3,4,5,6,7].map(n => (
                  <option key={n} value={n}>Dorm {n}</option>
                ))}
              </select>
            </Field>

            <Field
              label="Room"
              hint={rErr ?? `Floors 1–${maxFloor} (e.g. ${maxFloor < 10 ? "2" : "12"}04)`}
              error={!!rErr && room.length > 0}
              style={{ flex: 1 }}
            >
              <input
                style={{ ...input, borderColor: rErr && room ? "#ef4444" : undefined }}
                value={room}
                onChange={e => setRoom(e.target.value)}
                placeholder={maxFloor < 10 ? "204" : "1204"}
                required
              />
            </Field>
          </div>

          {/* Password */}
          <Field label="Password" hint="Minimum 8 characters">
            <input
              style={input}
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              minLength={8}
              required
              autoComplete="new-password"
            />
          </Field>

          {/* TA Code (optional) */}
          <Field label="TA Code" hint="Leave empty if you're a student">
            <input
              style={input}
              value={taCode}
              onChange={e => setTaCode(e.target.value)}
              placeholder="Optional — for Teaching Assistants"
              autoComplete="off"
            />
          </Field>

          {submitError && <ErrorBox>{submitError}</ErrorBox>}

          <button
            type="submit"
            disabled={loading || (!!rErr && room.length > 0)}
            style={{ ...btn, opacity: loading ? 0.75 : 1 }}
          >
            {loading ? <Spinner /> : "Create Account"}
          </button>
        </form>

        <p style={footer}>
          Already have an account?{" "}
          <Link to="/login" style={footerLink}>Sign in</Link>
        </p>
      </div>
    </div>
  );
}

/* ── small helpers ── */
function Field({ label, hint, error, children, style }: {
  label: string; hint?: string; error?: boolean; children: React.ReactNode; style?: React.CSSProperties;
}) {
  return (
    <div style={{ marginBottom: 16, ...style }}>
      <label style={lbl}>{label}</label>
      {children}
      {hint && <p style={{ margin: "4px 0 0", fontSize: 11, color: error ? "#ef4444" : "#9ca3af" }}>{hint}</p>}
    </div>
  );
}

function ErrorBox({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 8, padding: "10px 14px", fontSize: 13, color: "#dc2626", marginBottom: 14 }}>
      ⚠ {children}
    </div>
  );
}

function Spinner() {
  return <span style={{ display: "inline-block", width: 16, height: 16, border: "2px solid rgba(255,255,255,0.3)", borderTopColor: "#fff", borderRadius: "50%", animation: "spin 0.6s linear infinite" }} />;
}

/* ── styles ── */
const page: React.CSSProperties  = { minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "var(--bg-page)", padding: 24 };
const card: React.CSSProperties  = { background: "var(--bg-card)", borderRadius: 20, padding: "40px 36px", width: "100%", maxWidth: 420, boxShadow: "var(--shadow-md)", border: "1px solid var(--border)" };
const brand: React.CSSProperties = { textAlign: "center", marginBottom: 32 };
const brandTitle: React.CSSProperties = { margin: "8px 0 4px", fontSize: 19, fontWeight: 700, color: "var(--text-primary)" };
const brandSub: React.CSSProperties   = { margin: 0, fontSize: 14, color: "var(--text-secondary)" };
const lbl: React.CSSProperties   = { display: "block", fontSize: 13, fontWeight: 600, color: "var(--text-primary)", marginBottom: 6 };
const input: React.CSSProperties = { width: "100%", padding: "10px 14px", borderRadius: 8, border: "1.5px solid var(--border)", fontSize: 14, color: "var(--text-primary)", outline: "none", boxSizing: "border-box", background: "var(--bg-input)", fontFamily: "inherit" };
const btn: React.CSSProperties   = { width: "100%", padding: 13, background: "linear-gradient(135deg,#4f46e5,#7c3aed)", color: "#fff", border: "none", borderRadius: 10, fontSize: 15, fontWeight: 600, cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", gap: 8, marginTop: 4 };
const footer: React.CSSProperties     = { textAlign: "center", marginTop: 22, fontSize: 14, color: "var(--text-secondary)" };
const footerLink: React.CSSProperties = { color: "var(--accent)", fontWeight: 600, textDecoration: "none" };
