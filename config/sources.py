from typing import Dict, List

SOURCES = [
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
        'name': '极客公园',
        'url': 'https://www.geekpark.net/',
        'type': 'web',
        'region': '国内',
        'selectors': {
            'list': '.news-list li',
            'title': 'h3, .title',
            'link': 'a',
            'date': '.time',
            'content': '.desc'
        },
        'keywords': ['无人机', '科技', '智能']
    },
    {
        'name': 'DroneLife',
        'url': 'https://dronelife.com/',
        'type': 'web',
        'region': '国外',
        'selectors': {
            'list': '.post',
            'title': 'h2, .entry-title',
            'link': 'a',
            'date': '.date, time',
            'content': '.entry-content'
        },
        'keywords': ['drone', 'UAV', 'DJI', 'UAS']
    },
    {
        'name': 'sUAS News',
        'url': 'https://www.suasnews.com/',
        'type': 'web',
        'region': '国外',
        'selectors': {
            'list': 'article',
            'title': 'h2, .entry-title',
            'link': 'a',
            'date': '.published',
            'content': '.entry-content'
        },
        'keywords': ['UAV', 'drone', 'UAS']
    },
    {
        'name': 'Aviation Today',
        'url': 'https://www.aviationtoday.com/',
        'type': 'web',
        'region': '国外',
        'selectors': {
            'list': '.post',
            'title': 'h2',
            'link': 'a',
            'date': '.date',
            'content': '.content'
        },
        'keywords': ['UAV', 'drone', 'aviation']
    },
]

RSS_FEEDS = [
    {
        'name': 'DJI官方新闻',
        'url': 'https://www.dji.com/cn/newsroom/rss.xml',
        'type': 'rss',
        'region': '国内',
    },
    {
        'name': 'DroneLife RSS',
        'url': 'https://dronelife.com/feed/',
        'type': 'rss',
        'region': '国外',
    },
    {
        'name': 'sUAS News RSS',
        'url': 'https://www.suasnews.com/feed/',
        'type': 'rss',
        'region': '国外',
    },
    {
        'name': 'UAS Vision RSS',
        'url': 'https://www.uasvision.com/feed/',
        'type': 'rss',
        'region': '国外',
    },
    {
        'name': 'The Drone Girl RSS',
        'url': 'https://thedronegirl.com/feed/',
        'type': 'rss',
        'region': '国外',
    },
]

API_SOURCES = [
    {
        'name': 'The Drone Girl',
        'url': 'https://thedronegirl.com/wp-json/wp/v2/posts?per_page=20',
        'type': 'api',
        'region': '国外',
    },
]

SEARCH_KEYWORDS = [
    '大疆 Mavic',
    'DJI Air',
    'DJI Mini',
    '无人机 新品',
    '无人机 发布',
    'UAV new release',
    'drone 2024',
    'eVTOL',
    '无人机 物流',
    'drone delivery',
    '固定翼 无人机',
    '四旋翼 无人机',
]

DRONE_COMPANIES = [
    '大疆创新', 'DJI', '大疆',
    '极飞科技', '极飞',
    '亿航智能', '亿航',
    '道通智能', '道通',
    '派诺特', 'Parrot',
    'Skydio',
    'Wing',
    'Amazon Prime Air',
    '3D Robotics',
    'Autel Robotics',
    'ZeroTech', '零度智控',
]
