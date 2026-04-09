import { format } from "date-fns";
import { ru } from "date-fns/locale";
import type { Booking, Resource } from "../store";

const CATEGORY_LABELS: Record<string, string> = {
  washing_machine: "Стиральная машина",
  meeting_room: "Переговорная",
  rest_area: "Зона отдыха",
};

const STATUS_COLORS: Record<string, string> = {
  available: "#4caf50",
  maintenance: "#ff9800",
  retired: "#9e9e9e",
};

interface Props {
  resources: Resource[];
  bookings: Booking[];
  onBook: (resource: Resource) => void;
}

export default function ResourceTable({ resources, bookings, onBook }: Props) {
  const now = new Date();

  const isCurrentlyBooked = (resourceId: string) =>
    bookings.some(
      (b) =>
        b.resource_id === resourceId &&
        b.status === "confirmed" &&
        new Date(b.starts_at) <= now &&
        new Date(b.ends_at) > now
    );

  return (
    <div style={{ overflowX: "auto" }}>
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 14 }}>
        <thead>
          <tr style={{ background: "#f5f5f5" }}>
            <th style={th}>Название</th>
            <th style={th}>Категория</th>
            <th style={th}>Расположение</th>
            <th style={th}>Вместимость</th>
            <th style={th}>Статус</th>
            <th style={th}>Сейчас</th>
            <th style={th}>Действие</th>
          </tr>
        </thead>
        <tbody>
          {resources.map((r) => {
            const booked = isCurrentlyBooked(r.id);
            return (
              <tr key={r.id} style={{ borderBottom: "1px solid #eee" }}>
                <td style={td}>{r.name}</td>
                <td style={td}>{CATEGORY_LABELS[r.category] ?? r.category}</td>
                <td style={td}>{r.location}</td>
                <td style={td}>{r.capacity}</td>
                <td style={td}>
                  <span style={{ color: STATUS_COLORS[r.status], fontWeight: 600 }}>
                    {r.status === "available" ? "Доступен" : r.status === "maintenance" ? "Обслуживание" : "Выведен"}
                  </span>
                </td>
                <td style={td}>
                  {r.status !== "available" ? "—" : booked ? (
                    <span style={{ color: "#e53935", fontWeight: 600 }}>🔴 Занято</span>
                  ) : (
                    <span style={{ color: "#43a047", fontWeight: 600 }}>✅ Свободно</span>
                  )}
                </td>
                <td style={td}>
                  {r.status === "available" && !booked && (
                    <button
                      onClick={() => onBook(r)}
                      style={{ background: "#1a73e8", color: "#fff", border: "none", padding: "4px 12px", borderRadius: 4, cursor: "pointer" }}
                    >
                      Забронировать
                    </button>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

const th: React.CSSProperties = { padding: "10px 12px", textAlign: "left", fontWeight: 600 };
const td: React.CSSProperties = { padding: "10px 12px" };
