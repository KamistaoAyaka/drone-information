
"""
默认数据源配置 - 用户可配置的初始数据源网站
这些网站会在每次采集时自动加入，与AI发现的网站一起采集
"""

DEFAULT_SOURCES = [
    {
        'name': '新浪军事无人机',
        'url': 'https://mil.news.sina.com.cn/',
        'type': 'web',
        'region': '国内',
        'selectors': {
            'list': '.item',
            'title': 'h2, .item-title',
            'link': 'a',
            'date': '.item-date',
            'content': '.item-text'
        },
        'keywords': ['无人机', 'UAV', '大疆', 'DJI']
    },
    {
        'name': '搜狐军事',
        'url': 'https://www.sohu.com/',
        'type': 'web',
        'region': '国内',
        'selectors': {
            'list': 'article',
            'title': 'h3, h4',
            'link': 'a',
            'date': 'time, .time',
            'content': '.text'
        },
        'keywords': ['无人机', 'UAV', '大疆']
    },
    {
        'name': '36氪无人机',
        'url': 'https://36kr.com/',
        'type': 'web',
        'region': '国内',
        'selectors': {
            'list': '.article-item',
            'title': '.item-title',
            'link': 'a',
            'date': '.item-date',
            'content': '.item-desc'
        },
        'keywords': ['无人机', '科技', '智能硬件']
    },
    {
        'name': 'UAS Vision',
        'url': 'https://www.uasvision.com/',
        'type': 'web',
        'region': '国外',
        'selectors': {
            'list': 'article, .post',
            'title': 'h2, h3, .title',
            'link': 'a',
            'date': 'time, .date',
            'content': '.content, p'
        },
        'keywords': ['UAV', 'drone', 'unmanned', 'aerial', 'system']
    },
    {
        'name': 'DroneLife',
        'url': 'https://dronelife.com/',
        'type': 'web',
        'region': '国外',
        'selectors': {
            'list': 'article, .post',
            'title': 'h2, h3, .title',
            'link': 'a',
            'date': 'time, .date',
            'content': '.content, p'
        },
        'keywords': ['drone', 'UAV', 'unmanned', 'aerial']
    },
]

def get_default_sources():
    """获取默认数据源列表"""
    return DEFAULT_SOURCES.copy()

def add_default_source(source_dict):
    """添加新的默认数据源"""
    DEFAULT_SOURCES.append(source_dict)

def remove_default_source(source_name):
    """移除默认数据源"""
    global DEFAULT_SOURCES
    DEFAULT_SOURCES = [s for s in DEFAULT_SOURCES if s['name'] != source_name]

def update_default_source(source_name, updates):
    """更新默认数据源"""
    for source in DEFAULT_SOURCES:
        if source['name'] == source_name:
            source.update(updates)
            break
