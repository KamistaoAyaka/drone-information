// miniprogram/pages/index/index.js
const app = getApp()
const api = require('../../utils/api.js')
const util = require('../../utils/util.js')

Page({
  data: {
    statistics: {
      total: 0,
      today: 0,
      sources: 0
    },
    latestArticles: [],
    isLoading: true,
    refreshTime: ''
  },

  onLoad: function() {
    this.loadData()
  },

  onShow: function() {
    // 每次显示页面时检查是否需要刷新
    const lastSync = wx.getStorageSync('lastSyncTime')
    if (lastSync) {
      this.setData({
        refreshTime: util.getRelativeTime(lastSync)
      })
    }
  },

  onPullDownRefresh: function() {
    this.loadData()
  },

  /**
   * 加载数据
   */
  async loadData() {
    this.setData({ isLoading: true })

    try {
      // 并行加载统计数据和文章列表
      const [statsResult, articlesResult] = await Promise.all([
        api.getStatistics(),
        api.getArticles({ page: 1, pageSize: 10 })
      ])

      if (statsResult.success) {
        this.setData({
          'statistics.total': statsResult.data.total || 0,
          'statistics.today': statsResult.data.today || 0
        })
      }

      if (articlesResult.success) {
        this.setData({
          latestArticles: articlesResult.data || []
        })
        
        // 更新缓存
        wx.setStorageSync('cachedArticles', articlesResult.data)
        wx.setStorageSync('lastSyncTime', new Date().toISOString())
      }
    } catch (error) {
      console.error('加载数据失败:', error)
      util.showError('加载失败，请稍后重试')
      
      // 尝试使用缓存数据
      const cached = api.getCachedArticles()
      if (cached.length > 0) {
        this.setData({
          latestArticles: cached
        })
      }
    } finally {
      this.setData({ isLoading: false })
      wx.stopPullDownRefresh()
    }
  },

  /**
   * 跳转到文章详情
   */
  goToArticle: function(e) {
    const articleId = e.currentTarget.dataset.id
    wx.navigateTo({
      url: '/pages/article/article?id=' + articleId
    })
  },

  /**
   * 跳转到资讯列表
   */
  goToList: function() {
    wx.switchTab({
      url: '/pages/list/list'
    })
  },

  /**
   * 分享到朋友
   */
  onShareAppMessage: function() {
    return {
      title: '🚁 无人机前沿情报系统',
      desc: '实时采集全球无人机行业最新资讯',
      path: '/pages/index/index'
    }
  },

  /**
   * 分享到朋友圈
   */
  onShareTimeline: function() {
    return {
      title: '🚁 无人机前沿情报系统 - 最新资讯',
      query: ''
    }
  }
})
