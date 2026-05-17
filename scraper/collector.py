import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time
import random
import hashlib
import json
import re
from database.db import Database

class DataCollector:
    def __init__(self, db: Database):
        self.db = db
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }

    def generate_simhash(self, text: str) -> str:
        if not text:
            return ""
        hash_obj = hashlib.md5(text.encode('utf-8'))
        return hash_obj.hexdigest()

    def collect_from_source(self, source: Dict) -> int:
        source_type = source.get('type', 'web')
        collected = 0

        try:
            if source_type == 'rss':
                collected = self._collect_rss(source)
            elif source_type == 'api':
                collected = self._collect_api(source)
            else:
                collected = self._collect_web(source)
        except Exception as e:
            print(f"Error collecting from {source.get('name')}: {e}")

        return collected

    def _collect_web(self, source: Dict) -> int:
        collected = 0
        base_url = source.get('url')
        selectors = source.get('selectors', {})

        try:
            response = requests.get(base_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'

            soup = BeautifulSoup(response.text, 'lxml')

            article_list = soup.select(selectors.get('list', 'article, .article, .post'))

            for article_elem in article_list:
                try:
                    title_elem = article_elem.select_one(selectors.get('title', 'h2, h3, .title'))
                    link_elem = article_elem.select_one(selectors.get('link', 'a'))
                    date_elem = article_elem.select_one(selectors.get('date', '.date, .time, time'))
                    content_elem = article_elem.select_one(selectors.get('content', '.content, .summary, p'))

                    if not title_elem or not link_elem:
                        continue

                    title = title_elem.get_text(strip=True)
                    url = link_elem.get('href', '')
                    if url and not url.startswith('http'):
                        url = base_url.rstrip('/') + '/' + url

                    if self.db.article_exists_by_url(url):
                        continue

                    content = content_elem.get_text(strip=True) if content_elem else ""
                    date_str = self._parse_date(date_elem.get_text(strip=True) if date_elem else "")

                    article = {
                        'title': title,
                        'url': url,
                        'content': content[:500] if content else "",
                        'source': source.get('name', ''),
                        'publish_date': date_str,
                        'region': source.get('region', '国内'),
                        'drone_type': None,
                        'company': self._extract_company(title + " " + content),
                        'simhash': self.generate_simhash(title + content)
                    }

                    if not self.db.article_exists_by_simhash(article['simhash']):
                        if self.db.insert_article(article):
                            collected += 1

                    time.sleep(random.uniform(1, 3))

                except Exception as e:
                    print(f"Error parsing article: {e}")
                    continue

        except Exception as e:
            print(f"Error fetching {base_url}: {e}")

        return collected

    def _collect_rss(self, source: Dict) -> int:
        collected = 0
        try:
            response = requests.get(source.get('url'), headers=self.headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'xml')
            items = soup.find_all('item')

            for item in items[:20]:
                try:
                    title = item.find('title')
                    link = item.find('link')
                    pubdate = item.find('pubDate')
                    description = item.find('description')

                    if not title or not link:
                        continue

                    title_text = title.get_text(strip=True)
                    url = link.get_text(strip=True)

                    if self.db.article_exists_by_url(url):
                        continue

                    description_text = description.get_text(strip=True) if description else ""
                    content = self._extract_text_from_html(description_text)
                    original_content = content
                    
                    content_encoded = item.find('content:encoded')
                    if content_encoded:
                        encoded_text = content_encoded.get_text(strip=True)
                        encoded_content = self._extract_text_from_html(encoded_text)
                        if len(encoded_content) > len(content):
                            content = encoded_content
                    
                    if len(content) < 150 and url:
                        try:
                            full_content = self._fetch_full_article(url)
                            if full_content and len(full_content) > len(content) and len(full_content) > 150:
                                content = full_content
                        except Exception as e:
                            pass
                    
                    cleaned_content = self._clean_content(content)
                    if len(cleaned_content) >= 30:
                        content = cleaned_content
                    else:
                        content = original_content if len(original_content) > 0 else content
                    
                    if len(content) < 30:
                        continue
                    
                    date_str = self._parse_date(pubdate.get_text(strip=True) if pubdate else "")
                    
                    image_url = self._extract_image_url(description)

                    article = {
                        'title': title_text,
                        'url': url,
                        'content': content[:2000] if content else "",
                        'image_url': image_url,
                        'source': source.get('name', ''),
                        'publish_date': date_str,
                        'region': source.get('region', '国内'),
                        'drone_type': None,
                        'company': self._extract_company(title_text + " " + content),
                        'simhash': self.generate_simhash(title_text + content)
                    }

                    if not self.db.article_exists_by_simhash(article['simhash']):
                        if self.db.insert_article(article):
                            collected += 1

                    time.sleep(random.uniform(0.5, 1.5))

                except Exception as e:
                    continue

        except Exception as e:
            print(f"Error collecting RSS from {source.get('name')}: {e}")

        return collected

    def _collect_api(self, source: Dict) -> int:
        collected = 0
        try:
            response = requests.get(source.get('url'), headers=self.headers, timeout=10)
            response.raise_for_status()

            data = response.json()
            items = data if isinstance(data, list) else data.get('articles', data.get('data', []))

            for item in items[:20]:
                try:
                    title = item.get('title', '')
                    url = item.get('url', item.get('link', ''))
                    content = item.get('content', item.get('description', ''))
                    date_str = item.get('publish_date', item.get('date', ''))

                    if not title or not url:
                        continue

                    if self.db.article_exists_by_url(url):
                        continue

                    article = {
                        'title': title,
                        'url': url,
                        'content': content[:500] if content else "",
                        'source': source.get('name', ''),
                        'publish_date': self._parse_date(date_str),
                        'region': source.get('region', '国内'),
                        'drone_type': None,
                        'company': self._extract_company(title + " " + content),
                        'simhash': self.generate_simhash(title + content)
                    }

                    if not self.db.article_exists_by_simhash(article['simhash']):
                        if self.db.insert_article(article):
                            collected += 1

                except Exception as e:
                    continue

        except Exception as e:
            print(f"Error collecting API from {source.get('name')}: {e}")

        return collected

    def _parse_date(self, date_str: str) -> str:
        if not date_str:
            return datetime.now().strftime('%Y-%m-%d')

        try:
            date_str = date_str.strip()

            formats = [
                '%Y-%m-%d',
                '%Y/%m/%d',
                '%Y年%m月%d日',
                '%Y-%m-%d %H:%M:%S',
                '%Y/%m/%d %H:%M:%S',
                '%a, %d %b %Y %H:%M:%S %z',
                '%d %b %Y %H:%M:%S',
            ]

            for fmt in formats:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.strftime('%Y-%m-%d')
                except:
                    continue

            months_cn = {
                '一月': '01', '二月': '02', '三月': '03', '四月': '04',
                '五月': '05', '六月': '06', '七月': '07', '八月': '08',
                '九月': '09', '十月': '10', '十一月': '11', '十二月': '12'
            }

            for cn, num in months_cn.items():
                if cn in date_str:
                    match = re.search(r'(\d{1,2})日?', date_str)
                    if match:
                        day = match.group(1).zfill(2)
                        year_match = re.search(r'(\d{4})年', date_str)
                        year = year_match.group(1) if year_match else datetime.now().year
                        return f"{year}-{num}-{day}"

        except:
            pass

        return datetime.now().strftime('%Y-%m-%d')

    def _extract_text_from_html(self, html_content: str) -> str:
        if not html_content:
            return ""
        
        soup = BeautifulSoup(html_content, 'lxml')
        
        for img in soup.find_all('img'):
            img.decompose()
        
        for script in soup.find_all('script'):
            script.decompose()
        
        for style in soup.find_all('style'):
            style.decompose()
        
        text = soup.get_text(separator=' ', strip=True)
        
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()

    def _extract_image_url(self, description_tag) -> Optional[str]:
        if not description_tag:
            return None
        
        try:
            description_text = description_tag.get_text(strip=True) if description_tag else ""
            
            soup = BeautifulSoup(description_text, 'html.parser')
            img_tag = soup.find('img')
            if img_tag and img_tag.get('src'):
                return img_tag['src']
            
            import re
            img_pattern = r'<img[^>]+src=["\']([^"\']+)["\']'
            match = re.search(img_pattern, description_text)
            if match:
                return match.group(1)
            
            media_pattern = r'https?://[^\s]+\.(jpg|jpeg|png|gif|webp)'
            match = re.search(media_pattern, description_text, re.IGNORECASE)
            if match:
                return match.group(0)
            
        except Exception as e:
            print(f"Error extracting image URL: {e}")
        
        return None

    def _fetch_full_article(self, url: str) -> Optional[str]:
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            content_selectors = [
                'article',
                '.article-content',
                '.post-content',
                '.entry-content',
                '#content',
                '.content',
                '.main-content',
                '.story-content',
                '.body-content',
                '.news-content'
            ]
            
            content = ""
            for selector in content_selectors:
                element = soup.select_one(selector)
                if element:
                    content = element.get_text(strip=False)
                    if len(content) > 200:
                        break
            
            if not content or len(content) < 200:
                paragraphs = soup.find_all('p')
                if paragraphs:
                    content = ' '.join([p.get_text(strip=True) for p in paragraphs[:10]])
            
            return content.strip() if content else None
            
        except Exception as e:
            print(f"Error fetching full article from {url}: {e}")
            return None

    def _clean_content(self, content: str) -> str:
        if not content:
            return ""
        
        content = re.sub(r'\s+', ' ', content)
        
        content = re.sub(r'[^\w\s\u4e00-\u9fff.,!?;:()\-\'\"<>/\\]', '', content)
        
        lines = content.split('.')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if len(line) > 5:
                cleaned_lines.append(line)
        
        content = '. '.join(cleaned_lines)
        
        if len(content) < 30:
            return ""
        
        return content.strip()

    def _extract_company(self, text: str) -> Optional[str]:
        companies = [
            '大疆创新', 'DJI', '大疆', '极飞科技', '极飞', '零度智控', '零度',
            '亿航智能', '亿航', '道通智能', '道通', '派诺特', 'Parrot',
            '3D Robotics', '3DR', 'Autel Robotics', 'Autel', 'Skydio',
            'Wing', 'Amazon Prime Air', 'Alphabet', 'Uber Elevate',
            '小米', '华为', '腾讯', '阿里', '百度'
        ]

        text_lower = text.lower()
        for company in companies:
            if company.lower() in text_lower:
                if company == 'DJI':
                    return '大疆创新'
                elif company == '3DR':
                    return '3D Robotics'
                return company

        return None

    def search_and_collect(self, keyword: str, max_results: int = 20) -> int:
        collected = 0
        search_url = f"https://www.bing.com/search?q={keyword}+无人机+UAV+drone&first=0"

        try:
            response = requests.get(search_url, headers=self.headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'lxml')
            results = soup.select('.b_algo h2 a')[:max_results]

            for result in results:
                try:
                    title = result.get_text(strip=True)
                    url = result.get('href', '')

                    if not url or 'http' not in url:
                        continue

                    if self.db.article_exists_by_url(url):
                        continue

                    article = {
                        'title': title,
                        'url': url,
                        'content': '',
                        'source': '搜索引擎',
                        'publish_date': datetime.now().strftime('%Y-%m-%d'),
                        'region': '国内' if 'cn' in url else '国外',
                        'drone_type': None,
                        'company': self._extract_company(title),
                        'simhash': self.generate_simhash(title)
                    }

                    if not self.db.article_exists_by_simhash(article['simhash']):
                        if self.db.insert_article(article):
                            collected += 1

                    time.sleep(random.uniform(2, 4))

                except Exception as e:
                    continue

        except Exception as e:
            print(f"Error searching: {e}")

        return collected

    def collect_all(self, sources: List[Dict]) -> Dict[str, int]:
        results = {}
        total = 0

        for source in sources:
            print(f"正在采集: {source.get('name')}...")
            count = self.collect_from_source(source)
            results[source.get('name')] = count
            total += count
            print(f"  完成: {count} 篇文章")

        results['total'] = total
        return results
