import client from "./client";
import type { Resource } from "../store";

export const listResources = () => client.get<Resource[]>("/resources");

export const getAvailability = (resourceId: string, date: string) =>
  client.get<{ starts_at: string; ends_at: string; is_available: boolean }[]>(
    `/resources/${resourceId}/availability`,
    { params: { date } }
  );

export const updateResourceStatus = (id: string, status: "available" | "maintenance") =>
  client.patch<Resource>(`/resources/${id}`, { status });
