import { useEffect, useState } from "react";
import { format } from "date-fns";
import { listResources } from "../api/resources";
import { updateResourceStatus } from "../api/resources";
import { listAllBookings, cancelBooking, type AdminBooking } from "../api/bookings";
import { useAuthStore } from "../store";
import type { Resource } from "../store";

type Tab = "resources" | "bookings";

export default function AdminDashboard() {
  const user = useAuthStore(s => s.user);
  const [tab, setTab] = useState<Tab>("resources");
  const [resources, setResources] = useState<Resource[]>([]);
  const [bookings, setBookings]   = useState<AdminBooking[]>([]);
  const [loadingId, setLoadingId] = useState<string | null>(null);

  useEffect(() => {
    listResources().then(r => setResources(r.data));
    listAllBookings().then(r => setBookings(r.data));
  }, []);

  const handleToggleStatus = async (r: Resource) => {
    const next = r.status === "available" ? "maintenance" : "available";
    setLoadingId(r.id);
    try {
      const { data } = await updateResourceStatus(r.id, next);
      setResources(prev => prev.map(x => x.id === r.id ? data : x));
    } finally {
      setLoadingId(null);
    }
  };

  const handleCancelBooking = async (id: string) => {
    if (!window.confirm("Cancel this booking?")) return;
    setLoadingId(id);
    try {
      await cancelBooking(id);
      setBookings(prev => prev.filter(b => b.id !== id));
    } finally {
      setLoadingId(null);
    }
  };

  // Group resources by category
  const grouped: Record<string, Resource[]> = {};
  for (const r of resources) {
    if (!grouped[r.category]) grouped[r.category] = [];
    grouped[r.category].push(r);
  }

  const CAT_LABEL: Record<string, string> = {
    study_room: "Study Rooms",
    washing_machine: "Washing Machines",
    dryer: "Dryers",
    meeting_room: "Meeting Rooms",
    rest_area: "Rest Areas",
  };

  return (
    <div style={page}>
      {/* Header */}
      <div style={headerRow}>
        <div>
          <h1 style={title}>Admin Panel</h1>
          <p style={subtitle}>Logged in as {user?.full_name}</p>
        </div>
        <div style={statsRow}>
          <div style={statCard}>
            <span style={statNum}>{resources.length}</span>
            <span style={statLbl}>Resources</span>
          </div>
          <div style={statCard}>
            <span style={statNum}>{resources.filter(r => r.status === "maintenance").length}</span>
            <span style={{ ...statLbl, color: "#f59e0b" }}>Maintenance</span>
          </div>
          <div style={statCard}>
            <span style={statNum}>{bookings.length}</span>
            <span style={statLbl}>Active bookings</span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div style={tabBar}>
        <button style={tab === "resources" ? tabActive : tabInactive} onClick={() => setTab("resources")}>
          Resources
        </button>
        <button style={tab === "bookings" ? tabActive : tabInactive} onClick={() => setTab("bookings")}>
          All Bookings
          {bookings.length > 0 && <span style={badge}>{bookings.length}</span>}
        </button>
      </div>

      {/* Resources tab */}
      {tab === "resources" && (
        <div>
          {Object.entries(grouped).map(([cat, items]) => (
            <div key={cat} style={section}>
              <h3 style={sectionTitle}>{CAT_LABEL[cat] ?? cat}</h3>
              <div style={tableWrap}>
                <table style={table}>
                  <thead>
                    <tr>
                      <th style={th}>Name</th>
                      <th style={th}>Location</th>
                      <th style={th}>Status</th>
                      <th style={th}>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {items.map(r => {
                      const isMaintenance = r.status === "maintenance";
                      return (
                        <tr key={r.id} style={{ background: isMaintenance ? "rgba(245,158,11,0.06)" : undefined }}>
                          <td style={td}>{r.name}</td>
                          <td style={{ ...td, color: "var(--text-secondary)", fontSize: 12 }}>{r.location}</td>
                          <td style={td}>
                            <span style={{
                              display: "inline-block",
                              padding: "3px 10px", borderRadius: 20, fontSize: 11, fontWeight: 700,
                              background: isMaintenance ? "#fef3c7" : "#f0fdf4",
                              color: isMaintenance ? "#92400e" : "#059669",
                              border: `1px solid ${isMaintenance ? "#fde68a" : "#a7f3d0"}`,
                            }}>
                              {isMaintenance ? "Maintenance" : "Available"}
                            </span>
                          </td>
                          <td style={td}>
                            <button
                              onClick={() => handleToggleStatus(r)}
                              disabled={loadingId === r.id}
                              style={{
                                padding: "5px 14px", borderRadius: 7, fontSize: 12, fontWeight: 600,
                                cursor: "pointer", border: "none",
                                background: isMaintenance ? "#4f46e5" : "#f59e0b",
                                color: "#fff",
                                opacity: loadingId === r.id ? 0.5 : 1,
                              }}
                            >
                              {isMaintenance ? "Set Available" : "Set Maintenance"}
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Bookings tab */}
      {tab === "bookings" && (
        <div style={section}>
          {bookings.length === 0 ? (
            <div style={empty}>No active bookings</div>
          ) : (
            <div style={tableWrap}>
              <table style={table}>
                <thead>
                  <tr>
                    <th style={th}>Resource</th>
                    <th style={th}>User</th>
                    <th style={th}>Date</th>
                    <th style={th}>Time</th>
                    <th style={th}>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {bookings.map(b => (
                    <tr key={b.id}>
                      <td style={{ ...td, fontWeight: 600 }}>{b.resource_name}</td>
                      <td style={td}>{b.user_name}</td>
                      <td style={{ ...td, color: "var(--text-secondary)", fontSize: 12 }}>
                        {format(new Date(b.starts_at), "MMM d, yyyy")}
                      </td>
                      <td style={{ ...td, color: "var(--text-secondary)", fontSize: 12 }}>
                        {format(new Date(b.starts_at), "HH:mm")}–{format(new Date(b.ends_at), "HH:mm")}
                      </td>
                      <td style={td}>
                        <button
                          onClick={() => handleCancelBooking(b.id)}
                          disabled={loadingId === b.id}
                          style={{
                            padding: "5px 14px", borderRadius: 7, fontSize: 12, fontWeight: 600,
                            cursor: "pointer", border: "1.5px solid #fca5a5",
                            background: "none", color: "#ef4444",
                            opacity: loadingId === b.id ? 0.5 : 1,
                          }}
                        >
                          Cancel
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

const page: React.CSSProperties = { maxWidth: 1200, margin: "0 auto", padding: "28px 24px" };
const headerRow: React.CSSProperties = { display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 24, flexWrap: "wrap", gap: 16 };
const title: React.CSSProperties = { margin: 0, fontSize: 22, fontWeight: 800, color: "var(--text-primary)" };
const subtitle: React.CSSProperties = { margin: "4px 0 0", fontSize: 13, color: "var(--text-secondary)" };
const statsRow: React.CSSProperties = { display: "flex", gap: 12 };
const statCard: React.CSSProperties = { background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 12, padding: "12px 20px", textAlign: "center", minWidth: 90, boxShadow: "var(--shadow-sm)" };
const statNum: React.CSSProperties = { display: "block", fontSize: 22, fontWeight: 800, color: "var(--accent-text)" };
const statLbl: React.CSSProperties = { display: "block", fontSize: 11, color: "var(--text-muted)", marginTop: 2, fontWeight: 600 };
const tabBar: React.CSSProperties = { display: "flex", gap: 4, marginBottom: 20, borderBottom: "2px solid var(--border)" };
const tabBase: React.CSSProperties = { padding: "8px 20px", border: "none", background: "none", cursor: "pointer", fontSize: 14, fontWeight: 600, borderBottom: "2px solid transparent", marginBottom: -2, display: "flex", alignItems: "center", gap: 8 };
const tabActive: React.CSSProperties = { ...tabBase, color: "var(--tab-active)", borderBottomColor: "var(--tab-active)" };
const tabInactive: React.CSSProperties = { ...tabBase, color: "var(--tab-inactive)" };
const badge: React.CSSProperties = { background: "var(--accent)", color: "#fff", borderRadius: 20, padding: "1px 7px", fontSize: 11 };
const section: React.CSSProperties = { marginBottom: 28 };
const sectionTitle: React.CSSProperties = { margin: "0 0 12px", fontSize: 14, fontWeight: 700, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.06em" };
const tableWrap: React.CSSProperties = { background: "var(--bg-card)", borderRadius: 12, border: "1px solid var(--border)", overflow: "hidden", boxShadow: "var(--shadow-sm)" };
const table: React.CSSProperties = { width: "100%", borderCollapse: "collapse" };
const th: React.CSSProperties = { textAlign: "left", padding: "10px 16px", fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em", background: "var(--bg-secondary)", borderBottom: "1px solid var(--border)" };
const td: React.CSSProperties = { padding: "11px 16px", fontSize: 13, color: "var(--text-primary)", borderBottom: "1px solid var(--border-light)" };
const empty: React.CSSProperties = { padding: "40px 24px", textAlign: "center", color: "var(--text-muted)", fontSize: 14, background: "var(--bg-card)", borderRadius: 12, border: "1px solid var(--border)" };
