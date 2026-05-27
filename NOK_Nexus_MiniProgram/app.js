// NOK Nexus 微信小程序
App({
  onLaunch() {
    console.log('NOK Nexus MiniProgram Launch')

    // 检查登录状态
    this.checkLoginStatus()
  },

  // 检查登录状态
  checkLoginStatus() {
    const token = wx.getStorageSync('token')
    const userInfo = wx.getStorageSync('userInfo')

    if (token && userInfo) {
      this.globalData.token = token
      this.globalData.userInfo = userInfo
    }
  },

  // 退出登录
  logout() {
    wx.removeStorageSync('token')
    wx.removeStorageSync('userInfo')
    wx.removeStorageSync('loginTime')
    this.globalData.token = null
    this.globalData.userInfo = null
  },

  globalData: {
    token: null,
    userInfo: null,
    // 后端 API 地址
    // 开发环境：如果使用 Mac，可能需要用局域网 IP
    // apiBaseUrl: 'http://localhost:8000/api/v1'
    apiBaseUrl: 'http://127.0.0.1:8000/api/v1'
    // 或者用你的局域网 IP: 'http://192.168.x.x:8000/api/v1'
    // 生产环境改为：https://your-domain.com/api/v1
  }
})
