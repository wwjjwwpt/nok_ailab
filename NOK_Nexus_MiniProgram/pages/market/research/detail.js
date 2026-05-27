// 调研详情页面
const app = getApp()

Page({
  data: {
    researchId: null,
    research: null,
  },

  onLoad(options) {
    if (options.id) {
      this.setData({ researchId: options.id })
      this.loadDetail(options.id)
    }
  },

  // 加载详情
  async loadDetail(id) {
    try {
      const token = wx.getStorageSync('token')
      const res = await wx.request({
        url: `${app.globalData.apiBaseUrl}/market-research/${id}`,
        method: 'GET',
        header: {
          'Authorization': `Bearer ${token}`
        }
      })

      this.setData({ research: res.data })
    } catch (error) {
      wx.showToast({
        title: '加载失败',
        icon: 'none'
      })
    }
  },

  // 显示操作菜单
  showActions() {
    wx.showActionSheet({
      itemList: ['编辑', '删除'],
      success: (res) => {
        if (res.tapIndex === 0) {
          this.editResearch()
        } else if (res.tapIndex === 1) {
          this.deleteResearch()
        }
      }
    })
  },

  // 编辑调研
  editResearch() {
    wx.navigateTo({
      url: `/pages/market/research/edit?id=${this.data.researchId}`
    })
  },

  // 删除调研
  deleteResearch() {
    wx.showModal({
      title: '确认删除',
      content: '确定要删除这条调研记录吗？',
      success: async (res) => {
        if (res.confirm) {
          try {
            const token = wx.getStorageSync('token')
            await wx.request({
              url: `${app.globalData.apiBaseUrl}/market-research/${this.data.researchId}`,
              method: 'DELETE',
              header: {
                'Authorization': `Bearer ${token}`
              }
            })

            wx.showToast({
              title: '删除成功',
              icon: 'success'
            })

            setTimeout(() => {
              wx.navigateBack()
            }, 1500)
          } catch (error) {
            wx.showToast({
              title: '删除失败',
              icon: 'none'
            })
          }
        }
      }
    })
  },

  // 返回
  goBack() {
    wx.navigateBack()
  }
})
