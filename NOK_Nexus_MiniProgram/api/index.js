/**
 * API 接口管理
 */

import request from '../utils/request'

// ==================== 认证相关 ====================

/**
 * 账号密码登录
 */
export function login(data) {
  return request.post('/auth/login', data)
}

/**
 * 微信登录
 */
export function wechatLogin(data) {
  return request.post('/auth/wechat/login', data)
}

/**
 * 微信绑定账号
 */
export function bindWechat(data) {
  return request.post('/auth/wechat/bind', data)
}

/**
 * 发送短信验证码
 */
export function sendSms(data) {
  return request.post('/auth/send-sms', data)
}

/**
 * 获取当前用户信息
 */
export function getCurrentUser() {
  return request.get('/auth/me')
}

/**
 * 退出登录
 */
export function logout() {
  return request.post('/auth/logout')
}

// ==================== 用户管理 ====================

/**
 * 获取用户列表
 */
export function getUserList(params) {
  return request.get('/users', params)
}

/**
 * 创建用户
 */
export function createUser(data) {
  return request.post('/users', data)
}

/**
 * 更新用户
 */
export function updateUser(id, data) {
  return request.put(`/users/${id}`, data)
}

/**
 * 删除用户
 */
export function deleteUser(id) {
  return request.delete(`/users/${id}`)
}

/**
 * 分配角色
 */
export function assignRole(userId, data) {
  return request.post(`/users/${userId}/roles`, data)
}

// ==================== 角色管理 ====================

/**
 * 获取角色列表
 */
export function getRoleList(params) {
  return request.get('/roles', params)
}

/**
 * 创建角色
 */
export function createRole(data) {
  return request.post('/roles', data)
}

/**
 * 更新角色
 */
export function updateRole(id, data) {
  return request.put(`/roles/${id}`, data)
}

/**
 * 删除角色
 */
export function deleteRole(id) {
  return request.delete(`/roles/${id}`)
}

/**
 * 分配权限
 */
export function assignPermissions(roleId, data) {
  return request.post(`/roles/${roleId}/permissions`, data)
}

// ==================== 菜单管理 ====================

/**
 * 获取菜单树
 */
export function getMenuTree() {
  return request.get('/menus/tree')
}

/**
 * 获取所有菜单
 */
export function getAllMenus(params) {
  return request.get('/menus', params)
}

/**
 * 创建菜单
 */
export function createMenu(data) {
  return request.post('/menus', data)
}

/**
 * 更新菜单
 */
export function updateMenu(id, data) {
  return request.put(`/menus/${id}`, data)
}

/**
 * 删除菜单
 */
export function deleteMenu(id) {
  return request.delete(`/menus/${id}`)
}

// ==================== 部门管理 ====================

/**
 * 获取部门列表
 */
export function getDeptList(params) {
  return request.get('/departments', params)
}

/**
 * 创建部门
 */
export function createDept(data) {
  return request.post('/departments', data)
}

/**
 * 更新部门
 */
export function updateDept(id, data) {
  return request.put(`/departments/${id}`, data)
}

/**
 * 删除部门
 */
export function deleteDept(id) {
  return request.delete(`/departments/${id}`)
}

// ==================== 日志管理 ====================

/**
 * 获取登录日志
 */
export function getLoginLogs(params) {
  return request.get('/logs/login', params)
}

/**
 * 获取操作日志
 */
export function getOperationLogs(params) {
  return request.get('/logs/operation', params)
}

export default {
  // 认证
  login,
  wechatLogin,
  bindWechat,
  sendSms,
  getCurrentUser,
  logout,
  // 用户
  getUserList,
  createUser,
  updateUser,
  deleteUser,
  assignRole,
  // 角色
  getRoleList,
  createRole,
  updateRole,
  deleteRole,
  assignPermissions,
  // 菜单
  getMenuTree,
  getAllMenus,
  createMenu,
  updateMenu,
  deleteMenu,
  // 部门
  getDeptList,
  createDept,
  updateDept,
  deleteDept,
  // 日志
  getLoginLogs,
  getOperationLogs
}
