import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface Resource {
  id: string;
  name: string;
  category: "washing_machine" | "meeting_room" | "rest_area" | "study_room" | "dryer";
  location: string;
  capacity: number;
  status: "available" | "maintenance" | "retired";
}

export interface Booking {
  id: string;
  user_id: string;
  resource_id: string;
  starts_at: string;
  ends_at: string;
  status: "confirmed" | "cancelled" | "completed" | "no_show";
  notes: string | null;
}

export interface WsEvent {
  event: "booking_created" | "booking_cancelled";
  booking_id: string;
  resource_id: string;
  resource_name?: string;
  user_name?: string;
  starts_at?: string;
  ends_at?: string;
  status?: string;
}

interface AuthState {
  token: string | null;
  user: { id: string; full_name: string; building: number | null; room_number: string | null; is_admin: boolean; is_ta: boolean } | null;
  setAuth: (token: string, user: AuthState["user"]) => void;
  logout: () => void;
}

interface ResourceState {
  resources: Resource[];
  setResources: (resources: Resource[]) => void;
}

interface BookingState {
  bookings: Booking[];
  timelineVersion: number;
  setBookings: (bookings: Booking[]) => void;
  applyWsEvent: (event: WsEvent) => void;
  addBooking: (booking: Booking) => void;
  removeBooking: (id: string) => void;
  bumpTimeline: () => void;
}

interface ThemeState {
  theme: "light" | "dark";
  toggleTheme: () => void;
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set) => ({
      theme: "light",
      toggleTheme: () => set((s) => ({ theme: s.theme === "light" ? "dark" : "light" })),
    }),
    { name: "theme" }
  )
);

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      setAuth: (token, user) => set({ token, user }),
      logout: () => set({ token: null, user: null }),
    }),
    { name: "auth" }
  )
);

export const useResourceStore = create<ResourceState>((set) => ({
  resources: [],
  setResources: (resources) => set({ resources }),
}));

export const useBookingStore = create<BookingState>((set) => ({
  bookings: [],
  timelineVersion: 0,
  setBookings: (bookings) => set({ bookings }),
  addBooking: (booking) => set((s) => ({ bookings: [...s.bookings, booking] })),
  bumpTimeline: () => set((s) => ({ timelineVersion: s.timelineVersion + 1 })),
  removeBooking: (id) =>
    set((s) => ({
      bookings: s.bookings.map((b) =>
        b.id === id ? { ...b, status: "cancelled" as const } : b
      ),
    })),
  applyWsEvent: (event) => {
    if (event.event === "booking_created") {
      set((s) => {
        // Deduplicate: if booking already added locally (own booking), don't add again
        if (s.bookings.some((b) => b.id === event.booking_id)) {
          return { timelineVersion: s.timelineVersion + 1 };
        }
        return {
          timelineVersion: s.timelineVersion + 1,
          bookings: [
            ...s.bookings,
            {
              id: event.booking_id,
              resource_id: event.resource_id,
              user_id: "",
              starts_at: event.starts_at!,
              ends_at: event.ends_at!,
              status: "confirmed" as const,
              notes: null,
            },
          ],
        };
      });
    } else if (event.event === "booking_cancelled") {
      set((s) => ({
        timelineVersion: s.timelineVersion + 1,
        // Remove cancelled booking from store entirely
        bookings: s.bookings.filter((b) => b.id !== event.booking_id),
      }));
    }
  },
}));
