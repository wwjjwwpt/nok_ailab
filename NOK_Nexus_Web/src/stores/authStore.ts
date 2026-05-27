import { create } from "zustand";
import type { User } from "@/types";

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  token: string | null;

  // Actions
  setUser: (user: User | null) => void;
  setToken: (token: string | null) => void;
  logout: () => void;
  // 登录时调用来确保状态同步
  loginSuccess: (user: User, token: string) => void;
  // 从 localStorage 恢复状态
  restoreFromStorage: () => void;
}

// 从 localStorage 获取初始状态
const getInitialState = () => {
  if (typeof window === 'undefined') {
    return { user: null, isAuthenticated: false, token: null };
  }
  try {
    const stored = localStorage.getItem('auth-storage');
    if (stored) {
      const parsed = JSON.parse(stored);
      return {
        user: parsed.user || null,
        isAuthenticated: parsed.isAuthenticated || false,
        token: parsed.token || null,
      };
    }
  } catch (e) {
    console.error('Failed to parse auth-storage:', e);
  }
  return { user: null, isAuthenticated: false, token: null };
};

const initialState = getInitialState();

export const useAuthStore = create<AuthState>()((set) => ({
  user: initialState.user,
  isAuthenticated: initialState.isAuthenticated,
  token: initialState.token,

  setUser: (user) => {
    set({ user, isAuthenticated: !!user });
    // 保存到 localStorage
    const state = useAuthStore.getState();
    localStorage.setItem('auth-storage', JSON.stringify({
      user: state.user,
      isAuthenticated: state.isAuthenticated,
      token: state.token,
    }));
  },
  setToken: (token) => {
    if (token) {
      localStorage.setItem("access_token", token);
    }
    set({ token });
    const state = useAuthStore.getState();
    localStorage.setItem('auth-storage', JSON.stringify({
      user: state.user,
      isAuthenticated: state.isAuthenticated,
      token: state.token,
    }));
  },
  logout: () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("auth-storage");
    set({ user: null, isAuthenticated: false, token: null });
  },
  loginSuccess: (user, token) => {
    localStorage.setItem("access_token", token);
    set({ user, isAuthenticated: true, token });
    localStorage.setItem('auth-storage', JSON.stringify({
      user,
      isAuthenticated: true,
      token,
    }));
  },
  restoreFromStorage: () => {
    const stored = localStorage.getItem('auth-storage');
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        set({
          user: parsed.user || null,
          isAuthenticated: parsed.isAuthenticated || false,
          token: parsed.token || null,
        });
      } catch (e) {
        console.error('Failed to restore auth state:', e);
      }
    }
  },
}));
