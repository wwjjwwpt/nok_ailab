// 个人中心
const app = getApp()

Page({
  data: {
    userInfo: null,
  },

  onLoad() {
    const userInfo = wx.getStorageSync('userInfo')
    if (userInfo) {
      this.setData({ userInfo })
    } else {
      wx.reLaunch({
        url: '/pages/login/index'
      })
    }
  },

  onShow() {
    const userInfo = wx.getStorageSync('userInfo')
    if (userInfo) {
      this.setData({ userInfo })
    }
  },

  // 导航
  navigateTo(e) {
    const url = e.currentTarget.dataset.url
    wx.showToast({
      title: '功能开发中...',
      icon: 'none'
    })
  },

  // 退出登录
  handleLogout() {
    wx.showModal({
      title: '确认退出',
      content: '确定要退出登录吗？',
      success: (res) => {
        if (res.confirm) {
          // 清除本地存储
          wx.removeStorageSync('token')
          wx.removeStorageSync('userInfo')
          wx.removeStorageSync('loginTime')
          app.globalData.token = null
          app.globalData.userInfo = null

          // 跳转到登录页
          wx.reLaunch({
            url: '/pages/login/index'
          })
        }
      }
    })
  }
})
