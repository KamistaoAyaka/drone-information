import re
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import jieba
from datetime import datetime

class DataCleaner:
    def __init__(self):
        self.noise_patterns = [
            r'分享到.*?(微博|微信|QQ|空间)',
            r'点击.*?查看更多',
            r'免责声明|版权声明|违法和不良信息举报',
            r'相关阅读|推荐阅读|热门推荐',
            r'广告|AD|Advertisement',
            r'登录|注册|立即注册|免费注册',
            r'关注.*?获取更多',
            r'扫码.*?下载',
            r'\d+年\d+月\d+日\s+\d+:\d+',
            r'作者：.*?|来源：.*?|责任编辑：.*?',
        ]

    def clean_html(self, html_content: str) -> str:
        if not html_content:
            return ""

        soup = BeautifulSoup(html_content, 'lxml')

        for tag in soup.find_all(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe']):
            tag.decompose()

        for tag in soup.find_all(class_=re.compile(r'(ad|advertisement|sidebar|menu|nav|comment|share|footer|header)', re.I)):
            tag.decompose()

        text = soup.get_text(separator=' ', strip=True)

        text = re.sub(r'\s+', ' ', text)

        for pattern in self.noise_patterns:
            text = re.sub(pattern, '', text, flags=re.I)

        return text.strip()

    def clean_text(self, text: str) -> str:
        if not text:
            return ""

        text = re.sub(r'<[^>]+>', '', text)

        text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', text)

        text = re.sub(r'[\u200b-\u200f\u2028-\u202f\ufeff]', '', text)

        text = re.sub(r'https?://\S+', '', text)

        text = re.sub(r'\s+', ' ', text)

        return text.strip()

    def extract_main_content(self, html: str) -> str:
        if not html:
            return ""

        soup = BeautifulSoup(html, 'lxml')

        content_tags = soup.find_all(['article', 'main', 'div'],
                                    class_=re.compile(r'(content|article|post|entry|body|text)', re.I))

        if content_tags:
            content = content_tags[0]
        else:
            paragraphs = soup.find_all('p')
            if paragraphs:
                content = '\n'.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 50])
            else:
                content = soup.get_text()

        return content

    def normalize_date(self, date_str: str) -> Optional[str]:
        if not date_str:
            return None

        date_str = date_str.strip()

        patterns = [
            (r'(\d{4})-(\d{1,2})-(\d{1,2})', '%Y-%m-%d'),
            (r'(\d{4})/(\d{1,2})/(\d{1,2})', '%Y/%m/%d'),
            (r'(\d{4})年(\d{1,2})月(\d{1,2})日', '%Y年%m月%d日'),
            (r'(\d{1,2})-(\d{1,2})-(\d{4})', '%m-%d-%Y'),
        ]

        for pattern, fmt in patterns:
            match = re.search(pattern, date_str)
            if match:
                try:
                    if '年' in fmt:
                        dt = datetime.strptime(date_str[:10], '%Y年%m月%d日')
                    else:
                        dt = datetime.strptime(match.group(0)[:10], fmt.replace('%', ''))
                    return dt.strftime('%Y-%m-%d')
                except:
                    continue

        return None

    def truncate_content(self, content: str, max_length: int = 500) -> str:
        if not content:
            return ""

        if len(content) <= max_length:
            return content

        truncated = content[:max_length]

        last_punct = max(truncated.rfind('。'), truncated.rfind('.'), truncated.rfind('!'), truncated.rfind('?'))
        if last_punct > max_length * 0.7:
            truncated = truncated[:last_punct + 1]

        return truncated + '...'

    def remove_duplicates_sentences(self, text: str) -> str:
        if not text:
            return ""

        sentences = re.split(r'[。！？\n]+', text)
        seen = set()
        unique_sentences = []

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            normalized = re.sub(r'\s+', '', sentence).lower()

            if normalized not in seen and len(sentence) > 10:
                seen.add(normalized)
                unique_sentences.append(sentence)

        return '。'.join(unique_sentences) + '。' if unique_sentences else text

    def clean_article(self, article: Dict) -> Dict:
        cleaned = article.copy()

        if 'content' in cleaned and cleaned['content']:
            cleaned['content'] = self.clean_text(cleaned['content'])
            cleaned['content'] = self.truncate_content(cleaned['content'])

        if 'title' in cleaned and cleaned['title']:
            cleaned['title'] = self.clean_text(cleaned['title'])

        if 'publish_date' in cleaned:
            cleaned['publish_date'] = self.normalize_date(cleaned['publish_date']) or cleaned.get('publish_date', '')

        return cleaned

    def batch_clean(self, articles: List[Dict]) -> List[Dict]:
        return [self.clean_article(article) for article in articles]
