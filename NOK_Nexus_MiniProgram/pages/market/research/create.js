// 创建调研页面
const app = getApp()

Page({
  data: {
    formData: {
      city: '',
      region: [],
      manufacturer: '',
      product_name: '',
      price: '',
      research_date: '',
      remark: ''
    },
    submitting: false
  },

  // 地区选择变化
  onRegionChange(e) {
    const region = e.detail.value
    const city = region[2] || region[1] || region[0] || ''
    this.setData({
      'formData.city': city,
      'formData.region': region
    })
  },

  // 厂商输入
  onManufacturerInput(e) {
    this.setData({ 'formData.manufacturer': e.detail.value })
  },

  // 商品输入
  onProductNameInput(e) {
    this.setData({ 'formData.product_name': e.detail.value })
  },

  // 价格输入
  onPriceInput(e) {
    this.setData({ 'formData.price': e.detail.value })
  },

  // 备注输入
  onRemarkInput(e) {
    this.setData({ 'formData.remark': e.detail.value })
  },

  // 选择日期
  chooseDate() {
    wx.showDatePicker({
      mode: 'date',
      start: '2020-01-01',
      end: '2030-12-31',
      success: (res) => {
        this.setData({ 'formData.research_date': res.date })
      }
    })
  },

  // 提交表单
  async submitForm() {
    const { formData, submitting } = this.data

    if (submitting) return

    // 验证必填项
    if (!formData.city) {
      wx.showToast({ title: '请输入城市', icon: 'none' })
      return
    }
    if (!formData.manufacturer) {
      wx.showToast({ title: '请输入厂商', icon: 'none' })
      return
    }
    if (!formData.product_name) {
      wx.showToast({ title: '请输入商品', icon: 'none' })
      return
    }
    if (!formData.price) {
      wx.showToast({ title: '请输入价格', icon: 'none' })
      return
    }

    this.setData({ submitting: true })

    try {
      const token = wx.getStorageSync('token')

      // 转换价格为数字
      const submitData = {
        ...formData,
        price: parseFloat(formData.price)
      }

      // 如果日期为空，使用今天
      if (!submitData.research_date) {
        const today = new Date()
        submitData.research_date = today.toISOString().split('T')[0]
      }

      await wx.request({
        url: `${app.globalData.apiBaseUrl}/market-research`,
        method: 'POST',
        data: submitData,
        header: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      wx.showToast({
        title: '创建成功',
        icon: 'success'
      })

      // 返回列表页
      setTimeout(() => {
        wx.navigateBack()
      }, 1500)

    } catch (error) {
      console.error('创建调研失败', error)
      wx.showToast({
        title: error.data?.detail || '创建失败',
        icon: 'none'
      })
    } finally {
      this.setData({ submitting: false })
    }
  },

  // 返回
  goBack() {
    wx.navigateBack()
  }
})
