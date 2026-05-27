// 工作台首页
const app = getApp()

Page({
  data: {
    userInfo: null,
  },

  onLoad() {
    this.checkLoginStatus()
  },

  onShow() {
    this.checkLoginStatus()
    const userInfo = wx.getStorageSync('userInfo')
    if (userInfo) {
      this.setData({ userInfo })
    }
  },

  checkLoginStatus() {
    const token = wx.getStorageSync('token')
    const userInfo = wx.getStorageSync('userInfo')
    if (!token || !userInfo) {
      wx.reLaunch({
        url: '/pages/login/index'
      })
    }
  },

  navigateTo(e) {
    const url = e.currentTarget.dataset.url
    wx.navigateTo({ url })
  },

  goToProfile() {
    wx.navigateTo({
      url: '/pages/profile/index'
    })
  },

  createResearch() {
    wx.navigateTo({
      url: '/pages/market/research/create'
    })
  }
})
