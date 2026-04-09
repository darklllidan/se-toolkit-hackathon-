import { useEffect, useRef, useState } from "react";
import { useAuthStore, useBookingStore } from "../store";

export function useWebSocket() {
  const token = useAuthStore((s) => s.token);
  const applyWsEvent = useBookingStore((s) => s.applyWsEvent);
  const wsRef = useRef<WebSocket | null>(null);
  const [status, setStatus] = useState<"connecting" | "live" | "disconnected">("connecting");

  useEffect(() => {
    if (!token) return;

    let reconnectTimeout: ReturnType<typeof setTimeout>;
    let unmounted = false;

    const connect = () => {
      if (unmounted) return;
      setStatus("connecting");
      const protocol = location.protocol === "https:" ? "wss" : "ws";
      const ws = new WebSocket(`${protocol}://${location.host}/ws/dashboard?token=${token}`);

      ws.onopen = () => {
        if (!unmounted) setStatus("live");
      };

      ws.onmessage = (e) => {
        try {
          applyWsEvent(JSON.parse(e.data));
        } catch {
          // ignore malformed messages
        }
      };

      ws.onclose = (e) => {
        if (unmounted) return;
        setStatus("disconnected");
        // code 4001 = auth rejected — back off longer to avoid spam
        const delay = e.code === 4001 ? 30000 : 3000;
        reconnectTimeout = setTimeout(connect, delay);
      };

      wsRef.current = ws;
    };

    connect();

    return () => {
      unmounted = true;
      clearTimeout(reconnectTimeout);
      wsRef.current?.close();
    };
  }, [token, applyWsEvent]);

  return status;
}
