// 登录页面
const app = getApp()

Page({
  data: {
    username: '',
    password: '',
    loading: false,
  },

  onLoad() {
    // 检查是否已登录
    this.checkLoginStatus()
  },

  // 检查登录状态
  checkLoginStatus() {
    const token = wx.getStorageSync('token')
    const userInfo = wx.getStorageSync('userInfo')

    if (token && userInfo) {
      // 已登录，直接跳转到首页
      wx.switchTab({
        url: '/pages/dashboard/index'
      })
    }
  },

  // 用户名输入
  onUsernameInput(e) {
    this.setData({
      username: e.detail.value
    })
  },

  // 密码输入
  onPasswordInput(e) {
    this.setData({
      password: e.detail.value
    })
  },

  // 登录处理
  async handleLogin() {
    const { username, password, loading } = this.data

    if (loading) return

    if (!username || !password) {
      wx.showToast({
        title: '请输入用户名和密码',
        icon: 'none'
      })
      return
    }

    this.setData({ loading: true })
    wx.showLoading({ title: '登录中...', mask: true })

    try {
      // 1. 调用登录接口
      const loginRes = await new Promise((resolve, reject) => {
        wx.request({
          url: `${app.globalData.apiBaseUrl}/auth/login`,
          method: 'POST',
          data: { username, password },
          success: resolve,
          fail: reject
        })
      })

      console.log('登录响应 statusCode:', loginRes.statusCode)
      console.log('登录响应 data:', loginRes.data)

      // 检查响应状态
      if (loginRes.statusCode !== 200) {
        throw new Error(loginRes.data?.detail || loginRes.data?.message || '登录失败')
      }

      // FastAPI 返回的数据格式可能是直接的 token 对象
      const data = loginRes.data

      // 尝试多种可能的字段名
      const accessToken = data.access_token || data.accessToken || data.token

      if (!accessToken) {
        console.error('未找到 access_token，完整响应:', data)
        throw new Error('后端返回数据格式错误')
      }

      const refreshToken = data.refresh_token || data.refreshToken || ''

      // 2. 获取用户信息
      const userRes = await new Promise((resolve, reject) => {
        wx.request({
          url: `${app.globalData.apiBaseUrl}/auth/me`,
          method: 'GET',
          header: {
            'Authorization': `Bearer ${accessToken}`
          },
          success: resolve,
          fail: reject
        })
      })

      console.log('用户信息响应:', userRes.data)

      const userInfo = userRes.data

      // 保存登录状态
      wx.setStorageSync('token', accessToken)
      wx.setStorageSync('refreshToken', refreshToken)
      wx.setStorageSync('userInfo', userInfo)
      wx.setStorageSync('loginTime', Date.now())

      app.globalData.token = accessToken
      app.globalData.userInfo = userInfo

      wx.hideLoading()
      wx.showToast({
        title: '登录成功',
        icon: 'success'
      })

      // 跳转到首页
      setTimeout(() => {
        wx.switchTab({
          url: '/pages/dashboard/index'
        })
      }, 1000)

    } catch (error) {
      console.error('登录失败', error)
      wx.hideLoading()

      let errorMsg = '登录失败'

      if (error.errMsg && error.errMsg.includes('fail')) {
        errorMsg = '无法连接后端服务'
      } else if (error.message) {
        errorMsg = error.message
      }

      wx.showToast({
        title: errorMsg,
        icon: 'none'
      })
    } finally {
      this.setData({ loading: false })
    }
  },
})
