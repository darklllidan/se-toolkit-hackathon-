import { format } from "date-fns";
import type { Booking, Resource } from "../store";

interface Props {
  bookings: Booking[];
  resources: Resource[];
  onCancel: (id: string) => void;
}

export default function MyBookings({ bookings, resources, onCancel }: Props) {
  const confirmed = bookings
    .filter(b => b.status === "confirmed")
    .sort((a, b) => new Date(a.starts_at).getTime() - new Date(b.starts_at).getTime());

  if (confirmed.length === 0) {
    return (
      <div style={emptyState}>
        <span style={{ fontSize: 36, marginBottom: 8 }}>📋</span>
        <p style={{ margin: 0, color: "var(--text-muted)", fontSize: 14 }}>No upcoming bookings</p>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      {confirmed.map(b => {
        const res = resources.find(r => r.id === b.resource_id);
        const now = new Date();
        const isActive = new Date(b.starts_at) <= now && new Date(b.ends_at) > now;
        const isPast = new Date(b.ends_at) < now;

        return (
          <div key={b.id} style={{ ...row, borderLeft: `3px solid ${isActive ? "#10b981" : "var(--accent)"}` }}>
            <div style={{ width:40, height:40, borderRadius:10, background: isActive ? "#f0fdf4" : "var(--bg-chip)", display:"flex", alignItems:"center", justifyContent:"center", fontSize:18, flexShrink:0 }}>
              {isActive ? "▶️" : "🗓️"}
            </div>
            <div style={{ flex:1, minWidth:0 }}>
              <div style={{ fontWeight:600, fontSize:14, color:"var(--text-primary)", marginBottom:2 }}>
                {res?.name ?? "Unknown resource"}
              </div>
              <div style={{ fontSize:12, color:"var(--text-secondary)" }}>
                {format(new Date(b.starts_at), "MMM d, yyyy")} &nbsp;·&nbsp;
                {format(new Date(b.starts_at), "HH:mm")}–{format(new Date(b.ends_at), "HH:mm")}
              </div>
            </div>
            {isActive && (
              <span style={{ fontSize:11, fontWeight:700, color:"#10b981", background:"#f0fdf4", padding:"3px 10px", borderRadius:20, whiteSpace:"nowrap" }}>
                Active now
              </span>
            )}
            {!isPast && (
              <button
                onClick={() => { if (window.confirm("Cancel this booking?")) onCancel(b.id); }}
                style={cancelBtn}
              >
                Cancel
              </button>
            )}
          </div>
        );
      })}
    </div>
  );
}

const row: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 14,
  background: "var(--bg-card)",
  border: "1px solid var(--border)",
  borderRadius: 12,
  padding: "14px 16px",
  boxShadow: "var(--shadow-sm)",
};

const cancelBtn: React.CSSProperties = {
  background: "none",
  border: "1.5px solid #fca5a5",
  color: "#ef4444",
  padding: "5px 14px",
  borderRadius: 8,
  cursor: "pointer",
  fontSize: 12,
  fontWeight: 600,
  whiteSpace: "nowrap",
};

const emptyState: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
  justifyContent: "center",
  padding: "40px 24px",
  background: "var(--bg-empty)",
  borderRadius: 14,
  border: "1.5px dashed var(--border)",
};
