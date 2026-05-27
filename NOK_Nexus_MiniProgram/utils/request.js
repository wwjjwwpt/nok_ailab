/**
 * HTTP 请求封装工具
 */

const app = getApp()

/**
 * 基础请求封装
 */
function request(options) {
  return new Promise((resolve, reject) => {
    const token = wx.getStorageSync('token')

    wx.request({
      ...options,
      url: `${app.globalData.apiBaseUrl}${options.url}`,
      header: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : '',
        ...options.header
      },
      success: (res) => {
        // 处理 401 未登录
        if (res.statusCode === 401) {
          clearLoginStatus()
          wx.reLaunch({
            url: '/pages/login/index'
          })
          reject(new Error('登录已过期'))
          return
        }

        // 处理业务错误
        if (res.data && res.data.detail) {
          wx.showToast({
            title: res.data.detail || '请求失败',
            icon: 'none'
          })
          reject(res.data)
          return
        }

        resolve(res.data)
      },
      fail: (err) => {
        wx.showToast({
          title: '网络错误',
          icon: 'none'
        })
        reject(err)
      }
    })
  })
}

// 清除登录状态
function clearLoginStatus() {
  wx.removeStorageSync('token')
  wx.removeStorageSync('refreshToken')
  wx.removeStorageSync('userInfo')
  wx.removeStorageSync('loginTime')
  app.globalData.token = null
  app.globalData.userInfo = null
}

// 快捷方法
const get = (url, data) => request({ url, method: 'GET', data })
const post = (url, data) => request({ url, method: 'POST', data })
const put = (url, data) => request({ url, method: 'PUT', data })
const del = (url, data) => request({ url, method: 'DELETE', data })

export default {
  request,
  get,
  post,
  put,
  delete: del,
  clearLoginStatus
}
