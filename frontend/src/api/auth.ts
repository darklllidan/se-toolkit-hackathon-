import client from "./client";

export const register = (
  full_name: string,
  building: number,
  room_number: string,
  password: string,
  ta_code?: string,
) =>
  client.post("/auth/register", { full_name, building, room_number, password, ta_code: ta_code || null });

export const login = (full_name: string, building: number, room_number: string, password: string) =>
  client.post<{ access_token: string; refresh_token: string; token_type: string }>(
    "/auth/token",
    { full_name, building, room_number, password }
  );

export const adminLogin = (username: string, password: string) =>
  client.post<{ access_token: string; refresh_token: string; token_type: string }>(
    "/auth/admin/token",
    { username, password }
  );

export const getMe = (token?: string) =>
  client.get<{
    id: string;
    full_name: string;
    building: number | null;
    room_number: string | null;
    is_admin: boolean;
    is_ta: boolean;
    telegram_id: number | null;
  }>("/users/me", token ? { headers: { Authorization: `Bearer ${token}` } } : undefined);

export const generateLinkCode = () =>
  client.post<{ code: string; expires_in_seconds: number }>("/auth/link-telegram");
