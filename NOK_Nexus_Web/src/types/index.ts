// API 类型定义

export interface User {
  id: number;
  username: string;
  email?: string;
  phone?: string;
  nickname?: string;
  avatar?: string;
  dept_id?: number;
  status: number;
  email_verified: boolean;
  phone_verified: boolean;
  last_login_time?: string;
  created_at: string;
  updated_at: string;
}

export interface Role {
  id: number;
  name: string;
  code: string;
  description?: string;
  is_system: boolean;
  created_at: string;
  updated_at: string;
}

export interface Menu {
  id: number;
  name: string;
  code: string;
  parent_id: number;
  path?: string;
  component?: string;
  icon?: string;
  type: number;
  sort_order: number;
  visible: boolean;
  permission?: string;
  children?: Menu[];
}

export interface Permission {
  id: number;
  name: string;
  code: string;
  menu_id?: number;
  type: string;
  api_method?: string;
  api_path?: string;
  description?: string;
}

export interface DataScope {
  id: number;
  name: string;
  code: string;
  scope_type: number;
  scope_config?: Record<string, unknown>;
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface Department {
  id: number;
  name: string;
  parent_id: number;
  leader_name?: string;
  phone?: string;
  email?: string;
  sort_order: number;
  full_path?: string;
  created_at: string;
  updated_at: string;
  children?: Department[];
}

export interface LoginRequest {
  username: string;
  password: string;
  verify_code?: string;
}

export interface RegisterRequest {
  username: string;
  password: string;
  email: string;
  phone?: string;
  verify_code: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface ApiResponse<T = unknown> {
  code: number;
  message: string;
  data?: T;
}

export interface PageResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
}
