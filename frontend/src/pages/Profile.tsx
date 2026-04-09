import { useAuthStore } from "../store";

export default function Profile() {
  const { user } = useAuthStore();
  if (!user) return null;

  const initials = user.full_name.split(" ").map(w => w[0]).join("").toUpperCase().slice(0, 2);

  const fields: { label: string; value: string }[] = [
    { label: "Full Name", value: user.full_name },
    ...(user.building ? [
      { label: "Dorm", value: `Dorm ${user.building}` },
      { label: "Room", value: user.room_number ?? "—" },
    ] : []),
    { label: "Role", value: user.is_admin ? "Administrator" : "Student" },
  ];

  return (
    <div style={page}>
      <h1 style={title}>Profile</h1>

      {/* Avatar card */}
      <div style={avatarCard}>
        <div style={avatarWrap}>
          <div style={avatar}>{initials}</div>
          <div style={avatarGlow} />
        </div>
        <div>
          <div style={{ fontSize: 22, fontWeight: 800, color: "#fff", letterSpacing: "-0.02em" }}>
            {user.full_name}
          </div>
          {user.building && (
            <div style={{ fontSize: 14, color: "rgba(255,255,255,0.65)", marginTop: 5 }}>
              Dorm {user.building} · Room {user.room_number}
            </div>
          )}
          {user.is_admin && (
            <span style={adminBadge}>Administrator</span>
          )}
        </div>
      </div>

      {/* Details card */}
      <div style={detailCard}>
        <h2 style={cardTitle}>Account Details</h2>
        <div style={grid}>
          {fields.map(f => (
            <div key={f.label} style={fieldRow}>
              <span style={fieldLabel}>{f.label}</span>
              <span style={fieldValue}>{f.value}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

const page: React.CSSProperties = {
  maxWidth: 640, margin: "0 auto", padding: "32px 24px",
};
const title: React.CSSProperties = {
  fontSize: 22, fontWeight: 700, color: "var(--text-primary)", margin: "0 0 20px",
};

/* Avatar card — always dark/gradient regardless of theme */
const avatarCard: React.CSSProperties = {
  background: "linear-gradient(135deg, #3730a3 0%, #4f46e5 50%, #7c3aed 100%)",
  borderRadius: 16,
  padding: "28px 28px",
  marginBottom: 16,
  display: "flex",
  alignItems: "center",
  gap: 24,
  boxShadow: "0 8px 32px rgba(79,70,229,0.35)",
};
const avatarWrap: React.CSSProperties = {
  position: "relative", flexShrink: 0,
};
const avatar: React.CSSProperties = {
  width: 72, height: 72, borderRadius: "50%",
  background: "rgba(255,255,255,0.18)",
  border: "3px solid rgba(255,255,255,0.35)",
  backdropFilter: "blur(8px)",
  color: "#fff", fontSize: 26, fontWeight: 800,
  display: "flex", alignItems: "center", justifyContent: "center",
  position: "relative", zIndex: 1,
};
const avatarGlow: React.CSSProperties = {
  position: "absolute", inset: -4, borderRadius: "50%",
  background: "radial-gradient(circle, rgba(255,255,255,0.25) 0%, transparent 70%)",
};
const adminBadge: React.CSSProperties = {
  display: "inline-block", marginTop: 8,
  padding: "4px 12px", background: "rgba(255,255,255,0.20)",
  border: "1px solid rgba(255,255,255,0.35)",
  color: "#fff", borderRadius: 20, fontSize: 11, fontWeight: 700,
};

/* Details card — theme-aware */
const detailCard: React.CSSProperties = {
  background: "var(--bg-card)",
  borderRadius: 14,
  padding: "22px 24px",
  border: "1px solid var(--border)",
  boxShadow: "var(--shadow-sm)",
};
const cardTitle: React.CSSProperties = {
  margin: "0 0 18px", fontSize: 14, fontWeight: 700,
  color: "var(--text-secondary)", textTransform: "uppercase",
  letterSpacing: "0.06em",
};
const grid: React.CSSProperties = {
  display: "flex", flexDirection: "column", gap: 0,
};
const fieldRow: React.CSSProperties = {
  display: "flex", justifyContent: "space-between", alignItems: "center",
  padding: "13px 0",
  borderBottom: "1px solid var(--border-light)",
};
const fieldLabel: React.CSSProperties = {
  fontSize: 13, color: "var(--text-secondary)", fontWeight: 500,
};
const fieldValue: React.CSSProperties = {
  fontSize: 14, fontWeight: 600,
  background: "var(--bg-chip)",
  padding: "4px 12px", borderRadius: 8,
  border: "1px solid var(--chip-border)",
  color: "var(--accent-text)",
};
