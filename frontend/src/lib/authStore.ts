import { create } from "zustand";
import axios from "axios";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

export type UserRole = "government" | "ngo" | "volunteer" | "hospital" | "citizen";

export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  organization_name?: string | null;
  phone?: string | null;
  is_active: boolean;
  is_verified?: boolean;
  created_at?: string;
}

interface AuthState {
  token: string | null;
  user: UserProfile | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => void;
  fetchProfile: () => Promise<UserProfile | null>;
  initAuth: () => Promise<void>;
  setUser: (user: UserProfile | null) => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  token: localStorage.getItem("resqmesh_token"),
  user: null,
  isAuthenticated: Boolean(localStorage.getItem("resqmesh_token")),
  isLoading: true,
  error: null,

  setUser: (user) => set({ user }),

  login: async (email, password) => {
    set({ isLoading: true, error: null });
    try {
      const params = new URLSearchParams();
      params.append("username", email);
      params.append("password", password);

      const response = await axios.post(`${API_BASE_URL}/auth/login`, params, {
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
      });

      const token = response.data?.access_token;
      if (!token) {
        throw new Error("No access token returned from login server.");
      }

      localStorage.setItem("resqmesh_token", token);
      set({ token, isAuthenticated: true });

      // Fetch active user profile
      const profile = await get().fetchProfile();
      set({ isLoading: false });
      return Boolean(profile);
    } catch (err: unknown) {
      let errorMsg = "Login failed. Please check your credentials.";
      if (axios.isAxiosError(err) && err.response) {
        const detail = err.response.data?.detail;
        if (typeof detail === "string") {
          errorMsg = detail;
        } else if (err.response.data?.message) {
          errorMsg = err.response.data.message;
        }
      }
      set({ isLoading: false, error: errorMsg, token: null, isAuthenticated: false, user: null });
      localStorage.removeItem("resqmesh_token");
      return false;
    }
  },

  logout: () => {
    localStorage.removeItem("resqmesh_token");
    set({ token: null, user: null, isAuthenticated: false, isLoading: false, error: null });
  },

  fetchProfile: async () => {
    const token = get().token || localStorage.getItem("resqmesh_token");
    if (!token) {
      set({ user: null, isAuthenticated: false, isLoading: false });
      return null;
    }

    try {
      const res = await axios.get(`${API_BASE_URL}/auth/me`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      const profile: UserProfile = res.data?.data;
      if (profile) {
        set({ user: profile, isAuthenticated: true, isLoading: false, error: null });
        return profile;
      }
    } catch (err: unknown) {
      console.warn("Failed to fetch user profile:", err);
      // If token expired or invalid, clear state
      if (axios.isAxiosError(err) && err.response?.status === 401) {
        get().logout();
        return null;
      }
    }

    set({ isLoading: false });
    return get().user;
  },

  initAuth: async () => {
    const token = localStorage.getItem("resqmesh_token");
    if (token) {
      set({ token, isAuthenticated: true, isLoading: true });
      await get().fetchProfile();
    } else {
      set({ isLoading: false, isAuthenticated: false, user: null });
    }
  },
}));
