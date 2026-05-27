import { create } from "zustand";
import type { Menu } from "@/types";

interface MenuState {
  menus: Menu[];
  permissionCodes: string[];

  // Actions
  setMenus: (menus: Menu[]) => void;
  setPermissionCodes: (codes: string[]) => void;
  hasPermission: (code: string) => boolean;
}

export const useMenuStore = create<MenuState>()((set, get) => ({
  menus: [],
  permissionCodes: [],

  setMenus: (menus) => set({ menus }),
  setPermissionCodes: (codes) => set({ permissionCodes: codes }),

  hasPermission: (code: string) => {
    const codes = get().permissionCodes;
    return codes.includes(code);
  },
}));
