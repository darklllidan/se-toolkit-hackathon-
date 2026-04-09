import { useEffect, useRef, useState, useCallback } from "react";
import { format, addHours } from "date-fns";
import { useResourceStore, useAuthStore, useThemeStore } from "../store";
import type { Resource } from "../store";
import { getTimeline, type TimelineItem, cancelBooking } from "../api/bookings";
import BookingModal from "./BookingModal";
import { useBookingStore } from "../store";

/* ── constants ──────────────────────────────────────────────────── */
const H_START  = 0;
const H_END    = 24;
const HOURS    = H_END - H_START;
const PX_HOUR  = 96;
const ROW_H    = 42;
const SIDEBAR  = 190;
const HEADER_H = 40;

/* ── helpers ────────────────────────────────────────────────────── */
function parseLoc(location: string) {
  const m = location.match(/Dorm (\d+), Floor (\d+)/);
  return m ? { dorm: +m[1], floor: +m[2] } : null;
}

function todayStr() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,"0")}-${String(d.getDate()).padStart(2,"0")}`;
}

function timeToX(isoStr: string): number {
  const d = new Date(isoStr);
  const h = d.getHours() + d.getMinutes() / 60;
  return (h - H_START) * PX_HOUR;
}

function nowX(): number {
  const now = new Date();
  return (now.getHours() + now.getMinutes() / 60 - H_START) * PX_HOUR;
}

function shortLabel(r: Resource): string {
  if (r.category === "study_room")      return "Study Room";
  if (r.category === "washing_machine") return r.name.endsWith("-2") ? "Washer 2" : "Washer 1";
  if (r.category === "dryer")           return r.name.endsWith("-2") ? "Dryer 2"  : "Dryer 1";
  return r.name;
}

const CAT_COLOR: Record<string, string> = {
  study_room:      "#8b5cf6",
  washing_machine: "#0ea5e9",
  dryer:           "#06b6d4",
  meeting_room:    "#f59e0b",
  rest_area:       "#10b981",
};

/* ── theme tokens ─────────────────────────────────────────────────── */
interface TL {
  wrap:         string;
  controls:     string;
  ctrlText:     string;
  ctrlBorder:   string;
  navBtn:       string;
  navBtnBorder: string;
  dormTab:      string;
  dormTabText:  string;
  legendBg:     string;
  legendText:   string;
  timeAxisBg:   string;
  timeAxisText: string;
  timeAxisBorder: string;
  sidebarBg:    string;
  sidebarText:  string;
  rowBg:        string;
  rowBorder:    string;
  gridLine:     string;
  floorLabelText: string;
  bookingOther: string;
  bookingOtherText: string;
  bookingOtherBorder: string;
  datePick:     string;
  datePickText: string;
  datePickBorder: string;
}

function useThemeTokens(): TL {
  const theme = useThemeStore(s => s.theme);
  const dark = theme === "dark";
  return {
    wrap:          dark ? "#111827"                    : "#f0f4ff",
    controls:      dark ? "#1e1b4b"                    : "#4f46e5",
    ctrlText:      dark ? "#e5e7eb"                    : "#ffffff",
    ctrlBorder:    dark ? "rgba(255,255,255,0.08)"     : "rgba(255,255,255,0.18)",
    navBtn:        dark ? "rgba(255,255,255,0.08)"     : "rgba(255,255,255,0.15)",
    navBtnBorder:  dark ? "rgba(255,255,255,0.15)"     : "rgba(255,255,255,0.30)",
    dormTab:       dark ? "rgba(255,255,255,0.06)"     : "rgba(255,255,255,0.15)",
    dormTabText:   dark ? "#9ca3af"                    : "rgba(255,255,255,0.75)",
    legendBg:      dark ? "#1a1a2e"                    : "#ede9fe",
    legendText:    dark ? "#9ca3af"                    : "#4338ca",
    timeAxisBg:    dark ? "#1e1b4b"                    : "#3730a3",
    timeAxisText:  dark ? "#a5b4fc"                    : "#c7d2fe",
    timeAxisBorder: dark ? "rgba(255,255,255,0.08)"   : "rgba(255,255,255,0.15)",
    sidebarBg:     dark ? "#161b2e"                    : "#312e81",
    sidebarText:   dark ? "#e5e7eb"                    : "#e0e7ff",
    rowBg:         dark ? "#111827"                    : "#eef2ff",
    rowBorder:     dark ? "rgba(255,255,255,0.04)"     : "rgba(67,56,202,0.10)",
    gridLine:      dark ? "rgba(255,255,255,0.04)"     : "rgba(99,102,241,0.10)",
    floorLabelText: dark ? "#6b7280"                   : "#818cf8",
    bookingOther:  dark ? "#374151"                    : "#c7d2fe",
    bookingOtherText: dark ? "#9ca3af"                 : "#3730a3",
    bookingOtherBorder: dark ? "rgba(255,255,255,0.1)" : "rgba(99,102,241,0.25)",
    datePick:      dark ? "rgba(255,255,255,0.08)"     : "rgba(255,255,255,0.15)",
    datePickText:  dark ? "#e5e7eb"                    : "#ffffff",
    datePickBorder: dark ? "rgba(255,255,255,0.15)"    : "rgba(255,255,255,0.30)",
  };
}

/* ── component ───────────────────────────────────────────────────── */
interface Props { onMyBookingsChange?: () => void; }

export default function TimelineView({ onMyBookingsChange }: Props) {
  const resources    = useResourceStore(s => s.resources);
  const authUser     = useAuthStore(s => s.user);
  const { bookings, removeBooking, timelineVersion } = useBookingStore();
  const t            = useThemeTokens();

  const [selectedDorm, setSelectedDorm] = useState(() => authUser?.building ?? 1);
  const [selectedDate, setSelectedDate] = useState(todayStr);
  const [timeline, setTimeline]         = useState<TimelineItem[]>([]);
  const [bookTarget, setBookTarget]     = useState<{ resource: Resource; hour: number } | null>(null);
  const [loadingTimeline, setLoadingTimeline] = useState(false);

  const scrollRef = useRef<HTMLDivElement>(null);
  const isToday   = selectedDate === todayStr();

  const loadTimeline = useCallback(async () => {
    setLoadingTimeline(true);
    try {
      const { data } = await getTimeline(selectedDate);
      setTimeline(data);
    } finally {
      setLoadingTimeline(false);
    }
  }, [selectedDate]);

  useEffect(() => { loadTimeline(); }, [loadTimeline]);

  // Reload timeline when any booking changes via WebSocket
  useEffect(() => { if (timelineVersion > 0) loadTimeline(); }, [timelineVersion]);

  useEffect(() => {
    if (scrollRef.current && isToday) {
      scrollRef.current.scrollLeft = Math.max(0, SIDEBAR + nowX() - 120);
    }
  }, [isToday]);

  const dormResources = resources
    .filter(r => { const p = parseLoc(r.location); return p?.dorm === selectedDorm; })
    .sort((a, b) => {
      const pa = parseLoc(a.location)!; const pb = parseLoc(b.location)!;
      if (pa.floor !== pb.floor) return pa.floor - pb.floor;
      const order = ["study_room","washing_machine","dryer","meeting_room","rest_area"];
      return order.indexOf(a.category) - order.indexOf(b.category);
    });

  const floors = [...new Set(dormResources.map(r => parseLoc(r.location)!.floor))].sort((a,b)=>a-b);

  function handleRowClick(e: React.MouseEvent<HTMLDivElement>, resource: Resource) {
    if (resource.status !== "available") return;
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left; // getBoundingClientRect is viewport-relative, no scrollLeft needed
    const fractHours = x / PX_HOUR + H_START;
    const hour = Math.max(H_START, Math.min(H_END - 1, Math.floor(fractHours)));
    setBookTarget({ resource, hour });
  }

  async function handleCancel(id: string) {
    if (!window.confirm("Cancel this booking?")) return;
    await cancelBooking(id);
    removeBooking(id);
    loadTimeline();
    onMyBookingsChange?.();
  }

  const totalW = HOURS * PX_HOUR;

  return (
    <div style={{ background: t.wrap, borderRadius: 16, overflow: "hidden", border: `1px solid ${t.ctrlBorder}` }}>
      {/* Controls */}
      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", padding:"14px 16px", background: t.controls, borderBottom:`1px solid ${t.ctrlBorder}`, flexWrap:"wrap", gap:10 }}>
        <div style={{ display:"flex", alignItems:"center", gap:10 }}>
          <button onClick={() => { const d = new Date(selectedDate); d.setDate(d.getDate()-1); setSelectedDate(d.toISOString().slice(0,10)); }}
            style={{ background: t.navBtn, border:`1px solid ${t.navBtnBorder}`, color: t.ctrlText, width:32, height:32, borderRadius:6, cursor:"pointer", fontSize:16 }}>
            ‹
          </button>
          <input type="date" value={selectedDate} onChange={e => setSelectedDate(e.target.value)}
            style={{ background: t.datePick, border:`1px solid ${t.datePickBorder}`, color: t.datePickText, padding:"5px 10px", borderRadius:6, fontSize:13, outline:"none" }} />
          <button onClick={() => { const d = new Date(selectedDate); d.setDate(d.getDate()+1); setSelectedDate(d.toISOString().slice(0,10)); }}
            style={{ background: t.navBtn, border:`1px solid ${t.navBtnBorder}`, color: t.ctrlText, width:32, height:32, borderRadius:6, cursor:"pointer", fontSize:16 }}>
            ›
          </button>
          {!isToday && (
            <button onClick={() => setSelectedDate(todayStr())}
              style={{ background:"rgba(255,255,255,0.20)", border:"none", color:"#fff", padding:"5px 12px", borderRadius:6, cursor:"pointer", fontSize:12, fontWeight:600 }}>
              Today
            </button>
          )}
        </div>

        {/* Dorm tabs */}
        <div style={{ display:"flex", gap:4 }}>
          {[1,2,3,4,5,6,7].map(d => (
            <button key={d} onClick={() => setSelectedDorm(d)}
              style={{
                background: selectedDorm===d ? "rgba(255,255,255,0.25)" : t.dormTab,
                border: selectedDorm===d ? "1px solid rgba(255,255,255,0.4)" : `1px solid ${t.navBtnBorder}`,
                color: selectedDorm===d ? "#fff" : t.dormTabText,
                fontWeight: selectedDorm===d ? 700 : 500,
                padding:"5px 12px", borderRadius:6, cursor:"pointer", fontSize:12,
              }}>
              D{d}
            </button>
          ))}
        </div>
      </div>

      {/* Legend */}
      <div style={{ display:"flex", gap:16, padding:"8px 16px", background: t.legendBg, borderBottom:`1px solid ${t.ctrlBorder}`, flexWrap:"wrap" }}>
        {([["study_room","Study Room"],["washing_machine","Washer"],["dryer","Dryer"]] as const)
          .map(([cat,label]) => (
          <div key={cat} style={{ display:"flex", alignItems:"center", gap:5 }}>
            <div style={{ width:10, height:10, borderRadius:2, background:CAT_COLOR[cat] }} />
            <span style={{ fontSize:11, color: t.legendText }}>{label}</span>
          </div>
        ))}
        <div style={{ display:"flex", alignItems:"center", gap:5 }}>
          <div style={{ width:10, height:10, borderRadius:2, background:"#4f46e5" }} />
          <span style={{ fontSize:11, color: t.legendText }}>My booking</span>
        </div>
        <div style={{ display:"flex", alignItems:"center", gap:5 }}>
          <div style={{ width:10, height:10, borderRadius:2, background: t.bookingOther }} />
          <span style={{ fontSize:11, color: t.legendText }}>Taken</span>
        </div>
      </div>

      {/* Timeline grid — single scroll container for both axes */}
      <div ref={scrollRef} style={{ overflow:"auto", maxHeight:600, background: t.rowBg }}>
        {/* Inner wrapper: wide enough for sidebar + full grid */}
        <div style={{ width: SIDEBAR + totalW, minWidth:"100%" }}>

          {/* ── Time axis header row (sticky top) ── */}
          <div style={{ display:"flex", position:"sticky", top:0, zIndex:10 }}>
            {/* Corner cell — sticky both top (via parent) and left */}
            <div style={{ width:SIDEBAR, flexShrink:0, height:HEADER_H, background: t.timeAxisBg, borderBottom:`1px solid ${t.timeAxisBorder}`, borderRight:`1px solid ${t.ctrlBorder}`, position:"sticky", left:0, zIndex:11 }} />
            {/* Time labels */}
            <div style={{ width:totalW, flexShrink:0, height:HEADER_H, background: t.timeAxisBg, borderBottom:`1px solid ${t.timeAxisBorder}`, position:"relative" }}>
              {Array.from({ length: HOURS+1 }, (_,i) => (
                <div key={i} style={{ position:"absolute", left: i * PX_HOUR, top:0, bottom:0, width:1 }}>
                  <span style={{ position:"absolute", bottom:6, left:4, fontSize:11, color: t.timeAxisText, whiteSpace:"nowrap", fontWeight:600 }}>
                    {String(H_START+i).padStart(2,"0")}:00
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* ── Data rows ── */}
          {floors.map(floor => {
            const floorRows = dormResources.filter(r => parseLoc(r.location)!.floor === floor);
            return (
              <div key={floor}>
                {/* Floor label row */}
                <div style={{ display:"flex", height:30, background: t.sidebarBg }}>
                  {/* Sidebar floor label — sticky left */}
                  <div style={{ width:SIDEBAR, flexShrink:0, display:"flex", alignItems:"center", paddingLeft:12, fontSize:10, color: t.floorLabelText, fontWeight:700, textTransform:"uppercase", letterSpacing:"0.08em", borderBottom:`1px solid ${t.rowBorder}`, borderRight:`1px solid ${t.ctrlBorder}`, position:"sticky", left:0, zIndex:4, background: t.sidebarBg }}>
                    Floor {floor}
                  </div>
                  {/* Grid floor separator */}
                  <div style={{ width:totalW, flexShrink:0, borderBottom:`1px solid ${t.rowBorder}` }} />
                </div>

                {/* Resource rows */}
                {floorRows.map(r => {
                  const rowBookings = timeline.filter(b => b.resource_id === r.id);
                  const nx = isToday ? nowX() : -1;
                  return (
                    <div key={r.id} style={{ display:"flex", height:ROW_H }}>
                      {/* Sidebar label — sticky left */}
                      <div style={{ width:SIDEBAR, flexShrink:0, display:"flex", alignItems:"center", gap:6, paddingLeft:12, paddingRight:6, borderBottom:`1px solid ${t.rowBorder}`, borderRight:`1px solid ${t.ctrlBorder}`, borderLeft:`3px solid ${r.status === "maintenance" ? "#ef4444" : (CAT_COLOR[r.category] ?? "#9ca3af")}`, position:"sticky", left:0, zIndex:3, background: r.status === "maintenance" ? "rgba(239,68,68,0.08)" : t.sidebarBg }}>
                        <span style={{ fontSize:12, fontWeight:600, color: r.status === "maintenance" ? "#ef4444" : t.sidebarText, lineHeight:1.2, opacity: r.status === "maintenance" ? 0.7 : 1 }}>{shortLabel(r)}</span>
                        {r.status === "maintenance" && <span style={{ fontSize:10, color:"#ef4444", opacity:0.8 }}>🔒</span>}
                      </div>
                      {/* Grid cell */}
                      <div
                        style={{ width:totalW, flexShrink:0, height:ROW_H, position:"relative", borderBottom:`1px solid ${t.rowBorder}`, cursor: r.status==="available" ? "crosshair" : "not-allowed" }}
                        onClick={e => handleRowClick(e, r)}
                      >
                        {/* Maintenance overlay — hatched pattern */}
                        {r.status === "maintenance" && (
                          <div style={{
                            position:"absolute", inset:0, zIndex:1, pointerEvents:"none",
                            background: `repeating-linear-gradient(-45deg, transparent, transparent 5px, rgba(239,68,68,0.13) 5px, rgba(239,68,68,0.13) 10px)`,
                            backgroundColor: "rgba(239,68,68,0.06)",
                          }} />
                        )}

                        {/* Hour grid lines */}
                        {Array.from({ length: HOURS }, (_,i) => (
                          <div key={i} style={{ position:"absolute", left: i*PX_HOUR, top:0, bottom:0, width:1, background: t.gridLine }} />
                        ))}

                        {/* Current time line per row */}
                        {nx >= 0 && nx <= totalW && (
                          <div style={{ position:"absolute", left:nx, top:0, bottom:0, width:2, background:"#ef4444", zIndex:5, pointerEvents:"none" }} />
                        )}

                        {/* Booking blocks */}
                        {rowBookings.map(b => {
                          const x    = timeToX(b.starts_at);
                          const xEnd = timeToX(b.ends_at);
                          const w    = Math.max(4, xEnd - x);
                          if (x > totalW || xEnd < 0) return null;
                          const mine = b.is_mine;
                          return (
                            <div
                              key={b.id}
                              onClick={e => { e.stopPropagation(); if (mine) handleCancel(b.id); }}
                              title={mine ? `${b.user_name} — click to cancel` : b.user_name}
                              style={{
                                position:"absolute",
                                left: Math.max(0, x),
                                width: w - 2,
                                top: 4, bottom: 4,
                                background: mine ? "#4f46e5" : t.bookingOther,
                                borderRadius: 5,
                                border: mine ? "1px solid #818cf8" : `1px solid ${t.bookingOtherBorder}`,
                                display:"flex", alignItems:"center", paddingLeft:7,
                                overflow:"hidden",
                                cursor: mine ? "pointer" : "default",
                                zIndex: 2,
                              }}
                            >
                              <span style={{ fontSize:11, color: mine ? "#e0e7ff" : t.bookingOtherText, fontWeight:600, whiteSpace:"nowrap", overflow:"hidden", textOverflow:"ellipsis" }}>
                                {b.user_name.split(" ")[0]}
                              </span>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  );
                })}
              </div>
            );
          })}

          {/* Current time label — rendered once, pinned via first visible row */}
          {isToday && (() => {
            const x = nowX();
            return x >= 0 && x <= totalW ? (
              <div style={{ position:"sticky", bottom: 0, height:0, pointerEvents:"none" }}>
                <div style={{ position:"absolute", left: SIDEBAR + x - 20, bottom: 4, background:"#ef4444", borderRadius:4, padding:"1px 5px", fontSize:10, color:"#fff", fontWeight:700, whiteSpace:"nowrap", zIndex:20 }}>
                  {format(new Date(), "HH:mm")}
                </div>
              </div>
            ) : null;
          })()}
        </div>
      </div>

      {/* Booking modal */}
      {bookTarget && (
        <BookingModal
          resource={bookTarget.resource}
          initialDate={selectedDate}
          initialHour={bookTarget.hour}
          onClose={() => setBookTarget(null)}
          onBooked={() => { loadTimeline(); onMyBookingsChange?.(); }}
        />
      )}
    </div>
  );
}
