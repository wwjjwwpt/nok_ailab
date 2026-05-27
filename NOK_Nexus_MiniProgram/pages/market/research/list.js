// 市场调研列表页
const app = getApp()

Page({
  data: {
    researchList: [],
    stats: {
      total: 0
    },
    searchKeyword: '',
    page: 1,
    pageSize: 10,
    hasMore: true,
    loading: false,
  },

  onLoad() {
    this.loadResearchList()
  },

  onShow() {
    this.loadResearchList()
  },

  onReachBottom() {
    if (this.data.hasMore && !this.data.loading) {
      this.loadMore()
    }
  },

  // 加载调研列表
  async loadResearchList() {
    if (this.data.loading) return

    this.setData({ loading: true })

    try {
      const token = wx.getStorageSync('token')
      const { page, pageSize, searchKeyword } = this.data

      const res = await wx.request({
        url: `${app.globalData.apiBaseUrl}/market-research`,
        method: 'GET',
        data: {
          page,
          page_size: pageSize,
          city: searchKeyword,
          manufacturer: searchKeyword
        },
        header: {
          'Authorization': `Bearer ${token}`
        }
      })

      const { items, total, has_next } = res.data

      this.setData({
        researchList: page === 1 ? items : [...this.data.researchList, ...items],
        stats: { total },
        hasMore: has_next,
        loading: false
      })
    } catch (error) {
      console.error('加载调研列表失败', error)
      this.setData({ loading: false })
      wx.showToast({
        title: '加载失败',
        icon: 'none'
      })
    }
  },

  // 加载更多
  loadMore() {
    this.setData({ page: this.data.page + 1 })
    this.loadResearchList()
  },

  // 搜索输入
  onSearchInput(e) {
    this.setData({ searchKeyword: e.detail.value })
  },

  // 执行搜索
  doSearch() {
    this.setData({ page: 1, researchList: [] })
    this.loadResearchList()
  },

  // 查看详情
  viewDetail(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({
      url: `/pages/market/research/detail?id=${id}`
    })
  },

  // 显示操作菜单
  showActions(e) {
    const id = e.currentTarget.dataset.id
    wx.showActionSheet({
      itemList: ['编辑', '删除'],
      success: (res) => {
        if (res.tapIndex === 0) {
          this.editResearch(id)
        } else if (res.tapIndex === 1) {
          this.deleteResearch(id)
        }
      }
    })
  },

  // 编辑调研
  editResearch(id) {
    wx.navigateTo({
      url: `/pages/market/research/edit?id=${id}`
    })
  },

  // 删除调研
  async deleteResearch(id) {
    wx.showModal({
      title: '确认删除',
      content: '确定要删除这条调研记录吗？',
      success: async (res) => {
        if (res.confirm) {
          try {
            const token = wx.getStorageSync('token')
            await wx.request({
              url: `${app.globalData.apiBaseUrl}/market-research/${id}`,
              method: 'DELETE',
              header: {
                'Authorization': `Bearer ${token}`
              }
            })

            wx.showToast({
              title: '删除成功',
              icon: 'success'
            })

            this.loadResearchList()
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

  // 创建调研
  createResearch() {
    wx.navigateTo({
      url: '/pages/market/research/create'
    })
  },

  // 返回
  goBack() {
    wx.navigateBack()
  }
})
