import { useEffect, useRef, useState } from "react";
import { chat, type ChatMessage } from "../api/assistant";
import { useBookingStore } from "../store";

interface Props { onBookingMade?: () => void; }

export default function AssistantPanel({ onBookingMade }: Props) {
  const bumpTimeline = useBookingStore(s => s.bumpTimeline);
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen) bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isOpen]);

  const send = async () => {
    const text = input.trim();
    if (!text || loading) return;
    const updated: ChatMessage[] = [...messages, { role: "user", content: text }];
    setMessages(updated);
    setInput("");
    setLoading(true);
    try {
      const { data } = await chat(updated);
      setMessages([...updated, { role: "assistant", content: data.reply }]);
      bumpTimeline();
      onBookingMade?.();
    } catch {
      setMessages([...updated, { role: "assistant", content: "Something went wrong. Please try again." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {/* Toggle button */}
      <button onClick={() => setIsOpen(v => !v)} style={toggleBtn} title="AI Assistant">
        {isOpen ? "✕" : "✨"}
      </button>

      {isOpen && (
        <div style={panel}>
          {/* Header */}
          <div style={panelHeader}>
            <div style={{ display:"flex", alignItems:"center", gap:10 }}>
              <div style={headerIcon}>✨</div>
              <div>
                <div style={{ fontWeight:700, fontSize:14, color:"#fff" }}>AI Assistant</div>
                <div style={{ fontSize:11, color:"rgba(255,255,255,0.6)" }}>Answers from live DB</div>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              style={{ background:"rgba(255,255,255,0.12)", border:"none", color:"#fff", width:28, height:28, borderRadius:6, cursor:"pointer", fontSize:13, display:"flex", alignItems:"center", justifyContent:"center" }}
            >
              ✕
            </button>
          </div>

          {/* Messages */}
          <div style={msgList}>
            {messages.length === 0 && (
              <div style={{ padding:"8px 4px" }}>
                <p style={{ margin:"0 0 12px", fontWeight:600, fontSize:13, color:"var(--text-primary)" }}>
                  Hi! I can help you book campus resources.
                </p>
                {[
                  "What study rooms are available today?",
                  "Book a washing machine tomorrow at 10:00",
                  "Show my bookings",
                ].map(s => (
                  <button key={s} onClick={() => setInput(s)} style={suggBtn}>{s}</button>
                ))}
              </div>
            )}
            {messages.map((m, i) => (
              <div key={i} style={m.role === "user" ? userBubble : aiBubble}>
                {m.content}
              </div>
            ))}
            {loading && (
              <div style={aiBubble}>
                <span style={{ opacity:0.5 }}>Thinking…</span>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Input */}
          <div style={inputRow}>
            <textarea
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }}
              placeholder="Ask about resources or bookings…"
              rows={1}
              style={textarea}
              disabled={loading}
            />
            <button onClick={send} disabled={!input.trim() || loading} style={sendBtn}>
              ➤
            </button>
          </div>
        </div>
      )}
    </>
  );
}

const toggleBtn: React.CSSProperties = {
  position:"fixed", bottom:24, right:24,
  width:52, height:52, borderRadius:"50%",
  background:"linear-gradient(135deg, #4f46e5, #7c3aed)",
  color:"#fff", border:"none", fontSize:22, cursor:"pointer",
  boxShadow:"0 4px 20px rgba(79,70,229,0.45)",
  zIndex:1100, display:"flex", alignItems:"center", justifyContent:"center",
};

const panel: React.CSSProperties = {
  position:"fixed", bottom:88, right:24,
  width:360, height:500,
  background:"var(--bg-card)",
  borderRadius:16,
  boxShadow:"var(--shadow-modal)",
  zIndex:1099,
  display:"flex", flexDirection:"column", overflow:"hidden",
  border:"1px solid var(--border)",
};

const panelHeader: React.CSSProperties = {
  background:"linear-gradient(135deg, #3730a3, #4f46e5, #7c3aed)",
  color:"#fff", padding:"14px 16px",
  display:"flex", alignItems:"center", justifyContent:"space-between",
  flexShrink:0,
};

const headerIcon: React.CSSProperties = {
  width:34, height:34, borderRadius:8,
  background:"rgba(255,255,255,0.15)",
  display:"flex", alignItems:"center", justifyContent:"center", fontSize:16,
};

const msgList: React.CSSProperties = {
  flex:1, overflowY:"auto", padding:"14px 12px 4px",
  display:"flex", flexDirection:"column", gap:8,
};

const suggBtn: React.CSSProperties = {
  display:"block", width:"100%", textAlign:"left",
  background:"var(--bg-chip)", border:"1px solid var(--chip-border)",
  borderRadius:8, padding:"7px 12px", fontSize:12,
  color:"var(--accent-text)", cursor:"pointer", marginBottom:6, fontWeight:500,
};

const userBubble: React.CSSProperties = {
  alignSelf:"flex-end",
  background:"linear-gradient(135deg, #4f46e5, #7c3aed)",
  color:"#fff", padding:"9px 13px",
  borderRadius:"14px 14px 2px 14px",
  maxWidth:"80%", fontSize:13, lineHeight:1.5, whiteSpace:"pre-wrap",
};

const aiBubble: React.CSSProperties = {
  alignSelf:"flex-start",
  background:"var(--bg-secondary)",
  color:"var(--text-primary)",
  border:"1px solid var(--border)",
  padding:"9px 13px",
  borderRadius:"14px 14px 14px 2px",
  maxWidth:"85%", fontSize:13, lineHeight:1.5, whiteSpace:"pre-wrap",
};

const inputRow: React.CSSProperties = {
  display:"flex", gap:8, padding:"10px 12px 12px",
  borderTop:"1px solid var(--border)", flexShrink:0,
};

const textarea: React.CSSProperties = {
  flex:1, resize:"none",
  border:"1.5px solid var(--border)",
  borderRadius:10, padding:"8px 12px",
  fontSize:13, fontFamily:"inherit", outline:"none",
  background:"var(--bg-input)", color:"var(--text-primary)",
};

const sendBtn: React.CSSProperties = {
  background:"linear-gradient(135deg, #4f46e5, #7c3aed)",
  color:"#fff", border:"none", borderRadius:10,
  width:38, cursor:"pointer", fontSize:16,
  display:"flex", alignItems:"center", justifyContent:"center",
};
