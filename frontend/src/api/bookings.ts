import client from "./client";
import type { Booking } from "../store";

export interface TimelineItem {
  id: string;
  resource_id: string;
  resource_name: string;
  starts_at: string;
  ends_at: string;
  is_mine: boolean;
  user_name: string;
}

export const listBookings = (status?: string) =>
  client.get<Booking[]>("/bookings", { params: status ? { status } : undefined });

export const createBooking = (
  resource_id: string,
  starts_at: string,
  ends_at: string,
  notes?: string
) => client.post<Booking>("/bookings", { resource_id, starts_at, ends_at, notes });

export const cancelBooking = (id: string) => client.delete(`/bookings/${id}`);

export const getTimeline = (date: string) =>
  client.get<TimelineItem[]>(`/bookings/timeline?date=${date}`);

export interface AdminBooking {
  id: string;
  resource_id: string;
  resource_name: string;
  user_name: string;
  starts_at: string;
  ends_at: string;
  status: string;
}

export const listAllBookings = () =>
  client.get<AdminBooking[]>("/bookings/admin/all");
