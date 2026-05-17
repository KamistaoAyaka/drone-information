"""
静态网站生成器
将数据库中的无人机资讯生成为静态HTML页面
"""
import os
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json


def get_timestamp_comment() -> str:
    """生成时间戳注释，确保每次生成的文件内容不同，Git能检测到变更"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return f"\n<!-- Generated at: {timestamp} -->\n"

class StaticSiteGenerator:
    def __init__(self, db_path: str = "data/drone_scout.db", output_dir: str = "static_site"):
        self.db_path = db_path
        self.output_dir = output_dir
        self.articles_per_page = 20
        
    def _apply_translation(self, article: Dict) -> Dict:
        """如果存在翻译内容，优先使用翻译后的字段"""
        if article.get('title_translated'):
            article['title'] = article['title_translated']
        if article.get('summary_translated'):
            article['summary'] = article['summary_translated']
        if article.get('content_translated'):
            article['content'] = article['content_translated']
        return article

    def _get_articles(self, limit: int = 100, days: int = 30) -> List[Dict]:
        """获取最近的资讯"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        cursor.execute("""
            SELECT * FROM articles 
            WHERE publish_date >= ? 
            ORDER BY publish_date DESC, created_at DESC
            LIMIT ?
        """, (start_date, limit))
        
        articles = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        articles = [self._apply_translation(a) for a in articles]
        
        return articles
    
    def _get_article_by_id(self, article_id: str) -> Optional[Dict]:
        """根据ID获取文章"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM articles WHERE id = ?", (article_id,))
        row = cursor.fetchone()
        article = dict(row) if row else None
        conn.close()
        
        if article:
            article = self._apply_translation(article)
        
        return article
    
    def _ensure_output_dir(self):
        """确保输出目录存在"""
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "articles"), exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "assets", "css"), exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "assets", "js"), exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "assets", "images"), exist_ok=True)
    
    def generate_base_templates(self):
        """生成基础模板文件"""
        self._ensure_output_dir()
        
        # 生成CSS
        css_content = """
/* 基础样式 */
:root {
    --primary: #0a192f;
    --secondary: #172a45;
    --accent: #64ffda;
    --text: #e6f1ff;
    --text-muted: #8892b0;
    --card-bg: #112240;
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
    background: var(--primary);
    color: var(--text);
    line-height: 1.6;
    min-height: 100vh;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

/* 头部样式 */
header {
    background: var(--secondary);
    padding: 40px 20px;
    text-align: center;
    border-bottom: 2px solid var(--accent);
}

header h1 {
    color: var(--accent);
    font-size: 2.5rem;
    margin-bottom: 10px;
}

header .subtitle {
    color: var(--text-muted);
    font-size: 1.1rem;
}

/* 导航栏 */
nav {
    background: var(--secondary);
    padding: 15px 20px;
    display: flex;
    justify-content: center;
    gap: 30px;
    flex-wrap: wrap;
}

nav a {
    color: var(--text);
    text-decoration: none;
    padding: 8px 16px;
    border-radius: 5px;
    transition: all 0.3s;
}

nav a:hover {
    background: var(--accent);
    color: var(--primary);
}

/* 统计栏 */
.stats-bar {
    display: flex;
    justify-content: center;
    gap: 40px;
    padding: 30px 20px;
    background: var(--secondary);
    margin-bottom: 30px;
    flex-wrap: wrap;
}

.stat-item {
    text-align: center;
}

.stat-number {
    font-size: 2rem;
    font-weight: bold;
    color: var(--accent);
}

.stat-label {
    color: var(--text-muted);
    font-size: 0.9rem;
}

/* 文章列表 */
.articles-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
    gap: 20px;
    padding: 20px 0;
}

.article-card {
    background: var(--card-bg);
    border-radius: 8px;
    padding: 20px;
    transition: transform 0.3s, box-shadow 0.3s;
    cursor: pointer;
}

.article-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 10px 30px rgba(100, 255, 218, 0.1);
}

.article-meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
    font-size: 0.9rem;
    color: var(--text-muted);
}

.article-meta .source {
    color: var(--accent);
}

.article-card h2 {
    font-size: 1.3rem;
    margin-bottom: 10px;
    color: var(--text);
    line-height: 1.4;
}

.article-card .summary {
    color: var(--text-muted);
    font-size: 0.95rem;
    line-height: 1.6;
}

.article-card .tags {
    display: flex;
    gap: 8px;
    margin-top: 15px;
    flex-wrap: wrap;
}

.tag {
    background: var(--secondary);
    color: var(--accent);
    padding: 4px 12px;
    border-radius: 15px;
    font-size: 0.85rem;
}

.read-more {
    display: inline-block;
    margin-top: 15px;
    color: var(--accent);
    text-decoration: none;
    font-weight: 500;
}

/* 文章详情页 */
.article-detail {
    max-width: 900px;
    margin: 0 auto;
    padding: 40px 20px;
}

.article-detail header {
    text-align: left;
    background: none;
    padding: 0 0 30px 0;
    border-bottom: 1px solid var(--secondary);
    margin-bottom: 30px;
}

.article-detail h1 {
    font-size: 2.2rem;
    margin-bottom: 20px;
    line-height: 1.4;
}

.article-detail .meta {
    display: flex;
    gap: 20px;
    color: var(--text-muted);
    font-size: 0.95rem;
    flex-wrap: wrap;
}

.article-detail .meta span {
    display: flex;
    align-items: center;
    gap: 5px;
}

.article-detail .content {
    background: var(--card-bg);
    padding: 40px;
    border-radius: 8px;
    font-size: 1.1rem;
    line-height: 1.8;
    white-space: pre-wrap;
}

.article-detail .content img {
    max-width: 100%;
    height: auto;
    border-radius: 8px;
    margin: 20px 0;
}

.article-detail .back-link {
    display: inline-block;
    margin-top: 30px;
    color: var(--accent);
    text-decoration: none;
}

/* 分页 */
.pagination {
    display: flex;
    justify-content: center;
    gap: 10px;
    margin: 40px 0;
}

.pagination a, .pagination span {
    padding: 10px 20px;
    background: var(--card-bg);
    color: var(--text);
    text-decoration: none;
    border-radius: 5px;
    transition: all 0.3s;
}

.pagination a:hover {
    background: var(--accent);
    color: var(--primary);
}

.pagination .current {
    background: var(--accent);
    color: var(--primary);
}

/* 页脚 */
footer {
    text-align: center;
    padding: 40px 20px;
    background: var(--secondary);
    color: var(--text-muted);
    margin-top: 60px;
}

footer a {
    color: var(--accent);
    text-decoration: none;
}

/* 响应式 */
@media (max-width: 768px) {
    header h1 {
        font-size: 1.8rem;
    }
    
    .articles-grid {
        grid-template-columns: 1fr;
    }
    
    .article-detail .content {
        padding: 20px;
        font-size: 1rem;
    }
    
    nav {
        gap: 10px;
    }
    
    .stats-bar {
        gap: 20px;
    }
}
"""
        
        with open(os.path.join(self.output_dir, "assets", "css", "style.css"), 'w', encoding='utf-8') as f:
            f.write(css_content)
        
        print("✅ CSS样式文件已生成")
    
    def generate_homepage(self, articles: List[Dict]):
        """生成首页"""
        # 统计数据
        total_articles = len(articles)
        sources = len(set(a['source'] for a in articles if a.get('source')))
        regions = len(set(a['region'] for a in articles if a.get('region')))
        
        # 最新文章
        latest_articles = articles[:8]
        latest_html = ""
        for article in latest_articles:
            summary = article.get('summary', '')[:120] + '...' if article.get('summary') else '暂无摘要'
            latest_html += f"""
                <article class="article-card" onclick="location.href='/articles/{article['id']}.html'">
                    <div class="article-meta">
                        <span class="source">{article.get('source', '未知来源')}</span>
                        <span>{article.get('publish_date', '未知日期')}</span>
                    </div>
                    <h2>{article.get('title', '无标题')}</h2>
                    <p class="summary">{summary}</p>
                    <div class="tags">
                        {f'<span class="tag">{article.get("region", "")}</span>' if article.get('region') else ''}
                        {f'<span class="tag">{article.get("drone_type", "")}</span>' if article.get('drone_type') else ''}
                    </div>
                    <a href="/articles/{article['id']}.html" class="read-more">阅读全文 →</a>
                </article>
            """
        
        timestamp_comment = get_timestamp_comment()
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="无人机前沿情报系统 - 实时采集全球无人机行业最新资讯">
    <meta name="keywords" content="无人机, UAV, 无人机资讯, 行业动态">
    <title>无人机前沿情报系统</title>
    <link rel="stylesheet" href="/assets/css/style.css">
</head>
<body>
    <header>
        <h1>🚁 无人机前沿情报系统</h1>
        <p class="subtitle">实时采集全球无人机行业最新资讯</p>
    </header>
    
    <nav>
        <a href="/">首页</a>
        <a href="/list.html">全部资讯</a>
        <a href="/region.html">按区域</a>
        <a href="/type.html">按类型</a>
    </nav>
    
    <div class="stats-bar">
        <div class="stat-item">
            <div class="stat-number">{total_articles}</div>
            <div class="stat-label">最新资讯</div>
        </div>
        <div class="stat-item">
            <div class="stat-number">{sources}</div>
            <div class="stat-label">数据来源</div>
        </div>
        <div class="stat-item">
            <div class="stat-number">{regions}</div>
            <div class="stat-label">覆盖区域</div>
        </div>
    </div>
    
    <div class="container">
        <h2 style="margin-bottom: 20px; color: var(--accent);">最新资讯</h2>
        <div class="articles-grid">
            {latest_html}
        </div>
        
        <div style="text-align: center; margin-top: 40px;">
            <a href="/list.html" class="read-more" style="font-size: 1.1rem;">查看更多资讯 →</a>
        </div>
    </div>
    
    <footer>
        <p>© 2024 无人机前沿情报系统 | 数据每日自动更新</p>
        <p style="margin-top: 10px;">
            <a href="/list.html">全部资讯</a> | 
            <a href="/rss.xml">RSS订阅</a> | 
            <a href="/api.html">API接口</a>
        </p>
    </footer>
</body>
</html>{timestamp_comment}"""
        
        with open(os.path.join(self.output_dir, "index.html"), 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"✅ 首页已生成，包含 {len(latest_articles)} 篇最新文章")
    
    def generate_article_list(self, articles: List[Dict], page: int = 1):
        """生成文章列表页"""
        total_pages = (len(articles) + self.articles_per_page - 1) // self.articles_per_page
        start_idx = (page - 1) * self.articles_per_page
        end_idx = start_idx + self.articles_per_page
        page_articles = articles[start_idx:end_idx]
        
        articles_html = ""
        for article in page_articles:
            summary = article.get('summary', '')[:120] + '...' if article.get('summary') else '暂无摘要'
            articles_html += f"""
                <article class="article-card" onclick="location.href='/articles/{article['id']}.html'">
                    <div class="article-meta">
                        <span class="source">{article.get('source', '未知来源')}</span>
                        <span>{article.get('publish_date', '未知日期')}</span>
                    </div>
                    <h2>{article.get('title', '无标题')}</h2>
                    <p class="summary">{summary}</p>
                    <div class="tags">
                        {f'<span class="tag">{article.get("region", "")}</span>' if article.get('region') else ''}
                        {f'<span class="tag">{article.get("drone_type", "")}</span>' if article.get('drone_type') else ''}
                    </div>
                    <a href="/articles/{article['id']}.html" class="read-more">阅读全文 →</a>
                </article>
            """
        
        # 生成分页
        pagination_html = ""
        if total_pages > 1:
            pagination_html += f'<a href="/list.html">首页</a>'
            
            for p in range(1, total_pages + 1):
                if p == page:
                    pagination_html += f'<span class="current">{p}</span>'
                else:
                    pagination_html += f'<a href="/list-{p}.html">{p}</a>'
            
            if page < total_pages:
                pagination_html += f'<a href="/list-{page + 1}.html">下一页</a>'
        
        timestamp_comment = get_timestamp_comment()
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="无人机资讯列表 - 查看所有无人机行业最新资讯">
    <title>全部资讯 - 无人机前沿情报系统</title>
    <link rel="stylesheet" href="/assets/css/style.css">
</head>
<body>
    <header>
        <h1>📰 全部资讯</h1>
        <p class="subtitle">共 {len(articles)} 篇资讯</p>
    </header>
    
    <nav>
        <a href="/">首页</a>
        <a href="/list.html">全部资讯</a>
        <a href="/region.html">按区域</a>
        <a href="/type.html">按类型</a>
    </nav>
    
    <div class="container">
        <div class="articles-grid">
            {articles_html}
        </div>
        
        <div class="pagination">
            {pagination_html}
        </div>
    </div>
    
    <footer>
        <p>© 2024 无人机前沿情报系统 | 数据每日自动更新</p>
    </footer>
</body>
</html>{timestamp_comment}"""
        
        if page == 1:
            with open(os.path.join(self.output_dir, "list.html"), 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"✅ 文章列表页已生成（第1页，共{total_pages}页）")
        else:
            with open(os.path.join(self.output_dir, f"list-{page}.html"), 'w', encoding='utf-8') as f:
                f.write(html)
    
    def generate_article_detail(self, article: Dict):
        """生成文章详情页"""
        content = article.get('content') or ''
        summary = article.get('summary') or ''
        title = article.get('title', '无标题')
        source = article.get('source', '未知来源')
        url = article.get('url', '')
        
        display_parts = []
        
        if content and content.strip():
            display_parts.append(content)
        elif summary and summary.strip():
            display_parts.append(f"<h3>文章摘要</h3>\n<p>{summary}</p>")
        
        if not content or not content.strip():
            if url:
                display_parts.append(f'<p style="margin-top: 20px;"><a href="{url}" target="_blank" style="color: var(--accent);">🔗 阅读原文 →</a></p>')
            else:
                display_parts.append('<p style="color: var(--text-muted); margin-top: 20px;">暂无详细内容</p>')
        
        display_content = '\n'.join(display_parts)
        
        timestamp_comment = get_timestamp_comment()
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{summary[:150]}">
    <title>{title} - 无人机前沿情报系统</title>
    <link rel="stylesheet" href="/assets/css/style.css">
</head>
<body>
    <header>
        <nav style="background: var(--primary); padding: 10px 20px; text-align: left;">
            <a href="/" style="color: var(--accent);">← 返回首页</a>
        </nav>
    </header>
    
    <article class="article-detail">
        <header>
            <h1>{title}</h1>
            <div class="meta">
                <span>📰 {source}</span>
                <span>📅 {article.get('publish_date', '未知日期')}</span>
                {f'<span>🌍 {article.get("region", "")}</span>' if article.get('region') else ''}
                {f'<span>🛸 {article.get("drone_type", "")}</span>' if article.get('drone_type') else ''}
                {f'<span>🏢 {article.get("company", "")}</span>' if article.get('company') else ''}
            </div>
        </header>
        
        <div class="content">
{display_content}
        </div>
        
        <a href="/list.html" class="back-link">← 返回资讯列表</a>
    </article>
    
    <footer>
        <p>© 2024 无人机前沿情报系统 | 数据每日自动更新</p>
    </footer>
</body>
</html>{timestamp_comment}"""
        
        filename = f"{article['id']}.html"
        with open(os.path.join(self.output_dir, "articles", filename), 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"✅ 文章详情页已生成: {article['title'][:30]}...")
    
    def generate_all(self):
        """生成所有静态页面"""
        print("🚀 开始生成静态网站...")
        print("=" * 50)
        
        # 生成基础模板
        self.generate_base_templates()
        
        # 获取文章
        articles = self._get_articles(limit=200, days=90)
        print(f"📰 获取到 {len(articles)} 篇资讯")
        
        if not articles:
            print("⚠️ 没有文章数据，跳过生成")
            return
        
        # 生成首页
        self.generate_homepage(articles)
        
        # 生成分页列表
        total_pages = (len(articles) + self.articles_per_page - 1) // self.articles_per_page
        for page in range(1, total_pages + 1):
            self.generate_article_list(articles, page)
        
        # 生成文章详情
        for article in articles[:50]:  # 限制生成前50篇详情页
            self.generate_article_detail(article)
        
        print("=" * 50)
        print(f"✨ 静态网站生成完成！")
        print(f"📁 输出目录: {self.output_dir}")
        print(f"📄 首页: {self.output_dir}/index.html")
        print(f"📰 列表: {self.output_dir}/list.html")


if __name__ == "__main__":
    generator = StaticSiteGenerator()
    generator.generate_all()
