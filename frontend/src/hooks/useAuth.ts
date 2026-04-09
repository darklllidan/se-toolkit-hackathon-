import { useAuthStore } from "../store";
import * as authApi from "../api/auth";

export function useAuth() {
  const { setAuth, logout, token, user } = useAuthStore();

  const signIn = async (full_name: string, building: number, room_number: string, password: string) => {
    const { data } = await authApi.login(full_name, building, room_number, password);
    const meRes = await authApi.getMe(data.access_token);
    setAuth(data.access_token, meRes.data);
  };

  const signUp = async (
    full_name: string,
    building: number,
    room_number: string,
    password: string,
    ta_code?: string,
  ) => {
    await authApi.register(full_name, building, room_number, password, ta_code);
    await signIn(full_name, building, room_number, password);
  };

  const adminSignIn = async (username: string, password: string) => {
    const { data } = await authApi.adminLogin(username, password);
    const meRes = await authApi.getMe(data.access_token);
    setAuth(data.access_token, meRes.data);
  };

  return { token, user, signIn, signUp, adminSignIn, logout };
}
