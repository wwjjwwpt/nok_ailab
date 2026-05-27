// 编辑调研页面
const app = getApp()

Page({
  data: {
    researchId: null,
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

  onLoad(options) {
    if (options.id) {
      this.setData({ researchId: options.id })
      this.loadResearchDetail(options.id)
    }
  },

  // 加载调研详情
  async loadResearchDetail(id) {
    try {
      const token = wx.getStorageSync('token')
      const res = await wx.request({
        url: `${app.globalData.apiBaseUrl}/market-research/${id}`,
        method: 'GET',
        header: {
          'Authorization': `Bearer ${token}`
        }
      })

      const data = res.data
      this.setData({
        formData: {
          city: data.city,
          manufacturer: data.manufacturer,
          product_name: data.product_name,
          price: String(data.price),
          research_date: data.research_date,
          remark: data.remark || ''
        }
      })
    } catch (error) {
      wx.showToast({
        title: '加载失败',
        icon: 'none'
      })
    }
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
    const today = new Date()
    const maxDate = new Date()
    maxDate.setFullYear(today.getFullYear() + 1)

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
    const { researchId, formData, submitting } = this.data

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

      const submitData = {
        city: formData.city,
        manufacturer: formData.manufacturer,
        product_name: formData.product_name,
        price: parseFloat(formData.price),
        research_date: formData.research_date,
        remark: formData.remark
      }

      await wx.request({
        url: `${app.globalData.apiBaseUrl}/market-research/${researchId}`,
        method: 'PUT',
        data: submitData,
        header: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      wx.showToast({
        title: '保存成功',
        icon: 'success'
      })

      // 返回列表页
      setTimeout(() => {
        wx.navigateBack()
      }, 1500)

    } catch (error) {
      wx.showToast({
        title: error.data?.detail || '保存失败',
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
