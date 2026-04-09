import type { Booking, Resource } from "../store";

const CATEGORY_META: Record<string, { label: string; icon: string; color: string }> = {
  washing_machine: { label: "Washing Machine", icon: "🧺", color: "#0ea5e9" },
  meeting_room:    { label: "Meeting Room",    icon: "🗓️", color: "#8b5cf6" },
  rest_area:       { label: "Rest Area",       icon: "🛋️", color: "#10b981" },
};

interface Props {
  resource: Resource;
  bookings: Booking[];
  onBook: (resource: Resource) => void;
}

export default function ResourceCard({ resource, bookings, onBook }: Props) {
  const now = new Date();
  const isOccupied = bookings.some(
    b => b.resource_id === resource.id && b.status === "confirmed" &&
         new Date(b.starts_at) <= now && new Date(b.ends_at) > now
  );

  const meta = CATEGORY_META[resource.category] ?? { label: resource.category, icon: "📦", color: "#6b7280" };
  const unavailable = resource.status !== "available";
  const canBook = !unavailable && !isOccupied;

  const statusLabel = unavailable
    ? resource.status === "maintenance" ? "Maintenance" : "Retired"
    : isOccupied ? "Occupied" : "Available";

  const statusColor = unavailable ? "#9ca3af" : isOccupied ? "#ef4444" : "#10b981";
  const statusBg   = unavailable ? "#f3f4f6" : isOccupied ? "#fef2f2" : "#f0fdf4";

  return (
    <div style={card}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 16 }}>
        <div style={{ ...iconBox, background: meta.color + "18" }}>
          <span style={{ fontSize: 24 }}>{meta.icon}</span>
        </div>
        <span style={{ ...statusBadge, background: statusBg, color: statusColor }}>
          <span style={{ width: 6, height: 6, borderRadius: "50%", background: statusColor, display: "inline-block", marginRight: 5 }} />
          {statusLabel}
        </span>
      </div>

      <div style={{ fontWeight: 700, fontSize: 15, color: "#111827", marginBottom: 4 }}>{resource.name}</div>
      <div style={{ fontSize: 12, color: "#6b7280", marginBottom: 2 }}>{resource.location}</div>
      <div style={{ fontSize: 11, color: "#9ca3af", marginBottom: 16 }}>
        {meta.label} · Capacity {resource.capacity}
      </div>

      <button
        onClick={() => onBook(resource)}
        disabled={!canBook}
        style={canBook ? bookBtn : { ...bookBtn, ...bookBtnDisabled }}
      >
        {canBook ? "Book Now" : statusLabel}
      </button>
    </div>
  );
}

const card: React.CSSProperties = {
  background: "#fff",
  border: "1px solid #f0f0f0",
  borderRadius: 14,
  padding: 20,
  display: "flex",
  flexDirection: "column",
  boxShadow: "0 1px 4px rgba(0,0,0,0.04)",
  transition: "box-shadow 0.15s",
};

const iconBox: React.CSSProperties = {
  width: 48,
  height: 48,
  borderRadius: 12,
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
};

const statusBadge: React.CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  padding: "3px 10px",
  borderRadius: 20,
  fontSize: 11,
  fontWeight: 600,
};

const bookBtn: React.CSSProperties = {
  marginTop: "auto",
  width: "100%",
  padding: "9px 0",
  background: "linear-gradient(135deg, #4f46e5, #7c3aed)",
  color: "#fff",
  border: "none",
  borderRadius: 8,
  cursor: "pointer",
  fontWeight: 600,
  fontSize: 13,
  letterSpacing: "0.01em",
};

const bookBtnDisabled: React.CSSProperties = {
  background: "#f3f4f6",
  color: "#9ca3af",
  cursor: "default",
};
