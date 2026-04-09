import { useEffect, useState } from "react";
import { format, addHours } from "date-fns";
import type { Resource } from "../store";
import { getAvailability } from "../api/resources";
import { createBooking } from "../api/bookings";
import { useBookingStore, useAuthStore } from "../store";

interface Slot { starts_at: string; ends_at: string; is_available: boolean; }

interface Props {
  resource: Resource;
  onClose: () => void;
  onBooked?: () => void;
  initialDate?: string;
  initialHour?: number;
}

export default function BookingModal({ resource, onClose, onBooked, initialDate, initialHour }: Props) {
  const [date, setDate] = useState(initialDate ?? format(new Date(), "yyyy-MM-dd"));
  const [slots, setSlots] = useState<Slot[]>([]);
  const [selected, setSelected] = useState<Slot | null>(null);
  const [duration, setDuration] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const addBooking = useBookingStore(s => s.addBooking);
  const user = useAuthStore(s => s.user);
  const isPrivileged = user?.is_ta || user?.is_admin;
  const durationOptions = isPrivileged ? [1, 2, 3, 4, 6, 8] : [1, 2, 3];

  useEffect(() => {
    getAvailability(resource.id, date).then(r => {
      setSlots(r.data);
      if (initialHour !== undefined) {
        const match = r.data.find(
          (s: Slot) => s.is_available && new Date(s.starts_at).getHours() === initialHour
        );
        setSelected(match ?? null);
      } else {
        setSelected(null);
      }
    });
  }, [resource.id, date]);

  const available = slots.filter(s => s.is_available);

  const handleBook = async () => {
    if (!selected) return;
    setLoading(true); setError("");
    try {
      const ends_at = addHours(new Date(selected.starts_at), duration).toISOString();
      const { data } = await createBooking(resource.id, selected.starts_at, ends_at);
      addBooking(data);
      onBooked?.();
      onClose();
    } catch (e: any) {
      setError(e.response?.data?.detail ?? "Booking failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={overlay} onClick={e => { if (e.target === e.currentTarget) onClose(); }}>
      <div style={modal}>
        {/* Header */}
        <div style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-start", marginBottom:20 }}>
          <div>
            <h2 style={{ margin:0, fontSize:18, fontWeight:700, color:"var(--text-primary)" }}>{resource.name}</h2>
            <p style={{ margin:"4px 0 0", fontSize:13, color:"var(--text-secondary)" }}>{resource.location}</p>
          </div>
          <button onClick={onClose} style={closeBtn}>✕</button>
        </div>

        {/* Date */}
        <label style={lbl}>Date</label>
        <input type="date" value={date} onChange={e => setDate(e.target.value)} style={inp} />

        {/* Slots */}
        <label style={lbl}>Available time slots</label>
        {available.length === 0 ? (
          <div style={{ padding:"14px", background:"var(--bg-empty)", borderRadius:8, textAlign:"center", color:"var(--text-muted)", fontSize:13, marginBottom:16, border:"1px solid var(--border)" }}>
            No slots available for this date
          </div>
        ) : (
          <div style={{ display:"flex", flexWrap:"wrap", gap:8, marginBottom:16 }}>
            {available.map(s => {
              const isSelected = selected?.starts_at === s.starts_at;
              return (
                <button
                  key={s.starts_at}
                  onClick={() => setSelected(s)}
                  style={{
                    padding:"7px 14px",
                    borderRadius:8,
                    border:`1.5px solid ${isSelected ? "var(--accent)" : "var(--border)"}`,
                    background: isSelected ? "var(--accent-light)" : "var(--bg-card)",
                    color: isSelected ? "var(--accent-text)" : "var(--text-primary)",
                    fontWeight: isSelected ? 700 : 500,
                    cursor:"pointer",
                    fontSize:13,
                  }}
                >
                  {format(new Date(s.starts_at), "HH:mm")}
                </button>
              );
            })}
          </div>
        )}

        {/* Duration */}
        <label style={lbl}>Duration {isPrivileged && <span style={{ fontSize:11, color:"var(--text-muted)", fontWeight:400 }}>(TA/Admin — extended options)</span>}</label>
        <div style={{ display:"flex", gap:8, marginBottom:20, flexWrap:"wrap" }}>
          {durationOptions.map(h => (
            <button
              key={h}
              onClick={() => setDuration(h)}
              style={{
                flex:1,
                padding:"8px 0",
                borderRadius:8,
                border:`1.5px solid ${duration === h ? "var(--accent)" : "var(--border)"}`,
                background: duration === h ? "var(--accent-light)" : "var(--bg-card)",
                color: duration === h ? "var(--accent-text)" : "var(--text-primary)",
                fontWeight: duration === h ? 700 : 500,
                cursor:"pointer",
                fontSize:13,
              }}
            >
              {h}h
            </button>
          ))}
        </div>

        {selected && (
          <div style={{ background:"var(--bg-chip)", border:"1px solid var(--chip-border)", borderRadius:10, padding:"10px 14px", marginBottom:16, fontSize:13, color:"var(--chip-text)" }}>
            📅 {format(new Date(selected.starts_at), "MMM d")} &nbsp;
            {format(new Date(selected.starts_at), "HH:mm")} – {format(addHours(new Date(selected.starts_at), duration), "HH:mm")}
          </div>
        )}

        {error && (
          <div style={{ background:"#fef2f2", border:"1px solid #fecaca", borderRadius:8, padding:"10px 14px", fontSize:13, color:"#dc2626", marginBottom:12 }}>
            {error}
          </div>
        )}

        <div style={{ display:"flex", gap:10 }}>
          <button onClick={onClose} style={secondaryBtn}>Cancel</button>
          <button
            onClick={handleBook}
            disabled={!selected || loading}
            style={!selected || loading ? { ...primaryBtn, opacity:0.5, cursor:"default" } : primaryBtn}
          >
            {loading ? "Booking…" : "Confirm Booking"}
          </button>
        </div>
      </div>
    </div>
  );
}

const overlay: React.CSSProperties = { position:"fixed", inset:0, background:"rgba(17,24,39,0.55)", display:"flex", alignItems:"center", justifyContent:"center", zIndex:1000, padding:16, backdropFilter:"blur(3px)" };
const modal: React.CSSProperties = { background:"var(--bg-card)", borderRadius:16, padding:28, width:"100%", maxWidth:480, boxShadow:"var(--shadow-modal)" };
const closeBtn: React.CSSProperties = { background:"var(--bg-secondary)", border:"1px solid var(--border)", width:32, height:32, borderRadius:8, cursor:"pointer", fontSize:14, color:"var(--text-secondary)", display:"flex", alignItems:"center", justifyContent:"center", flexShrink:0 };
const lbl: React.CSSProperties = { display:"block", fontSize:13, fontWeight:600, color:"var(--text-primary)", marginBottom:8 };
const inp: React.CSSProperties = { width:"100%", padding:"9px 12px", borderRadius:8, border:"1.5px solid var(--border)", fontSize:14, marginBottom:16, boxSizing:"border-box", outline:"none", background:"var(--bg-input)", color:"var(--text-primary)" };
const primaryBtn: React.CSSProperties = { flex:1, padding:"11px", background:"linear-gradient(135deg, #4f46e5, #7c3aed)", color:"#fff", border:"none", borderRadius:8, cursor:"pointer", fontWeight:600, fontSize:14 };
const secondaryBtn: React.CSSProperties = { padding:"11px 20px", background:"var(--btn-secondary-bg)", color:"var(--btn-secondary-text)", border:"1px solid var(--border)", borderRadius:8, cursor:"pointer", fontWeight:600, fontSize:14 };
