import axios from "axios";
import type { ApiResponse } from "@/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

// 创建 axios 实例
export const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

// 请求拦截器 - 添加 Token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器 - 处理错误
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response) {
      // 401 未授权，清除 token 并跳转登录
      // 但登录接口 (/auth/login) 的 401 错误不跳转，由调用方处理
      const requestUrl = error.config?.url || '';
      if (error.response.status === 401 && !requestUrl.includes('/auth/login')) {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

// 通用 API 方法
export const api = {
  // 认证相关
  auth: {
    login: (data: { username: string; password: string }) =>
      apiClient.post<{ access_token: string; refresh_token: string; token_type: string; expires_in: number }>("/auth/login", data),
    logout: () => apiClient.post<ApiResponse>("/auth/logout"),
    register: (data: { username: string; password: string; email: string; verify_code: string }) =>
      apiClient.post<ApiResponse>("/auth/register", data),
    refreshToken: (refreshToken: string) =>
      apiClient.post<{ access_token: string; refresh_token: string; token_type: string; expires_in: number }>("/auth/refresh", { refresh_token: refreshToken }),
    getCurrentUser: () => apiClient.get<ApiResponse>("/auth/me"),
    changePassword: (data: { old_password: string; new_password: string }) =>
      apiClient.post<ApiResponse>("/auth/change-password", data),
    sendVerifyCode: (data: { email?: string; phone?: string; type: string }) =>
      apiClient.post<ApiResponse>("/auth/send-verify-code", data),
    verifyCode: (data: { email?: string; phone?: string; code: string; type: string }) =>
      apiClient.post<ApiResponse>("/auth/verify-code", data),
  },

  // 用户管理
  users: {
    list: (params?: { page?: number; page_size?: number; username?: string; dept_id?: number; status?: number }) =>
      apiClient.get("/users", { params }),
    get: (id: number) => apiClient.get(`/users/${id}`),
    create: (data: Record<string, unknown>) => apiClient.post("/users", data),
    update: (id: number, data: Record<string, unknown>) => apiClient.put(`/users/${id}`, data),
    delete: (id: number) => apiClient.delete(`/users/${id}`),
    assignRoles: (userId: number, roleIds: number[]) =>
      apiClient.post(`/users/${userId}/roles`, roleIds),
    getRoles: (userId: number) => apiClient.get(`/users/${userId}/roles`),
  },

  // 角色管理
  roles: {
    list: () => apiClient.get("/roles"),
    get: (id: number) => apiClient.get<ApiResponse>(`/roles/${id}`),
    create: (data: Record<string, unknown>) => apiClient.post<ApiResponse>("/roles", data),
    update: (id: number, data: Record<string, unknown>) => apiClient.put<ApiResponse>(`/roles/${id}`, data),
    delete: (id: number) => apiClient.delete<ApiResponse>(`/roles/${id}`),
    getPermissions: (roleId: number) => apiClient.get<ApiResponse>(`/roles/${roleId}/permissions`),
    assignPermissions: (roleId: number, permissionIds: number[]) =>
      apiClient.post<ApiResponse>(`/roles/${roleId}/permissions`, permissionIds),
  },

  // 菜单管理
  menus: {
    tree: () => apiClient.get("/menus/tree"),
    list: () => apiClient.get<ApiResponse>("/menus"),
    get: (id: number) => apiClient.get<ApiResponse>(`/menus/${id}`),
    create: (data: Record<string, unknown>) => apiClient.post<ApiResponse>("/menus", data),
    update: (id: number, data: Record<string, unknown>) => apiClient.put<ApiResponse>(`/menus/${id}`, data),
    delete: (id: number) => apiClient.delete<ApiResponse>(`/menus/${id}`),
    getPermissions: (menuId: number) => apiClient.get<ApiResponse>(`/menus/${menuId}/permissions`),
    bindPermissions: (menuId: number, permissionIds: number[]) =>
      apiClient.post<ApiResponse>(`/menus/${menuId}/permissions`, permissionIds),
  },

  // 权限管理
  permissions: {
    list: (menuId?: number) => apiClient.get<ApiResponse>("/permissions", { params: { menu_id: menuId } }),
    get: (id: number) => apiClient.get<ApiResponse>(`/permissions/${id}`),
    create: (data: Record<string, unknown>) => apiClient.post<ApiResponse>("/permissions", data),
    update: (id: number, data: Record<string, unknown>) => apiClient.put<ApiResponse>(`/permissions/${id}`, data),
    delete: (id: number) => apiClient.delete<ApiResponse>(`/permissions/${id}`),
  },

  // 部门管理
  departments: {
    tree: () => apiClient.get<ApiResponse>("/departments/tree"),
    list: () => apiClient.get<ApiResponse>("/departments"),
    create: (data: Record<string, unknown>) => apiClient.post<ApiResponse>("/departments", data),
    update: (id: number, data: Record<string, unknown>) => apiClient.put<ApiResponse>(`/departments/${id}`, data),
    delete: (id: number) => apiClient.delete<ApiResponse>(`/departments/${id}`),
  },

  // 日志管理
  logs: {
    login: (params?: { page?: number; page_size?: number; username?: string; status?: string }) =>
      apiClient.get<ApiResponse>("/logs/login", { params }),
    operation: (params?: { page?: number; page_size?: number; username?: string; module?: string; status?: string }) =>
      apiClient.get<ApiResponse>("/logs/operation", { params }),
  },

  // 市场调研
  marketResearch: {
    list: (params?: { page?: number; page_size?: number; city?: string; manufacturer?: string; product_name?: string }) =>
      apiClient.get<ApiResponse>("/market-research", { params }),
    get: (id: number) => apiClient.get<ApiResponse>(`/market-research/${id}`),
    create: (data: Record<string, unknown>) => apiClient.post<ApiResponse>("/market-research", data),
    update: (id: number, data: Record<string, unknown>) => apiClient.put<ApiResponse>(`/market-research/${id}`, data),
    delete: (id: number) => apiClient.delete<ApiResponse>(`/market-research/${id}`),
  },
};
