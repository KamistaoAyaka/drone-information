/**
 * API服务模块
 * 处理与后端的数据交互
 */

// 云开发环境ID
const CLOUD_ENV = 'YOUR_CLOUD_ENV_ID'

// 数据库集合名称
const COLLECTIONS = {
  ARTICLES: 'articles',
  STATISTICS: 'statistics'
}

/**
 * 获取文章列表
 * @param {object} options 查询选项
 * @returns {Promise} 文章列表
 */
async function getArticles(options = {}) {
  const {
    page = 1,
    pageSize = 20,
    region = '',
    droneType = '',
    days = 30
  } = options

  try {
    const db = wx.cloud.database()
    
    // 构建查询条件
    const query = {}
    
    // 时间范围筛选
    const now = new Date()
    const startDate = new Date(now.getTime() - days * 24 * 60 * 60 * 1000)
    query.publish_date = db.command.gte(startDate.toISOString().split('T')[0])
    
    // 区域筛选
    if (region && region !== 'all') {
      query.region = region
    }
    
    // 类型筛选
    if (droneType && droneType !== 'all') {
      query.drone_type = droneType
    }

    const result = await db.collection(COLLECTIONS.ARTICLES)
      .where(query)
      .orderBy('publish_date', 'desc')
      .orderBy('created_at', 'desc')
      .skip((page - 1) * pageSize)
      .limit(pageSize)
      .get()

    return {
      success: true,
      data: result.data,
      total: result.data.length
    }
  } catch (error) {
    console.error('获取文章列表失败:', error)
    return {
      success: false,
      error: error.message,
      data: []
    }
  }
}

/**
 * 获取文章详情
 * @param {string} articleId 文章ID
 * @returns {Promise} 文章详情
 */
async function getArticleDetail(articleId) {
  try {
    const db = wx.cloud.database()
    
    const result = await db.collection(COLLECTIONS.ARTICLES)
      .doc(articleId)
      .get()

    if (result.data) {
      return {
        success: true,
        data: result.data
      }
    } else {
      return {
        success: false,
        error: '文章不存在'
      }
    }
  } catch (error) {
    console.error('获取文章详情失败:', error)
    return {
      success: false,
      error: error.message
    }
  }
}

/**
 * 获取统计数据
 * @returns {Promise} 统计数据
 */
async function getStatistics() {
  try {
    const db = wx.cloud.database()
    
    // 获取文章总数
    const articlesCount = await db.collection(COLLECTIONS.ARTICLES).count()
    
    // 获取今日新增
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    
    const todayCount = await db.collection(COLLECTIONS.ARTICLES)
      .where({
        created_at: db.command.gte(today.toISOString())
      })
      .count()

    return {
      success: true,
      data: {
        total: articlesCount.total,
        today: todayCount.total
      }
    }
  } catch (error) {
    console.error('获取统计数据失败:', error)
    return {
      success: false,
      error: error.message,
      data: {
        total: 0,
        today: 0
      }
    }
  }
}

/**
 * 搜索文章
 * @param {string} keyword 搜索关键词
 * @param {number} pageSize 返回数量
 * @returns {Promise} 搜索结果
 */
async function searchArticles(keyword, pageSize = 20) {
  try {
    const db = wx.cloud.database()
    
    const result = await db.collection(COLLECTIONS.ARTICLES)
      .where(
        db.command.or(
          {
            title: db.RegExp({
              regexp: '.*' + keyword + '.*',
              option: 'i'
            })
          },
          {
            summary: db.RegExp({
              regexp: '.*' + keyword + '.*',
              option: 'i'
            })
          },
          {
            content: db.RegExp({
              regexp: '.*' + keyword + '.*',
              option: 'i'
            })
          }
        )
      )
      .orderBy('publish_date', 'desc')
      .limit(pageSize)
      .get()

    return {
      success: true,
      data: result.data
    }
  } catch (error) {
    console.error('搜索文章失败:', error)
    return {
      success: false,
      error: error.message,
      data: []
    }
  }
}

/**
 * 同步数据到本地
 * 用于定期更新本地缓存
 */
async function syncDataToLocal() {
  try {
    // 获取最近的文章
    const result = await getArticles({ page: 1, pageSize: 100 })
    
    if (result.success) {
      // 存储到本地存储
      wx.setStorageSync('cachedArticles', result.data)
      wx.setStorageSync('lastSyncTime', new Date().toISOString())
      return {
        success: true,
        count: result.data.length
      }
    }
    
    return result
  } catch (error) {
    console.error('同步数据失败:', error)
    return {
      success: false,
      error: error.message
    }
  }
}

/**
 * 获取缓存的文章数据
 * @returns {Array} 缓存的文章列表
 */
function getCachedArticles() {
  try {
    const cached = wx.getStorageSync('cachedArticles')
    const lastSync = wx.getStorageSync('lastSyncTime')
    
    // 检查缓存是否过期（超过1小时）
    if (lastSync) {
      const lastSyncDate = new Date(lastSync)
      const now = new Date()
      const diff = now - lastSyncDate
      
      if (diff > 60 * 60 * 1000) {
        // 缓存过期，返回空数组
        return []
      }
    }
    
    return cached || []
  } catch (error) {
    console.error('获取缓存失败:', error)
    return []
  }
}

module.exports = {
  getArticles,
  getArticleDetail,
  getStatistics,
  searchArticles,
  syncDataToLocal,
  getCachedArticles,
  COLLECTIONS
}
