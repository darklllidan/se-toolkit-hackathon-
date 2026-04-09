import { useEffect, useState } from "react";
import { listResources } from "../api/resources";
import { listBookings, cancelBooking } from "../api/bookings";
import { useResourceStore, useBookingStore, useAuthStore } from "../store";
import MyBookings from "../components/MyBookings";
import TimelineView from "../components/TimelineView";
import AssistantPanel from "../components/AssistantPanel";
import { useWebSocket } from "../hooks/useWebSocket";

type Tab = "timeline" | "bookings";

export default function Dashboard() {
  const { setResources }          = useResourceStore();
  const { bookings, setBookings, removeBooking } = useBookingStore();
  const user                      = useAuthStore(s => s.user);
  const [tab, setTab]             = useState<Tab>("timeline");
  const resources                 = useResourceStore(s => s.resources);

  const wsStatus = useWebSocket();

  const loadData = async () => {
    listResources().then(r => setResources(r.data));
    listBookings("confirmed").then(r => setBookings(r.data));
  };

  useEffect(() => { loadData(); }, []);

  const handleCancel = async (id: string) => {
    await cancelBooking(id);
    removeBooking(id);
  };

  const confirmed = bookings.filter(b => b.status === "confirmed");

  return (
    <div style={page}>
      {/* Header */}
      <div style={header}>
        <div>
          <h1 style={title}>
            {user ? `Welcome, ${user.full_name.split(" ")[0]}` : "Dashboard"}
          </h1>
          <p style={subtitle}>Dorm {user?.building ?? "—"}, Room {user?.room_number ?? "—"}</p>
        </div>
        <div style={{ display:"flex", alignItems:"center", gap:10 }}>
          <div style={{
            ...chip,
            background: wsStatus === "live" ? "var(--live-bg)" : "var(--bg-chip)",
            color:      wsStatus === "live" ? "var(--live-text)" : "var(--text-secondary)",
            border:     `1px solid ${wsStatus === "live" ? "var(--live-border)" : "var(--chip-border)"}`,
          }}>
            <span style={{
              width:6, height:6, borderRadius:"50%", flexShrink:0,
              background: wsStatus === "live" ? "var(--live-text)" : "var(--text-muted)",
            }} />
            {wsStatus === "live" ? "Live" : "Connecting"}
          </div>
          <div style={{ ...chip, background:"var(--bg-chip)", color:"var(--chip-text)", border:"1px solid var(--chip-border)" }}>
            🗓️ {confirmed.length} booking{confirmed.length !== 1 ? "s" : ""}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div style={tabBar}>
        <button style={tab==="timeline" ? tabActive : tabInactive} onClick={() => setTab("timeline")}>
          Timeline
        </button>
        <button style={tab==="bookings" ? tabActive : tabInactive} onClick={() => setTab("bookings")}>
          My Bookings {confirmed.length > 0 && <span style={badge}>{confirmed.length}</span>}
        </button>
      </div>

      {/* AI Assistant floating widget */}
      <AssistantPanel onBookingMade={loadData} />

      {/* Content */}
      {tab === "timeline" ? (
        <TimelineView onMyBookingsChange={loadData} />
      ) : (
        <div style={{ padding: "0 0 80px" }}>
          <MyBookings bookings={bookings} resources={resources} onCancel={handleCancel} />
        </div>
      )}
    </div>
  );
}

const page:     React.CSSProperties = { maxWidth:1300, margin:"0 auto", padding:"24px 24px 0" };
const header:   React.CSSProperties = { display:"flex", justifyContent:"space-between", alignItems:"flex-start", marginBottom:20, flexWrap:"wrap", gap:12 };
const title:    React.CSSProperties = { margin:0, fontSize:22, fontWeight:700, color:"var(--text-primary)" };
const subtitle: React.CSSProperties = { margin:"4px 0 0", fontSize:13, color:"var(--text-secondary)" };
const chip:     React.CSSProperties = { display:"flex", alignItems:"center", gap:6, padding:"6px 12px", borderRadius:8, fontSize:12, fontWeight:600 };
const tabBar:   React.CSSProperties = { display:"flex", gap:4, marginBottom:16, borderBottom:"2px solid var(--border)", paddingBottom:0 };
const tabBase:  React.CSSProperties = { padding:"8px 18px", border:"none", background:"none", cursor:"pointer", fontSize:14, fontWeight:600, borderBottom:"2px solid transparent", marginBottom:-2, display:"flex", alignItems:"center", gap:8, color:"var(--tab-inactive)" };
const tabActive:   React.CSSProperties = { ...tabBase, color:"var(--tab-active)", borderBottomColor:"var(--tab-active)" };
const tabInactive: React.CSSProperties = { ...tabBase, color:"var(--tab-inactive)" };
const badge:    React.CSSProperties = { background:"var(--accent)", color:"#fff", borderRadius:20, padding:"1px 7px", fontSize:11 };
