"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuthStore } from "@/stores/authStore";
import { useMenuStore } from "@/stores/menuStore";
import { api } from "@/lib/api";
import type { User } from "@/types";

export function useAuth() {
  const router = useRouter();
  const { user, isAuthenticated, loginSuccess, logout: storeLogout } = useAuthStore();
  const { setMenus, setPermissionCodes } = useMenuStore();

  const login = async (username: string, password: string) => {
    try {
      const response = await api.auth.login({ username, password });

      // 后端直接返回 token，没有外层 data 包装
      const tokenData = response.data;
      if (!tokenData || !tokenData.access_token) {
        return { success: false, error: "登录失败，未返回 token" };
      }

      const { access_token, refresh_token } = tokenData;

      localStorage.setItem("access_token", access_token);
      localStorage.setItem("refresh_token", refresh_token);

      // 获取用户信息
      const userResponse = await api.auth.getCurrentUser();
      const userData = (userResponse.data as any);

      // 使用 loginSuccess 同时设置 user 和 token
      if (userData) {
        loginSuccess(userData as User, access_token);
      }

      // 获取菜单和权限
      const menusResponse = await api.menus.tree();
      const menusData = (menusResponse.data as any) || [];
      setMenus(menusData);

      // 从菜单中提取权限码：优先使用 permission 字段，如果没有则使用 code 字段
      const extractPermissionCodes = (menus: any[]): string[] => {
        const codes: string[] = [];
        menus.forEach(menu => {
          // 如果有 permission 字段则使用，否则使用 code 字段
          const code = menu.permission || menu.code;
          if (code) {
            codes.push(code);
          }
          if (menu.children && menu.children.length > 0) {
            codes.push(...extractPermissionCodes(menu.children));
          }
        });
        return codes;
      };
      const permissionCodes = extractPermissionCodes(menusData);
      setPermissionCodes(permissionCodes);

      return { success: true };
    } catch (error: unknown) {
      // 处理 axios 错误 - 使用 any 类型安全访问
      const err = error as any;
      if (err?.response?.data) {
        const errorMsg = err.response.data.detail || err.response.data.message || err.response.data.error || "登录失败";
        return {
          success: false,
          error: errorMsg,
        };
      }
      if (err?.message) {
        return { success: false, error: err.message };
      }
      return { success: false, error: "登录失败，请稍后重试" };
    }
  };

  const logout = async () => {
    try {
      await api.auth.logout();
    } catch (error) {
      console.error("登出失败:", error);
    } finally {
      storeLogout();
      setMenus([]);
      setPermissionCodes([]);
      router.push("/login");
    }
  };

  const checkAuth = async () => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      storeLogout();
      router.push("/login");
      return false;
    }

    try {
      const response = await api.auth.getCurrentUser();
      const userData = (response.data as any);
      if (userData) {
        loginSuccess(userData as User, token);
      }

      // 获取菜单和权限（如果还没有加载）
      const menuStore = useMenuStore.getState();
      if (menuStore.menus.length === 0) {
        const menusResponse = await api.menus.tree();
        const menusData = (menusResponse.data as any) || [];
        setMenus(menusData);

        // 从菜单中提取权限码
        const extractPermissionCodes = (menus: any[]): string[] => {
          const codes: string[] = [];
          menus.forEach(menu => {
            const code = menu.permission || menu.code;
            if (code) {
              codes.push(code);
            }
            if (menu.children && menu.children.length > 0) {
              codes.push(...extractPermissionCodes(menu.children));
            }
          });
          return codes;
        };
        const permissionCodes = extractPermissionCodes(menusData);
        setPermissionCodes(permissionCodes);
      }

      return true;
    } catch (error) {
      // Token 过期，尝试刷新
      const refreshToken = localStorage.getItem("refresh_token");
      if (refreshToken) {
        try {
          const refreshResponse = await api.auth.refreshToken(refreshToken);
          const { access_token } = refreshResponse.data;
          localStorage.setItem("access_token", access_token);

          const userResponse = await api.auth.getCurrentUser();
          const userData = (userResponse.data as any);
          if (userData) {
            loginSuccess(userData as User, access_token);
          }

          // 获取菜单和权限
          const menusResponse = await api.menus.tree();
          const menusData = (menusResponse.data as any) || [];
          setMenus(menusData);

          const extractPermissionCodes = (menus: any[]): string[] => {
            const codes: string[] = [];
            menus.forEach(menu => {
              const code = menu.permission || menu.code;
              if (code) {
                codes.push(code);
              }
              if (menu.children && menu.children.length > 0) {
                codes.push(...extractPermissionCodes(menu.children));
              }
            });
            return codes;
          };
          const permissionCodes = extractPermissionCodes(menusData);
          setPermissionCodes(permissionCodes);

          return true;
        } catch {
          storeLogout();
          router.push("/login");
          return false;
        }
      }
      storeLogout();
      router.push("/login");
      return false;
    }
  };

  const initMenus = async () => {
    try {
      const menusResponse = await api.menus.tree();
      const menusData = (menusResponse.data as any) || [];
      setMenus(menusData);

      // 从菜单中提取权限码
      const extractPermissionCodes = (menus: any[]): string[] => {
        const codes: string[] = [];
        menus.forEach(menu => {
          const code = menu.permission || menu.code;
          if (code) {
            codes.push(code);
          }
          if (menu.children && menu.children.length > 0) {
            codes.push(...extractPermissionCodes(menu.children));
          }
        });
        return codes;
      };
      const permissionCodes = extractPermissionCodes(menusData);
      setPermissionCodes(permissionCodes);
    } catch (error) {
      console.error("获取菜单失败:", error);
    }
  };

  return {
    user,
    isAuthenticated,
    login,
    logout,
    checkAuth,
    initMenus,
  };
}
